import mimetypes

import boto3
from botocore.exceptions import ClientError, NoRegionError

from app.core.config import settings


def get_s3_client():
    try:
        return boto3.client(
            "s3",
            aws_access_key_id=settings.AWS_ACCESS_KEY,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            region_name=settings.AWS_REGION,  # Make sure this is set in your config
        )
    except NoRegionError:
        print("AWS_REGION is not set. Please set it in your configuration.")
        raise
    except Exception as e:
        print(f"Error creating S3 client: {e}")
        raise


s3_client = get_s3_client()


def upload_file_to_s3(file, folder, filename):
    try:
        key = f"{folder}/{filename}"
        content_type, _ = mimetypes.guess_type(filename)
        if content_type is None:
            content_type = "application/octet-stream"

        s3_client.upload_fileobj(
            file, settings.S3_BUCKET_NAME, key, ExtraArgs={"ContentType": content_type}
        )
        return key
    except ClientError as e:
        print(f"Error uploading file to S3: {e}")
        return None


def delete_file_from_s3(key):
    try:
        s3_client.delete_object(Bucket=settings.S3_BUCKET_NAME, Key=key)
        print(f"File {key} successfully deleted from S3")
        return True
    except ClientError as e:
        print(f"Error deleting file from S3: {e}")
        return False


def delete_folder_from_s3(folder_key):
    try:
        paginator = s3_client.get_paginator("list_objects_v2")
        pages = paginator.paginate(Bucket=settings.S3_BUCKET_NAME, Prefix=folder_key)
        delete_keys = []
        for page in pages:
            if "Contents" in page:
                delete_keys.extend([{"Key": obj["Key"]} for obj in page["Contents"]])

        if delete_keys:
            s3_client.delete_objects(
                Bucket=settings.S3_BUCKET_NAME, Delete={"Objects": delete_keys}
            )
            print(f"Folder {folder_key} successfully deleted from S3")
        else:
            print(f"No objects found for folder {folder_key} in S3")
        return True
    except ClientError as e:
        print(f"Error deleting folder from S3: {e}")
        return False
