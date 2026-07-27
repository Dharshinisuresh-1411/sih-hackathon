import os
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-change-me")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # ---- Database selection ----
    # DB_ENGINE = "mysql" (default, production/demo) or "sqlite" (fallback for
    # environments where MySQL is not available, e.g. quick local testing).
    SQLALCHEMY_DATABASE_URI = os.environ.get("SQLALCHEMY_DATABASE_URI")
    if not SQLALCHEMY_DATABASE_URI:
        DB_ENGINE = os.environ.get("DB_ENGINE", "mysql").lower()
        if DB_ENGINE == "sqlite":
            SQLALCHEMY_DATABASE_URI = "sqlite:///" + os.path.join(BASE_DIR, "panchayat.db")
        else:
            DB_HOST = os.environ.get("DB_HOST", "localhost")
            DB_PORT = os.environ.get("DB_PORT", "3306")
            DB_NAME = os.environ.get("DB_NAME", "panchayat_street_light")
            DB_USER = os.environ.get("DB_USER", "root")
            DB_PASSWORD = os.environ.get("DB_PASSWORD", "")
            SQLALCHEMY_DATABASE_URI = (
                f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
            )

    # Repeat offender ranking window, in months. Change here to change it everywhere.
    REPEAT_OFFENDER_MONTHS = int(os.environ.get("REPEAT_OFFENDER_MONTHS", "12"))
