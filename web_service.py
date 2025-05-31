"""Provides a web service to host the Todoist Sorter"""
import json
import os
import sys
import logging
import threading

from flask import Flask, request

from todoist_sorter import Sorter

app = Flask(__name__)

logging.getLogger().setLevel(level=os.getenv('LOGLEVEL', 'INFO').upper())
logging.basicConfig(
    format="%(name)s: %(asctime)s | %(levelname)s | %(filename)s:%(lineno)s | %(message)s")

# Validate necessary config is provided
project = os.getenv("PROJECT", None)
api_token = os.getenv("APITOKEN", None)
sync_interval = int(os.getenv("SYNC_INTERVAL", "300"))

if None in (project, api_token):
    logging.error("Environment variables cannot be None - exiting.")
    sys.exit(1)

api = Sorter(api_token, project)

# Perform a one-time learn of all tasks
def reconcile():
    """Request a full reconcile instead of waiting for webhooks"""
    logging.debug("Initiating reconcile loop")
    api.reconcile()
    threading.Timer(sync_interval, reconcile).start()

reconcile()

@app.route("/todoist", methods=['POST'])
def webhook():
    """Expose a webhook for Todoist to send updates"""
    bytes_data = request.data.decode('ASCII')
    body = json.loads(bytes_data)

    logging.debug(json.dumps(body, indent=4, sort_keys=True))

    event_name = body['event_name']
    event_data = body['event_data']
    project_id = event_data['project_id']

    if event_name == "item:added" and str(project_id) == str(project):
        logging.info("%s | %s", event_name, event_data['content'])
        api.capitalize_item(event_data['id'], event_data['content'])
        api.learn(item=event_data)
        api.adjust_item_section(event_data)

    elif (event_name in ("item:completed", "item:updated")) and str(project_id) == str(project):
        logging.info("%s | %s", event_name, event_data['content'])
        api.learn(item=event_data)

    else:
        logging.warning("Unhandled event %s | %s", event_name, json.dumps(event_data))
        return "", 422

    return "", 200


@app.route("/", methods=['POST', 'GET'])
def hello():
    """Default endpoint for health checks"""
    return "TodoistSorter service is running..."


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5005)
