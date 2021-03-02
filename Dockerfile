FROM python:3.8-alpine

RUN adduser -D eeeing

WORKDIR /home/eeeing

COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt

COPY . ./app
RUN chmod +x start.sh

ENV FLASK_APP main.py

RUN chown -R eeeing:eeeing ./
USER eeeing

EXPOSE 5000
ENTRYPOINT ["./start.sh"]