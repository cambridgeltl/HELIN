from flair.data import Sentence
from flair.models import SequenceTagger
from functools import lru_cache
from google_drive_downloader import GoogleDriveDownloader as gdd
from segtok.segmenter import split_single
from Snomed import Snomed
from tqdm import tqdm
from transformers import AutoTokenizer, AutoModel

import faiss
import os
import numpy as np

NUM_TOKENS = 8
EL_CACHE_SIZE = 4096
BATCH_SIZE = 128
DEFAULT_MODEL_PATH = 'static/models/best-model.pt'
DEFAULT_SNOMED_PATH = 'static/snomed'


class Tagger:

    def __init__(self, model_path=DEFAULT_MODEL_PATH, snomed_path=DEFAULT_SNOMED_PATH):
        """
        Initialises the tagger.

        :param model_path: the path of the NER model.
        :param snomed_path: the path of the SNOMED model.
        """
        print("Loading tagger...")

        if not os.path.isfile(model_path):
            print('Warning: the provided model does not exist! Downloading default model...')

            os.makedirs('static/models', exist_ok=True)
            gdd.download_file_from_google_drive(file_id='1pZ9oMPuUnZp6IiBv-TBh-LlYdHZg-3Oa',
                                                dest_path=DEFAULT_MODEL_PATH,
                                                )

        self.ner_model = SequenceTagger.load(model_path)
        self.el_model = None
        self.tokenizer = None
        self.snomed_surface_index_pairs = []
        self.index = None

        print('Loading SNOMED...')
        self.snomed = Snomed(snomed_path)
        self.snomed.load_snomed()
        self.build_normalizer()
        print('Tagger ready.')

    def build_normalizer(self):
        """
        Loads the entity linking model and builds the index used for similarity lookup.
        """

        print('Loading SNOMED definitions...')

        for snomed_id in tqdm(self.snomed.graph.nodes):

            node_descs = self.snomed.index_definition[snomed_id]
            for d in node_descs:
                self.snomed_surface_index_pairs.append((d, snomed_id))

        all_names = [p[0] for p in self.snomed_surface_index_pairs]

        self.tokenizer = AutoTokenizer.from_pretrained(
            "cambridgeltl/SapBERT-from-PubMedBERT-fulltext",
            use_fast=True)
        self.el_model = AutoModel.from_pretrained("cambridgeltl/SapBERT-from-PubMedBERT-fulltext")

        all_reps = []

        cache_path = os.path.join(DEFAULT_SNOMED_PATH, 'snomed')

        if os.path.exists(str(cache_path) + '.npz'):

            print('Loading cache...')
            all_reps_emb = np.load(str(cache_path) + '.npz')['snomed_encoded']

        else:
            for i in tqdm(np.arange(0, len(all_names), BATCH_SIZE), desc='Encoding SNOMED labels'):
                toks = self.tokenizer.batch_encode_plus(all_names[i:i + BATCH_SIZE],
                                                        padding="max_length",
                                                        max_length=NUM_TOKENS,
                                                        truncation=True,
                                                        return_tensors="pt")
                output = self.el_model(**toks)
                cls_rep = output[0][:, 0, :]

                all_reps.append(cls_rep.cpu().detach().numpy())

            all_reps_emb = np.concatenate(all_reps, axis=0)
            np.savez_compressed(cache_path, snomed_encoded=all_reps_emb)

        # initialise Faiss index

        # Basic index:
        # self.index = faiss.IndexFlatL2(all_reps_emb.shape[1])
        # self.index.add(all_reps_emb)

        # Quicker index:
        d = all_reps_emb.shape[1]
        quantizer = faiss.IndexFlatL2(d)  # the other index
        self.index = faiss.IndexIVFFlat(quantizer, d, 100)
        self.index.train(all_reps_emb)
        self.index.add(all_reps_emb)
        self.index.nprobe = 10

    def normalize(self, query):
        """
        Wrapper for the actual normalisation function; it just brings the string to lowercase
        and strips it of whitespaces. This allows to reduce the cache size since similar queries
        ("headache" vs "Headache") will be conflated.

        :param query: the string to normalise.
        :return: an (entity_name, entity_id) pair.
        """
        query = query.strip().lower()
        return self.normalize_cached(query)

    @lru_cache(maxsize=EL_CACHE_SIZE)
    def normalize(self, query):
        """
        Normalisation function. Gets a string an finds the closest SNOMED concept. The function result
        is cached so that subsequent calls to the function with the same query should be quicker.

        :param query: the string to normalise.
        :return: an (entity_name, entity_id) pair.
        """

        # tokenise the query
        query_toks = self.tokenizer.encode_plus(query,
                                                padding="max_length",
                                                max_length=NUM_TOKENS,
                                                truncation=True,
                                                return_tensors="pt")

        # get the output
        query_output = self.el_model(**query_toks)
        query_cls_rep = query_output[0][:, 0, :].cpu().detach().numpy()

        # get the index of the closest vector
        nn_index = self.index.search(query_cls_rep, 1)[1][0][0]
        return self.snomed_surface_index_pairs[nn_index]

    def tag(self, text):
        """
        Finds the entities in a string and normalises them to SNOMED.

        :param text: the string to tag.
        :return: a (`text`, `entities`) pair, where `text` is the original, stripped text, and `entities` is the list
        of entities found in the text.
        """

        text = text.strip()
        # split into sentences
        sentences = [sent for sent in split_single(text)]
        entities = []

        i = 1

        for sentence in sentences:
            # find the entities in the sentence using Flair
            offset = text.index(sentence)
            sentence = Sentence(sentence, use_tokenizer=True)
            self.ner_model.predict(sentence)

            for ent in sentence.get_spans('ner'):

                # for each entity, normalise it to SNOMED and return it
                snomed_name, snomed_id = self.normalize(ent.text)
                snomed_id = 'SCTID: ' + snomed_id

                entities.append([
                    'T' + str(i),
                    ent.tag,
                    [[ent.start_pos + offset, ent.end_pos + offset]],
                    snomed_name,
                    snomed_id
                ])
                i += 1

        return text, entities
