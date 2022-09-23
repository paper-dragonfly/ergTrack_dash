FROM ubuntu 
WORKDIR kaja
RUN mkdir -p ./pages
RUN mkdir -p ./tests
RUN mkdir -p ./config 
COPY pages pages
COPY tests tests
COPY constants.py .
COPY dash_app.py .
COPY dash_fns.py .
COPY erg_cartoon.png .
COPY ocr_pipeline.py . 
COPY README.md .
COPY requirements.txt .
RUN apt update
RUN apt-get update
RUN apt-get install ffmpeg libsm6 libxext6  -y
RUN apt install -y python3
RUN apt install -y python3-pip 
RUN apt install -y tesseract-ocr
RUN pip install -r requirements.txt