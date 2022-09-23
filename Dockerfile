FROM ubuntu 
WORKDIR kaja
RUN mkdir -p ./pages
RUN mkdir -p ./tests
RUN mkdir -p ./config 
COPY src src 
COPY requirements.txt .
COPY post_classes.py .
COPY config .
COPY tests tests
COPY initialize_db.py . 
RUN apt update
RUN apt install -y python3
RUN apt install -y python3-pip 
RUN pip install -r requirements.txt