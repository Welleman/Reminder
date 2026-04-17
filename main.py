from fastapi import FastAPI
from config.settings import Settings

app = FastAPI()
settings = Settings()

@app.get("/")
def read_root():
    print(f'APP name - {settings.app_name}')
    return {"Hello": "World"}

    