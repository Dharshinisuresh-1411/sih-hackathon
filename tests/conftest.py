import os
import sys
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

os.environ["DB_ENGINE"] = "sqlite"
os.environ["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"

from app import create_app
from models import db as _db
from models.pole import Pole
from models.electrician import Electrician


@pytest.fixture
def app():
    app = create_app()
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    app.config["TESTING"] = True

    with app.app_context():
        _db.create_all()
        yield app
        _db.session.remove()
        _db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def sample_pole(app):
    pole = Pole(pole_number="P-001", ward="Ward 1", location="Main Road")
    _db.session.add(pole)
    _db.session.commit()
    return pole


@pytest.fixture
def active_electrician(app):
    e = Electrician(name="Murugan S", phone="9840012345", is_active=True)
    _db.session.add(e)
    _db.session.commit()
    return e


@pytest.fixture
def inactive_electrician(app):
    e = Electrician(name="Ravi Shankar", phone="9840012349", is_active=False)
    _db.session.add(e)
    _db.session.commit()
    return e
