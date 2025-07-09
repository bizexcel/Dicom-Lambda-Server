import os
import logging
import numpy as np
from PIL import Image
import pydicom
from pydicom.pixel_data_handlers.util import apply_voi_lut
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

class DicomConverter:
    """Handles DICOM to JPG conversion"""
    
    def __init__(self):
        """Initialize the DICOM converter"""
        pass
    
    def convert_to_jpg(self, dicom_file_path: str, output_dir: str, quality: int = 85) -> str:
        """
        Convert DICOM file to JPG format
        
        Args:
            dicom_file_path: Path to the DICOM file
            output_dir: Directory to save the JPG file
            quality: JPG quality (1-100)
            
        Returns:
            Path to the converted JPG file
        """
        try:
            # Read DICOM file
            logger.info(f"Reading DICOM file: {dicom_file_path}")
            dicom_data = pydicom.dcmread(dicom_file_path)
            
            # Extract pixel data
            pixel_array = self._extract_pixel_data(dicom_data)
            
            # Convert to 8-bit grayscale or RGB
            image_array = self._normalize_pixel_data(pixel_array, dicom_data)
            
            # Create PIL Image
            if len(image_array.shape) == 2:
                # Grayscale image
                pil_image = Image.fromarray(image_array, mode='L')
            else:
                # RGB image
                pil_image = Image.fromarray(image_array, mode='RGB')
            
            # Generate output filename
            base_name = os.path.splitext(os.path.basename(dicom_file_path))[0]
            output_path = os.path.join(output_dir, f"{base_name}.jpg")
            
            # Save as JPG
            pil_image.save(output_path, 'JPEG', quality=quality, optimize=True)
            
            logger.info(f"Successfully converted DICOM to JPG: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Failed to convert DICOM to JPG: {str(e)}")
            raise Exception(f"DICOM conversion failed: {str(e)}")
    
    def _extract_pixel_data(self, dicom_data: pydicom.Dataset) -> np.ndarray:
        """Extract pixel data from DICOM dataset"""
        try:
            # Get pixel array
            pixel_array = dicom_data.pixel_array
            
            # Apply VOI LUT (Value of Interest Look-Up Table) if available
            # This handles window/level adjustments
            if hasattr(dicom_data, 'WindowCenter') and hasattr(dicom_data, 'WindowWidth'):
                try:
                    pixel_array = apply_voi_lut(pixel_array, dicom_data)
                except Exception as e:
                    logger.warning(f"Failed to apply VOI LUT: {str(e)}")
            
            return pixel_array
            
        except Exception as e:
            logger.error(f"Failed to extract pixel data: {str(e)}")
            raise Exception(f"Failed to extract pixel data: {str(e)}")
    
    def _normalize_pixel_data(self, pixel_array: np.ndarray, dicom_data: pydicom.Dataset) -> np.ndarray:
        """Normalize pixel data to 8-bit range"""
        try:
            # Handle different photometric interpretations
            photometric_interpretation = getattr(dicom_data, 'PhotometricInterpretation', 'MONOCHROME2')
            
            if photometric_interpretation == 'MONOCHROME1':
                # Invert grayscale values
                pixel_array = np.max(pixel_array) - pixel_array
            
            # Handle multi-frame images (take first frame)
            if len(pixel_array.shape) > 2:
                if pixel_array.shape[0] > 1:
                    pixel_array = pixel_array[0]
                    logger.info("Multi-frame DICOM detected, using first frame")
            
            # Normalize to 0-255 range
            pixel_array = pixel_array.astype(np.float64)
            
            # Remove any invalid values
            pixel_array = np.nan_to_num(pixel_array, nan=0.0, posinf=0.0, neginf=0.0)
            
            # Apply percentile-based normalization for better contrast
            if pixel_array.max() > pixel_array.min():
                # Use 1st and 99th percentiles to avoid outliers
                p1, p99 = np.percentile(pixel_array, [1, 99])
                pixel_array = np.clip(pixel_array, p1, p99)
                
                # Normalize to 0-255
                pixel_array = (pixel_array - p1) / (p99 - p1) * 255
            else:
                # If all values are the same, create a uniform image
                pixel_array = np.full_like(pixel_array, 128)
            
            # Convert to uint8
            pixel_array = np.clip(pixel_array, 0, 255).astype(np.uint8)
            
            return pixel_array
            
        except Exception as e:
            logger.error(f"Failed to normalize pixel data: {str(e)}")
            raise Exception(f"Failed to normalize pixel data: {str(e)}")
    
    def get_dicom_metadata(self, dicom_file_path: str) -> dict:
        """
        Extract useful metadata from DICOM file
        
        Args:
            dicom_file_path: Path to the DICOM file
            
        Returns:
            Dictionary containing DICOM metadata
        """
        try:
            dicom_data = pydicom.dcmread(dicom_file_path)
            
            metadata = {}
            
            # Patient information
            metadata['PatientName'] = str(getattr(dicom_data, 'PatientName', 'Unknown'))
            metadata['PatientID'] = str(getattr(dicom_data, 'PatientID', 'Unknown'))
            metadata['PatientBirthDate'] = str(getattr(dicom_data, 'PatientBirthDate', 'Unknown'))
            metadata['PatientSex'] = str(getattr(dicom_data, 'PatientSex', 'Unknown'))
            
            # Study information
            metadata['StudyDate'] = str(getattr(dicom_data, 'StudyDate', 'Unknown'))
            metadata['StudyTime'] = str(getattr(dicom_data, 'StudyTime', 'Unknown'))
            metadata['StudyDescription'] = str(getattr(dicom_data, 'StudyDescription', 'Unknown'))
            metadata['Modality'] = str(getattr(dicom_data, 'Modality', 'Unknown'))
            
            # Image information
            metadata['ImageType'] = str(getattr(dicom_data, 'ImageType', 'Unknown'))
            metadata['PhotometricInterpretation'] = str(getattr(dicom_data, 'PhotometricInterpretation', 'Unknown'))
            metadata['Rows'] = int(getattr(dicom_data, 'Rows', 0))
            metadata['Columns'] = int(getattr(dicom_data, 'Columns', 0))
            metadata['PixelSpacing'] = str(getattr(dicom_data, 'PixelSpacing', 'Unknown'))
            
            # Window/Level information
            metadata['WindowCenter'] = str(getattr(dicom_data, 'WindowCenter', 'Unknown'))
            metadata['WindowWidth'] = str(getattr(dicom_data, 'WindowWidth', 'Unknown'))
            
            return metadata
            
        except Exception as e:
            logger.error(f"Failed to extract DICOM metadata: {str(e)}")
            return {'error': str(e)}
    
    def validate_dicom_file(self, file_path: str) -> bool:
        """
        Validate if the file is a valid DICOM file
        
        Args:
            file_path: Path to the file to validate
            
        Returns:
            True if valid DICOM file, False otherwise
        """
        try:
            # Try to read the file as DICOM
            dicom_data = pydicom.dcmread(file_path)
            
            # Check if it has pixel data
            if not hasattr(dicom_data, 'pixel_array'):
                logger.warning("DICOM file has no pixel data")
                return False
            
            # Check if pixel data is accessible
            pixel_array = dicom_data.pixel_array
            if pixel_array is None or pixel_array.size == 0:
                logger.warning("DICOM file has empty pixel data")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"DICOM validation failed: {str(e)}")
            return False 