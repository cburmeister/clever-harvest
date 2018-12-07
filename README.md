clever-harvest
==============

[![Build Status](https://travis-ci.org/cburmeister/clever-harvest.svg?branch=master)](https://travis-ci.org/cburmeister/clever-harvest)

Gather environmental metrics from an array of sensors connected to a Raspberry
Pi deployed via [balenaCloud](https://balena.io/).

---

## Metrics

An image is captured at regular intervals annotated with the following metrics:

- A UTC timestamp
- The relative humidity
- The temperature
- Whether or not the soil contains moisture

The image is captured entirely in memory before it is shipped to s3. The
metrics data is appended to a google sheet.

## Hardware

- Any [Raspberry Pi](http://a.co/d/hdHM1Nb) model
- A [Micro SD card](http://a.co/d/7VNbSxb)
- A [DHT22 sensor](http://a.co/d/2Otsggy)
- A [Soil moisture sensor](http://a.co/d/02xTN9r)
- A [Raspberry Pi compatible camera module](http://a.co/d/9tghOgA)

## Configuration

The following environment variables are *required*:

| Name                                           | Purpose                                  |
|------------------------------------------------|------------------------------------------|
| `CLEVER_HARVEST_DHT22_PIN`                     | A GPIO pin                               |
| `CLEVER_HARVEST_GOOGLE_API_CLIENT_SECRET_JSON` | Your Google API credentials as JSON      |
| `CLEVER_HARVEST_IMAGE_ROTATION`                | Degrees to rotate the captured images    |
| `CLEVER_HARVEST_MOISTURE_PIN`                  | A GPIO pin                               |
| `CLEVER_HARVEST_S3_ACCESS_KEY_ID`              | An S3 access key ID                      |
| `CLEVER_HARVEST_S3_BUCKET_NAME`                | An S3 bucket name                        |
| `CLEVER_HARVEST_S3_SECRET_ACCESS_KEY`          | An s3 secret access key                  |
| `CLEVER_HARVEST_TITLE`                         | The title of the google sheet            |
| `CLEVER_HARVEST_WEB_PASSWORD`                  | Password to access the dashboard         |

## Deployment

Devices running this software managed with [balenaCloud](https://balena.io/).

You'll need to configure an SSH key and add the balena git remote to your repository.

Then you can deploy to all devices in the fleet with a simple `git push`:
```bash
git push balena master
```

### Continuous Integration

Master builds of this repository are automatically deployed with [TravisCI](https://travis-ci.org/).

See the `.travis.yml` configuration for more details on how this is automated.
