FROM python:3.10

WORKDIR /app
ENV PYHTONUNBUFFERED=1
RUN apt-get update \
 && apt-get install -y --no-install-recommends git ffmpeg tesseract-ocr\
 && apt-get -y clean \
 && rm -rf /var/lib/apt/lists/*
RUN mkdir -p /usr/share/tesseract-ocr/4.00/tessdata/script/
RUN wget https://github.com/tesseract-ocr/tessdata_fast/raw/main/script/Devanagari.traineddata -P /usr/share/tesseract-ocr/4.00/tessdata/script/
ENV TESSDATA_PREFIX=/usr/share/tesseract-ocr/4.00/tessdata
COPY requirements.txt /tmp
RUN pip install --upgrade pip 
RUN pip install -r /tmp/requirements.txt \
 && rm /tmp/requirements.txt
COPY . .


CMD ["python3", "./main.py"]

