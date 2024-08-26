import logging
from pathlib import Path

from omegaconf import OmegaConf

config_path = Path(__file__).parents[1] / "config.yaml"

settings = OmegaConf.load(config_path)


# Check paths
for dir in settings.watch_directories:
    # Convert path strings to Path objects
    dir.watch = Path(dir.watch)
    dir.output = Path(dir.output)

    # Check if all watch directories exist
    if not dir.watch.exists():
        raise FileNotFoundError(f"Watch directory not found: {dir.watch}")

    # Handle output pattern
    if "output_pattern" in dir:
        output_directory = Path(
            dir.output_pattern.replace("{watch_dir}", str(dir.watch))
        )

    # Create the directories if they don't exist
    dir.output.mkdir(parents=True, exist_ok=True)

# Setup logging
log_level = logging.getLevelName(settings.log.level.upper())
logger = logging.getLogger()
logger.setLevel(log_level)

# Create a file handler
file_handler = logging.FileHandler(settings.log.file)
file_handler.setLevel(log_level)

# Create a console handler
console_handler = logging.StreamHandler()
console_handler.setLevel(log_level)

# Define the logging format
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

# Add handlers to the logger
logger.addHandler(file_handler)
logger.addHandler(console_handler)

if __name__ == "__main__":
    print(settings)
    print(settings.watch_directories)
    print(settings.watch_directories[0].watch)
    print(settings.watch_directories[0].output)
    print(settings.proc.image_extensions)
    print(settings.proc.remove_on_delete)
    print(settings.proc.skip_existing)
    print(settings.log.file)
