import os

from fastapi import APIRouter
from fastapi import Request
from supabase import create_client

router = APIRouter()


def get_supabase_client():
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
    return create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)


@router.post("/landing/new-email")
async def add_user(request: Request):
    print("📩 Recibida petición al endpoint /new-email")
    body = await request.json()
    email = body.get("email")
    print("📩 email:", email)

    supabase = get_supabase_client()

    res = supabase.table("emails").insert({
        "email": email,
    }).execute()

    return {"message": "Usuario guardado", "user": res.data}


@router.get("/")
def root():
    return {"message": "API working"}
