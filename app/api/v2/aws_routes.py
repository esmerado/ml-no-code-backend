# FastAPI pipeline: AutoML desde CSV hasta resultados (entrenamiento, predicción, métricas)

import json
import os
import traceback
from uuid import uuid4

import boto3
from fastapi import FastAPI, UploadFile, File, HTTPException, Depends, APIRouter, Form
from pydantic import BaseModel
from supabase import create_client

from app.utils.auth import verify_token
from app.utils.s3_utils import bytes_to_fileobj
from app.utils.supabase_utils import save_model_prediction

app = FastAPI()
router = APIRouter()

# AWS Clients
BUCKET_NAME = "mindlessmldatasets"
BUCKET_OUTPUT_NAME = "s3://mindlessmloutputs/"
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")

s3 = boto3.client(
    "s3",
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name="eu-west-3"
)
lambda_client = boto3.client("lambda", region_name="eu-west-3")

sf = boto3.client('stepfunctions', region_name="eu-west-3")

# Supabase Client
SUPABASE_URL = os.getenv("SUPABASE_MINDLESSML_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_MINDLESSML_SERVICE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)


@router.post("/api/upload")
async def upload_dataset(
        file: UploadFile = File(...),
        user: dict = Depends(verify_token),
        model_id: str = None
):
    user_id = user.get("id")

    if model_id is None:
        model_id = str(uuid4())

    file_id = f"freemium/{user_id}/{model_id}_{file.filename}"
    contents = await file.read()

    try:
        s3.upload_fileobj(
            Fileobj=bytes_to_fileobj(contents),
            Bucket=BUCKET_NAME,
            Key=file_id
        )

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Upload S3 failed: {e}")

    return {"message": "Archivo subido", "s3_key": file_id, "model_id": model_id}


@router.post("/api/upload-prediction")
async def upload_dataset(
        file: UploadFile = File(...),
        user: dict = Depends(verify_token),
        model_id: str = Form(...),
):
    user_id = user.get("id")
    print("Uploading prediction file for user:", user_id, "and model:", model_id)
    file_id = f"freemium/{user_id}/{model_id}_{file.filename}"
    contents = await file.read()

    try:
        s3.upload_fileobj(
            Fileobj=bytes_to_fileobj(contents),
            Bucket=BUCKET_NAME,
            Key=file_id
        )

        save_model_prediction(model_id, file_id)

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Upload S3 failed: {e}")

    return {"message": "Archivo subido", "s3_key": file_id, "model_id": model_id}


class TrainRequest(BaseModel):
    s3_key: str
    target_column: str = "target"


# DONE
@router.post("/api/train")
def start_training(
        request: TrainRequest,
        # user: dict = Depends(verify_token)
):
    # user_id = user.get("user_id")
    try:
        response = lambda_client.invoke(
            FunctionName="start-automl-job",
            InvocationType="RequestResponse",
            Payload=json.dumps({
                "dataset_s3_path": request.s3_key,
                "target_column": request.target_column,
                "output_s3_path": BUCKET_OUTPUT_NAME
            })
        )
        result = json.loads(response["Payload"].read())
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class TrainStatusRequest(BaseModel):
    job_name: str


@router.post("/api/train-status")
def start_training(
        request: TrainStatusRequest
        # user: dict = Depends(verify_token)
):
    try:
        response = lambda_client.invoke(
            FunctionName="check-job-status",
            InvocationType="RequestResponse",
            Payload=json.dumps({
                "auto_ml_job_name": request.job_name,
            })
        )
        result = json.loads(response["Payload"].read())
        result_body = json.loads(result["body"])
        print("result_body", result_body)
        data_body = {
            "user_id": "a6b47208-ae41-455c-bdcd-e48a7204eec1",
            "status": result_body["status"],
            "sagemaker_job_name": request.job_name,
        }
        supabase.table("jobs").insert(data_body).execute()

        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class BestModelRequest(BaseModel):
    job_name: str


@router.post("/api/best-model")
def get_best_model(request: BestModelRequest):
    try:
        response = lambda_client.invoke(
            FunctionName="get-best-model",
            InvocationType="RequestResponse",
            Payload=json.dumps({
                "auto_ml_job_name": request.job_name,
            })
        )
        result = json.loads(response["Payload"].read())
        body = json.loads(result["body"])

        return {
            "model_name": body["best_model_name"],
            "metric": body["metric"],
            "container": body["container"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class RegisterModelRequest(BaseModel):
    model_name: str
    metric: dict
    container: list


@router.post("/api/register-model")
def register_model(request: RegisterModelRequest):
    try:
        response = lambda_client.invoke(
            FunctionName="register-model",
            InvocationType="RequestResponse",
            Payload=json.dumps({
                "best_model_name": request.model_name,
                "metric": request.metric,
                "container": request.container
            })
        )
        result = json.loads(response["Payload"].read())
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class BatchInferenceRequest(BaseModel):
    model_name: str
    input_s3: str
    output_s3: str


@router.post("/api/batch-inference")
def run_batch_inference(request: BatchInferenceRequest):
    try:
        response = lambda_client.invoke(
            FunctionName="run-batch-inference",
            InvocationType="RequestResponse",
            Payload=json.dumps({
                "model_name": request.model_name,
                "input_s3": request.input_s3,
                "output_s3": request.output_s3
            })
        )
        result = json.loads(response["Payload"].read())
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class StoreResultsRequest(BaseModel):
    s3_path: str


@router.post("/api/store-results")
def store_results(request: StoreResultsRequest):
    try:
        response = lambda_client.invoke(
            FunctionName="store-results",
            InvocationType="RequestResponse",
            Payload=json.dumps({
                "s3_path": request.s3_path
            })
        )
        result = json.loads(response["Payload"].read())
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class CreateModelRequest(BaseModel):
    dataset_s3_path: str
    target_column: str = "target"
    output_s3_path: str


# DONE
@router.post("/api/create-model")
def create_model(request: CreateModelRequest):
    try:
        response = sf.start_execution(
            stateMachineArn='arn:aws:states:eu-west-3:517681924045:stateMachine:MindlessML',
            input=json.dumps({
                "dataset_s3_path": request.dataset_s3_path,
                "target_column": request.target_column,
                "output_s3_path": request.output_s3_path
            })
        )
        # No es necesario leer ni cargar JSON, ya es un dict
        return {
            "executionArn": response["executionArn"],
            "startDate": str(response["startDate"])
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class ModelStatus(BaseModel):
    execution_arn: str


@router.get("/api/model-status")
def get_model_status(request: ModelStatus):
    try:
        resp = sf.describe_execution(executionArn=request.execution_arn)

        return {
            "status": resp["status"],
            "output": json.loads(resp["output"]) if resp.get("output") else None,
            "startDate": str(resp["startDate"]),
            "stopDate": str(resp.get("stopDate"))
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class GetModelHistoryRequest(BaseModel):
    execution_arn: str


@router.get("/api/model-history")
def get_model_history(request: GetModelHistoryRequest):
    try:
        events = sf.get_execution_history(
            executionArn=request.execution_arn,
            maxResults=50,
            reverseOrder=True
        )
        return events["events"]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
