#!/usr/bin/env python3
"""
Build Script for DICOM Server Lambda Project
This script creates clean deployment packages for GitHub upload and AWS Lambda deployment.
"""

import os
import sys
import shutil
import zipfile
from datetime import datetime
from pathlib import Path

class ProjectBuilder:
    """Handles building and packaging the DICOM Lambda project"""
    
    def __init__(self):
        """Initialize the project builder"""
        self.project_root = Path.cwd()
        self.output_dir = self.project_root / "output"
        self.project_name = "dicom-server-lambda"
        
        # Files to include in the package
        self.project_files = [
            ".gitignore",
            "build.py",
            "deploy.py", 
            "dicom_converter.py",
            "file_downloader.py",
            "lambda_config.json",
            "lambda_function.py",
            "QUICKSTART.md",
            "README.md",
            "requirements.txt",
            "temp_cleaner.py",
            "test_lambda.py",
            "test_local_dicom.py"
        ]
        
        # Directories to exclude
        self.exclude_dirs = {
            "__pycache__",
            ".venv",
            "temp",
            "output",
            ".git",
            "node_modules"
        }
        
        # File patterns to exclude
        self.exclude_patterns = {
            "*.pyc",
            "*.pyo",
            "*.pyd",
            ".DS_Store",
            "Thumbs.db",
            "*.log",
            "*.tmp",
            "*.temp",
            "converted_*.jpg",
            "test_output_*.jpg",
            "*-deployment.zip"
        }
    
    def setup_output_directory(self):
        """Create and clean the output directory"""
        print("📁 Setting up output directory...")
        
        # Create output directory if it doesn't exist
        self.output_dir.mkdir(exist_ok=True)
        
        # Clean existing build files
        for file in self.output_dir.glob("*.zip"):
            try:
                file.unlink()
                print(f"   Removed old build: {file.name}")
            except Exception as e:
                print(f"   Warning: Could not remove {file.name}: {str(e)}")
        
        print(f"✅ Output directory ready: {self.output_dir}")
    
    def validate_project_files(self):
        """Validate that all required project files exist"""
        print("🔍 Validating project files...")
        
        missing_files = []
        for file_path in self.project_files:
            if not (self.project_root / file_path).exists():
                missing_files.append(file_path)
        
        if missing_files:
            print(f"❌ Missing required files: {', '.join(missing_files)}")
            return False
        
        print(f"✅ All {len(self.project_files)} required files found")
        return True
    
    def should_exclude_file(self, file_path: Path) -> bool:
        """Check if a file should be excluded from the package"""
        # Check if in excluded directory
        for part in file_path.parts:
            if part in self.exclude_dirs:
                return True
        
        # Check file patterns
        for pattern in self.exclude_patterns:
            if file_path.match(pattern):
                return True
        
        return False
    
    def create_github_package(self):
        """Create ZIP package for GitHub upload"""
        print("📦 Creating GitHub package...")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        zip_path = self.output_dir / f"{self.project_name}-github-{timestamp}.zip"
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            file_count = 0
            total_size = 0
            
            for file_path in self.project_files:
                source_path = self.project_root / file_path
                if source_path.exists():
                    zip_file.write(source_path, file_path)
                    file_count += 1
                    total_size += source_path.stat().st_size
                    print(f"   Added: {file_path}")
        
        zip_size = zip_path.stat().st_size
        compression_ratio = (1 - zip_size / total_size) * 100 if total_size > 0 else 0
        
        print(f"✅ GitHub package created: {zip_path.name}")
        print(f"   Files: {file_count}")
        print(f"   Original size: {total_size:,} bytes")
        print(f"   ZIP size: {zip_size:,} bytes")
        print(f"   Compression: {compression_ratio:.1f}%")
        
        return zip_path
    
    def create_lambda_package(self):
        """Create ZIP package for AWS Lambda deployment"""
        print("🚀 Creating Lambda deployment package...")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        zip_path = self.output_dir / f"{self.project_name}-lambda-{timestamp}.zip"
        
        # Lambda-specific files (exclude test files and docs)
        lambda_files = [
            "lambda_function.py",
            "dicom_converter.py", 
            "file_downloader.py",
            "temp_cleaner.py",
            "requirements.txt"
        ]
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            file_count = 0
            total_size = 0
            
            for file_path in lambda_files:
                source_path = self.project_root / file_path
                if source_path.exists():
                    zip_file.write(source_path, file_path)
                    file_count += 1
                    total_size += source_path.stat().st_size
                    print(f"   Added: {file_path}")
        
        zip_size = zip_path.stat().st_size
        compression_ratio = (1 - zip_size / total_size) * 100 if total_size > 0 else 0
        
        print(f"✅ Lambda package created: {zip_path.name}")
        print(f"   Files: {file_count}")
        print(f"   Original size: {total_size:,} bytes")
        print(f"   ZIP size: {zip_size:,} bytes")
        print(f"   Compression: {compression_ratio:.1f}%")
        
        return zip_path
    
    def create_simple_package(self):
        """Create simple ZIP package with current name for compatibility"""
        print("📄 Creating simple package...")
        
        zip_path = self.output_dir / f"{self.project_name}.zip"
        
        # Remove existing file if it exists
        if zip_path.exists():
            zip_path.unlink()
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            file_count = 0
            total_size = 0
            
            for file_path in self.project_files:
                source_path = self.project_root / file_path
                if source_path.exists():
                    zip_file.write(source_path, file_path)
                    file_count += 1
                    total_size += source_path.stat().st_size
        
        zip_size = zip_path.stat().st_size
        
        print(f"✅ Simple package created: {zip_path.name}")
        print(f"   Files: {file_count}")
        print(f"   ZIP size: {zip_size:,} bytes")
        
        return zip_path
    
    def display_package_info(self, packages):
        """Display information about created packages"""
        print("\n" + "="*60)
        print("📋 BUILD SUMMARY")
        print("="*60)
        
        for package_type, zip_path in packages.items():
            if zip_path and zip_path.exists():
                size = zip_path.stat().st_size
                print(f"✅ {package_type}: {zip_path.name} ({size:,} bytes)")
            else:
                print(f"❌ {package_type}: Failed to create")
        
        print(f"\n📁 All packages saved to: {self.output_dir}")
        print(f"🕒 Build completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    def build_all(self):
        """Build all package types"""
        print("🏗️  DICOM Server Lambda Build System")
        print("="*60)
        
        try:
            # Setup
            self.setup_output_directory()
            
            # Validate
            if not self.validate_project_files():
                return False
            
            # Build packages
            packages = {}
            packages["GitHub Package"] = self.create_github_package()
            packages["Lambda Package"] = self.create_lambda_package() 
            packages["Simple Package"] = self.create_simple_package()
            
            # Summary
            self.display_package_info(packages)
            
            return True
            
        except Exception as e:
            print(f"❌ Build failed: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

def main():
    """Main build function"""
    
    # Parse command line arguments
    build_type = "all"
    if len(sys.argv) > 1:
        build_type = sys.argv[1].lower()
    
    builder = ProjectBuilder()
    
    if build_type == "github":
        builder.setup_output_directory()
        if builder.validate_project_files():
            builder.create_github_package()
    elif build_type == "lambda": 
        builder.setup_output_directory()
        if builder.validate_project_files():
            builder.create_lambda_package()
    elif build_type == "simple":
        builder.setup_output_directory()
        if builder.validate_project_files():
            builder.create_simple_package()
    elif build_type == "all":
        success = builder.build_all()
        if not success:
            sys.exit(1)
    else:
        print("Usage: python build.py [all|github|lambda|simple]")
        print("  all    - Build all package types (default)")
        print("  github - Build package for GitHub upload")
        print("  lambda - Build package for AWS Lambda deployment")
        print("  simple - Build simple package with standard name")
        sys.exit(1)
    
    print("\n🎉 Build completed successfully!")

if __name__ == "__main__":
    main() 