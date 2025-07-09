# Quick Start Guide - DICOM to JPG Lambda

This guide will get you up and running with the DICOM to JPG Lambda function in under 10 minutes.

## Prerequisites Checklist

- [ ] Python 3.9+ installed
- [ ] AWS CLI installed and configured
- [ ] AWS account with Lambda permissions
- [ ] Internet connection for downloading dependencies

## Quick Setup (5 minutes)

### 1. Setup Environment
```bash
# Create and activate virtual environment
python -m venv dicom-env
source dicom-env/bin/activate  # On Windows: dicom-env\Scripts\activate

# Install deployment dependencies
pip install boto3 awscli
```

### 2. Configure AWS (if not already done)
```bash
aws configure
# Enter your AWS Access Key ID
# Enter your AWS Secret Access Key
# Enter your region (e.g., us-east-1)
# Enter output format (json)
```

### 3. Deploy the Function
```bash
# Deploy using the automated script
python deploy.py dicom-to-jpg-converter us-east-1
```

That's it! Your function is now deployed and ready to use.

## Quick Test

### Test the deployed function:
```bash
# Test with AWS CLI
aws lambda invoke \
  --function-name dicom-to-jpg-converter \
  --payload '{"url": "https://example.com/sample.dcm"}' \
  response.json

# Check the response
cat response.json
```

### Test locally (optional):
```bash
# Install dependencies for local testing
pip install -r requirements.txt

# Run local test
python test_lambda.py
```

## Usage Examples

### Basic Usage
```json
{
  "url": "https://your-domain.com/medical-image.dcm"
}
```

### With Options
```json
{
  "url": "https://your-s3-bucket.s3.amazonaws.com/path/to/image.dcm",
  "storage_type": "s3",
  "quality": 90
}
```

### FTP Example
```json
{
  "url": "ftp://username:password@ftp.example.com/path/to/image.dcm",
  "storage_type": "ftp"
}
```

## Response Format
```json
{
  "success": true,
  "message": "DICOM successfully converted to JPG",
  "data": {
    "image_base64": "base64_encoded_image_data",
    "file_size": 123456,
    "format": "jpg",
    "quality": 85
  },
  "timestamp": "2024-01-01T12:00:00"
}
```

## Common Issues & Solutions

### Issue: "Package too large"
**Solution**: The function will work within Lambda limits. If you encounter this, reduce the numpy version or use Lambda layers.

### Issue: "Timeout"
**Solution**: Increase timeout in the deploy script (line 157) or use the AWS console.

### Issue: "Permission denied"
**Solution**: Check your AWS credentials and IAM permissions.

### Issue: "Module not found"
**Solution**: Ensure all dependencies are installed in the deployment package.

## Next Steps

1. **Set up API Gateway**: Create a REST API endpoint for HTTP access
2. **Add monitoring**: Set up CloudWatch alarms for errors and performance
3. **Configure CORS**: If using from a web browser
4. **Add authentication**: Implement API keys or OAuth for security

## API Gateway Setup (Optional)

### Create API Gateway:
```bash
# Create REST API
aws apigateway create-rest-api \
  --name dicom-converter-api \
  --description "DICOM to JPG converter API"

# Note the api-id from the response
```

### Test API Gateway:
```bash
# After setting up API Gateway
curl -X POST https://your-api-id.execute-api.region.amazonaws.com/prod/convert \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com/sample.dcm"}'
```

## Support

- Check the main [README.md](README.md) for detailed documentation
- Review CloudWatch logs for debugging
- Test locally first if issues occur

## File Structure Created
```
├── lambda_function.py      # Main handler
├── dicom_converter.py      # DICOM processing
├── file_downloader.py      # Download logic
├── temp_cleaner.py         # Cleanup logic
├── requirements.txt        # Dependencies
├── deploy.py              # Deployment script
├── test_lambda.py         # Test script
├── lambda_config.json     # Configuration
├── README.md             # Full documentation
└── QUICKSTART.md         # This guide
```

## Cleanup

To remove the Lambda function:
```bash
# Delete the function
aws lambda delete-function --function-name dicom-to-jpg-converter

# Delete the IAM role
aws iam delete-role --role-name dicom-to-jpg-converter-execution-role
```

---

🎉 **Congratulations!** Your DICOM to JPG converter is now running on AWS Lambda and ready to process medical images! 