#!/usr/bin/env python3
"""
AWS Lambda Deployment Script for DICOM to JPG Converter
This script helps deploy the Lambda function with all dependencies.
"""

import os
import sys
import json
import boto3
import zipfile
import shutil
import subprocess
from pathlib import Path
from datetime import datetime

class LambdaDeployer:
    def __init__(self, function_name: str, region: str = 'us-east-1'):
        """
        Initialize the Lambda deployer
        
        Args:
            function_name: Name of the Lambda function
            region: AWS region
        """
        self.function_name = function_name
        self.region = region
        self.lambda_client = boto3.client('lambda', region_name=region)
        self.iam_client = boto3.client('iam', region_name=region)
        
        # Deployment configuration
        self.deployment_package = f"{function_name}-deployment.zip"
        self.temp_dir = "lambda_deployment_temp"
        
    def create_deployment_package(self):
        """Create deployment package with all dependencies"""
        print("Creating deployment package...")
        
        # Clean up any existing temp directory
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
        
        # Create temp directory
        os.makedirs(self.temp_dir)
        
        # Install dependencies
        print("Installing dependencies...")
        subprocess.run([
            sys.executable, '-m', 'pip', 'install',
            '-r', 'requirements.txt',
            '-t', self.temp_dir
        ], check=True)
        
        # Copy source files
        print("Copying source files...")
        source_files = [
            'lambda_function.py',
            'dicom_converter.py',
            'file_downloader.py',
            'temp_cleaner.py'
        ]
        
        for file in source_files:
            if os.path.exists(file):
                shutil.copy2(file, self.temp_dir)
            else:
                print(f"Warning: {file} not found")
        
        # Create ZIP package
        print("Creating ZIP package...")
        with zipfile.ZipFile(self.deployment_package, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for root, dirs, files in os.walk(self.temp_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, self.temp_dir)
                    zip_file.write(file_path, arcname)
        
        # Clean up temp directory
        shutil.rmtree(self.temp_dir)
        
        print(f"Deployment package created: {self.deployment_package}")
        print(f"Package size: {os.path.getsize(self.deployment_package) / (1024*1024):.2f} MB")
        
    def create_execution_role(self):
        """Create IAM execution role for Lambda"""
        role_name = f"{self.function_name}-execution-role"
        
        trust_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {
                        "Service": "lambda.amazonaws.com"
                    },
                    "Action": "sts:AssumeRole"
                }
            ]
        }
        
        try:
            # Try to get existing role
            response = self.iam_client.get_role(RoleName=role_name)
            role_arn = response['Role']['Arn']
            print(f"Using existing role: {role_arn}")
            
        except self.iam_client.exceptions.NoSuchEntityException:
            # Create new role
            print(f"Creating IAM role: {role_name}")
            
            response = self.iam_client.create_role(
                RoleName=role_name,
                AssumeRolePolicyDocument=json.dumps(trust_policy),
                Description=f"Execution role for {self.function_name} Lambda function"
            )
            
            role_arn = response['Role']['Arn']
            
            # Attach basic execution policy
            self.iam_client.attach_role_policy(
                RoleName=role_name,
                PolicyArn='arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole'
            )
            
            # Attach S3 read policy for downloading files
            s3_policy = {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Effect": "Allow",
                        "Action": [
                            "s3:GetObject",
                            "s3:GetObjectVersion"
                        ],
                        "Resource": "*"
                    }
                ]
            }
            
            self.iam_client.put_role_policy(
                RoleName=role_name,
                PolicyName=f"{self.function_name}-s3-policy",
                PolicyDocument=json.dumps(s3_policy)
            )
            
            print(f"Created role: {role_arn}")
            
        return role_arn
    
    def deploy_function(self, role_arn: str):
        """Deploy or update Lambda function"""
        
        # Read the deployment package
        with open(self.deployment_package, 'rb') as f:
            zip_content = f.read()
        
        try:
            # Try to update existing function
            print(f"Updating existing function: {self.function_name}")
            
            response = self.lambda_client.update_function_code(
                FunctionName=self.function_name,
                ZipFile=zip_content
            )
            
            # Update configuration
            self.lambda_client.update_function_configuration(
                FunctionName=self.function_name,
                Runtime='python3.9',
                Handler='lambda_function.lambda_handler',
                Role=role_arn,
                Timeout=300,  # 5 minutes
                MemorySize=1024,  # 1GB
                Environment={
                    'Variables': {
                        'PYTHONPATH': '/var/task'
                    }
                }
            )
            
            print(f"Function updated successfully")
            
        except self.lambda_client.exceptions.ResourceNotFoundException:
            # Create new function
            print(f"Creating new function: {self.function_name}")
            
            response = self.lambda_client.create_function(
                FunctionName=self.function_name,
                Runtime='python3.9',
                Role=role_arn,
                Handler='lambda_function.lambda_handler',
                Code={'ZipFile': zip_content},
                Description='DICOM to JPG converter Lambda function',
                Timeout=300,  # 5 minutes
                MemorySize=1024,  # 1GB
                Environment={
                    'Variables': {
                        'PYTHONPATH': '/var/task'
                    }
                }
            )
            
            print(f"Function created successfully")
        
        return response['FunctionArn']
    
    def create_api_gateway_trigger(self, function_arn: str):
        """Create API Gateway trigger for the Lambda function"""
        try:
            # Add permission for API Gateway to invoke Lambda
            self.lambda_client.add_permission(
                FunctionName=self.function_name,
                StatementId='api-gateway-invoke',
                Action='lambda:InvokeFunction',
                Principal='apigateway.amazonaws.com',
                SourceArn=f"arn:aws:execute-api:{self.region}:*:*/*/*"
            )
            
            print("Added API Gateway permission")
            
        except self.lambda_client.exceptions.ResourceConflictException:
            print("API Gateway permission already exists")
    
    def deploy(self):
        """Full deployment process"""
        print(f"Starting deployment of {self.function_name}...")
        print(f"Region: {self.region}")
        print(f"Timestamp: {datetime.now().isoformat()}")
        print("-" * 50)
        
        try:
            # Step 1: Create deployment package
            self.create_deployment_package()
            
            # Step 2: Create execution role
            role_arn = self.create_execution_role()
            
            # Step 3: Deploy function
            function_arn = self.deploy_function(role_arn)
            
            # Step 4: Create API Gateway trigger
            self.create_api_gateway_trigger(function_arn)
            
            print("-" * 50)
            print("Deployment completed successfully!")
            print(f"Function ARN: {function_arn}")
            print(f"Function URL: https://console.aws.amazon.com/lambda/home?region={self.region}#/functions/{self.function_name}")
            
            # Clean up deployment package
            if os.path.exists(self.deployment_package):
                os.remove(self.deployment_package)
                
        except Exception as e:
            print(f"Deployment failed: {str(e)}")
            sys.exit(1)

def main():
    """Main deployment function"""
    
    if len(sys.argv) < 2:
        print("Usage: python deploy.py <function-name> [region]")
        print("Example: python deploy.py dicom-to-jpg-converter us-east-1")
        sys.exit(1)
    
    function_name = sys.argv[1]
    region = sys.argv[2] if len(sys.argv) > 2 else 'us-east-1'
    
    deployer = LambdaDeployer(function_name, region)
    deployer.deploy()

if __name__ == "__main__":
    main() 