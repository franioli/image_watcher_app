import logging
from pathlib import Path

from config import settings
from resize_image import resize
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

logger = logging.getLogger()


class FileHandler(FileSystemEventHandler):
    def __init__(
        self,
        watch_directory: Path,
        output_directory: Path = None,
        remove_on_delete: bool = True,
        skip_existing: bool = True,
        image_extensions: list = settings.proc.image_extensions,
        **kwargs,
    ):
        # Set the watch and output directories
        self.watch_directory = Path(watch_directory)
        self.output_directory = Path(output_directory) if output_directory else None
        if not self.watch_directory.exists():
            raise FileNotFoundError(
                f"Watch directory not found: {self.watch_directory}"
            )
        if not self.output_directory:
            self.output_directory = self.watch_directory.parent / "proc"
            self.output_directory.mkdir(parents=True, exist_ok=True)

        # Get the total number of images in the watch directory
        self.total_images = len(list(self.watch_directory.glob("*.*")))

        # Initialize the image map to store the original and resized image paths
        self.image_map = {}
        self.update_image_map()

        # Initialize the processed and failed image counters
        self.processed_images = 0
        self.failed_images = 0

        # Store additional keyword arguments
        self.remove_on_delete = remove_on_delete
        self.skip_existing = skip_existing
        self.image_extensions = image_extensions
        if self.remove_on_delete:
            logger.info("Images will be deleted on file delete event.")

        self.opt = kwargs

        # Placeholder for the observer thread
        self.observer_thread = None

    def process_existing_images(self):
        logger.info("Processing existing images...")
        for file_path in self.watch_directory.glob("*.*"):
            if self.skip_existing:
                if self.image_map[str(file_path)]:
                    continue
            self.process_image(file_path)

    def update_image_map(self):
        self.image_map = {
            str(file_path): str(self.output_directory / file_path.name)
            if (self.output_directory / file_path.name).exists()
            else None
            for file_path in sorted(self.watch_directory.glob("*.*"), reverse=True)
        }

    def update_total_images(self):
        self.total_images = len(list(self.watch_directory.glob("*.*")))

    def on_any_event(self, event):
        self.update_total_images()

    def on_created(self, event):
        if not event.is_directory:
            logger.info(f"New file created: {event.src_path}")
            self.process_image(event.src_path)

    def on_modified(self, event):
        if not event.is_directory:
            logger.info(f"File modified: {event.src_path}")
            self.process_image(event.src_path)

    def on_moved(self, event):
        if not event.is_directory:
            logger.info(f"File moved: {event.src_path} to {event.dest_path}")
            # Handle the move event by processing the new file path
            self.process_image(event.dest_path)

    def on_deleted(self, event):
        if not event.is_directory and self.remove_on_delete:
            logger.info(f"File deleted: {event.src_path}")
            self.delete_file(event.src_path)

    def process_image(self, file_path):
        w_max = self.opt.get("w_max", -1)
        if w_max < 0:
            logger.info(f"Invalid resize resolution. Skipping image {file_path}")
            return

        file_path = Path(file_path)
        if file_path.suffix.lower() in self.image_extensions:
            try:
                resized_file_path = resize(file_path, self.output_directory, w_max)
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
        self.total_images = len(list(self.watch_directory.glob("*.*")))
        thread_status = (
            "running..."
            if self.observer_thread and self.observer_thread.is_alive()
            else "stopped."
        )
        return {
            "status": thread_status,
            "watch_directory": str(self.watch_directory),
            "output_directory": str(self.output_directory),
            "resize_resolution": f"{self.opt.get('w_max', settings.proc.w_max)}px width",
            "total_images": self.total_images,
            "processed_images": self.processed_images,
            "failed_images": self.failed_images,
        }


def start_observer(watch_directory: Path, output_directory: Path = None):
    handler = FileHandler(
        watch_directory=watch_directory,
        output_directory=output_directory,
        remove_on_delete=settings.proc.remove_on_delete,
        skip_existing=settings.proc.skip_existing,
        image_extensions=settings.proc.image_extensions,
        w_max=settings.proc.w_max,
    )
    observer = Observer()
    observer.schedule(handler, str(watch_directory), recursive=settings.proc.recursive)
    observer.start()
    
    # Assign the observer thread to the handler
    handler.observer_thread = observer

    return observer, handler


def start_observers():
    observers = []
    for directory_config in settings.watch_directories:
        observer, handler = start_observer(
            directory_config.watch, directory_config.output
        )
        observers.append((observer, handler))

    return observers


if __name__ == "__main__":
    # Join observers on the main thread
    import time

    # Start the observer threads
    observers_and_handlers = start_observers()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        for observer, _ in observers_and_handlers:
            observer.stop()

        for observer, _ in observers_and_handlers:
            observer.join()
