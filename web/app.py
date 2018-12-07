import json
import os

from dateutil.parser import parse
from flask import Flask, render_template
from flask_httpauth import HTTPBasicAuth
from oauth2client.service_account import ServiceAccountCredentials
from pytz import timezone
import gspread

app = Flask(__name__)

auth = HTTPBasicAuth()

TITLE = os.environ.get('CLEVER_HARVEST_TITLE')
GOOGLE_API_CLIENT_SECRET_JSON = os.environ.get(
    'CLEVER_HARVEST_GOOGLE_API_CLIENT_SECRET_JSON',
    None
)


@auth.get_password
def get_pw(username):
    """Returns the password required for certain endpoints."""
    return os.environ['CLEVER_HARVEST_WEB_PASSWORD']


@app.route('/')
@auth.login_required
def dashboard():

    # Get the measurements from the google spreadsheet
    gspread_client = gspread.authorize(
        ServiceAccountCredentials.from_json_keyfile_dict(
            json.loads(GOOGLE_API_CLIENT_SECRET_JSON), [
                'https://www.googleapis.com/auth/drive',
                'https://spreadsheets.google.com/feeds',
            ]
        )
    )
    gsheet = gspread_client.open(TITLE).sheet1

    # Pluck out the last row so we can show the current environment
    all_values = gsheet.get_all_values()
    last_row = all_values[-1]

    # Setup some data for use with chart.js
    charts = {}
    sample_of_measurements = all_values[-12:]
    labels = [
        parse(x[0]).astimezone(timezone('US/Pacific')).strftime('%H:%M')
        for x in sample_of_measurements
    ]
    charts = {
        'temperature': {
            'type': 'line',
            'data': {
                'labels': labels,
                'datasets': [{
                    'data': [float(x[2]) for x in sample_of_measurements],
                    'label': 'Temperature ({})'.format(str(last_row[2])),
                    'borderColor': '#3e95cd',
                    'fill': False,
                }],
            },
        },
        'humidity': {
            'type': 'line',
            'data': {
                'labels': labels,
                'datasets': [{
                    'data': [float(x[1]) for x in sample_of_measurements],
                    'label': 'Humidity ({})'.format(str(last_row[1])),
                    'borderColor': '#8e5ea2',
                    'fill': False,
                }],
            },
        },
        'moisture': {
            'type': 'line',
            'data': {
                'labels': labels,
                'datasets': [{
                    'data': [
                        bool(x[3] == 'TRUE') for x in sample_of_measurements
                    ],
                    'label': 'Moisture ({})'.format(
                        'Wet' if last_row[3] == 'TRUE' else 'Dry'
                    ),
                    'borderColor': '#e0a732',
                    'fill': False,
                }],
            },
        },
    }

    # Render the template with the following data
    data = {
        'charts': charts,
        'last_image_path': last_row[-1],
        'title': TITLE,
    }
    return render_template('dashboard.html', data=data)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=80)
