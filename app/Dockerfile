FROM tiangolo/uvicorn-gunicorn:python3.8-slim

RUN python -m pip install --upgrade pip
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

COPY . ./app

ENV FLASK_APP main.py

EXPOSE 80
ENTRYPOINT ["uvicorn", "main:app",   "--reload"]