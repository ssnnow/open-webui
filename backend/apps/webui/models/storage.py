import os
import boto3
from botocore.exceptions import ClientError
from config import (S3_SECRET_ID, S3_SECRET_KEY, S3_REGION, S3_BUCKET_NAME, S3_ENDPOINT,
                    STORAGE_PROVIDER, UPLOAD_DIR)
LOCAL_UPLOAD_DIR = UPLOAD_DIR
class StorageProvider:
    def __init__(self):
        if STORAGE_PROVIDER == 'local':
            self._storage_type = 'local'       
        elif STORAGE_PROVIDER == 's3':
            self._storage_type = 's3'
            self.client = boto3.client(
                's3',
                region_name=S3_REGION,
                endpoint_url=S3_ENDPOINT,
                aws_access_key_id=S3_SECRET_ID,
                aws_secret_access_key=S3_SECRET_KEY
            )
        else:
            raise ValueError("Unsupported storage provider specified in the configuration.")

    def _get_bucket(self):
        if self._storage_type == 'cos':
            return S3_BUCKET_NAME
        elif self._storage_type == 's3':
            return S3_BUCKET_NAME

    def upload_file(self, file, filename):
        if self._storage_type == 'local':
            file_path = os.path.join(LOCAL_UPLOAD_DIR, filename)
            with open(file_path, 'wb') as f:
                f.write(file.read())
            return filename
        else:
            try:
                bucket = self._get_bucket()
                self.client.upload_fileobj(file, bucket, filename)
                return filename
            except ClientError as e:
                raise RuntimeError(f"Error uploading file: {e}")

    def list_files(self):
        if self._storage_type == 'local':
            return [f for f in os.listdir(LOCAL_UPLOAD_DIR) if os.path.isfile(os.path.join(LOCAL_UPLOAD_DIR, f))]
        else:
            try:
                bucket = self._get_bucket()
                response = self.client.list_objects_v2(Bucket=bucket)
                if 'Contents' in response:
                    return [content['Key'] for content in response['Contents']]
                return []
            except ClientError as e:
                raise RuntimeError(f"Error listing files: {e}")

    def delete_all_files(self):
        if self._storage_type == 'local':
            for filename in os.listdir(LOCAL_UPLOAD_DIR):
                file_path = os.path.join(LOCAL_UPLOAD_DIR, filename)
                if os.path.isfile(file_path):
                    os.remove(file_path)
        else:
            try:
                bucket = self._get_bucket()
                response = self.client.list_objects_v2(Bucket=bucket)
                if 'Contents' in response:
                    for content in response['Contents']:
                        self.client.delete_object(Bucket=bucket, Key=content['Key'])
            except ClientError as e:
                raise RuntimeError(f"Error deleting all files: {e}")

    def get_file(self, filename):
        if self._storage_type == 'local':
            file_path = os.path.join(LOCAL_UPLOAD_DIR, filename)
            if os.path.isfile(file_path):
                with open(file_path, 'rb') as f:
                    return f.read(), 'application/octet-stream'
            else:
                raise FileNotFoundError(f"File {filename} not found in local storage.")
        else:
            try:
                bucket = self._get_bucket()
                response = self.client.get_object(Bucket=bucket, Key=filename)
                return response['Body'].read(), response['ContentType']
            except ClientError as e:
                raise RuntimeError(f"Error fetching file: {e}")
    def delete_file(self, filename):
        if self._storage_type == 'local':
            file_path = os.path.join(LOCAL_UPLOAD_DIR, filename)
            if os.path.isfile(file_path):
                os.remove(file_path)
            else:
                raise FileNotFoundError(f"File {filename} not found in local storage.")
        else:
            try:
                bucket = self._get_bucket()
                self.client.delete_object(Bucket=bucket, Key=filename)
            except ClientError as e:
                raise RuntimeError(f"Error deleting file: {e}")
