"""
Take a measurement from the connected sensors and record the results.
"""
from collections import OrderedDict
from datetime import datetime
import io
import json
import logging
import os
import subprocess
import sys
import time

from oauth2client.service_account import ServiceAccountCredentials
import RPi.GPIO as GPIO
import boto3
import gspread
import picamera

# See https://forums.balena.io/t/dht-sensor-on-rpi-3/3898
try:
    package = 'Adafruit-DHT==1.3.4'
    subprocess.call([sys.executable, '-m', 'pip', 'install', package])
    import Adafruit_DHT  # noqa
except Exception:
    raise ValueError('Failed to import and install Adafruit-DHT.')


DHT22_PIN = int(os.environ.get('CLEVER_HARVEST_DHT22_PIN', 0))
GOOGLE_API_CLIENT_SECRET_JSON = json.loads(
    os.environ.get('CLEVER_HARVEST_GOOGLE_API_CLIENT_SECRET_JSON', {})
)
IMAGE_ROTATION = int(os.environ.get('CLEVER_HARVEST_IMAGE_ROTATION', 0))
LOG_LEVEL = os.environ.get('CLEVER_HARVEST_LOG_LEVEL', 'INFO').upper()
MOISTURE_PIN = int(os.environ.get('CLEVER_HARVEST_MOISTURE_PIN', 0))
S3_ACCESS_KEY_ID = os.environ.get('CLEVER_HARVEST_S3_ACCESS_KEY_ID')
S3_BUCKET_NAME = os.environ.get('CLEVER_HARVEST_S3_BUCKET_NAME')
S3_SECRET_ACCESS_KEY = os.environ.get('CLEVER_HARVEST_S3_SECRET_ACCESS_KEY')
TITLE = os.environ.get('CLEVER_HARVEST_TITLE')

logging.basicConfig(stream=sys.stdout, level=LOG_LEVEL)


def main():
    now = datetime.utcnow()

    # Read the temperature and humidity from the connected DHT22 sensor
    humidity, temperature = None, None
    if DHT22_PIN:
        humidity, temperature = Adafruit_DHT.read_retry(
            Adafruit_DHT.DHT22,
            DHT22_PIN
        )
        if temperature:
            temperature = temperature * 9/5.0 + 32  # Convert to Fahrenheit
        humidity, temperature = round(humidity, 2), round(temperature, 2)

    # Determine if the soil is wet or dry
    moisture = None
    if MOISTURE_PIN:
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(MOISTURE_PIN, GPIO.IN)
        moisture = not bool(GPIO.input(MOISTURE_PIN))

    # Capture an image
    image_url = None
    if all([S3_BUCKET_NAME, S3_ACCESS_KEY_ID, S3_SECRET_ACCESS_KEY]):
        try:
            image_stream = io.BytesIO()
            with picamera.PiCamera() as camera:
                camera.start_preview()
                camera.resolution = (1640, 1232)
                camera.rotation = IMAGE_ROTATION
                camera.annotate_background = picamera.Color('black')
                camera.annotate_text = '{} T: {} H: {}% S: {}'.format(
                    now,
                    temperature,
                    humidity,
                    'Wet' if moisture else 'Dry',
                )
                time.sleep(5)  # Camera warm-up time
                camera.capture(image_stream, format='jpeg')
                image_stream.seek(0)
        except picamera.exc.PiCameraError as e:
            logging.error('Error capturing image: {}'.format(str(e)))

        # Then ship it to s3
        try:
            now_as_string = now.strftime('%Y-%m-%dT%H:%M:%S%z')
            key = '{}/{}.jpg'.format(TITLE, now_as_string)
            s3 = boto3.client(
                's3',
                aws_access_key_id=S3_ACCESS_KEY_ID,
                aws_secret_access_key=S3_SECRET_ACCESS_KEY,
            )
            s3.put_object(Bucket=S3_BUCKET_NAME, Key=key, Body=image_stream)
            image_url = s3.generate_presigned_url(
                'get_object',
                Params=dict(
                    Bucket=S3_BUCKET_NAME,
                    Key=key,
                    ResponseContentType='image/jpeg',
                ),
                ExpiresIn=86400
            )
        except Exception:
            logging.error('Error saving image: {}'.format(str(e)))

    measurement = OrderedDict([
        ('ts', now.isoformat()),
        ('humidity', humidity),
        ('temperature', temperature),
        ('moisture', moisture),
        ('image_url', image_url),
    ])
    logging.info(measurement)

    # Write the measurement to a google sheet
    if GOOGLE_API_CLIENT_SECRET_JSON:
        try:
            gspread_client = gspread.authorize(
                ServiceAccountCredentials.from_json_keyfile_dict(
                    GOOGLE_API_CLIENT_SECRET_JSON, [
                        'https://www.googleapis.com/auth/drive',
                        'https://spreadsheets.google.com/feeds',
                    ]
                )
            )
            gsheet = gspread_client.open(TITLE).sheet1
            gsheet.append_row([x for x in measurement.values()])
        except Exception:
            logging.error('Error saving measurement: {}'.format(str(e)))


if __name__ == '__main__':
    while True:
        main()
        time.sleep(60 * 5)  # 5 Minutes
