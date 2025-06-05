import os

from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_MINDLESSML_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_MINDLESSML_SERVICE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)


def save_model_metadata(user_id, model_id, target_column, s3_path, data_s3_path, metrics):
    print("Saving model metadata to Supabase...")
    data = {
        "user_id": user_id,
        "model_id": model_id,
        "target_column": target_column,
        "model_s3_path": s3_path,
        "model_s3_data_path": data_s3_path,
        "accuracy": metrics["accuracy"],
        "f1_score": metrics["f1_score"],
        "precision": metrics["precision"],
        "recall": metrics["recall"],
    }
    print("Saving model metadata:", data)
    supabase.table("models").insert(data).execute()


def get_user_data(user_id: str):
    # Get all models that the user has trained
    user = supabase.table("users").select("*").eq("id", user_id).execute()

    return user.data[0] if user.data else None


def get_user_models(user_id: str):
    models = supabase.table("models").select("*").eq("user_id", user_id).execute()

    return models.data if models.data else []
