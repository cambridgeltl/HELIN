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

BATCH_SIZE = 128
DEFAULT_MODEL_PATH = 'static/models/best-model.pt'
DEFAULT_SNOMED_PATH = 'static/snomed'


class Tagger:

    def __init__(self, model_path=DEFAULT_MODEL_PATH, snomed_path=DEFAULT_SNOMED_PATH):
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
        self.snomed = Snomed(DEFAULT_SNOMED_PATH)
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
            print('Encoding labels..')
            for i in tqdm(np.arange(0, len(all_names), BATCH_SIZE)):
                toks = self.tokenizer.batch_encode_plus(all_names[i:i + BATCH_SIZE],
                                                        padding="max_length",
                                                        max_length=8,
                                                        truncation=True,
                                                        return_tensors="pt")
                output = self.el_model(**toks)
                cls_rep = output[0][:, 0, :]

                all_reps.append(cls_rep.cpu().detach().numpy())

            all_reps_emb = np.concatenate(all_reps, axis=0)
            np.savez_compressed(cache_path, snomed_encoded=self.all_reps_emb)

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
        query = query.strip().lower()
        return self.normalize_cached(query)

    @lru_cache(maxsize=4096)
    def normalize(self, query):

        query_toks = self.tokenizer.encode_plus(query,
                                                padding="max_length",
                                                max_length=8,
                                                truncation=True,
                                                return_tensors="pt")

        query_output = self.el_model(**query_toks)
        query_cls_rep = query_output[0][:, 0, :].cpu().detach().numpy()

        nn_index = self.index.search(query_cls_rep, 1)[1][0][0]
        return self.snomed_surface_index_pairs[nn_index]

    def tag(self, text):
        text = text.strip()

        sentences = [sent for sent in split_single(text)]

        entities = []

        i = 1

        for sentence in sentences:
            offset = text.index(sentence)
            sentence = Sentence(sentence, use_tokenizer=True)
            self.ner_model.predict(sentence)

            for ent in sentence.get_spans('ner'):

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