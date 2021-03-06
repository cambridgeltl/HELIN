# Entity Linking Demo

This repository contains a web API demo for performing entity linking on biomedical text. 

The demo is based on:
- A Flask web server;
- The NER module from [Bioreddit](https://www.aclweb.org/anthology/D19-6205/) ([repo](https://github.com/basaldella/bioreddit));
- The Entity Linking code from [COMETA](https://arxiv.org/abs/2010.03295) and [SAPBERT](https://arxiv.org/abs/2010.11784) ([repo](https://github.com/cambridgeltl/cometa));
- A Docker container that runs the server.

Note that the NER system is trained on general-purpose text from a health-themed online forum, so it's not recommended to use this 
system to perform biomedical NER/EL on medical data.

## Running the demo

> Note: the first run of the demo requires 64 GB RAM to build the embedding matrix. If your webserver has less RAM, 
please see section "Pretraining SNOMED embeddings".

To run the demo you must:
- Install Docker;
- Clone this repo;
- Get a copy of SNOMED and place the `Snapshot` folder inside it in `src/static/snomed`;
- Open a terminal and navigate into the `docker-scripts` directory;
- Run `./build_image.sh`;
- Run `./start_container.sh -s`.

This will start a Flask server within the Docker container listening on port 5000.
If you open [http://localhost:5000]() you should see the welcome page with a link to a simple api call.

The API can be accessed by doing simple HTTP requests, using both a browser or whatever software you prefer. 
We provide a single endpoint, `tag_string`, with a single parameter `txt`. The call returns a JSON response with the
detected entities and for each entity an unique ID, the NER type, its span, the SCTID of the linked SNOMED Entity, \
and the name of the linked SNOMED entity.

For example, a call to:
```http://127.0.0.1:5000/tag_string?txt='Today I woke up with migraine and I took an aspirine.'```
Will return
```json
{
  "entities": [
    [
      "T1",
      "Phenotype",
      [
        [
          22,
          30
        ]
      ],
      "Migraine",
      "SCTID: 37796009"
    ],
    [
      "T2",
      "Molecule",
      [
        [
          45,
          53
        ]
      ],
      "Aspirin",
      "SCTID: 387458008"
    ]
  ],
  "text": "'Today I woke up with migraine and I took an aspirine.'"
}
```

As you see, the engine recognises the entities `migraine` and `aspirine` (even if misspelled) and links them to SNOMED.

**NOTE**: the first run will take a while to encode SNOMED labels. Subsequent runs will be much quicker to start 
and should use much less RAM; in our tests, the webserver should run just fine with 8 GB RAM.

## Pretraining SNOMED embeddings

The first run encodes all the SNOMED labels in a big matrix using our flavour of BERT, called SapBERT. This requires about
64 GB or RAM and ~1 hour on an 8-core Intel Core i7-7700K CPU @ 4.20GHz. Please note that this is based on the current version 
of SNOMED at the time of writing (early 2021); newer version of SNOMED, with more concepts, might require more RAM.

If your webserver doesn't have enough resources to build the embedding matrix you can build it on another machine, and then 
transfer it manually to the webserver. You will only need to move the cache file `src/static/snomed/snomed.npz`.

## Technical Tidbits

### Using the tagger without the webserver

You can also use the tagger without having to start the whole webserver. The usage is straightforward:

```python
from tagger import Tagger

tagger = Tagger()
text, entities = tagger.tag("I have headache")
```

The dependencies are the ones listed in `docker-scripts/requirements.txt` (minus Flask and Gunicorn) and the file `Snomed.py`.

### Named Entity Recognition

The Named Entity Recognition model is based on [Flair](https://github.com/flairNLP/flair) and it's trained on a private dataset
from [HealthUnlocked](https://healthunlocked.com/). The model is automatically downloaded from Google Drive. If the download fails, 
or if you prefer downloading the model yourself, you can find it in the Releases section of this repository, or you can get it
from [here](https://github.com/cambridgeltl/hdr-entity-linking-demo/releases/download/v0.1-beta/best-model.pt). Please download the 
file and copy it in `src/static/models`.

### Query Cache 

The webserver caches the last 4096 EL queries using Python's `lru_cache` (see documentation [here](https://docs.python.org/3/library/functools.html#functools.lru_cache)). You can increase or decrease the cache size by changing the variable `EL_CACHE_SIZE` in 
`src/tagger.py`.

### Tokens used

The EL system tokenises the candidate entity and the SNOMED labels using BERT's wordpiece tokenizer. To keep the embedding matrix 
small, we use 8 tokens to embed SNOMED concepts and candidate entities. You can increase or decrease this value by changing the 
variable `NUM_TOKENS` in `src/tagger.py`.

### Approximate Search

The system works by finding the concept in SNOMED with the closest embedding to the candidate token. To speed the search, we use
Facebook's Faiss library. We use the [faster](https://github.com/facebookresearch/faiss/wiki/Faster-search) search, which allows
us to lookup the entire SNOMED space in ~0.1 seconds (on an Intel Core i7-7700K). However, this lookup is based on an approximate
search and might cause misses in some edge cases. If the library consistently fails to find the correct concept, you can disable 
approximate search in `src/tagger.py` by uncommenting the relative code and commenting out the approximate search. However, this
search did not cause any issues in our experiments.

### Server Performance & Security

Please be aware that this project is to be regarded as a technical demo only and it not meant to be production ready. The server
uses Flask's development server; to enhance performance and security, you should choose one of Flask's 
[deployment options](https://flask.palletsprojects.com/en/1.1.x/deploying/).

Please be aware that **you should not have any expectation of security or performance** by using the provided development server.

### Docker

The container is based on Ubuntu 20.04. The provided scripts should be enough to build and launch the image; the code should be
pretty self-explanatory. Some things of note are:
- The image uses Python 3.7. This is mandatory due to the fact that later versions of Python are not supported by PyTorch at the
time of writing. Do not force Python 3.8+ for any reason.
- To start the container, you have three options:
  - `./start_container.sh -s`: Starts the container and the web service.
  - `./start_container.sh -d`: Starts the container and the web service, but in detached mode.
  - `./start_container.sh -i`: Starts the container and starts a bash console.
  The script will automatically mount the folder with the code. **DO NOT MOVE FILES AROUND** or the service will break.
- The other scripts are mainly for maintanance and are used to shut down the service (`remove_container.sh`) and to log into the 
container when started in detached mode (`login_running_container.sh`). 
