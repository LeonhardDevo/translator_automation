import logging
from pathlib import Path
from typing import Tuple
from PIL import Image
import pytesseract
import cv2
import numpy as np
from collections import Counter

from backend.logging_setup import get_logger
logger = get_logger(__name__)

class DocumentValidator:
    """
    A validator to determine if an uploaded image represents a real document containing readable text
    suitable for OCR and translation.
    """
    
    def __init__(self):
        """Initialize the document validator"""
        logger.info("✓ Document Validator initialized")
    
    def preprocess_image(self, image_path: Path) -> np.ndarray:
        """
        Preprocess the image to enhance text visibility for OCR
        """
        img = cv2.imread(str(image_path))
        if img is None:
            raise ValueError(f"Could not load image from {image_path}")
        
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        kernel = np.ones((1, 1), np.uint8)
        opening = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel, iterations=1)
        
        return opening
    
    def calculate_text_density(self, image_path: Path) -> Tuple[float, int]:
        """
        Calculate text density by performing OCR and counting characters
        """
        try:
            processed_img = self.preprocess_image(image_path)
            
            data = pytesseract.image_to_data(processed_img, output_type=pytesseract.Output.DICT, lang='eng')
            
            n_boxes = len(data['level'])
            text_chars = 0
            valid_text_boxes = 0
            
            for i in range(n_boxes):
                if int(data['conf'][i]) > 30:
                    text = data['text'][i].strip()
                    if text:
                        text_chars += len(text)
                        valid_text_boxes += 1
            
            total_area = processed_img.shape[0] * processed_img.shape[1]
            text_density = text_chars / max(1, total_area / 1000)
            
            return text_density, text_chars
            
        except Exception as e:
            logger.error(f"Error calculating text density: {e}")
            return 0.0, 0
    
    def validate_document(self, image_path: Path) -> str:
        """
        Validate if the image represents a real document with readable text.
        
        Returns:
            "ACCEPT_DOCUMENT" if the image is a valid document
            "REJECT_NOT_A_DOCUMENT" if the image is not suitable for OCR/translation
        """
        try:
            logger.info(f"Validating document: {image_path.name}")
            
            try:
                img = Image.open(image_path)
                width, height = img.size
                if width < 50 or height < 50:
                    logger.warning(f"Image too small: {width}x{height}")
                    return "REJECT_NOT_A_DOCUMENT"
            except Exception:
                logger.error(f"Invalid image file: {image_path}")
                return "REJECT_NOT_A_DOCUMENT"
            
            text_density, char_count = self.calculate_text_density(image_path)
            
            logger.info(f"Text density: {text_density:.4f}, Character count: {char_count}")
            
            if text_density == 0.0 and char_count == 0:
                logger.warning("OCR failed or tesseract not available, using fallback validation")
                if width > 100 and height > 100:
                    logger.info("Fallback validation passed - image is of reasonable size")
                    return "ACCEPT_DOCUMENT"
                else:
                    logger.warning("Image too small for document")
                    return "REJECT_NOT_A_DOCUMENT"
            
            if char_count < 100:
                logger.warning(f"Not enough text detected: {char_count} characters")
                return "REJECT_NOT_A_DOCUMENT"
            
            if text_density < 0.01:
                logger.warning(f"Text density too low: {text_density}")
                return "REJECT_NOT_A_DOCUMENT"
            
            try:
                processed_img = self.preprocess_image(image_path)
                text = pytesseract.image_to_string(processed_img, lang='eng')
                
                lines = [line.strip() for line in text.split('\n') if line.strip()]
                paragraph_count = len([line for line in lines if len(line) > 20])
                
                if len(lines) < 3 and paragraph_count < 2:
                    logger.warning(f"Lacks document structure: {len(lines)} lines, {paragraph_count} paragraphs")
                    return "REJECT_NOT_A_DOCUMENT"
            except:
                logger.warning("Could not perform advanced document structure validation")
            
            logger.info("Document validation passed")
            return "ACCEPT_DOCUMENT"
            
        except Exception as e:
            logger.error(f"Error during document validation: {e}")
            logger.info("Allowing document due to validation error")
            return "ACCEPT_DOCUMENT"

def validate_document_image(image_path: Path) -> str:
    """
    Convenience function to validate a document image
    """
    validator = DocumentValidator()
    return validator.validate_document(image_path)