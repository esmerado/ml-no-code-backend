import os

from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY")  # o SUPABASE_ANON_KEY si solo necesitas acceso limitado

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("SUPABASE_URL o SUPABASE_SERVICE_KEY no están definidos en las variables de entorno.")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
