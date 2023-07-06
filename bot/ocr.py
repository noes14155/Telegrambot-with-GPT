from io import BytesIO
import pytesseract
import requests
from PIL import Image, ImageEnhance

class OCR:
    def __init__(self, config=None):
        self.config = config

    def process_image(self, url):
        try:
            # Load the image
            response = requests.get(url)
            img = Image.open(BytesIO(response.content))

            # Preprocess the image for better contrast
            enhancer = ImageEnhance.Contrast(img)
            img = enhancer.enhance(1.5)

            # Convert image to grayscale
            gray = img.convert('L')

            # Apply thresholding to binarize the image
            thresh = gray.point(lambda x: 0 if x < 128 else 255, '1')

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