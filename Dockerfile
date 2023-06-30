FROM python:3.10

WORKDIR /app
ENV PYHTONUNBUFFERED=1
RUN apt-get update \
 && apt-get install -y --no-install-recommends git ffmpeg tesseract-ocr\
 && apt-get -y clean \
 && rm -rf /var/lib/apt/lists/*
RUN mkdir -p /usr/share/tesseract-ocr/4.00/tessdata/script/
RUN wget https://github.com/tesseract-ocr/tessdata_fast/raw/main/script/Devanagari.traineddata -P /usr/share/tesseract-ocr/4.00/tessdata/script/
#RUN  curl https://github.com/tesseract-ocr/tessdata/raw/main/script/Devanagari.traineddata --create-dirs -o /usr/share/tesseract-ocr/4.00/tessdata/Devanagari.traineddata
ENV TESSDATA_PREFIX=/usr/share/tesseract-ocr/4.00/tessdata
COPY requirements.txt /tmp
RUN pip install openai-whisper
RUN pip install --upgrade pip 
RUN pip install -r /tmp/requirements.txt \
 && rm /tmp/requirements.txt
RUN git clone https://github.com/ItsCEED/Imaginepy /tmp/repo
RUN pip install /tmp/repo \
 && rm -rf /tmp/repo
COPY . .


CMD ["python3", "./main.py"]

