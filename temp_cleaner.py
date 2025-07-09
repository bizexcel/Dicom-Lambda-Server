import os
import shutil
import tempfile
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import List

logger = logging.getLogger(__name__)

class TempCleaner:
    """Handles cleanup of temporary files and directories"""
    
    def __init__(self, max_age_hours: int = 24):
        """
        Initialize the temp cleaner
        
        Args:
            max_age_hours: Maximum age in hours before files are deleted
        """
        self.max_age_hours = max_age_hours
        self.temp_base_dir = tempfile.gettempdir()
        
    def cleanup_old_files(self) -> dict:
        """
        Clean up temp files older than max_age_hours
        
        Returns:
            Dictionary with cleanup statistics
        """
        try:
            cutoff_time = datetime.now() - timedelta(hours=self.max_age_hours)
            
            cleaned_files = 0
            cleaned_dirs = 0
            total_size_freed = 0
            errors = []
            
            logger.info(f"Starting cleanup of files older than {self.max_age_hours} hours")
            
            # Look for directories with our prefix
            temp_dirs = self._find_temp_directories()
            
            for temp_dir in temp_dirs:
                try:
                    # Get directory creation time
                    dir_stat = os.stat(temp_dir)
                    dir_time = datetime.fromtimestamp(dir_stat.st_mtime)
                    
                    if dir_time < cutoff_time:
                        # Calculate size before deletion
                        dir_size = self._get_directory_size(temp_dir)
                        
                        # Remove the directory
                        shutil.rmtree(temp_dir)
                        
                        cleaned_dirs += 1
                        total_size_freed += dir_size
                        
                        logger.info(f"Cleaned up temp directory: {temp_dir}")
                        
                except Exception as e:
                    error_msg = f"Failed to clean directory {temp_dir}: {str(e)}"
                    logger.error(error_msg)
                    errors.append(error_msg)
            
            # Also clean individual files with our prefix
            temp_files = self._find_temp_files()
            
            for temp_file in temp_files:
                try:
                    # Get file modification time
                    file_stat = os.stat(temp_file)
                    file_time = datetime.fromtimestamp(file_stat.st_mtime)
                    
                    if file_time < cutoff_time:
                        # Get file size before deletion
                        file_size = file_stat.st_size
                        
                        # Remove the file
                        os.remove(temp_file)
                        
                        cleaned_files += 1
                        total_size_freed += file_size
                        
                        logger.info(f"Cleaned up temp file: {temp_file}")
                        
                except Exception as e:
                    error_msg = f"Failed to clean file {temp_file}: {str(e)}"
                    logger.error(error_msg)
                    errors.append(error_msg)
            
            result = {
                'cleaned_directories': cleaned_dirs,
                'cleaned_files': cleaned_files,
                'total_size_freed_bytes': total_size_freed,
                'total_size_freed_mb': round(total_size_freed / (1024 * 1024), 2),
                'errors': errors,
                'cleanup_time': datetime.now().isoformat()
            }
            
            logger.info(f"Cleanup completed. Dirs: {cleaned_dirs}, Files: {cleaned_files}, Size freed: {result['total_size_freed_mb']} MB")
            
            return result
            
        except Exception as e:
            logger.error(f"Cleanup operation failed: {str(e)}")
            return {
                'error': str(e),
                'cleanup_time': datetime.now().isoformat()
            }
    
    def cleanup_directory(self, directory_path: str) -> bool:
        """
        Clean up a specific directory
        
        Args:
            directory_path: Path to the directory to clean up
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if os.path.exists(directory_path):
                shutil.rmtree(directory_path)
                logger.info(f"Cleaned up directory: {directory_path}")
                return True
            else:
                logger.warning(f"Directory not found: {directory_path}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to clean directory {directory_path}: {str(e)}")
            return False
    
    def cleanup_file(self, file_path: str) -> bool:
        """
        Clean up a specific file
        
        Args:
            file_path: Path to the file to clean up
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"Cleaned up file: {file_path}")
                return True
            else:
                logger.warning(f"File not found: {file_path}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to clean file {file_path}: {str(e)}")
            return False
    
    def _find_temp_directories(self) -> List[str]:
        """Find temporary directories created by our Lambda function"""
        try:
            temp_dirs = []
            
            # Look for directories with our prefix
            for item in os.listdir(self.temp_base_dir):
                item_path = os.path.join(self.temp_base_dir, item)
                if os.path.isdir(item_path) and item.startswith('dicom_lambda_'):
                    temp_dirs.append(item_path)
            
            return temp_dirs
            
        except Exception as e:
            logger.error(f"Failed to find temp directories: {str(e)}")
            return []
    
    def _find_temp_files(self) -> List[str]:
        """Find temporary files created by our Lambda function"""
        try:
            temp_files = []
            
            # Look for files with our prefix
            for item in os.listdir(self.temp_base_dir):
                item_path = os.path.join(self.temp_base_dir, item)
                if os.path.isfile(item_path) and (
                    item.startswith('dicom_lambda_') or 
                    item.startswith('tmp') and (item.endswith('.dcm') or item.endswith('.jpg'))
                ):
                    temp_files.append(item_path)
            
            return temp_files
            
        except Exception as e:
            logger.error(f"Failed to find temp files: {str(e)}")
            return []
    
    def _get_directory_size(self, directory_path: str) -> int:
        """Get the total size of a directory in bytes"""
        try:
            total_size = 0
            
            for dirpath, dirnames, filenames in os.walk(directory_path):
                for filename in filenames:
                    file_path = os.path.join(dirpath, filename)
                    try:
                        total_size += os.path.getsize(file_path)
                    except (OSError, IOError):
                        # Skip files that can't be accessed
                        pass
            
            return total_size
            
        except Exception as e:
            logger.error(f"Failed to get directory size: {str(e)}")
            return 0
    
    def get_temp_usage_stats(self) -> dict:
        """
        Get statistics about temp directory usage
        
        Returns:
            Dictionary with temp directory statistics
        """
        try:
            stats = {
                'total_temp_directories': 0,
                'total_temp_files': 0,
                'total_size_bytes': 0,
                'oldest_file_age_hours': 0,
                'newest_file_age_hours': 0
            }
            
            temp_dirs = self._find_temp_directories()
            temp_files = self._find_temp_files()
            
            stats['total_temp_directories'] = len(temp_dirs)
            stats['total_temp_files'] = len(temp_files)
            
            # Calculate sizes and ages
            current_time = datetime.now()
            oldest_time = current_time
            newest_time = current_time
            
            for temp_dir in temp_dirs:
                try:
                    dir_size = self._get_directory_size(temp_dir)
                    stats['total_size_bytes'] += dir_size
                    
                    dir_stat = os.stat(temp_dir)
                    dir_time = datetime.fromtimestamp(dir_stat.st_mtime)
                    
                    if dir_time < oldest_time:
                        oldest_time = dir_time
                    if dir_time > newest_time:
                        newest_time = dir_time
                        
                except Exception:
                    pass
            
            for temp_file in temp_files:
                try:
                    file_stat = os.stat(temp_file)
                    stats['total_size_bytes'] += file_stat.st_size
                    
                    file_time = datetime.fromtimestamp(file_stat.st_mtime)
                    
                    if file_time < oldest_time:
                        oldest_time = file_time
                    if file_time > newest_time:
                        newest_time = file_time
                        
                except Exception:
                    pass
            
            # Calculate ages in hours
            if oldest_time != current_time:
                stats['oldest_file_age_hours'] = (current_time - oldest_time).total_seconds() / 3600
            if newest_time != current_time:
                stats['newest_file_age_hours'] = (current_time - newest_time).total_seconds() / 3600
            
            stats['total_size_mb'] = round(stats['total_size_bytes'] / (1024 * 1024), 2)
            
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get temp usage stats: {str(e)}")
            return {'error': str(e)} 