FROM python:3

WORKDIR /microphone

COPY requirements.txt ./
COPY *.py ./

RUN apt-get update
RUN apt-get install -y portaudio19-dev python-pyaudio python3-pyaudio
RUN pip install --no-cache-dir -r requirements.txt

CMD  [ "python", "./__main__.py" ]
