import os
import json
import requests
import time
from datetime import datetime, timezone
from google.cloud import bigquery
from google.cloud.exceptions import NotFound
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

# Configuration
class Config:
    MAIN_URL = "https://rentprogress.com/houses-for-rent"
    API_URL_TEMPLATE = "https://rentprogress.com/bin/progress-residential/property-search.state-{state}.page-1.rows-10000.nr-1.json"
    PROJECT_ID = 'homevest-data'
    DATASET_ID = 'sfr_rental_listings'
    TABLE_ID = f'{PROJECT_ID}.{DATASET_ID}.progress_raw'

    STATES = [
        'AL', 'AR', 'AZ', 'CA', 'CO', 'CT', 'DE', 'FL', 'GA', 'IA', 'ID', 'IL',
        'IN', 'KS', 'KY', 'LA', 'MA', 'MD', 'ME', 'MI', 'MN', 'MO', 'MS', 'MT',
        'NC', 'ND', 'NE', 'NH', 'NJ', 'NM', 'NV', 'NY', 'OH', 'OK', 'OR', 'PA',
        'RI', 'SC', 'SD', 'TN', 'TX', 'UT', 'VA', 'VT', 'WA', 'WI', 'WV', 'WY'
    ]


def setup_selenium():
    """Initialize and configure Selenium WebDriver"""
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36")
    driver = webdriver.Chrome(options=options)
    try:
        driver.get(Config.MAIN_URL)
        print("Visited main page to set cookies.")
        time.sleep(5)
    except Exception as e:
        print(f"Error visiting main page: {e}")
    return driver


def setup_bigquery():
    """Initialize BigQuery table if it doesn't exist"""
    client = bigquery.Client(project=Config.PROJECT_ID)
    schema = [
        bigquery.SchemaField("property_id", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("pull_timestamp", "STRING", mode="NULLABLE"),
        bigquery.SchemaField("data", "JSON", mode="NULLABLE"),
    ]
    try:
        client.get_table(Config.TABLE_ID)
        print(f"Table {Config.TABLE_ID} already exists.")
    except NotFound:
        print(f"Creating table {Config.TABLE_ID} with JSON schema...")
        table = bigquery.Table(Config.TABLE_ID, schema=schema)
        client.create_table(table)
        print(f"Table {Config.TABLE_ID} created with JSON schema.")
    return client


def fetch_properties(driver, state_abbr, count=0):
    """Fetch properties from API for given state"""
    url = Config.API_URL_TEMPLATE.format(state=state_abbr.lower())
    try:
        driver.get(url)
        if count == 0:
            time.sleep(10)
        body = driver.find_element(By.TAG_NAME, "body").text
        try:
            data = json.loads(body)
            return data.get('results', []), data.get('recordsFound', 0)
        except json.JSONDecodeError as json_err:
            print(f"Invalid JSON response for state {state_abbr}: {json_err}")
            with open(f"error_response_{state_abbr}.txt", "w", encoding="utf-8") as f:
                f.write(body)
            print(f"Response saved to error_response_{state_abbr}.txt for debugging")
            return [], 0
    except Exception as e:
        print(f"Error for state {state_abbr}: {e}")
        return [], 0


def process_properties(props, pull_timestamp, unique_properties, inserted_ids):
    """Process properties and prepare them for insertion"""
    new_props_to_insert = []
    for prop in props:
        prop_id = prop.get('propertyId')
        if prop_id and prop_id not in unique_properties:
            unique_properties[prop_id] = prop
            if prop_id not in inserted_ids:
                row = {
                    "property_id": prop_id,
                    "pull_timestamp": pull_timestamp,
                    "data": json.dumps(prop)
                }
                new_props_to_insert.append(row)
                inserted_ids.add(prop_id)
    return new_props_to_insert


def send_slack_message(text: str):
    slack_client = WebClient(token=os.getenv("SLACK_TOKEN"))
    try:
        resp = slack_client.chat_postMessage(channel='dashboard-data-alerts', text=text)
        if not resp["ok"]:
            print(f"Slack API error: {resp['error']}")
    except SlackApiError as e:
        print(f"Slack request failed: {e.response['error']}")


def main(event, context):
    driver = setup_selenium()
    bigquery_client = setup_bigquery()
    pull_timestamp = datetime.now(timezone.utc).isoformat()
    
    unique_properties = {}
    inserted_ids = set()
    total_inserted = 0
    count = 0
    
    for state_abbr in Config.STATES:
        try:
            props, record_count = fetch_properties(driver, state_abbr, count)
            count += 1
            
            current_count = len(props)
            print(f"Fetched for state {state_abbr}: got {current_count} properties, total available: {record_count}")
            
            new_props = process_properties(props, pull_timestamp, unique_properties, inserted_ids)
            
            if new_props:
                errors = bigquery_client.insert_rows_json(Config.TABLE_ID, new_props)
                if errors:
                    print(f"Encountered errors while inserting batch for state {state_abbr}: {errors}")
                else:
                    batch_size = len(new_props)
                    total_inserted += batch_size
                    print(f"Successfully inserted {batch_size} new unique properties for state {state_abbr} "
                          f"(total inserted so far: {total_inserted})")
            
            print(f"Completed collection for state {state_abbr} (total unique so far: {len(unique_properties)})")
        except (requests.RequestException, json.JSONDecodeError) as e:
            send_slack_message(f"❌ Progress scraper failed for state {state_abbr}: {e}")
            print(f"Error processing state {state_abbr}: {e}")
            continue

    print(f"Successfully inserted a total of {total_inserted} unique properties to {Config.TABLE_ID}")
    send_slack_message(f"✅ Progress scraper succeeded: {len(inserted_ids)} records inserted.")
    driver.quit()

