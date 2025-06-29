import os

from dotenv import load_dotenv

load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_API_KEY")
SUPABASE_BUCKET = "datasets"
BUCKET_NAME = "mindlessmldatasets"
BUCKET_OUTPUT_NAME = "s3://mindlessmloutputs/"

import boto3
import os
from io import BytesIO


def upload_file_to_s3(file_bytes: bytes, filename: str, folder: str = "datasets") -> str:
    s3 = boto3.client(
        "s3",
        aws_access_key_id=os.environ["AWS_ACCESS_KEY_ID"],
        aws_secret_access_key=os.environ["AWS_SECRET_ACCESS_KEY"],
        region_name="eu-west-3"
    )

    key = f"{folder}/{filename}"
    print(f"Subiendo archivo a S3: {key}")
    try:
        print(f"Subiendo archivo a S3: {key} con tamaño {len(file_bytes)} bytes")
        s3.put_object(
            Bucket=BUCKET_NAME,
            Key=key,
            Body=file_bytes,
            ContentType="application/octet-stream"
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise RuntimeError(f"❌ Fallo al subir a S3: {e}")

    return key


def download_file_from_s3(s3_key: str, local_path: str):
    s3 = boto3.client(
        "s3",
        aws_access_key_id=os.environ["AWS_ACCESS_KEY_ID"],
        aws_secret_access_key=os.environ["AWS_SECRET_ACCESS_KEY"],
        region_name="eu-west-3"
    )
    try:
        s3.download_file(
            Bucket=BUCKET_NAME,
            Key=s3_key,
            Filename=local_path
        )

    except Exception as e:
        raise RuntimeError(f"❌ Error al descargar de S3: {e}")


def bytes_to_fileobj(data: bytes):
    return BytesIO(data)
