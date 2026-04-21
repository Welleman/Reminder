from fastapi import FastAPI
from config.settings import Settings

app = FastAPI()
settings = Settings()

@app.get("/")
def read_root():
    return {"app_name": settings.app_name}

    