import json
import os
import tempfile

import joblib
import pandas as pd
from dotenv import load_dotenv
from fastapi import File, UploadFile, Form, HTTPException
from supabase import create_client

from app.models.machine_learning import machine_learning_model
from app.utils.s3_upload import upload_file_to_supabase

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

load_dotenv()


class ModelService:
    def __init__(self,
                 file: UploadFile = File(...),
                 target: str = Form(...),
                 user_id: str = ''):
        self.file = file
        self.target = target
        self.user_id = user_id
        self.contents = None

    async def save_file(self):
        print(f"📁 Model Service -> save_file: {self.file.filename}")
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as tmp:
                contents = await self.file.read()
                tmp.write(contents)
                tmp_path = tmp.name

            file_url = upload_file_to_supabase(tmp_path, self.user_id)

            if file_url:
                existing = supabase.table("datasets").select("*").eq("file_url", file_url).execute()

                if existing.data:
                    return {"message": "Un dataset con esta url ya existe"}

                res = supabase.table("datasets").insert({
                    "user_id": self.user_id,
                    "filename": self.file.filename,
                    "file_url": file_url,
                    "file_type": self.file.content_type,
                }).execute()

            if res.data and 'id' in res.data[0]:
                dataset_id = res.data[0]['id']
            else:
                raise HTTPException(status_code=500, detail="❌ No se pudo obtener el ID del dataset desde Supabase.")

            os.remove(tmp_path)
            print(f"📁 Archivo CSV guardado con: {dataset_id}")
            return dataset_id

        except Exception as e:
            print(f"❌ Error en save_file: {e}")
            raise HTTPException(status_code=500, detail=f"Error en save_file: {str(e)}")

    async def save_model(self, model_path: str):
        print(f"📁 Model Service -> save_model")

        try:
            uploaded_url = upload_file_to_supabase(model_path, self.user_id)
            print(f"📁 Archivo PKL guardado con: {uploaded_url}")
            return uploaded_url

        except Exception as e:
            print(f"❌ Error en save_model: {e}")
            raise HTTPException(status_code=500, detail=f"Error guardando modelo: {str(e)}")

    async def train(self):
        print(f"📁 Model Service -> train: {self.file.filename}")
        try:
            suffix = self.file.filename.split(".")[-1]

            if self.contents is None:
                self.contents = await self.file.read()

            # Guardamos el archivo
            dataset_id = await self.save_file()

            # Creamos un archivo temporal
            with tempfile.NamedTemporaryFile(delete=False, suffix=f'.{suffix}') as tmp:
                tmp.write(self.contents)
                tmp_path = tmp.name

            df = pd.read_csv(tmp_path)

            # Entrenamos el modelo
            model = await machine_learning_model(
                df=df,
                target=self.target,
            )
            print(f"📁 Model entrenado SIUU", model["model_name"])

            # Guardamos el .pkl
            joblib.dump(model["best_model"], 'tmp/best_model.pkl')

            pkl_url = await self.save_model('tmp/best_model.pkl')
            print(f"📁 Modelo guardado en: {pkl_url}")

            # Ahora falla aquí
            metrics_jsonb = json.dumps(model.get("metrics", []))
            print(f"📁 Métricas guardadas en: {metrics_jsonb}")
            # Guardamos el modelo con toda la información
            print(f"📁 Haciendo la llamada", dataset_id)
            data = supabase.table("models").insert({
                "dataset_id": dataset_id,
                "user_id": self.user_id,
                "model_name": model.get("model_name"),
                "target_column": self.target,
                "metrics_json": metrics_jsonb,
                "predictions_url": 'FALTA',
                "model_blob_url": pkl_url,
                "problem_type": model.get("problem_type"),
            }).execute().data
            print(f"📁 Modelo guardado en: {data}")

            os.remove(tmp_path)
            os.remove('tmp/best_model.pkl')
            # Debug info
            print("🧪 TYPE OF RES:", type(data))
            print("🧪 RES CONTENT:", data)

            return data


        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Model Service -> train error: {str(e)}")
