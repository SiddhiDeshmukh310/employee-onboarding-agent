import os
from dotenv import load_dotenv

load_dotenv()

db_host = os.getenv('DB_HOST', 'localhost')
db_port = os.getenv('DB_PORT')
if db_port and ':' not in db_host:
    db_host = f"{db_host}:{db_port}"

class Config:
    SQLALCHEMY_DATABASE_URI = (
        f"mysql+pymysql://{os.getenv('DB_USER')}:"
        f"{os.getenv('DB_PASSWORD')}@"
        f"{db_host}/"
        f"{os.getenv('DB_NAME')}"
    )

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Automatically enable SSL for secure cloud databases (like Aiven)
    if 'localhost' not in db_host and '127.0.0.1' not in db_host:
        SQLALCHEMY_ENGINE_OPTIONS = {
            "connect_args": {
                "ssl": {
                    "ssl_mode": "REQUIRED"
                }
            }
        }