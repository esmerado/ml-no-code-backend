import json

import boto3
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()
sqs = boto3.client("sqs")

SQS_QUEUE_URL = "https://sqs.eu-west-3.amazonaws.com/517681924045/training-queue"


class TrainRequest(BaseModel):
    dataset_s3_path: str
    target_column: str
    output_s3_path: str


@app.post("/api/train-free-model")
def enqueue_training(request: TrainRequest):
    try:
        sqs.send_message(
            QueueUrl=SQS_QUEUE_URL,
            MessageBody=json.dumps(request.dict())
        )
        return {"message": "Modelo encolado correctamente"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
