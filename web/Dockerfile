FROM resin/raspberry-pi2-python:3

WORKDIR /usr/app

COPY ./requirements.txt /requirements.txt
RUN pip install -r /requirements.txt

COPY . ./

# See https://docs.resin.io/learn/develop/dockerfile/#init-system
ENV INITSYSTEM on

EXPOSE 80

CMD ["python", "-u", "app.py"]
