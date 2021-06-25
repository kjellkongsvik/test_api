FROM python:3.9.5-slim-buster

WORKDIR /code

COPY requirements.txt ./
RUN pip install -r requirements.txt

COPY test_integration.py .

CMD ["python", "-m", "pytest"]
