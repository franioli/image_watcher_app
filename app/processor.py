import logging
import threading
import time
from pathlib import Path

from config import settings
from resize_image import resize
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

logger = logging.getLogger()


class FileHandler(FileSystemEventHandler):
    def __init__(self):
        self.processed_images = 0
        self.failed_images = 0
        self.total_images = len(list(settings.watch_directory.glob("*.*")))

        # Initialize the image map to store the original and resized image paths
        self.image_map = {
            str(file_path): str(settings.resized_directory / file_path.name)
            for file_path in settings.watch_directory.glob("*.*")
        }

        if settings.remove_on_delete:
            logger.info("Images will be deleted on file delete event.")

    def process_existing_images(self):
        logger.info("Processing existing images...")
        for file_path in settings.watch_directory.glob("*.*"):
            if settings.skip_existing:
                if str(file_path) in self.image_map:
                    logger.info(f"Skipping existing image: {file_path}")
                    continue
            self.process_image(file_path)

    def on_created(self, event):
        if not event.is_directory:
            self.process_image(event.src_path)

    def on_modified(self, event):
        if not event.is_directory:
            self.process_image(event.src_path)

    def on_moved(self, event):
        if not event.is_directory:
            # Handle the move event by processing the new file path
            self.process_image(event.dest_path)

    def on_deleted(self, event):
        if not event.is_directory and settings.remove_on_delete:
            self.delete_file(event.src_path)

    def process_image(self, file_path):
        file_path = Path(file_path)
        if file_path.suffix.lower() in settings.image_extensions:
            logger.info(f"Processing image: {file_path}...")
            try:
                resized_file_path = resize(
                    file_path, settings.resized_directory, settings.w_max
                )
                self.image_map[str(file_path)] = str(resized_file_path)
                self.processed_images += 1
                logger.info(f"Resized image saved: {resized_file_path}")

            except Exception as e:
                logger.error(f"Failed to process image {file_path}: {e}")
                self.failed_images += 1

    def delete_file(self, file_path):
        file_path = Path(file_path)
        file_to_remove = self.image_map.pop(str(file_path), None)
        if file_to_remove:
            resized_path = Path(file_to_remove)
            if resized_path.exists():
                try:
                    resized_path.unlink()  # Delete the resized image
                    logger.info(f"Deleted resized image: {file_to_remove}")
                except Exception as e:
                    logger.error(
                        f"Failed to delete resized image {file_to_remove}: {e}"
                    )

    def get_status(self):
        self.total_images = len(list(settings.watch_directory.glob("*.*")))
        return {
            "status": "running..." if observer_thread.is_alive() else "stopped.",
            "watch_directory": str(settings.watch_directory),
            "resized_directory": str(settings.resized_directory),
            "resize_resolution": f"{settings.w_max}px width",
            "total_images": self.total_images,
            "processed_images": self.processed_images,
            "failed_images": self.failed_images,
        }


def start_observer(handler):
    observer = Observer()
    observer.schedule(handler, str(settings.watch_directory), recursive=False)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()

    observer.join()


if __name__ == "__main__":
    image_handler = FileHandler()
    observer_thread = threading.Thread(target=start_observer, args=(image_handler,))
    observer_thread.daemon = True
    observer_thread.start()
