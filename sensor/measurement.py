"""
Take a measurement from the connected sensors and record the results.
"""
from collections import OrderedDict
from datetime import datetime
import argparse
import io
import json
import logging
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


def main(args):
    now = datetime.utcnow()

    logging.basicConfig(stream=sys.stdout, level='INFO')

    # Read the temperature and humidity from the connected DHT22 sensor
    humidity, temperature = None, None
    if args.dht22_pin:
        humidity, temperature = Adafruit_DHT.read_retry(
            Adafruit_DHT.DHT22,
            args.dht22_pin
        )
        if temperature:
            temperature = temperature * 9/5.0 + 32  # Convert to Fahrenheit
        humidity, temperature = round(humidity, 2), round(temperature, 2)

    # Determine if the soil is wet or dry
    moisture = None
    if args.moisture_pin:
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(args.moisture_pin, GPIO.IN)
        moisture = not bool(GPIO.input(args.moisture_pin))

    # Capture an image
    image_url = None
    if all([
        args.s3_bucket_name,
        args.s3_access_key_id,
        args.s3_secret_access_key
    ]):
        try:
            image_stream = io.BytesIO()
            with picamera.PiCamera() as camera:
                camera.start_preview()
                camera.resolution = (1640, 1232)
                camera.rotation = args.image_rotation
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
            key = '{}/{}.jpg'.format(args.title, now_as_string)
            s3 = boto3.client(
                's3',
                aws_access_key_id=args.s3_access_key_id,
                aws_secret_access_key=args.s3_secret_access_key,
            )
            s3.put_object(
                Bucket=args.s3_bucket_name,
                Key=key,
                Body=image_stream
            )
            image_url = s3.generate_presigned_url(
                'get_object',
                Params=dict(
                    Bucket=args.s3_bucket_name,
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
    if args.google_api_client_secret_json:
        try:
            gspread_client = gspread.authorize(
                ServiceAccountCredentials.from_json_keyfile_dict(
                    json.loads(args.google_api_client_secret_json), [
                        'https://www.googleapis.com/auth/drive',
                        'https://spreadsheets.google.com/feeds',
                    ]
                )
            )
            gsheet = gspread_client.open(args.title).sheet1
            gsheet.append_row([x for x in measurement.values()])
        except Exception:
            logging.error('Error saving measurement: {}'.format(str(e)))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        '--dht22-pin',
        type=int,
        help='take a reading from the DHT22 sensor on this pin',
    )
    parser.add_argument(
        '--google-api-client-secret-json',
        help='your google API secret credentials as JSON'
    )
    parser.add_argument(
        '--image',
        action='store_true',
        help='capture an image with the connected camera module'
    )
    parser.add_argument(
        '--image-rotation',
        type=int,
        help='rotate image taken by the given amount in degrees'
    )
    parser.add_argument(
        '--moisture-pin',
        type=int,
        help='take a reading from the moisture sensor on this pin',
    )
    parser.add_argument('--s3-bucket-name', help='the name of the s3 bucket')
    parser.add_argument('--s3-access-key-id', help='the s3 access key id')
    parser.add_argument('--s3-secret-access-key', help='the s3 access key')
    parser.add_argument('--title', help='title of the project')
    args = parser.parse_args()
    while True:
        main(args)
        time.sleep(60 * 5)  # 5 Minutes
