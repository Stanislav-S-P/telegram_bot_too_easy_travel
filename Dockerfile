FROM python:3.8.10

COPY . /app
WORKDIR /app
COPY requirements.txt requirements.txt
RUN python -m pip install -r requirements.txt

ENTRYPOINT ["python", "main.py"]