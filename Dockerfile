FROM python:3.10-slim-buster

WORKDIR /app
RUN apt-get update -y
RUN apt-get install ffmpeg -y
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt
COPY . .


CMD ["python3", "./main.py"]

