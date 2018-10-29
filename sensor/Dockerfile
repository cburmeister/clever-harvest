FROM resin/raspberry-pi2-python:3

# See https://github.com/resin-io-projects/balena-rpi-python-picamera/issues/8
ENV READTHEDOCS True

COPY ./requirements.txt /requirements.txt
RUN pip install -r /requirements.txt

# See https://docs.resin.io/learn/develop/dockerfile/#init-system
ENV INITSYSTEM on

COPY . ./

CMD ["python", "measurement.py"]
