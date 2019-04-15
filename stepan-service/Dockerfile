FROM python:3

WORKDIR /stepan-service

COPY models/* ./models/
COPY Makefile ./
COPY requirements.txt ./
COPY *.py ./

RUN apt-get update
RUN apt-get install -y apt-utils
RUN apt-get install -y portaudio19-dev python-pyaudio python3-pyaudio
RUN apt-get install -y libavdevice-dev libavfilter-dev libopus-dev libvpx-dev pkg-config
RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8080 5006
CMD  [ "python", "./__main__.py" ]
