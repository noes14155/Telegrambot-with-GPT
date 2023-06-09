import cv2
from PIL import Image
import pytesseract
import requests
import numpy as np


class OCR:
    def __init__(self, config=None):
        self.config = config

    def process_image(self, url):
        try:
            # Load the image
            response = requests.get(url)
            img = cv2.imdecode(np.frombuffer(response.content, np.uint8), cv2.IMREAD_COLOR)

            # Preprocess the image for better contrast
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
            gray = clahe.apply(gray)

            # Apply thresholding to binarize the image
            _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY+cv2.THRESH_OTSU)

            # Perform OCR using Tesseract with custom configuration
            text = pytesseract.image_to_string(thresh, config=self.config)

            # Return the OCR output if it contains non-whitespace characters, otherwise return None
            if text.strip():
                return text.strip()
            else:
                return None

        except Exception as e:
            print(f"Error processing file {url}: {e}")
            return None
