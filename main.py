#!/usr/bin/env python3

from fastapi import FastAPI, UploadFile, File
import pandas as pd

app = FastAPI()

@app.get("/")
def home():
    return {"message": "Bienvenido a la api de Ml no code"}

@app.post("/upload/")
async def upload_dataset(file: UploadFile = File(...)):
    df = pd.read_csv(file.file)
    return {"message": "Archivo subido exitosamente", "data": df.head()}

@app.get("/train/{model_name}")
def train_model(model_name: str):
    return {"message": f"Entrenando modelo {model_name}"}