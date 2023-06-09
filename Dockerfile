FROM python:3.10

WORKDIR /app
ENV PYHTONUNBUFFERED=1
RUN apt-get update \
 && apt-get install -y --no-install-recommends ffmpeg tesseract-ocr\
 && apt-get -y clean \
 && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /tmp
RUN pip install --upgrade pip \
 && pip install -r /tmp/requirements.txt \
 && rm /tmp/requirements.txt
COPY . .


CMD ["python3", "./main.py"]

