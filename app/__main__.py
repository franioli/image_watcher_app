import logging
import threading
import time
from pathlib import Path

from config import settings
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from processor import image_handler

logger = logging.getLogger()

# FastAPI app setup
app = FastAPI()

# Serve the resized images and logs as static files
app.mount(
    "/resized-images",
    StaticFiles(directory=str(settings.resized_directory)),
    name="resized-images",
)

# Setup Jinja2 templates
templates = Jinja2Templates(directory="templates")


@app.get("/")
def read_root():
    image_files = list(Path(settings.resized_directory).glob("*.*"))
    images = [f"/resized-images/{image.name}" for image in image_files]
    return templates.TemplateResponse("index.html", {"request": {}, "images": images})


@app.get("/images/{image_name}")
async def get_image(image_name: str):
    image_path = settings.resized_directory / image_name
    if image_path.exists():
        return FileResponse(image_path)
    return {"error": "Image not found"}


@app.get("/image-list")
async def get_image_list():
    images = sorted([f for f in settings.resized_directory.iterdir() if f.is_file()])
    image_urls = [f"/images/{image.name}" for image in images]
    return {"image_urls": image_urls}


@app.get("/process-status")
def process_status():
    status_info = image_handler.get_status()
    # Include configuration details
    status_info.update(
        {
            "watch_directory": str(settings.watch_directory),
            "resized_directory": str(settings.resized_directory),
        }
    )
    return status_info


@app.get("/log")
def read_log():
    try:
        return FileResponse(settings.log_file)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def start_image_processing():
    if settings.process_on_start:
        image_handler.process_existing_images()


if __name__ == "__main__":
    import uvicorn

    # Start Uvicorn server
    server_thread = threading.Thread(
        target=lambda: uvicorn.run(app, host="0.0.0.0", port=8000)
    )
    server_thread.start()

    # Wait a moment to ensure the server is up before starting processing
    time.sleep(2)

    # Start image processing
    start_image_processing()
