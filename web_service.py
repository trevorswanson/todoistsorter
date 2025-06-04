"""Provides a web service to host the Todoist Sorter"""
import json
import os
import sys
import logging
import threading

from flask import Flask, request
from werkzeug import serving

from todoist_sorter import Sorter

parent_log_request = serving.WSGIRequestHandler.log_request


def log_request(self, *args, **kwargs):
    """Log handler to suppress healthcheck requests"""
    if self.path == '/healthz':
        return
    parent_log_request(self, *args, **kwargs)

serving.WSGIRequestHandler.log_request = log_request

app = Flask(__name__)

logging.getLogger().setLevel(level=os.getenv('LOGLEVEL', 'INFO').upper())
logging.basicConfig(
    format="%(name)s: %(asctime)s | %(levelname)s | %(filename)s:%(lineno)s | %(message)s")

# Validate necessary config is provided
project = os.getenv("PROJECT", None)
api_token = os.getenv("APITOKEN", None)
sync_interval = os.getenv("SYNC_INTERVAL", None)

if None in (project, api_token):
    logging.error("Environment variables cannot be None - exiting.")
    sys.exit(1)

api = Sorter(api_token, project)

def sanitize_log(body):
    """Remove newlines so that log entries cannot be forged as easily"""
    return body.replace('\n', '').replace('\r', '')

def reconcile():
    """Request a full reconcile instead of waiting for webhooks"""
    logging.debug("Initiating reconcile loop")
    api.reconcile()
    threading.Timer(sync_interval, reconcile).start()

# Start the reconcile loop
if sync_interval:
    try:
        sync_interval = int(sync_interval)
    except ValueError:
        logging.fatal("Invalid sync interval provided")
        sys.exit(1)
    reconcile()

@app.route("/todoist", methods=['POST'])
def webhook():
    """Expose a webhook for Todoist to send updates"""
    bytes_data = request.data.decode('ASCII')
    body = json.loads(bytes_data)

    logging.debug(sanitize_log(json.dumps(body)))

    event_name = body['event_name']
    event_data = body['event_data']
    project_id = event_data['project_id']

    if event_name == "item:added" and str(project_id) == str(project):
        logging.info("%s | %s", sanitize_log(event_name), sanitize_log(event_data['content']))
        api.capitalize_item(event_data['id'], event_data['content'])
        api.learn(item=event_data)
        api.adjust_item_section(event_data)

    elif (event_name in ("item:completed", "item:updated")) and str(project_id) == str(project):
        logging.info("%s | %s", sanitize_log(event_name), sanitize_log(event_data['content']))
        api.learn(item=event_data)

    else:
        logging.warning(
            "Unhandled event %s | %s",
            sanitize_log(event_name),
            sanitize_log(json.dumps(event_data))
        )
        return "", 422

    return "", 200

@app.route("/healthz", methods=['GET'])
def healthz():
    """Default health check endpoint"""
    api.healthcheck()
    return "TodoistSorter service is running...", 200

@app.route("/", methods=['POST', 'GET'])
def hello():
    """Default endpoint for /"""
    return "TodoistSorter service is running...", 200


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5005)
