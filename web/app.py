import os
import json

from flask import Flask
from flask_httpauth import HTTPBasicAuth
from jinja2 import Environment
from oauth2client.service_account import ServiceAccountCredentials
import gspread

app = Flask(__name__)

auth = HTTPBasicAuth()

TITLE = os.environ.get('CLEVER_HARVEST_TITLE')
GOOGLE_API_CLIENT_SECRET_JSON = os.environ.get(
    'CLEVER_HARVEST_GOOGLE_API_CLIENT_SECRET_JSON',
    None
)

HTML = """
<html>
  <!DOCTYPE html>
  <html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">
    <title>Clever Harvest</title>
    <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.1.3/css/bootstrap.min.css">
  </head>
  <body>
    <nav class="navbar navbar-dark bg-dark">
      <span class="navbar-brand mb-0 h1">Clever Harvest</span>
    </nav>
    <div class="container mt-3">
      <div class="row">
        <div class="col-md-8 mb-3">
          <div class="card">
            <img class="card-img-top" src="{{ data.last_image_path }}" alt="{{ data.title }}">
            <div class="card-body">
              <h5 class="card-title mb-0">{{ data.title }}</h5>
            </div>
          </div>
        </div>
      </div>
  </body>
</html>
"""


@auth.get_password
def get_pw(username):
    """Returns the password required for certain endpoints."""
    return os.environ['CLEVER_HARVEST_WEB_PASSWORD']


@app.route('/')
@auth.login_required
def dashboard():

    # Get the last measurement from the google spreadsheet
    gspread_client = gspread.authorize(
        ServiceAccountCredentials.from_json_keyfile_dict(
            json.loads(GOOGLE_API_CLIENT_SECRET_JSON), [
                'https://www.googleapis.com/auth/drive',
                'https://spreadsheets.google.com/feeds',
            ]
        )
    )
    gsheet = gspread_client.open(TITLE).sheet1

    all_values = gsheet.get_all_values()
    data = dict(
        last_image_path=all_values[-1][-1],
        title=TITLE,
    )
    jinja_env = Environment()
    return jinja_env\
        .from_string(HTML)\
        .render(data=data, trim_blocks=True)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=80)
