import os
import uuid

from dotenv import load_dotenv
from supabase import create_client

load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_API_KEY")
SUPABASE_BUCKET = "datasets"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


def upload_file_to_supabase(file_path: str, user_id: str) -> str:
    try:
        file_name = f"{user_id}/{uuid.uuid4()}.csv"

        with open(file_path, "rb") as f:
            supabase.storage.from_(SUPABASE_BUCKET).upload(file_name, f)

        public_url = supabase.storage.from_(SUPABASE_BUCKET).get_public_url(file_name)
        return public_url
    except Exception as e:
        print("❌ Error subiendo archivo a Supabase:", e)
        raise
