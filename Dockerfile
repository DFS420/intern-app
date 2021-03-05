FROM tiangolo/uvicorn-gunicorn:python3.8-slim

RUN python -m pip install --upgrade pip
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

COPY app/ ./app
COPY main.py ./main.py

ENV FLASK_APP main.py

EXPOSE 80
ENTRYPOINT ["gunicorn","-w", "4", "-b", ":80", "main:intern_app",   "--reload"]