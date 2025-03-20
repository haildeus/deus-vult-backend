from pydantic_settings import BaseSettings


class Config(BaseSettings):
    class Config:
        extra = "ignore"
        env_file = ".env"
        env_prefix = "GLOBAL_"


config = Config()
