# Image Watcher App

This is a simple app that continuously observe one or multiple directories and run some operations as soon as an image is added to the directory.

Currently, the app can only resize the image to a fixed size and save it to a different directory. Other actions will be added (e.g., upload to a cloud storage, include other image processing operations).
If you want to configure a new operation, just create a new ordinary function (check the file [resize_image.py](app/resize_image.py) for reference) and then add the corresponding method in the observer (check the file [observers.py](app/observers.py) for reference).

A simple frontend built with Fast API is also provided to show the status of all the observers and the images that have been processed.

The app is dockerized and can be run in a small container in order to be constantly running.

## Installation

1. Install locally for development purposes

   Clone the repository and install the required packages

   ```bash
   git clone https://github.com/franioli/image_watcher_app.git
   cd image_watcher_app
   ```

   Create a virtual environment with venv or conda:

   ```bash
   python -m venv venv
   source venv/bin/activate
   ```

   or

   ```bash
   conda create -n image_watcher_app python=3.12
   conda activate image_watcher_app
   ```

   Install the required packages:

   ```bash
   pip install -r requirements.txt
   ```

   For using the app, set the configuration in the `config.yaml` file.
   The `config.yaml` file is already set with the default values, but you can change it as you want.

   **Note**: The `config.yaml` file must be in the root directory of the cloned repo.

   **Note2**: If you are running the app locally, set the path to the directories you want to observe as for your local machine.

   Then, run the app and add the directories you want to observe with the following command:

   ```bash
   python app
   ```

   The app will be available at `http://localhost:9500`.

2. Install with Docker

   Set the configuration in the `config.yaml` file as you want.

   **Note**: the path must start with '/data/', as this is where the directories are mounted in the container. 

   Set the path to volume to be mounted as '/data/' in the container `docker-compose.yml` file (this is the path with the directories to be observed).

   Run the following command to build the docker image with docker compose and start the app:

   ```bash
   docker compose up
   ```

   The app will be available at `http://localhost:9500` (Port 9500 is used to avoid conflicts with other services, but you can change it in the `config.yaml`, `Dockerfile` and `docker-compose.yml` file. Remember to change all the files!).
