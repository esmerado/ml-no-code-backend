import os

from dotenv import load_dotenv
from fastapi import APIRouter
from fastapi import Request
from supabase import create_client

router = APIRouter()
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
print('SUPABASE_URL', SUPABASE_URL)
supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)


@router.post("/landing/new-email")
async def add_user(request: Request):
    body = await request.json()
    email = body.get("email")

    # Guarda en tu tabla
    res = supabase.table("emails").insert({
        "email": email,
    }).execute()

    return {"message": "Usuario guardado", "user": res.data}
