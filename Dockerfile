FROM python:3.8-slim

RUN apt-get update && apt-get install -y git

COPY requirements.txt /

RUN pip3 install --upgrade pip
RUN pip3 install -r requirements.txt

COPY ./src /app/src

ARG ARG_PYTHON_PROFILES_ACTIVE
ENV ARG_PYTHON_PROFILES_ACTIVE=$ARG_PYTHON_PROFILES_ACTIVE

WORKDIR /app

CMD [ "sh" ]