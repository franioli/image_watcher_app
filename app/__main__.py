import logging
import threading
import time

from config import settings
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from observers import start_observer

logger = logging.getLogger()

# FastAPI app setup
app = FastAPI()

# Setup Jinja2 templates
templates = Jinja2Templates(directory="templates")

# Dictionary to store image handlers and their respective observers
image_handlers = {}
observers = {}


# Function to start all observers based on the configuration
def start_all_observers():
    for i, directory_config in enumerate(settings.watch_directories):
        observer, handler = start_observer(
            watch_directory=directory_config.watch,
            output_directory=directory_config.output,
        )

        # Store the observer and handler with a unique key
        observers[i] = observer
        image_handlers[i] = handler

        # Mount static files for each output directory
        route_name = f"resized-images-{i}"
        app.mount(
            f"/{route_name}",
            StaticFiles(directory=str(directory_config.output)),
            name=route_name,
        )


# API Routes
@app.get("/")
def read_root():
    images_by_directory = {}
    for i, directory_config in enumerate(settings.watch_directories):
        route_name = f"resized-images-{i}"
        image_files = list(directory_config.output.glob("*.*"))
        images = [f"/{route_name}/{image.name}" for image in image_files]
        images_by_directory[i] = images  # Use i as the key to map to the directory

    return templates.TemplateResponse(
        "index.html", {"request": {}, "images_by_directory": images_by_directory}
    )


@app.get("/images/{dir_id}/{image_name}")
async def get_image(dir_id: str, image_name: str):
    try:
        directory_config = settings.watch_directories[int(dir_id)]
        image_path = directory_config.output / image_name
        if image_path.exists():
            return FileResponse(image_path)
        else:
            raise HTTPException(status_code=404, detail="Image not found")
    except IndexError:
        raise HTTPException(status_code=400, detail="Invalid directory ID")


@app.get("/image-list/{dir_id}")
async def get_image_list(dir_id: str):
    try:
        directory_config = settings.watch_directories[int(dir_id)]
        images = sorted([f for f in directory_config.output.iterdir() if f.is_file()])

        if settings.dashboard.display_last_n_images > 0:
            images = images[-settings.dashboard.display_last_n_images :]

        images = reversed(images)
        image_urls = [f"/images/{dir_id}/{image.name}" for image in images]
        return {"image_urls": image_urls}
    except IndexError:
        raise HTTPException(status_code=400, detail="Invalid directory ID")


@app.get("/process-status/{dir_id}")
def process_status(dir_id: int):
    try:
        handler = image_handlers[dir_id]
        status_info = handler.get_status()
        return status_info
    except (IndexError, KeyError):
        raise HTTPException(status_code=400, detail="Invalid directory ID")


@app.get("/log")
def read_log():
    try:
        return FileResponse(settings.log.file)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/directory-count")
def get_directory_count():
    count = len(settings.watch_directories)
    return {"directory_count": count}


if __name__ == "__main__":
    import uvicorn

    # Start all observers before launching the server
    start_all_observers()

    # Start Uvicorn server
    server_thread = threading.Thread(
        target=lambda: uvicorn.run(
            app, host=settings.dashboard.host, port=settings.dashboard.port
        )
    )
    server_thread.start()

    # Wait a moment to ensure the server is up before starting processing
    time.sleep(2)

    # Process existing images if configured
    if settings.proc.process_on_start:
        for handler in image_handlers.values():
            handler.process_existing_images()
