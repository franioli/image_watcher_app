import logging
from pathlib import Path

from PIL import Image

logger = logging.getLogger(__name__)


def resize(
    file_path: Path, resized_directory: Path = Path("resized"), w_max: int = 300
) -> Path:
    with Image.open(file_path) as img:
        w_percent = w_max / float(img.size[0])
        h_size = int((float(img.size[1]) * float(w_percent)))
        img = img.resize((w_max, h_size))

        # Save the resized image in the resized directory with the same name
        resized_path = resized_directory / file_path.name
        img.save(resized_path)
    return resized_path
