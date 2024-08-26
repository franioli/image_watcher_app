# Image Watcher App

This is a simple app that continuously observe one or multiple direcotries and run some operations as soon as an image is added to the directory.

Currentely, the app can only resize the image to a fixed size and save it to a different directory. Other actions will be added (e.g., upload to a cloud storage, include other image processing operations).
If you want to configure a new operation, just create a new ordinary function (check the file `resize_image.py` for reference) and then add the corresponding method to the observer (check the file `observers.py` for reference).

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
   conda create -n image_watcher_app python=3.8
   conda activate image_watcher_app
   ```

Install the required packages:

```bash
pip install -r requirements.txt
```

Start the app with the following command:

```bash
python app
```

The app will be available at `http://localhost:8000`.

2. Install with Docker

   Run the following command to build the docker image with docker compose and start the app:

   ```bash
   docker compose up
   ```

   The app will be available at `http://localhost:9500` (Port 9500 is used to avoid conflicts with other services that may be running on port 8000. but you can change it in the `docker-compose.yml` file).

## Usage

For using the app, remeber to set the configuration in the `config.yaml` file. Then, run the app and add the directories you want to observe.
