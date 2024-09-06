import logging
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple, Union

import cv2
import exifread
import numpy as np

logger = logging.getLogger(__name__)


def resize_image(
    image: np.ndarray,
    width: int = None,
    height: int = None,
    interpolation: int = cv2.INTER_AREA,
) -> np.ndarray:
    """
    Resize the input image to the specified width and/or height while maintaining aspect ratio.

        Args:
        image (np.ndarray): The input image to resize.
        width (int, optional): The desired width of the resized image. If None, width is calculated based on height.
        height (int, optional): The desired height of the resized image. If None, height is calculated based on width.
        interpolation (int, optional): The interpolation method to use for resizing. Default is cv2.INTER_AREA.

    Returns:
        np.ndarray: The resized image.
    """
    original_height, original_width = image.shape[:2]

    if width is None and height is None:
        raise ValueError("At least one of 'width' or 'height' must be specified.")
    elif width is not None and height is None:
        # Calculate height to maintain aspect ratio
        w_percent = width / float(original_width)
        new_height = int((float(original_height) * float(w_percent)))
        new_dim = (width, new_height)
    elif width is None and height is not None:
        # Calculate width to maintain aspect ratio
        h_percent = height / float(original_height)
        new_width = int((float(original_width) * float(h_percent)))
        new_dim = (new_width, height)

    else:
        # Resize to specified width and height directly
        new_dim = (width, height)

    # Resize the image
    resized = cv2.resize(image, new_dim, interpolation=interpolation)

    return resized


def read_date_from_exif(im_path: Union[Path, str]) -> datetime:
    """
    Reads the date from the EXIF metadata of an image file.

    Args:
        im_path (Union[Path, str]): The path to the image file.

    Returns:
        datetime: The datetime object representing the date and time the image was taken.
        None: If the date is not available in the EXIF metadata.

    Raises:
        FileNotFoundError: If the image file does not exist.
        ValueError: If the date format in the EXIF metadata is incorrect.
    """
    f = open(im_path, "rb")
    tags = exifread.process_file(f, details=False, stop_tag="DateTimeOriginal")
    if "Image DateTime" in tags.keys():
        date_str = tags["EXIF DateTimeOriginal"].values
        date_fmt = "%Y:%m:%d %H:%M:%S"
        date_time = datetime.strptime(date_str, date_fmt)
        return date_time
    else:
        logger.error("Date not available in exif.")
        return None


def read_date_from_filename(
    im_path: Union[Path, str],
    fmt: str = "%Y_%m_%d",
    sep: str = None,
    position: Union[int, List[int]] = None,
) -> datetime:
    """
    Extracts and parses a date from the filename.

    Args:
        im_path (Union[Path, str]): The path to the image file.
        fmt (str, optional): The date format to parse. Defaults to "%Y_%m_%d".
        sep (str, optional): The separator used in the filename. Defaults to None.
        position (Union[int, List[int]], optional): The position(s) of the date components in the filename. Defaults to None.

    Returns:
        datetime: The parsed date and time.
    """
    date_str = str(Path(im_path).stem)
    if sep is not None:
        date_str = date_str.split(sep)[position]
    date_time = datetime.strptime(date_str, fmt)
    return date_time


def overlay_string(
    image: np.ndarray,
    overlay_string: str,
    font_scale: int = 8,
    font_thickness: int = 8,
    left_border_percent: float = 0.7,
    bottom_border: int = 100,
    font_color: Tuple[int, int, int] = (255, 255, 255),
    font: int = cv2.FONT_HERSHEY_SIMPLEX,
) -> np.ndarray:
    """Overlay a string on the image.

    Args:
        image (np.ndarray): The input image on which to overlay the text.
        overlay_string (str): The string to overlay on the image.
        font_scale (int, optional): Font scale for the text. Defaults to 8.
        font_thickness (int, optional): Thickness of the text. Defaults to 8.
        left_border_percent (float, optional): Percentage of the image width from where the text will start. Defaults to 0.7.
        bottom_border (int, optional): Distance from the bottom of the image where the text will be placed. Defaults to 100.
        font_color (Tuple[int, int, int], optional): Color of the text in BGR format. Defaults to (255, 255, 255).
        font (int, optional): Font type for the text. Defaults to cv2.FONT_HERSHEY_SIMPLEX.

    Returns:
        np.ndarray: The image with the text overlay.
    """
    h, w, _ = image.shape
    left_border = int(left_border_percent * w)
    bottomLeftCornerOfText = (w - left_border, h - bottom_border)
    fontScale = int(font_scale)
    fontColor = font_color
    thickness = int(font_thickness)
    text_border = int(font_thickness * 0.8)
    lineType = cv2.LINE_8

    # Text border
    cv2.putText(
        image,
        overlay_string,
        bottomLeftCornerOfText,
        font,
        fontScale,
        (0,),
        thickness + text_border,
        lineType,
    )
    # Inner text
    cv2.putText(
        image,
        overlay_string,
        bottomLeftCornerOfText,
        font,
        fontScale,
        fontColor,
        thickness,
        lineType,
    )

    return image


def overlay_logo(
    img: np.ndarray, img_overlay: np.ndarray, padding: int = 0, alpha: float = 1.0
) -> np.ndarray:
    """
    Overlays a logo onto an image.

    Args:
        img (np.ndarray): The original image on which to overlay the logo.
        img_overlay (np.ndarray): The logo image to overlay.
        padding (int, optional): The padding between the logo and the image border. Defaults to 0.
        alpha (float, optional): The transparency factor of the logo overlay. Defaults to 1.0 (fully opaque).

    Returns:
        np.ndarray: The image with the logo overlay.
    """
    # Get dimensions of the overlay
    h, w = img_overlay.shape[:2]

    # Create an overlay image with the same size as the input image
    shapes = np.zeros_like(img, np.uint8)

    # Determine the position to place the logo
    y1, y2 = img.shape[0] - h - padding, img.shape[0] - padding
    x1, x2 = img.shape[1] - w - padding, img.shape[1] - padding

    # Place the overlay logo on the position with padding
    shapes[y1:y2, x1:x2] = img_overlay

    # Create a mask and apply the overlay with transparency
    mask = shapes.astype(bool)
    img[mask] = cv2.addWeighted(img, 1 - alpha, shapes, alpha, 0)[mask]

    return img


def process_image(
    file_path: Path,
    output_directory: Path = Path("resized"),
    w_max: int = 300,
    font_scale: int = 8,
    font_thickness: int = 8,
    left_border_percent: float = 0.7,
    bottom_border: int = 100,
    font_color: Tuple[int, int, int] = (255, 255, 255),
    font: int = cv2.FONT_HERSHEY_SIMPLEX,
    logo_path: Optional[str] = None,
) -> Path:
    """Process an image by adding a string overlay, logo, and resizing it.

    Args:
        file_path (Path): Path to the input image file.
        output_directory (Path, optional): Directory to save the processed image. Defaults to "resized".
        w_max (int, optional): Maximum width for resizing the image. Defaults to 300.
        font_scale (int, optional): Font scale for the text overlay. Defaults to 8.
        font_thickness (int, optional): Thickness of the text overlay. Defaults to 8.
        left_border_percent (float, optional): Percentage of the image width from where the text overlay will start. Defaults to 0.7.
        bottom_border (int, optional): Distance from the bottom of the image where the text will be placed. Defaults to 100.
        font_color (Tuple[int, int, int], optional): Color of the text overlay in BGR format. Defaults to (255, 255, 255).
        font (int, optional): Font type for the text overlay. Defaults to cv2.FONT_HERSHEY_SIMPLEX.
        logo_path (Optional[str], optional): Path to the logo image file. Defaults to None.

    Returns:
        Path: Path to the processed image file.
    """
    # Check if the image exists
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    # Get the date from the image exif
    date_time = read_date_from_exif(file_path)
    overlay_str = f"{date_time.year}/{date_time.month:02}/{date_time.day:02} {date_time.hour:02}:{date_time.minute:02}"

    # Read the image
    img = cv2.imread(str(file_path), cv2.IMREAD_COLOR)

    # Add the overlay string
    img = overlay_string(
        img,
        overlay_str,
        font_scale,
        font_thickness,
        left_border_percent,
        bottom_border,
        font_color,
        font,
    )

    # Add the logo
    if logo_path:
        logo = cv2.imread(logo_path, cv2.IMREAD_UNCHANGED)
        img = overlay_logo(img, logo, padding=50, alpha=1.0)

    # Resize image and save it
    resized_img = resize_image(img, width=w_max)
    out_path = output_directory / file_path.name
    cv2.imwrite(str(out_path), resized_img)

    return out_path


if __name__ == "__main__":
    print("Running the script")

    file_path = Path("data/p1/p1_20240904_075427_IMG_4809.JPG")
    output_directory = Path("data")
    logo_path: str = "data/logo_polimi.jpg"

    image = process_image(
        file_path,
        output_directory,
        w_max=1200,
        logo_path=logo_path,
        font_scale=10,
        font_thickness=16,
        left_border_percent=0.75,
    )
