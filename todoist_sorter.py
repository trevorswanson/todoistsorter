"""Module that automatically sorts new items in a Todoist project"""

import datetime
import sqlite3
import logging

from todoist_api_python.api import TodoistAPI


class Sorter:
    """The Todoist Sorter"""
    def __init__(self, api_token, project_id, dbfilename="data/Todoist.db"):
        self.token = api_token
        self.api = TodoistAPI(api_token)

        self.project_id = project_id
        self.dbfilename = dbfilename
        self.dbtableprefix = 'Sections_'
        self.dbtablename = self.dbtableprefix + str(project_id)

    def initialize_db(self):
        """Connect to and initialize SQLite DB"""
        conn = sqlite3.connect(self.dbfilename)
        cursor = conn.cursor()

        query = f"""
        CREATE TABLE IF NOT EXISTS {self.dbtablename}
        ("item_project" INT, "item_content" TEXT, "item_section" INT, "last_updated" TEXT)
        """

        cursor.execute(query)
        cursor.close()
        conn.commit()
        return conn

    # def get_section_name(self, section_id):
    #     """Return the section name based on ID"""
    #     section_list = self.api.state['sections']
    #     for section in section_list:
    #         if section['id'] == section_id:
    #             return section['name']
    #     # RETURN FALSE IF NO MATCH IS FOUND
    #     return False

    def get_historic_section(self, item_id=None, item_name=None):
        """Obtain the previously-used section for an item"""
        if None is item_name:
            item = self.api.get_task(item_id)
            item_name = item['content']

        conn = self.initialize_db()

        select_query = f"""
        SELECT item_content, item_section
        FROM {self.dbtablename}
        WHERE item_content = ?
        LIMIT 1
        """

        cursor = conn.cursor()
        result = cursor.execute(
            select_query,
            (
                item_name.lower()
            )
        ).fetchone()
        cursor.close()
        conn.commit()
        conn.close()
        if result is not None:
            return result[1]
        return None

    def capitalize_item(self, item_id, item_content):
        """Capitalize the first letter of the item"""
        if not item_content[0].isupper():
            new_content = item_content[0].upper() + item_content[1:]

            # WRITE UPDATED CONTENT TO TODOIST
            self.api.update_task(item_id, content=new_content)

    def learn(self, task=None, item=None, conn=None):
        """Read all items in Todoist and learn their preferred sections"""

        section_id = None
        if task is not None:
            section_id = task.section_id
            content = item.content
            project_id = item.project_id
        elif item is not None:
            section_id = item['section_id']
            content = item['content']
            project_id = item['project_id']
        else:
            logging.error("No task presented to learn function")
            return None

        if section_id is not None:
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")  # USED FOR DB UPDATES

            # GET HISTORIC SECTION
            historic_section = self.get_historic_section(item_name=content)
            if historic_section == section_id:  # NO UPDATE NEEDED
                pass

            # Reuse existing DB if possible
            if None is conn:
                conn = self.initialize_db()
                close_when_done = True
            else:
                close_when_done = False
            cursor = conn.cursor()

            if historic_section is None:  # ADD ITEM TO DB
                query = f"""
                INSERT INTO {self.dbtablename}
                (item_project, item_content, item_section, last_updated)
                VALUES (?,?,?,?)
                """
                cursor.execute(
                    query,
                    (
                        project_id,
                        content.lower(),
                        section_id,
                        timestamp
                    )
                )

            else:  # UPDATE CURRENT SECTION
                query = f"""
                UPDATE {self.dbtablename}
                SET
                item_section = ?,
                last_updated = ?
                WHERE item_content = ?
                AND item_project = ?
                """
                cursor.execute(
                    query,
                    (
                        section_id,
                        timestamp,
                        content.lower(),
                        project_id
                    )
                )

            cursor.close()
            if close_when_done:
                conn.commit()
                conn.close()


    def learn_all(self):
        """Learn the sections of all tasks"""
        conn = self.initialize_db()

        response = self.api.get_tasks(project_id=self.project_id)
        for task_list in response:
            for task in task_list:
                self.learn(task=task, conn=conn)

        conn.commit()
        conn.close()


    def adjust_item_section(self, item):
        """Change the section of an item"""
        new_section = self.get_historic_section(item_name=item['content'])
        if new_section is not None:
            self.api.move_task(item['id'], section_id=new_section)
