from io import BytesIO
import pytesseract
import requests
from PIL import Image, ImageEnhance

class OCR:
    """
    The OCR class is used for performing optical character recognition (OCR) on an image.
    It uses the Tesseract OCR engine to extract text from the image.
    """

    def __init__(self, config=None):
        """
        Initializes an instance of the OCR class with an optional configuration parameter.

        Args:
            config (str): Optional configuration parameter for Tesseract OCR.
        """
        self.config = config

    def process_image(self, url):
        """
        Processes an image from a given URL and returns the extracted text if it contains non-whitespace characters,
        otherwise returns None.

        Args:
            url (str): The URL of the image to be processed.

        Returns:
            str or None: The extracted text from the image, or None if no text is found.
        """
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