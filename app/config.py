import logging
from pathlib import Path

from dynaconf import Dynaconf

settings = Dynaconf(
    settings_files=["./config.yaml"],
    environments=True,
)

# Convert the path strings to Path objects
settings.watch_directory = Path(settings.watch_directory)
settings.resized_directory = Path(settings.resized_directory)

# Create the directories if they don't exist
settings.resized_directory.mkdir(parents=True, exist_ok=True)

# Setup logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Create a file handler
file_handler = logging.FileHandler(settings.log_file)
file_handler.setLevel(logging.INFO)

# Create a console handler
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

# Define the logging format
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

# Add handlers to the logger
logger.addHandler(file_handler)
logger.addHandler(console_handler)

if __name__ == "__main__":
    print(settings)
    print(settings.watch_directory)
    print(settings.resized_directory)
    print(settings.log_file)
    print(settings.image_extensions)
    print(settings.w_max)
