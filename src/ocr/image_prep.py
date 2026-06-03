# ocr/image_prep.py

from __future__ import annotations

from enum import Enum
from pathlib import Path

from PIL import Image, ImageEnhance, ImageFilter, ImageOps


class PreprocessMode(str, Enum):
    NONE = "none"
    BASIC = "basic"
    ARCHIVAL = "archival"


def preprocess_image(
    image_path: str | Path,
    mode: PreprocessMode | str = PreprocessMode.BASIC,
) -> Image.Image:
    """
    Load and preprocess an image for OCR.

    Returns a PIL Image in memory.
    Does not save the processed image to disk.
    """

    image_path = Path(image_path)
    mode = PreprocessMode(mode)

    if not image_path.exists():
        raise FileNotFoundError(f"Image file does not exist: {image_path}")

    image = Image.open(image_path)

    if mode == PreprocessMode.NONE:
        return image.convert("RGB")

    if mode == PreprocessMode.BASIC:
        return basic_preprocess(image)

    if mode == PreprocessMode.ARCHIVAL:
        return archival_preprocess(image)

    raise ValueError(f"Unknown preprocessing mode: {mode}")


def basic_preprocess(image: Image.Image) -> Image.Image:
    """
    Conservative preprocessing:
    - grayscale
    - mild contrast enhancement
    - mild sharpening

    Safe default for printed archival scans.
    """

    image = ImageOps.grayscale(image)

    contrast = ImageEnhance.Contrast(image)
    image = contrast.enhance(1.25)

    sharpness = ImageEnhance.Sharpness(image)
    image = sharpness.enhance(1.2)

    return image


def archival_preprocess(image: Image.Image) -> Image.Image:
    """
    Aggressive preprocessing:
    - grayscale
    - denoise
    - stronger contrast
    - adaptive threshold approximation
    - sharpen

    Useful for bad scans, but can damage faint marks or marginalia.
    """

    image = ImageOps.grayscale(image)

    image = image.filter(ImageFilter.MedianFilter(size=3))

    contrast = ImageEnhance.Contrast(image)
    image = contrast.enhance(1.6)

    image = adaptive_threshold(image)

    sharpness = ImageEnhance.Sharpness(image)
    image = sharpness.enhance(1.4)

    return image


def adaptive_threshold(
    image: Image.Image,
    block_size: int = 35,
    offset: int = 10,
) -> Image.Image:
    """
    Simple adaptive threshold approximation using PIL.

    Converts grayscale image to black/white based on local background.
    """

    if block_size % 2 == 0:
        block_size += 1

    background = image.filter(ImageFilter.BoxBlur(block_size // 2))

    thresholded = Image.new("L", image.size)

    image_pixels = image.load()
    background_pixels = background.load()
    output_pixels = thresholded.load()

    width, height = image.size

    for y in range(height):
        for x in range(width):
            local_threshold = background_pixels[x, y] - offset
            output_pixels[x, y] = 255 if image_pixels[x, y] > local_threshold else 0

    return thresholded