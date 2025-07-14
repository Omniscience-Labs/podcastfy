"""
Image Processing Utility Module

This module provides utilities for processing images for use with Podcastfy,
including base64 conversion for Gemini API compatibility.
"""

import base64
import os
import mimetypes
from pathlib import Path
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)

class ImageProcessor:
    """Utility class for processing images for AI model consumption."""
    
    @staticmethod
    def convert_to_base64(image_path: str) -> str:
        """
        Convert an image file to base64 encoded string.
        
        Args:
            image_path (str): Path to the image file
            
        Returns:
            str: Base64 encoded image string with data URL format
            
        Raises:
            FileNotFoundError: If image file doesn't exist
            ValueError: If file is not a valid image
        """
        try:
            # Validate file exists
            if not os.path.exists(image_path):
                raise FileNotFoundError(f"Image file not found: {image_path}")
            
            # Get MIME type
            mime_type, _ = mimetypes.guess_type(image_path)
            if not mime_type or not mime_type.startswith('image/'):
                raise ValueError(f"File is not a valid image: {image_path}")
            
            # Read and encode image
            with open(image_path, 'rb') as image_file:
                encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
            
            # Return data URL format
            return f"data:{mime_type};base64,{encoded_string}"
            
        except Exception as e:
            logger.error(f"Error converting image to base64: {str(e)}")
            raise
    
    @staticmethod
    def process_images_for_gemini(image_paths: List[str]) -> List[str]:
        """
        Process a list of image paths for Gemini API consumption.
        
        Args:
            image_paths (List[str]): List of image file paths
            
        Returns:
            List[str]: List of base64 encoded image strings
            
        Raises:
            ValueError: If any image cannot be processed
        """
        processed_images = []
        
        for image_path in image_paths:
            try:
                base64_image = ImageProcessor.convert_to_base64(image_path)
                processed_images.append(base64_image)
                logger.info(f"Successfully processed image: {image_path}")
            except Exception as e:
                logger.error(f"Failed to process image {image_path}: {str(e)}")
                raise ValueError(f"Failed to process image {image_path}: {str(e)}")
        
        return processed_images
    
    @staticmethod
    def validate_image_file(image_path: str) -> bool:
        """
        Validate that a file is a supported image format.
        
        Args:
            image_path (str): Path to the image file
            
        Returns:
            bool: True if file is a valid image, False otherwise
        """
        try:
            # Check file exists
            if not os.path.exists(image_path):
                return False
            
            # Check file size (max 20MB for Gemini)
            file_size = os.path.getsize(image_path)
            if file_size > 20 * 1024 * 1024:  # 20MB
                return False
            
            # Check MIME type
            mime_type, _ = mimetypes.guess_type(image_path)
            if not mime_type or not mime_type.startswith('image/'):
                return False
            
            # Check file extension
            supported_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'}
            file_extension = Path(image_path).suffix.lower()
            if file_extension not in supported_extensions:
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating image file {image_path}: {str(e)}")
            return False
    
    @staticmethod
    def get_image_info(image_path: str) -> dict:
        """
        Get information about an image file.
        
        Args:
            image_path (str): Path to the image file
            
        Returns:
            dict: Dictionary containing image information
        """
        try:
            if not os.path.exists(image_path):
                return {"error": "File not found"}
            
            file_size = os.path.getsize(image_path)
            mime_type, _ = mimetypes.guess_type(image_path)
            file_extension = Path(image_path).suffix.lower()
            
            return {
                "path": image_path,
                "size_bytes": file_size,
                "size_mb": round(file_size / (1024 * 1024), 2),
                "mime_type": mime_type,
                "extension": file_extension,
                "is_valid": ImageProcessor.validate_image_file(image_path)
            }
            
        except Exception as e:
            return {"error": str(e)}

def convert_images_for_podcastfy(image_paths: List[str]) -> List[str]:
    """
    Convenience function to convert images for Podcastfy use.
    
    Args:
        image_paths (List[str]): List of image file paths
        
    Returns:
        List[str]: List of base64 encoded image strings
    """
    return ImageProcessor.process_images_for_gemini(image_paths)

def validate_images_for_podcastfy(image_paths: List[str]) -> List[dict]:
    """
    Validate a list of images for Podcastfy use.
    
    Args:
        image_paths (List[str]): List of image file paths
        
    Returns:
        List[dict]: List of validation results for each image
    """
    results = []
    for image_path in image_paths:
        info = ImageProcessor.get_image_info(image_path)
        results.append(info)
    return results 