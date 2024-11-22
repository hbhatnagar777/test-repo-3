# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""helper class for all entity extraction entities extracted verification against solr as Destination and DB as source

"""
import sqlite3
import threading
import requests

from AutomationUtils import logger
from dynamicindex.utils import constants as Entity_constant


class EntityExtractionThread(threading.Thread):
    """ Helper thread to cross verify entity extracted and entities present in sqlite db"""

    def __init__(
            self,
            threadID,
            entity_name,
            db_path,
            db_query_field,
            solr_query_field,
            q_param,
            solr_url,
            entity_delimiter):
        """ Inits the entity extraction thread which will verify entities against solr

            Args:
                    threadID            (str)          --  Unique Id for thread

                    entity_name         (str)          --  Name of the entity which needs to be verified

                    db_path             (str)          --  sqlite db file path

                    db_query_field      (str)          --  query field name for db

                    solr_query_field    (str)          --  query field name for solr

                    q_param             (str)          --  criteria for querying solr

                    solr_url            (str)          --  Base url for solr

                        Example : "http://<searchengine_machinename>:<port no>/solr"

                    entity_delimiter (str)      -- Delimiter used in separating entities in sqlite db

        """
        threading.Thread.__init__(self)
        self.thread_id = threadID
        self.entity_name = entity_name
        self.db_path = db_path
        self.log = logger.get_log()
        self.criteria = q_param
        self.solr_url = solr_url
        self.db_query_field = db_query_field
        self.solr_query_field = solr_query_field
        self.success = 0
        self.failed = 0
        self.delimiter = entity_delimiter
        self.partial_success = 0

    def query_solr(self, criteria, start=0, rows=0, fields=None):
        """
            queries solr for given input and returns the response json

            Args:

                criteria       (str)        --  Solr query q param

                start          (int)        --  solr query start param

                rows           (int)        --  solr query rows param

                fields         (list)       --  list of solr fields which needs to be retrieved

            Returns:
                None

        """
        solr_url = self.solr_url + "/select?q={0}&start={1}&rows={2}&wt=json".format(criteria, start, rows)
        if fields is not None:
            updated_fl = ""
            for field in fields:
                updated_fl = updated_fl + field + ","
            solr_url = solr_url + "&fl={0}".format(updated_fl[:-1])
        self.log.info("Querying solr : %s", solr_url)
        response = requests.get(url=solr_url)
        if not response.ok:
            self.log.info("Unable to get response. Trying out one last time")
            response = requests.get(url=solr_url)
            if not response.ok:
                raise Exception("Solr query response was not ok. Aborting the thread")
        if start == 0 and rows == 0:
            return int(response.json()['response']['numFound'])
        return response.json()['response']['docs']

    def get_localised_entity_key(self, name):
        """
            get the localized entity name for the given regex entity display name

                Args:
                    name        (str)       --  Name of the activate regex entity

                Returns:
                    str     --  Localised entity name for the given activate regex entity
        """
        entity_name = Entity_constant.DB_COLUMN_NAMES
        entity_key = Entity_constant.DB_COLUMN_TO_KEY
        if name in entity_name:
            index = entity_name.index(name)
            return entity_key[index]
        self.log.info("Localised name not found for entity : %s", name)
        return name

    def query_db(self, db_path, field, field_values):
        """
           queries the sqlite db for given field and returns the rows as dict

            Args:
                db_path     (str)       --  Path to sqlite db

                field       (str)       --  table field name which needs to be queried

                field_values (str)      --  field values which needs to be queried

            Returns:
                dict    -- containing all rows & columns present in table in sqlite db
        """
        connection = sqlite3.connect(db_path)
        connection.row_factory = sqlite3.Row
        cursor = connection.cursor()
        query = 'select * from entity where {0} in ({1})'.format(field, field_values)
        self.log.info("Submitting query to DB : %s", query)
        column_names = []
        return_list = []
        result = cursor.execute(query)
        for row in result.description:
            column_names.append(self.get_localised_entity_key(row[0]))
        result = result.fetchall()
        for res in range(len(result)):
            temp_dict = {}
            for col in range(len(column_names)):
                temp_dict.update({column_names[col]: result[res][col]})
            return_list.append(temp_dict)
        return return_list

    def form_query_values(self, response, field):
        """
           forms the field query for the given solr response and solr field

            Args:

                response      (dict)    --  Solr response

                    Example : [{'url': 'C:\\754\\Lindsey good 311540831-5456\\Devin Chan others 3493.docx'}]

                field          (str)    --  field name which needs to be retrieved from solr response

            Returns:
                str     -- field values for each document in solr response separated by comma

            Exception:

                    if field is missing in solr response
        """
        value = ""
        for doc in response:
            if field not in doc:
                self.log.info("Required Field %s missing in solr response.", field)
                raise Exception("Required query Field is missing in the solr response. Please check")
            value = f"{value}\"{doc[field]}\","
        return value[:-1]

    def verify_entity(self, solr_response, db_response):
        """
           cross verifies whether extracted entity and entities in DB are matching

                Args:
                    solr_response       (dict)   --  response from solr containing documents url and entities extracted

                    Example : [{'url': 'C:\\754\\Lindsey 3493.docx','entity_ip': ['1.1.1.1']}}]

                    db_response         (dict)   --  response from sqlite db containing document details and entities

                    Example : [{'ID': 2, 'FilePath': 'C:\\754\\Lindsey 3493.docx', 'entity_ccn': None,
                    'entity_ssn': None, 'entity_ip': '1.1.1.1',
                     'Subject': 'Lindsey 3493.docx ce117a65c6aa4f9b8dd0cbe0c2978df7', 'Flag': 0}]

        """
        for solr_doc in solr_response:
            self.log.info("Verifying Doc [%s]", solr_doc[self.solr_query_field])
            if self.entity_name in solr_doc and solr_doc[self.entity_name] is not None:
                self.log.info("Entity[%s] is present in solr.", self.entity_name)
                found = False
                for db_doc in db_response:
                    if self.db_query_field not in db_doc:
                        self.db_query_field = self.get_localised_entity_key(self.db_query_field)
                        self.log.info(f"Changing DB query field as Localized key : {self.db_query_field}")
                    if db_doc[self.db_query_field].lower() == solr_doc[self.solr_query_field].lower():
                        found = True
                        self.log.info("Found Matching document from DB source. Doc : %s", db_doc[self.db_query_field])
                        if self.entity_name in db_doc:
                            self.log.info("Entity[%s] is present in DB. Going to verify it", self.entity_name)
                            if self.delimiter not in db_doc[self.entity_name] and db_doc[self.entity_name].strip(
                            ) in solr_doc[self.entity_name]:
                                self.log.info("Entity matched")
                                self.success = self.success + 1
                            elif self.delimiter not in db_doc[self.entity_name] and \
                                    solr_doc[self.entity_name][0] in db_doc[self.entity_name].strip():
                                self.log.info("Partial success")
                                self.partial_success = self.partial_success + 1
                                self.failed = self.failed + 1
                            elif self.delimiter in db_doc[self.entity_name]:
                                self.log.info("DB contains multiple entities. Split it")
                                multiple_entity = db_doc[self.entity_name].split(self.delimiter)
                                if len(multiple_entity) != len(solr_doc[self.entity_name]):
                                    msg = f"Entities missing. Actual entity count<{len(solr_doc[self.entity_name])}>" \
                                          f" Expected entity count <{len(multiple_entity)}>"
                                    self.log.info(msg)
                                    msg = f"Error: Actual entity {solr_doc[self.entity_name]}  " \
                                          f"Expected Entity {multiple_entity}"
                                    self.log.info(msg)
                                    self.failed = self.failed + 1
                                else:
                                    self.log.info("Multiple entity[%s] length matched", self.entity_name)
                                    multiple_entity.sort()
                                    solr_doc[self.entity_name].sort()
                                    if multiple_entity == solr_doc[self.entity_name]:
                                        self.log.info("Multiple entity[%s] verification done.", self.entity_name)
                                        self.success = self.success + 1
                                    else:
                                        self.failed = self.failed + 1
                                        self.partial_success = self.partial_success + 1
                                        msg = f"Error: For Entity {self.entity_name} --> " \
                                              f"Actual{solr_doc[self.entity_name]} Expected{multiple_entity}"
                                        self.log.info(msg)

                            else:
                                self.failed = self.failed + 1
                                self.log.info("Entity Mismatched")
                                self.log.info("Error: Expected : %s", db_doc[self.entity_name])
                                self.log.info("Error: Actual : %s", solr_doc[self.entity_name])
                        else:
                            self.log.info("Error: Entity[%s] is present in solr but not in DB", self.entity_name)
                            self.failed = self.failed + 1
                        break
                if not found:
                    self.log.info("Found flag : False. Document is missing in DB")
                    self.failed = self.failed + 1
            else:
                found = False
                for db_doc in db_response:
                    if self.db_query_field not in db_doc:
                        self.db_query_field = self.get_localised_entity_key(self.db_query_field)
                        self.log.info(f"Changing DB query field as Localized key : {self.db_query_field}")
                    if db_doc[self.db_query_field].lower() == solr_doc[self.solr_query_field].lower():
                        found = True
                        self.log.info("Found Matching document from DB source. Doc : %s", db_doc[self.db_query_field])
                        if self.entity_name in db_doc and db_doc[self.entity_name] is not None:
                            self.log.info(
                                "Error: Entity[%s] is not present in solr but present in DB with values",
                                self.entity_name)
                            self.log.info("Error: DB values for this entity : %s", db_doc[self.entity_name])
                            self.failed = self.failed + 1
                        else:
                            self.log.info(
                                "Entity[%s] is not present in solr & also in DB. consider as success",
                                self.entity_name)
                            self.success = self.success + 1
                        break
                if not found:
                    self.log.info("Found flag : False. Document is missing in DB")
                    self.failed = self.failed + 1

    def run(self):
        self.log.info("Started the thread : %s", self.thread_id)
        msg = f"Thread {threading.current_thread().ident} will verify the entity : {self.entity_name}"
        self.log.info(msg)
        total_documents = self.query_solr(criteria=self.criteria)
        fetched_documents = 0
        start = 0
        batch_size = 10
        batch_id = 1
        try:
            while fetched_documents < total_documents:
                self.log.info("Going to fetch batch[%s] from solr", batch_id)
                solr_response = self.query_solr(
                    criteria=self.criteria,
                    start=start,
                    rows=batch_size,
                    fields=[self.solr_query_field, self.entity_name])
                self.log.info("Solr response : %s", solr_response)
                solr_query_values = self.form_query_values(solr_response, self.solr_query_field)
                db_response = self.query_db(
                    db_path=self.db_path,
                    field=self.db_query_field,
                    field_values=solr_query_values)
                self.log.info("DB response : %s", db_response)
                # Mapping key(FilePath-->Url_idx) is not there in db. so handle it accordingly
                old_db_query_field = self.db_query_field
                self.verify_entity(solr_response=solr_response, db_response=db_response)
                self.db_query_field = old_db_query_field
                start = start + batch_size
                fetched_documents = fetched_documents + batch_size
                batch_id = batch_id + 1
            if self.success + self.partial_success != total_documents:
                self.log.info("Total documents and Success/Partial success count not matched")
                msg = f"Total success count {self.success} Partial success count {self.partial_success} " \
                      f"total document count {total_documents} Mismatched"
                raise Exception(msg)

        except Exception as exce:
            self.failed = self.failed + 1
            self.log.info("Something went wrong!!!")
            self.log.exception(exce)
