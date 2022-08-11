FROM python:3.9

RUN pip install --upgrade pip
RUN pip install docker aiodocker pylint pylint-pytest pytest pytest-asyncio yapf

RUN apt-get update && apt-get -y install nodejs npm && npm install -g pyright
