import os
import requests
import boto3
import logging
from ftplib import FTP
from urllib.parse import urlparse
from typing import Optional
from botocore.exceptions import ClientError, NoCredentialsError

logger = logging.getLogger(__name__)

class FileDownloader:
    """Handles downloading files from various storage types"""
    
    def __init__(self):
        """Initialize the file downloader"""
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'DICOM-Lambda-Converter/1.0'
        })
        
    def download(self, url: str, temp_dir: str, storage_type: str = 'auto') -> str:
        """
        Download a file from the given URL to temp directory
        
        Args:
            url: The URL to download from
            temp_dir: Temporary directory to save the file
            storage_type: Type of storage ('s3', 'r2', 'ftp', 'auto')
            
        Returns:
            Path to the downloaded file
        """
        if storage_type == 'auto':
            storage_type = self._detect_storage_type(url)
            
        logger.info(f"Downloading from {storage_type}: {url}")
        
        if storage_type == 's3':
            return self._download_from_s3(url, temp_dir)
        elif storage_type == 'r2':
            return self._download_from_r2(url, temp_dir)
        elif storage_type == 'ftp':
            return self._download_from_ftp(url, temp_dir)
        else:
            # Default to HTTP/HTTPS download
            return self._download_from_http(url, temp_dir)
    
    def _detect_storage_type(self, url: str) -> str:
        """Auto-detect storage type based on URL"""
        parsed = urlparse(url)
        
        if parsed.scheme == 'ftp':
            return 'ftp'
        elif 's3.amazonaws.com' in parsed.netloc or parsed.netloc.endswith('.s3.amazonaws.com'):
            return 's3'
        elif 'r2.cloudflarestorage.com' in parsed.netloc or '.r2.cloudflarestorage.com' in parsed.netloc:
            return 'r2'
        else:
            return 'http'
    
    def _download_from_s3(self, url: str, temp_dir: str) -> str:
        """Download file from S3"""
        try:
            parsed = urlparse(url)
            
            # Extract bucket and key from URL
            if parsed.netloc.endswith('.s3.amazonaws.com'):
                # Virtual hosted-style URL
                bucket = parsed.netloc.split('.')[0]
                key = parsed.path.lstrip('/')
            elif 's3.amazonaws.com' in parsed.netloc:
                # Path-style URL
                path_parts = parsed.path.lstrip('/').split('/', 1)
                bucket = path_parts[0]
                key = path_parts[1] if len(path_parts) > 1 else ''
            else:
                raise ValueError(f"Invalid S3 URL format: {url}")
            
            # Initialize S3 client
            s3_client = boto3.client('s3')
            
            # Generate filename
            filename = os.path.basename(key) or 'dicom_file.dcm'
            file_path = os.path.join(temp_dir, filename)
            
            # Download file
            s3_client.download_file(bucket, key, file_path)
            
            logger.info(f"Successfully downloaded from S3: {bucket}/{key}")
            return file_path
            
        except (ClientError, NoCredentialsError) as e:
            logger.error(f"S3 download failed: {str(e)}")
            # Fallback to HTTP download
            return self._download_from_http(url, temp_dir)
    
    def _download_from_r2(self, url: str, temp_dir: str) -> str:
        """Download file from Cloudflare R2"""
        try:
            # R2 can be accessed via S3-compatible API
            # Extract account ID and configure endpoint
            parsed = urlparse(url)
            
            # For R2, we need to configure the endpoint
            # R2 URLs typically look like: https://account-id.r2.cloudflarestorage.com/bucket/key
            if '.r2.cloudflarestorage.com' in parsed.netloc:
                account_id = parsed.netloc.split('.')[0]
                path_parts = parsed.path.lstrip('/').split('/', 1)
                bucket = path_parts[0]
                key = path_parts[1] if len(path_parts) > 1 else ''
                
                # Configure R2 client
                r2_client = boto3.client(
                    's3',
                    endpoint_url=f'https://{account_id}.r2.cloudflarestorage.com',
                    aws_access_key_id=os.environ.get('R2_ACCESS_KEY_ID'),
                    aws_secret_access_key=os.environ.get('R2_SECRET_ACCESS_KEY'),
                    region_name='auto'
                )
                
                # Generate filename
                filename = os.path.basename(key) or 'dicom_file.dcm'
                file_path = os.path.join(temp_dir, filename)
                
                # Download file
                r2_client.download_file(bucket, key, file_path)
                
                logger.info(f"Successfully downloaded from R2: {bucket}/{key}")
                return file_path
            else:
                # Fallback to HTTP download
                return self._download_from_http(url, temp_dir)
                
        except Exception as e:
            logger.error(f"R2 download failed: {str(e)}")
            # Fallback to HTTP download
            return self._download_from_http(url, temp_dir)
    
    def _download_from_ftp(self, url: str, temp_dir: str) -> str:
        """Download file from FTP server"""
        parsed = urlparse(url)
        
        # Extract FTP details
        host = parsed.hostname
        port = parsed.port or 21
        username = parsed.username or 'anonymous'
        password = parsed.password or 'anonymous@'
        file_path_on_server = parsed.path
        
        # Generate local filename
        filename = os.path.basename(file_path_on_server) or 'dicom_file.dcm'
        local_file_path = os.path.join(temp_dir, filename)
        
        try:
            # Connect to FTP server
            ftp = FTP()
            ftp.connect(host, port)
            ftp.login(username, password)
            
            # Download file
            with open(local_file_path, 'wb') as f:
                ftp.retrbinary(f'RETR {file_path_on_server}', f.write)
            
            ftp.quit()
            
            logger.info(f"Successfully downloaded from FTP: {host}{file_path_on_server}")
            return local_file_path
            
        except Exception as e:
            logger.error(f"FTP download failed: {str(e)}")
            raise Exception(f"Failed to download from FTP: {str(e)}")
    
    def _download_from_http(self, url: str, temp_dir: str) -> str:
        """Download file from HTTP/HTTPS URL"""
        try:
            # Make request
            response = self.session.get(url, stream=True, timeout=30)
            response.raise_for_status()
            
            # Get filename from URL or Content-Disposition header
            filename = self._get_filename_from_response(response, url)
            file_path = os.path.join(temp_dir, filename)
            
            # Download file in chunks
            with open(file_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            logger.info(f"Successfully downloaded from HTTP: {url}")
            return file_path
            
        except Exception as e:
            logger.error(f"HTTP download failed: {str(e)}")
            raise Exception(f"Failed to download from HTTP: {str(e)}")
    
    def _get_filename_from_response(self, response: requests.Response, url: str) -> str:
        """Extract filename from response headers or URL"""
        # Try to get filename from Content-Disposition header
        content_disposition = response.headers.get('Content-Disposition')
        if content_disposition:
            if 'filename=' in content_disposition:
                filename = content_disposition.split('filename=')[1].strip('"')
                if filename:
                    return filename
        
        # Fallback to URL path
        parsed = urlparse(url)
        filename = os.path.basename(parsed.path)
        
        # If no filename found, use default
        if not filename or '.' not in filename:
            filename = 'dicom_file.dcm'
        
        return filename 