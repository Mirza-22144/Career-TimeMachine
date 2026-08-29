from fastapi import FastAPI
from app.api.router import api_router  # import the API router
app = FastAPI(title="Career TimeMachine API")

app.include_router(api_router, prefix="/api/v1")  # include the API router with a prefix 


