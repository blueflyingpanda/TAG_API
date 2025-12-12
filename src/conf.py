from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=['../.env', '.env'])

    db_host: str
    db_port: int
    db_user: str
    db_pass: str
    db_name: str
    db_ssl_mode: str = 'disable'

    redis_host: str
    redis_port: int
    redis_pass: str
    redis_name: str

    oauth_gcloud_id: str
    oauth_gcloud_secret: str
    oauth_redirect_uri: str

    fe_url: str

    jwt_secret: str
    jwt_algorithm: str
    jwt_expires_in_days: int


settings = Settings()
