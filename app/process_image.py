import logging
from datetime import datetime
from pathlib import Path
from typing import List, Tuple, Union

import cv2
import exifread
import numpy as np

# from PIL import Image

logger = logging.getLogger(__name__)


# def resize_PIL(
#     file_path: Path, output_directory: Path = Path("resized"), w_max: int = 300
# ) -> Path:
#     with Image.open(file_path) as img:
#         w_percent = w_max / float(img.size[0])
#         h_size = int((float(img.size[1]) * float(w_percent)))
#         img = img.resize((w_max, h_size))

#         # Save the resized image in the resized directory with the same name
#         resized_path = output_directory / file_path.name
#         img.save(resized_path)
#     return resized_path


def read_date_from_filename(
    im_path: Union[Path, str],
    fmt: str = "%Y_%m_%d",
    sep: str = None,
    position: Union[int, List[int]] = None,
) -> datetime:
    date_str = str(Path(im_path).stem)
    if sep is not None:
        date_str = date_str.split(sep)[position]
    date_time = datetime.strptime(date_str, fmt)
    return date_time


def overlay_logo(
    img: np.ndarray,
    img_overlay: np.ndarray,
    pading: int = 0,
    alpha: float = 1,
):
    h, w = img_overlay.shape[:2]
    shapes = np.zeros_like(img, np.uint8)
    shapes[img.shape[0] - h - pading : -pading, img.shape[1] - w - pading : -pading] = (
        img_overlay
    )
    mask = shapes.astype(bool)
    img[mask] = cv2.addWeighted(img, 1 - alpha, shapes, alpha, 0)[mask]

    return img


def read_date_from_exif(im_path: Union[Path, str]) -> datetime:
    f = open(im_path, "rb")
    tags = exifread.process_file(f, details=False, stop_tag="DateTimeOriginal")
    if "Image DateTime" in tags.keys():
        date_str = tags["EXIF DateTimeOriginal"].values
        date_fmt = "%Y:%m:%d %H:%M:%S"
        date_time = datetime.strptime(date_str, date_fmt)
        return date_time
    else:
        print("Date not available in exif.")
        # return


def process_image(
    file_path,
    output_directory: Path = Path("resized"),
    w_max: int = 300,
    font_scale: int = 8,
    font_thickness: int = 8,
    left_border_percent: float = 0.7,
    font_color: Tuple[int, int, int] = (255, 255, 255),
    logo_path: str = None,
):
    # Check if the image exists
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    # Get the date from the image exif
    date_time = read_date_from_exif(file_path)
    over_str = f"{date_time.year}/{date_time.month:02}/{date_time.day:02} {date_time.hour:02}:{date_time.minute:02}"

    # Read the image and convert it to RGB
    img = cv2.imread(str(file_path), cv2.IMREAD_COLOR)
    # img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    h, w, _ = img.shape

    # Add the overlay text
    font = cv2.FONT_HERSHEY_SIMPLEX  # cv2.FONT_HERSHEY_DUPLEX
    bottom_border = 100
    left_border = int(left_border_percent * w)
    bottomLeftCornerOfText = (w - left_border, h - bottom_border)
    fontScale = int(font_scale)
    fontColor = font_color
    thickness = int(font_thickness)
    text_border = int(font_thickness * 0.8)
    lineType = cv2.LINE_8

    # Text border
    cv2.putText(
        img,
        over_str,
        bottomLeftCornerOfText,
        font,
        fontScale,
        (0,),
        thickness + text_border,
        lineType,
    )
    # Inner text
    cv2.putText(
        img,
        over_str,
        bottomLeftCornerOfText,
        font,
        fontScale,
        fontColor,
        thickness,
        lineType,
    )

    # Add the logo
    if logo_path:
        overlay = cv2.imread(logo_path)
        img = overlay_logo(img, overlay, pading=50, alpha=1)

    # Resize the image
    original_height, original_width = img.shape[:2]

    # Calculate the new dimensions
    w_percent = w_max / float(original_width)
    h_size = int((float(original_height) * float(w_percent)))
    new_dim = (w_max, h_size)

    # Resize the image
    resized_img = cv2.resize(img, new_dim, interpolation=cv2.INTER_AREA)

    # Save the resized image in the resized directory with the same name
    out_path = output_directory / file_path.name
    cv2.imwrite(str(out_path), resized_img)

    return out_path


if __name__ == "__main__":
    print("Running the script")

    file_path = Path("data/p1/p1_20240904_075427_IMG_4809.JPG")
    output_directory = Path("data")
    logo_path: str = "logo_polimi.jpg"

    image = process_image(
        file_path,
        output_directory,
        w_max=1200,
        logo_path=logo_path,
        font_scale=10,
        font_thickness=16,
        left_border_percent=0.75,
    )
