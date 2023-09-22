FROM python:3.10-slim

WORKDIR /app
ENV PYTHONUNBUFFERED=1

RUN apt-get update \
 && apt-get install -y --no-install-recommends git flac ffmpeg tesseract-ocr wget \
 && apt-get -y clean \
 && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

RUN mkdir -p /usr/share/tesseract-ocr/4.00/tessdata/script/
#RUN wget https://github.com/tesseract-ocr/tessdata_fast/raw/main/script/Devanagari.traineddata -P /usr/share/tesseract-ocr/4.00/tessdata/script/

#ENV TESSDATA_PREFIX=/usr/share/tesseract-ocr/4.00/tessdata

COPY requirements.txt .
RUN pip install --upgrade pip \
 && pip install -r requirements.txt \
 && rm requirements.txt \
 && pip cache purge \
 && rm -rf ~/.cache/pip/*

COPY . .
#VOLUME /app/personas
CMD ["python3", "./main.py"]