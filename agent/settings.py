from pydantic import SecretStr
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    aws_default_region: str = "eu-central-1"
    aws_access_key_id: str = ""
    aws_secret_access_key: str = ""
    aws_session_token: str = ""
