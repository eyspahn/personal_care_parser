"""Collection of functions to parse ingredients labels. In progress."""
import os
import sys
from PIL import Image
import pytesseract
from typing import List


def read_image(fp: str) -> str:
    """

    :param fp:
    :return: string from ingredient label

    """
    return str(((pytesseract.image_to_string(Image.open(fp)))))


def create_ingredients_list(text: str) -> List[str]:
    """

    :param text: The output from read_image: a single string text file.
    :return: a list of strings of ingredients
    """

    text = text.replace('\n', ' ')
    text = text.lower()
    text = text.replace('ingredients:', '')
    text = text.replace('ingredients', '')  # to capture cases where there may be a colon between ing & list.
    # todo make above two lines cleverer / combine

    # let's remove water





