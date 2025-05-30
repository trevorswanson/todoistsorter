"""Module that automatically sorts new items in a Todoist project"""

import datetime
import sqlite3
import uuid

import requests
from todoist.api import TodoistAPI


class Sorter:
    """The Todoist Sorter"""
    def __init__(self, api_token, project_id):
        self.token = api_token
        self.api = TodoistAPI(api_token)
        self.api.sync()

        self.project_id = project_id
        self.dbfilename = 'data/Todoist.db'
        self.dbtableprefix = 'Sections_'
        self.dbtablename = self.dbtableprefix + str(project_id)

    def initialize_db(self):
        """Connect to and initialize SQLite DB"""
        conn = sqlite3.connect(self.dbfilename)
        db = conn.cursor()

        query = f"""
        CREATE TABLE IF NOT EXISTS {self.dbtablename}
        ("item_project" INT, "item_content" TEXT, "item_section" INT, "last_updated" TEXT)
        """

        db.execute(query)
        db.close()

    def get_section_name(self, section_id):
        """Return the section name based on ID"""
        section_list = self.api.state['sections']
        for section in section_list:
            if section['id'] == section_id:
                return section['name']
        # RETURN FALSE IF NO MATCH IS FOUND
        return False

    def get_historic_section(self, item_id):
        """Obtain the previously-used section for an item"""
        item = self.api.items.get_by_id(item_id)

        self.initialize_db()
        conn = sqlite3.connect(self.dbfilename)

        select_query = f"""
        SELECT item_content, item_section
        FROM {self.dbtablename}
        WHERE item_content = ?
        LIMIT 1
        """

        db = conn.cursor()
        result = db.execute(select_query,(item['content'].lower())).fetchone()
        db.close()
        conn.commit()
        if result is not None:
            return result[1]
        return None

    def capitalize_item(self, item_id):
        """Capitalize the first letter of the item"""
        item_content = self.api.items.get_by_id(item_id)['content']
        if not item_content[0].isupper():
            new_content = item_content[0].upper() + item_content[1:]

            # WRITE UPDATED CONTENT TO TODOIST
            item = self.api.items.get_by_id(item_id)
            item.update(content=new_content)
            self.api.commit()


    def learn(self):
        """Read all items in Todoist and learn their preferred sections"""
        self.initialize_db()
        conn = sqlite3.connect(self.dbfilename)
        query = ""

        item_list = self.api.state['items']
        for item in item_list:
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")  # USED FOR DB UPDATES
            if item['project_id'] == self.project_id and item['section_id'] is not None:

                # GET HISTORIC SECTION
                historic_section = self.get_historic_section(item['id'])
                if historic_section == item['section_id']:  # NO UPDATE NEEDED
                    pass

                db = conn.cursor()

                if historic_section is None:  # ADD ITEM TO DB
                    query = f"""
                    INSERT INTO {self.dbtablename}
                    (item_project, item_content, item_section, last_updated)
                    VALUES (?,?,?,?)
                    """
                    db.execute(query,(item['project_id'],item['content'].lower(),item['section_id],timestamp']))

                else:  # UPDATE CURRENT SECTION
                    query = f"""
                    UPDATE {self.dbtablename}
                    SET
                    item_section = ?,
                    last_updated = ?
                    WHERE item_content = ?
                    """
                    db.execute(query,(item['section_id'],timestamp,item['content'].lower()))

                db.close()
                query = ""

        conn.commit()

    def adjust_item_section(self, item_id):
        """Change the section of an item"""
        # USING MANUAL METHOD AS SECTIONS ARENT SUPPORTED IN CURRENT VERSION OF TODOIST SYNC API
        state = uuid.uuid4()
        api_url_sync = "https://api.todoist.com/sync/v8/sync"
        commands = f"""
        [{{
            "type": "item_move",
            "uuid": "{str(state)}",
            "args": {{
                "id": {str(item_id)},
                "section_id": {str(self.get_historic_section(item_id))}
            }}
        }}]
        """

        payload = {"token": str(self.token), 'commands': commands}
        requests.post(api_url_sync, data=payload, timeout=10).json()
