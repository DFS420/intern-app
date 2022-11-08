from app.utils.db_dev_api import app as backend
from app.app import app as frontend
from fastapi.middleware.wsgi import WSGIMiddleware

backend.mount("/", WSGIMiddleware(frontend), name='frontend')

