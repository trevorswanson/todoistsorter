Todoistsorter 
=========
[![CodeQL](https://github.com/trevorswanson/todoistsorter/actions/workflows/github-code-scanning/codeql/badge.svg)](https://github.com/trevorswanson/todoistsorter/actions/workflows/github-code-scanning/codeql) [![Pylint](https://github.com/trevorswanson/todoistsorter/actions/workflows/pylint.yml/badge.svg)](https://github.com/trevorswanson/todoistsorter/actions/workflows/pylint.yml) [![Build](https://github.com/trevorswanson/todoistsorter/actions/workflows/docker-publish.yml/badge.svg)](https://github.com/trevorswanson/todoistsorter/actions/workflows/docker-publish.yml)

Todoistsorter sorts (and capitalizes first letter) of tasks on a given Todoist task-list into sub-sections, based on where tasks with the same name were last found.

This is a near-complete rewrite of [frostbox42/todoistsorter](https://github.com/frostbox42/todoistsorter) to use new Todoist APIs.


What does it do?
-------------
Todoistsorter has two methods of action:

### Webhooks
1. Receives incoming webhook from Todoist with a _single item_
2. For added items: capitalized first letter (if not already done)
4. For added items: check if exists in database of previously known items
4a. If item is previously known it is moved to the last known section
4b. If item is not known, item is left where it is
5. For updated or completed items: stores which section they were in

### Reconcile Loop (default: every 5 minutes)
1. Every `SYNC_INTERVAL` seconds, pull all active (not completed) tasks from your project
2. Capitalize the first letter (if not already done)
3. If the item is in a section, store that section in the database
4. If the item is not in a section, move it to the last known section

Prerequisites
-------------
* Todoist account (can be create here: https://todoist.com/users/showregister)
* Todoist app  (can be created here: https://developer.todoist.com/appconsole.html)
* * Setup "Webhooks callback URL" (url to reach the container)
* * Setup "Watched Events" (item:added, item:updated, item:completed)
* Container needs to be reachable from the internet (uses webhooks)
* API-token (can be found here: https://todoist.com/prefs/integrations, will look something like **be50z1p7zuisib8uj5unbe50z1p7zuisib8uj5un**
* Project (go to project using web-browser and see URL, will look something like this: **2F0123456789**)


Container parameters
-----------------
* `APITOKEN` *(required)* - Private API-token, can be retrieved from the "Integration" part of the settings in the Todoist web-interface (see above)
* `PROJECT` *(required)* - ID of the project the project to monitor, can be retrieved from the url of the project when accessed through web-browser (see above section)
* `SYNC_INTERVAL` *(optional, default 300)* - How often to run a full reconcile
* `LOGGING` *(optional, default INFO)* - What level of logging to use (CRITICAL, ERROR, WARNING, INFO, DEBUG)



Docker Compose
--------------
```yaml
services:
  todoistsorter:
    image: ghcr.io/trevorswanson/todoistsorter:latest
    container_name: todoistsorter
    volumes:
      ./data:/app/data
    environment:
      - APITOKEN=**INSERT API-TOKEN HERE**
      - PROJECT=**INSERT PROJECT-ID HERE**
    ports:
      - 5005:5005
    restart: unless-stopped
```


Docker Run
--------------
```bash
docker run -p 5005:5005 --restart unless-stopped -e APITOKEN=**INSERT API-TOKEN HERE** -e PROJECT=**INSERT PROJECT-ID HERE** tswanson/todoistsorter
```


Built Using
--------------
* Python v 3.13
* Alpine Linux
* Todoist API v1
* SQLite3

Authors
----------
* **Casper Frost** - [CasperFrost](https://github.com/casperfrost)
* **Trevor Swanson** - [trevorswanson](https://github.com/trevorswanson)
