#!/usr/bin/env python3

# Init
# uvicorn main:app --reload

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import landing_routes
from app.api.v1 import model_routes

app = FastAPI()

# client = OpenAI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(model_routes.router, prefix="/ml_backend/v1")
# app.include_router(supabase_routes.router, prefix="/ml_backend/v1")


app.include_router(landing_routes.router, prefix="/ml_backend/v1")
