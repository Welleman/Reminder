from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env')

    app_name:str
    bot_token:str
    secret_key:str
    algorithm:str
    access_token_expire_minutes:int
    db_host:str
    db_port:int
    db_user:str
    db_pass:str
    db_name:str

    # Асинхронное соединение
    @property
    def db_url_asynpg(self):
        # "postgresql+asyncpg://postgres:postgres@localhost:5432/reminder_db"
        return f"postgresql+asyncpg://{self.db_user}:{self.db_pass}@{self.db_host}:{self.db_port}/{self.db_name}"

settings = Settings()