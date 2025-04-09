import os

from fastapi import APIRouter, Request, HTTPException
from supabase import create_client

router = APIRouter()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)


@router.post("/user/sync")
async def sync_user(request: Request):
    body = await request.json()
    user_id = body.get("id")
    email = body.get("email")
    name = body.get("name")

    if not user_id or not email:
        raise HTTPException(status_code=400, detail="ID y email son requeridos")

    # Verifica si ya existe en tu tabla
    existing = supabase.table("users").select("*").eq("id", user_id).execute()
    if existing.data:
        return {"message": "El usuario ya existe"}

    # Guarda en tu tabla
    res = supabase.table("users").insert({
        "id": user_id,
        "email": email,
        "name": name or "Sin nombre"
    }).execute()

    return {"message": "Usuario guardado", "user": res.data}


@router.get("/models")
async def get_models():
    try:
        response = supabase.table("models").select("*").execute()

        if response.data is None:
            raise HTTPException(status_code=404, detail="No hay modelos")

        return {
            "message": "✅ Modelos encontrados",
            "data": response.data
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error con Supabase: {str(e)}")
