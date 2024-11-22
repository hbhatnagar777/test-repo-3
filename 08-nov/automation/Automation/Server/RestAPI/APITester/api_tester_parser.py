# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""

API Tester Parser for parsing and running the API test cases

APITester: Class to parse dependencies and run the tests

APITester:

run_test_cases()                           -- runs the test cases for the provided dependencies

"""

import inspect
import json
import ruamel.yaml as yaml_loader
from Server.RestAPI.APITester import entity
from AutomationUtils import logger
from AutomationUtils.machine import Machine


class APITester:

    """

    => this class reads all input documents and pass it to each entity to extract the required things.

    => it handles the entity in dependency file. it creates list of entites and store it.

    => then it build testcase set for each entity and run it.

    """

    def __init__(self, commcell_object, dependency_file_path, payload_values_json):
        """

        => this initialization method reads swagger document and dependency file and pass it to create entity instance.

        """

        self.entity_set = list([])

        try:
            assert dependency_file_path is not None, "dependency file required!"
            self.log = logger.get_log()
            self.server_base_url = commcell_object._web_service
            self.commcell_object = commcell_object
            # reading dependency file
            with open(dependency_file_path) as file_data:
                self.raw_entity_set = json.load(file_data)

            # reading swagger file
            self.client_machine = Machine(commcell_object.commserv_client)
            file_data = self.client_machine.read_file(
                self.client_machine.join_path(
                    commcell_object.commserv_client.install_directory,
                    "WebConsole",
                    "sandbox",
                    "apiexplorer",
                    "apiJson",
                    "OpenAPI3.yaml"))
            yaml = yaml_loader.YAML(typ='safe')
            self.parsed_swagger_json = yaml.load(file_data)

            # creating entity instance and storing it in an array
            for raw_entity in self.raw_entity_set:
                entity_to = entity.Entity(raw_entity, self.parsed_swagger_json, self.server_base_url, payload_values_json)
                self.entity_set.append(entity_to)

        except Exception as excp:
            raise Exception("\n {0} {1}".format(inspect.stack()[0][3], str(excp)))

    def run_test_cases(self):
        """

        => this method first log in and use the auth_token for furthur sending request.

        => it loop through each entity and build the testcases and run entity testcases.

        """
        try:
            counter = 0
            auth_token = self.commcell_object.auth_token

            for entity in self.entity_set:
                counter += 1
                self.log.info("<====================================================================================>")
                self.log.info("entity number : "+str(counter))

                # self.log.infoing entity name
                name = entity.get_entity_name()
                if name is not None:
                    self.log.info("entity name : "+name)

                # create testing sets for each entity (entity create api set for all its apis)
                entity.build()

                # run the created testcases for each entity
                entity.run_entity_test(auth_token)

                self.log.info("<====================================================================================>")

        except Exception as excp:
            raise Exception("\n {0} {1}".format(inspect.stack()[0][3], str(excp)))
