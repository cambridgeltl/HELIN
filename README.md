# Entity Linking Demo

This repository contains a web API demo for performing entity linking on biomedical text.

The demo is based on:
- A Flask web server;
- The NER module from [this paper](https://github.com/basaldella/bioreddit);
- The Entity Linking code from [COMETA](https://arxiv.org/abs/2010.03295) and [SAPBERT](https://arxiv.org/abs/2010.11784)
- A Docker container that runs the server.

## Running the demo

To run the demo you must:
- Install Docker;
- Clone this repo;
- Get a copy of SNOMED and place the `Snapshot` folder inside it in `src/static/snomed`;
- Open a terminal and navigate into the `docker-scripts` directory;
- Run `./build_image.sh`;
- Run `./start_container.sh -s`.

This will start a Flask server within the Docker container listening on port 5000.
If you open [http://localhost:5000]() you should see the welcome page with a link to a simple api call.

**NOTE**: the first run will take a while to encode SNOMED labels. Subsequent runs will be much quicker to start 
and should use much less RAM.