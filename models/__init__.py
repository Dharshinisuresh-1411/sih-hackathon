from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# Import models so they register with SQLAlchemy metadata when
# `from models import db` is used followed by `db.create_all()`.
from .pole import Pole          # noqa: E402,F401
from .electrician import Electrician  # noqa: E402,F401
from .complaint import Complaint      # noqa: E402,F401
from .work_record import WorkRecord   # noqa: E402,F401
