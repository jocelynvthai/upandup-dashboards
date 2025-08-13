## Initial Setup

Make sure you have a `.env` file at the root of the repo, with a `SLACK_TOKEN` attribute, like below:
```
SLACK_TOKEN=xoxp-0123456789
```
This is needed to allow each of the scrapers to alert the Slack channel `#dashboard-data-alerts` once it completes.

## Running Scrapers

To run one of the scrapers manually, use the following:
```
poetry run python <file-name>.py
```
The `progress.py` scraper in particular usually needs to be run manually, because their website is locked behind a CAPTCHA. If you need to pass the CAPTCHA manually, comment out the "headless" option before running the script - then you can click on the CAPTCHA checkbox yourself.