FROM python:3-alpine

RUN mkdir /code
WORKDIR /code
COPY requirements.txt /code
RUN pip install -q --no-cache-dir -r requirements.txt
VOLUME ["/code"]
