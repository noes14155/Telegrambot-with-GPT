FROM python:3.10

WORKDIR /app
ENV PYHTONUNBUFFERED=1
RUN apt-get update \
 && apt-get install -y --no-install-recommends git ffmpeg tesseract-ocr\
 && apt-get -y clean \
 && rm -rf /var/lib/apt/lists/*

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

