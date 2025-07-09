import json
import base64
import os
import tempfile
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

from dicom_converter import DicomConverter
from file_downloader import FileDownloader
from temp_cleaner import TempCleaner

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Main Lambda handler for DICOM to JPG conversion.
    
    Expected event structure:
    {
        "url": "https://example.com/file.dcm",
        "storage_type": "s3|r2|ftp",  # optional, will be auto-detected
        "output_format": "jpg",       # optional, defaults to jpg
        "quality": 85                 # optional, JPG quality (1-100)
    }
    """
    try:
        # Extract parameters from event
        url = event.get('url')
        if not url:
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'error': 'URL is required',
                    'message': 'Please provide a valid URL in the request body'
                })
            }
        
        storage_type = event.get('storage_type', 'auto')
        output_format = event.get('output_format', 'jpg')
        quality = event.get('quality', 85)
        
        logger.info(f"Processing URL: {url}")
        logger.info(f"Storage type: {storage_type}")
        
        # Initialize components
        downloader = FileDownloader()
        converter = DicomConverter()
        cleaner = TempCleaner()
        
        # Clean up old temp files first (background cleanup)
        cleaner.cleanup_old_files()
        
        # Create temporary directory for this request
        temp_dir = tempfile.mkdtemp(prefix='dicom_lambda_')
        
        try:
            # Download the file
            downloaded_file_path = downloader.download(url, temp_dir, storage_type)
            
            # Convert DICOM to JPG
            jpg_file_path = converter.convert_to_jpg(
                downloaded_file_path, 
                temp_dir, 
                quality=quality
            )
            
            # Read the converted JPG file and encode to base64
            with open(jpg_file_path, 'rb') as f:
                jpg_data = f.read()
                jpg_base64 = base64.b64encode(jpg_data).decode('utf-8')
            
            # Get file info
            file_size = len(jpg_data)
            
            logger.info(f"Successfully converted DICOM to JPG. Size: {file_size} bytes")
            
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({
                    'success': True,
                    'message': 'DICOM successfully converted to JPG',
                    'data': {
                        'image_base64': jpg_base64,
                        'file_size': file_size,
                        'format': output_format,
                        'quality': quality
                    },
                    'timestamp': datetime.utcnow().isoformat()
                })
            }
            
        finally:
            # Clean up temp files for this request
            cleaner.cleanup_directory(temp_dir)
            
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'success': False,
                'error': str(e),
                'message': 'Failed to process DICOM file',
                'timestamp': datetime.utcnow().isoformat()
            })
        }

# Health check endpoint
def health_check(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """Health check endpoint for the Lambda function"""
    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps({
            'status': 'healthy',
            'service': 'dicom-to-jpg-converter',
            'timestamp': datetime.utcnow().isoformat()
        })
    } 