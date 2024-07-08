import cv2
import pytesseract
import numpy as np

class ImageProcessor:
    def __init__(self):
        pass

    def processImage(self, image_path):
        image = cv2.imread(image_path)

        # adjusts range of pixel intensity
        norm_img = np.zeros((image.shape[0], image.shape[1]))
        normalized_image = cv2.normalize(image, norm_img, 0, 255, cv2.NORM_MINMAX)

        # grayscale image
        gray_img = cv2.cvtColor(normalized_image, cv2.COLOR_BGR2GRAY)

        # Use pytesseract to do OCR on the processed image
        text = pytesseract.image_to_string(gray_img)
        filename = image_path.split("/")[-1].split(".")[0]
        file_path = './docs/' + filename + '.txt'
        with open(file_path, 'w') as f:
            f.write(text)

