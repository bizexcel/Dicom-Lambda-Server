# DICOM to JPG Lambda Converter

A serverless AWS Lambda function that converts DICOM medical images to JPG format. This function can download DICOM files from various sources (S3, R2 storage, FTP, HTTP/HTTPS) and convert them to high-quality JPG images.

[![GitHub Repository](https://img.shields.io/badge/GitHub-dicom--server--lambda-blue?style=flat-square&logo=github)](https://github.com/bizexcel/dicom-server-lambda.git)
[![AWS Lambda](https://img.shields.io/badge/AWS-Lambda-orange?style=flat-square&logo=aws)](https://aws.amazon.com/lambda/)
[![Python](https://img.shields.io/badge/Python-3.9+-blue?style=flat-square&logo=python)](https://www.python.org/)

## Features

- **Multi-source support**: Download from S3, Cloudflare R2, FTP, or HTTP/HTTPS
- **Automatic cleanup**: Removes temporary files after processing
- **Background cleanup**: Deletes temp files older than 24 hours
- **Quality control**: Configurable JPG quality settings (1-100)
- **Error handling**: Comprehensive error handling and logging
- **Health check**: Built-in health check endpoint
- **Base64 output**: Returns converted images as base64 encoded strings
- **Organized file structure**: Clean temp folder organization
- **Free tier optimized**: Runs efficiently within AWS Lambda free tier limits

## Project Structure

```
dicom-server-lambda/
├── lambda_function.py      # Main Lambda handler
├── dicom_converter.py      # DICOM to JPG conversion logic
├── file_downloader.py      # Multi-source file downloader
├── temp_cleaner.py         # Temporary file cleanup
├── requirements.txt        # Python dependencies
├── deploy.py              # Automated deployment script
├── test_lambda.py         # Lambda function testing
├── test_local_dicom.py    # Local DICOM file testing
├── lambda_config.json     # Configuration settings
├── .gitignore            # Git ignore file
├── README.md             # This documentation
├── QUICKSTART.md         # Quick start guide
└── temp/                 # Temporary files (auto-created)
    └── converted_*.jpg   # Output files
```

## Prerequisites

### 1. Development Environment
- **Python 3.9+** installed
- **pip** package manager
- **Git** for version control

### 2. AWS Account Setup
- AWS account with appropriate permissions
- AWS CLI configured with credentials
- IAM permissions for:
  - Lambda function creation/management
  - IAM role creation
  - S3 access (if downloading from S3)
  - CloudWatch Logs access

### 3. AWS CLI Installation
```bash
# Install AWS CLI
pip install awscli

# Configure AWS credentials
aws configure
# Enter: AWS Access Key ID
# Enter: AWS Secret Access Key
# Enter: Default region (e.g., us-east-1)
# Enter: Default output format (json)
```

## Installation & Setup

### Step 1: Clone the Repository
```bash
# Clone from GitHub
git clone https://github.com/bizexcel/dicom-server-lambda.git
cd dicom-server-lambda

# Or download and extract ZIP file
```

### Step 2: Create Virtual Environment
```bash
# Create virtual environment
python -m venv dicom-lambda-env

# Activate virtual environment
# On Windows:
dicom-lambda-env\Scripts\activate
# On macOS/Linux:
source dicom-lambda-env/bin/activate
```

### Step 3: Install Dependencies
```bash
# Install Python dependencies
pip install -r requirements.txt

# Install additional deployment dependencies
pip install boto3 awscli
```

### Step 4: Configure AWS Credentials
```bash
# Configure AWS credentials (if not already done)
aws configure

# Verify credentials
aws sts get-caller-identity
```

### Step 5: Test Locally (Recommended)
```bash
# Test with your DICOM file
python test_local_dicom.py "path/to/your/dicom/file.dcm"

# Test with cleanup (removes temp files after test)
python test_local_dicom.py "path/to/your/dicom/file.dcm" --cleanup

# Test Lambda function components
python test_lambda.py
```

## AWS Lambda Deployment

### Option 1: Automated Deployment (Recommended)

The automated deployment script handles everything for you:

```bash
# Deploy using the automated script
python deploy.py dicom-to-jpg-converter us-east-1

# The script will:
# 1. Create deployment package with dependencies
# 2. Create IAM execution role with proper permissions
# 3. Deploy Lambda function with optimized settings
# 4. Set up API Gateway permissions
# 5. Display function URL and management links
```

### Option 2: AWS Console Deployment

#### Step 1: Create Deployment Package
```bash
# Create deployment package
mkdir deployment
pip install -r requirements.txt -t deployment/
cp *.py deployment/

# Create ZIP file
cd deployment
zip -r ../dicom-lambda-deployment.zip .
cd ..
```

#### Step 2: Create Lambda Function via AWS Console

1. **Go to AWS Lambda Console**
   - Navigate to [AWS Lambda Console](https://console.aws.amazon.com/lambda/)
   - Click "Create function"

2. **Function Configuration**
   - **Function name**: `dicom-to-jpg-converter`
   - **Runtime**: `Python 3.9`
   - **Architecture**: `x86_64`

3. **Upload Code**
   - Choose "Upload from" → ".zip file"
   - Upload `dicom-lambda-deployment.zip`

4. **Configure Function**
   - **Handler**: `lambda_function.lambda_handler`
   - **Timeout**: `300 seconds` (5 minutes)
   - **Memory**: `1024 MB`
   - **Environment variables**:
     - `PYTHONPATH`: `/var/task`
     - `LOG_LEVEL`: `INFO`

5. **Create Execution Role**
   - Go to IAM Console
   - Create role with Lambda service
   - Attach policies:
     - `AWSLambdaBasicExecutionRole`
     - `AmazonS3ReadOnlyAccess` (if using S3)

### Option 3: Manual AWS CLI Deployment

```bash
# Create execution role
aws iam create-role \
  --role-name dicom-lambda-execution-role \
  --assume-role-policy-document file://trust-policy.json

# Attach policies
aws iam attach-role-policy \
  --role-name dicom-lambda-execution-role \
  --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole

# Create Lambda function
aws lambda create-function \
  --function-name dicom-to-jpg-converter \
  --runtime python3.9 \
  --role arn:aws:iam::YOUR-ACCOUNT-ID:role/dicom-lambda-execution-role \
  --handler lambda_function.lambda_handler \
  --zip-file fileb://dicom-lambda-deployment.zip \
  --timeout 300 \
  --memory-size 1024
```

## Configuration

### Lambda Function Settings
- **Runtime**: Python 3.9
- **Memory**: 1024 MB (adjust based on image sizes)
- **Timeout**: 300 seconds (5 minutes)
- **Handler**: `lambda_function.lambda_handler`

### Environment Variables
Set these in your Lambda function:
- `PYTHONPATH`: `/var/task` (automatically set)
- `LOG_LEVEL`: `INFO` (optional)
- `R2_ACCESS_KEY_ID`: Your R2 access key (if using R2)
- `R2_SECRET_ACCESS_KEY`: Your R2 secret key (if using R2)

### Supported Storage Types
- **S3**: `s3://bucket/key` or `https://bucket.s3.amazonaws.com/key`
- **R2**: `https://account.r2.cloudflarestorage.com/bucket/key`
- **FTP**: `ftp://username:password@server/path/file.dcm`
- **HTTP/HTTPS**: `https://domain.com/path/file.dcm`

## Usage

### API Request Format
```json
{
  "url": "https://example.com/medical-image.dcm",
  "storage_type": "auto",
  "output_format": "jpg",
  "quality": 85
}
```

### Request Parameters
- `url` (required): URL to the DICOM file
- `storage_type` (optional): Storage type (`auto`, `s3`, `r2`, `ftp`, `http`)
- `output_format` (optional): Output format (default: `jpg`)
- `quality` (optional): JPG quality 1-100 (default: 85)

### Response Format
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
  "timestamp": "2024-01-01T12:00:00",
  "metadata": {
    "PatientName": "DOE^JOHN",
    "Modality": "CT",
    "Rows": 512,
    "Columns": 512
  }
}
```

## API Gateway Setup

### Create REST API
```bash
# Create REST API
aws apigateway create-rest-api \
  --name dicom-converter-api \
  --description "DICOM to JPG converter API"

# Get the API ID from the response
```

### Configure API Gateway
1. **Create Resource**: `/convert`
2. **Create Method**: `POST`
3. **Integration Type**: Lambda Function
4. **Lambda Function**: `dicom-to-jpg-converter`
5. **Enable CORS** (if needed)
6. **Deploy API** to stage (e.g., `prod`)

### API Endpoints
- `POST /convert` - Convert DICOM to JPG
- `GET /health` - Health check

### Test API
```bash
# Test via curl
curl -X POST https://your-api-id.execute-api.region.amazonaws.com/prod/convert \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com/sample.dcm",
    "quality": 90
  }'
```

## Testing

### Local Testing
```bash
# Test with local DICOM file
python test_local_dicom.py "path/to/file.dcm"

# Test with cleanup
python test_local_dicom.py "path/to/file.dcm" --cleanup

# Test Lambda function
python test_lambda.py

# Test with remote URL
python test_lambda.py "https://example.com/sample.dcm"
```

### Remote Testing
```bash
# Test deployed function
aws lambda invoke \
  --function-name dicom-to-jpg-converter \
  --payload '{"url": "https://example.com/sample.dcm"}' \
  response.json

# Check response
cat response.json
```

## Monitoring & Debugging

### CloudWatch Logs
- Function logs: `/aws/lambda/dicom-to-jpg-converter`
- View logs:
  ```bash
  aws logs tail /aws/lambda/dicom-to-jpg-converter --follow
  ```

### Performance Metrics
- **Invocations**: Number of function calls
- **Duration**: Execution time
- **Error rate**: Failed invocations
- **Memory usage**: Peak memory consumption

### Debug Commands
```bash
# Check function configuration
aws lambda get-function-configuration \
  --function-name dicom-to-jpg-converter

# Test with logging
aws lambda invoke \
  --function-name dicom-to-jpg-converter \
  --log-type Tail \
  --payload '{"url": "test"}' \
  response.json
```

## Security Best Practices

### IAM Security
- Use least privilege principle
- Create separate roles for different environments
- Regular permission audits
- Use AWS managed policies when possible

### Data Protection
- DICOM files contain sensitive medical data
- Ensure HIPAA/GDPR compliance if applicable
- Use encryption in transit and at rest
- Implement proper access controls

### Network Security
- Consider VPC configuration for private resources
- Use security groups appropriately
- Enable VPC Flow Logs for monitoring
- Implement API Gateway throttling

## Troubleshooting

### Common Issues

1. **Package Size Too Large**
   ```bash
   # Solution: Use Lambda layers
   aws lambda publish-layer-version \
     --layer-name dicom-dependencies \
     --zip-file fileb://layers.zip
   ```

2. **Timeout Errors**
   - Increase timeout setting (max 15 minutes)
   - Optimize image processing
   - Use async processing for large files

3. **Memory Errors**
   - Increase memory allocation
   - Process images in chunks
   - Monitor memory usage

4. **Permission Errors**
   - Check IAM role permissions
   - Verify S3 bucket policies
   - Ensure proper resource access

### Error Codes
- `400`: Invalid request (missing URL)
- `500`: Internal server error
- `403`: Permission denied
- `404`: Resource not found

## Cost Optimization

### AWS Lambda Pricing
- **Free Tier**: 1M requests/month, 400K GB-seconds/month
- **Paid**: $0.20 per 1M requests + $0.0000166667 per GB-second

### Optimization Tips
- Right-size memory allocation
- Optimize cold start times
- Use provisioned concurrency for consistent performance
- Monitor and optimize execution time
- Implement request batching if applicable

## Updating & Maintenance

### Update Function Code
```bash
# Update using deployment script
python deploy.py dicom-to-jpg-converter us-east-1

# Or update manually
aws lambda update-function-code \
  --function-name dicom-to-jpg-converter \
  --zip-file fileb://dicom-lambda-deployment.zip
```

### Update Configuration
```bash
# Update timeout and memory
aws lambda update-function-configuration \
  --function-name dicom-to-jpg-converter \
  --memory-size 2048 \
  --timeout 600
```

### Version Management
```bash
# Publish new version
aws lambda publish-version \
  --function-name dicom-to-jpg-converter \
  --description "Version 1.1 - Added temp folder organization"

# Create alias
aws lambda create-alias \
  --function-name dicom-to-jpg-converter \
  --name PROD \
  --function-version 1
```

## Contributing

### Development Setup
1. Fork the repository
2. Create feature branch: `git checkout -b feature/new-feature`
3. Make changes and test locally
4. Commit: `git commit -m "Add new feature"`
5. Push: `git push origin feature/new-feature`
6. Create Pull Request

### Code Standards
- Follow PEP 8 style guide
- Add docstrings to functions
- Include error handling
- Write unit tests
- Update documentation

## GitHub Repository

This project is maintained at: [https://github.com/bizexcel/dicom-server-lambda.git](https://github.com/bizexcel/dicom-server-lambda.git)

### Repository Setup
```bash
# Clone repository
git clone https://github.com/bizexcel/dicom-server-lambda.git
cd dicom-server-lambda

# Set up remote (if forking)
git remote add upstream https://github.com/bizexcel/dicom-server-lambda.git

# Push changes
git add .
git commit -m "Initial commit"
git push origin main
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support & Resources

### Documentation
- [AWS Lambda Documentation](https://docs.aws.amazon.com/lambda/)
- [pydicom Documentation](https://pydicom.github.io/)
- [Pillow Documentation](https://pillow.readthedocs.io/)

### Support Channels
1. **GitHub Issues**: For bug reports and feature requests
2. **AWS Support**: For AWS-related issues
3. **Community**: Stack Overflow with tags `aws-lambda`, `dicom`, `python`

### Useful Links
- [AWS Lambda Best Practices](https://docs.aws.amazon.com/lambda/latest/dg/best-practices.html)
- [DICOM Standard](https://www.dicomstandard.org/)
- [Medical Imaging Security](https://www.hhs.gov/hipaa/for-professionals/security/index.html)

## Changelog

### Version 1.1 (Current)
- Added temp folder organization
- Improved cleanup functionality
- Enhanced error handling
- Updated documentation
- Added GitHub integration

### Version 1.0
- Initial release
- Basic DICOM to JPG conversion
- Multi-source support
- AWS Lambda deployment

---

**Made with ❤️ for the medical imaging community**

For questions, issues, or contributions, please visit our [GitHub repository](https://github.com/bizexcel/dicom-server-lambda.git). 