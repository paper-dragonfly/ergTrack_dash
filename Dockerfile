FROM ubuntu 

#install stuff
RUN apt update
RUN apt-get update
RUN apt-get install ffmpeg libsm6 libxext6  -y 
    # something to do with cv2 ^
RUN apt install -y python3
RUN apt install -y python3-pip 
RUN apt install -y tesseract-ocr
COPY requirements.txt .
RUN pip install -r requirements.txt

# add files
WORKDIR kaja2
RUN mkdir -p ./pages
COPY pages pages
COPY constants.py .
COPY dash_app.py .
COPY dash_fns.py .
COPY erg_cartoon.png .
COPY ocr_pipeline.py . 
COPY README.md .

EXPOSE 5001
CMD gunicorn dash_app:server
