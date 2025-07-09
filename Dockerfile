FROM python:3.10.15-slim-bookworm

COPY ./requirements.txt requirements.txt

RUN apt-get update
RUN apt-get install -y libpq-dev gcc
RUN pip install --no-cache-dir -r requirements.txt

CMD ["tail", "-f", "/dev/null"]