"""Provides a web service to host the Todoist Sorter"""
import datetime
import json
import os
import sys

from flask import Flask, request

from todoist_sorter import Sorter

app = Flask(__name__)


@app.route("/todoist", methods=['POST'])
def webhook():
    """Expose a webhook for Todoist to send updates"""
    project = os.getenv("PROJECT", None)
    api_token = os.getenv("APITOKEN", None)

    if None in (project, api_token):
        print("Environment variables cannot be None - exiting.")
        sys.exit(1)

    bytes_data = request.data.decode('ASCII')
    body = json.loads(bytes_data)

    # USED FOR VERBOSE LOGGING
    #print(json.dumps(body, indent=4, sort_keys=True))
    #print("----------------------------")

    event_name = body['event_name']
    event_data = body['event_data']
    item_id = event_data['id']
    project_id = event_data['project_id']

    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

    if event_name == "item:added" and str(project_id) == str(project):
        print(timestamp, event_name, event_data['content'])
        api = Sorter(api_token, project_id)
        api.capitalize_item(item_id)
        api.learn()
        api.adjust_item_section(item_id)

    elif (event_name in ("item:completed", "item:updated")) and str(project_id) == str(project):
        print(timestamp, event_name, event_data['content'])
        api = Sorter(api_token, project_id)
        api.learn()

    else:
        return "", 422

    return "", 200


@app.route("/", methods=['POST', 'GET'])
def hello():
    """Default endpoint for health checks"""
    return "TodoistSorter service is running..."


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5005)
