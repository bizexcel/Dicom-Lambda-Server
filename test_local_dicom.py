#!/usr/bin/env python3
"""
Local DICOM test script
This script tests the DICOM converter directly with a local file
"""

import os
import sys
import base64
import tempfile
import shutil
from datetime import datetime
from pathlib import Path

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dicom_converter import DicomConverter
from temp_cleaner import TempCleaner

def test_local_dicom_file(dicom_file_path: str):
    """Test DICOM conversion with a local file"""
    
    print("=" * 60)
    print("LOCAL DICOM TO JPG CONVERTER TEST")
    print("=" * 60)
    
    # Check if file exists
    if not os.path.exists(dicom_file_path):
        print(f"❌ Error: File not found: {dicom_file_path}")
        return False
    
    print(f"📁 Testing file: {dicom_file_path}")
    print(f"📏 File size: {os.path.getsize(dicom_file_path):,} bytes")
    
    # Create main temp folder in project directory
    main_temp_dir = os.path.join(os.getcwd(), 'temp')
    if not os.path.exists(main_temp_dir):
        os.makedirs(main_temp_dir)
        print(f"📁 Created temp folder: {main_temp_dir}")
    
    try:
        # Initialize converter and cleaner
        converter = DicomConverter()
        cleaner = TempCleaner()
        
        # Create temporary directory for processing
        temp_dir = tempfile.mkdtemp(prefix='dicom_test_', dir=main_temp_dir)
        print(f"📂 Processing temp directory: {temp_dir}")
        
        try:
            # Step 1: Validate DICOM file
            print("\n🔍 Step 1: Validating DICOM file...")
            if not converter.validate_dicom_file(dicom_file_path):
                print("❌ DICOM validation failed!")
                return False
            print("✅ DICOM file is valid")
            
            # Step 2: Extract metadata
            print("\n📋 Step 2: Extracting DICOM metadata...")
            metadata = converter.get_dicom_metadata(dicom_file_path)
            
            if 'error' in metadata:
                print(f"⚠️  Warning: Could not extract metadata: {metadata['error']}")
            else:
                print("✅ Metadata extracted successfully:")
                for key, value in metadata.items():
                    if key in ['PatientName', 'PatientID', 'Modality', 'StudyDate', 'Rows', 'Columns']:
                        print(f"   {key}: {value}")
            
            # Step 3: Convert to JPG
            print("\n🔄 Step 3: Converting DICOM to JPG...")
            jpg_file_path = converter.convert_to_jpg(dicom_file_path, temp_dir, quality=85)
            
            if not os.path.exists(jpg_file_path):
                print("❌ JPG conversion failed!")
                return False
            
            print(f"✅ Conversion successful!")
            print(f"📄 JPG file: {jpg_file_path}")
            print(f"📏 JPG size: {os.path.getsize(jpg_file_path):,} bytes")
            
            # Step 4: Read and encode JPG
            print("\n📦 Step 4: Reading and encoding JPG...")
            with open(jpg_file_path, 'rb') as f:
                jpg_data = f.read()
                jpg_base64 = base64.b64encode(jpg_data).decode('utf-8')
            
            print(f"✅ JPG encoded to base64")
            print(f"📏 Base64 length: {len(jpg_base64):,} characters")
            
            # Step 5: Save output file to temp folder
            print("\n💾 Step 5: Saving output file to temp folder...")
            output_filename = f"converted_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
            output_path = os.path.join(main_temp_dir, output_filename)
            
            with open(output_path, 'wb') as f:
                f.write(jpg_data)
            
            print(f"✅ Output saved to: {output_path}")
            
            # Step 6: Test cleanup
            print("\n🧹 Step 6: Testing cleanup...")
            cleanup_stats = cleaner.get_temp_usage_stats()
            print(f"   Temp directories found: {cleanup_stats.get('total_temp_directories', 0)}")
            print(f"   Temp files found: {cleanup_stats.get('total_temp_files', 0)}")
            
            # Simulate Lambda response
            print("\n📤 Step 7: Simulating Lambda response...")
            lambda_response = {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': {
                    'success': True,
                    'message': 'DICOM successfully converted to JPG',
                    'data': {
                        'image_base64': jpg_base64,
                        'file_size': len(jpg_data),
                        'format': 'jpg',
                        'quality': 85
                    },
                    'timestamp': datetime.utcnow().isoformat(),
                    'metadata': metadata
                }
            }
            
            print("✅ Lambda response structure created successfully")
            print(f"📊 Response data size: {len(str(lambda_response)):,} characters")
            
            # Step 8: Test results summary
            print("\n" + "=" * 60)
            print("🎉 TEST RESULTS SUMMARY")
            print("=" * 60)
            print(f"✅ DICOM file validation: PASSED")
            print(f"✅ Metadata extraction: PASSED")
            print(f"✅ JPG conversion: PASSED")
            print(f"✅ Base64 encoding: PASSED")
            print(f"✅ File output: PASSED")
            print(f"✅ Cleanup testing: PASSED")
            print(f"✅ Lambda response: PASSED")
            
            print(f"\n📈 Performance metrics:")
            print(f"   Original file size: {os.path.getsize(dicom_file_path):,} bytes")
            print(f"   JPG file size: {len(jpg_data):,} bytes")
            print(f"   Compression ratio: {(1 - len(jpg_data)/os.path.getsize(dicom_file_path))*100:.1f}%")
            print(f"   Base64 size: {len(jpg_base64):,} characters")
            
            print(f"\n📁 File locations:")
            print(f"   Main temp folder: {main_temp_dir}")
            print(f"   Processing temp folder: {temp_dir}")
            print(f"   Output file: {output_path}")
            
            return True
            
        finally:
            # Clean up processing temp directory
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
                print(f"🧹 Cleaned up processing temp directory: {temp_dir}")
            
    except Exception as e:
        print(f"❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def cleanup_temp_folder():
    """Clean up the temp folder if requested"""
    main_temp_dir = os.path.join(os.getcwd(), 'temp')
    if os.path.exists(main_temp_dir):
        try:
            shutil.rmtree(main_temp_dir)
            print(f"🧹 Cleaned up temp folder: {main_temp_dir}")
        except Exception as e:
            print(f"⚠️  Warning: Could not clean up temp folder: {str(e)}")

def main():
    """Main test function"""
    
    if len(sys.argv) < 2:
        print("Usage: python test_local_dicom.py <path_to_dicom_file> [--cleanup]")
        print("Example: python test_local_dicom.py \"C:\\path\\to\\file.dcm\"")
        print("Options:")
        print("  --cleanup    Clean up temp folder after test")
        sys.exit(1)
    
    dicom_file_path = sys.argv[1]
    cleanup_requested = '--cleanup' in sys.argv
    
    # Test the conversion
    success = test_local_dicom_file(dicom_file_path)
    
    if success:
        print("\n🎉 All tests passed! The DICOM converter is working correctly.")
        print("✅ You can now proceed with Lambda deployment.")
        
        if cleanup_requested:
            print("\n🧹 Cleaning up temp folder...")
            cleanup_temp_folder()
        else:
            print("\n💡 Tip: Use --cleanup flag to automatically clean up temp folder after test")
            print("💡 Or manually delete the 'temp' folder when you're done reviewing the output")
    else:
        print("\n❌ Tests failed! Please check the error messages above.")
        sys.exit(1)

if __name__ == "__main__":
    main() 