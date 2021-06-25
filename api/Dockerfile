FROM python:3.9.5-slim-buster

RUN useradd --create-home user
WORKDIR /home/user
USER user

COPY ./requirements.txt ./setup.py ./

RUN pip install -r requirements.txt

COPY ./api ./api
ENV PATH=$HOME/.local/bin:${PATH}

RUN pip install .

EXPOSE 8000
CMD ["/home/user/.local/bin/uvicorn", "api.main:app", "--host", "0.0.0.0"]
