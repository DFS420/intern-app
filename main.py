from app.utils.db_dev_api import app as backend
from app.app import app as frontend
from fastapi.middleware.wsgi import WSGIMiddleware
import uvicorn

backend.mount("/", WSGIMiddleware(frontend), name='frontend')

if __name__ == "__main__":
    uvicorn.run(backend, host="localhost", port=5000)

