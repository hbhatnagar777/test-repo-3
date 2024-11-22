# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Main module which contains helpers CVDotNetContainer testcases

CVDNCTestcase: Helper class for CVDotNetContainer testcases

CVDNCTestcase:

    __init__()                  --  Initializes the CVDNCTestcase helper class

    save_setup_data()           --  Saves the setup data to the disk for further testcases to use

    load_setup_data()           --  Loads the service setup data from the disk

    set_host_machine()          --  Creates the host machine's client and machine object

    exec()                      --  Executes the command on the host machine

    request()                   --  Sends an HTTP request

    verify()                    --  Verifies the response received based on the args passed

    populate_random_data()      --  Populates random data on the CVDNC test service

    random_sentence()           --  Returns a random sentence

    random_guid()               --  Returns a random GUID

"""
import os
import json
import uuid
import random
import requests
import time

from AutomationUtils import logger
from AutomationUtils.machine import Machine


class CVDNCTestcase:
    """Helper class for CVDotNetContainer testcases"""

    def __init__(self, commcell):
        """Class constructor

            Args:
                commcell        (obj)       --      The CvPySDK commcell object

        """

        self.log = logger.get_log()
        self.commcell = commcell
        self.host_cl = None
        self.host_machine = None
        self.setup_data = None
        self.svc_url = None

    def save_setup_data(self, data):
        """Saves the setup data to the disk for further testcases to use

            Args:
                data            (dict)      --  The data to save to JSON file

        """

        data_file = os.path.join(logger.get_log_dir(), 'cvdnc_test_service.json')

        self.log.info('Saving service data to disk [%s]', data)
        with open(data_file, 'w+') as df:
            df.write(json.dumps(data, indent=4))

    def load_setup_data(self):
        """Loads the service setup data from the disk"""

        data_file = os.path.join(logger.get_log_dir(), 'cvdnc_test_service.json')

        if not os.path.exists(data_file):
            raise Exception('Service setup data file not present/not set up.')

        with open(data_file, 'r') as df:
            data = json.load(df)

        self.log.info('Loaded service data from local disk [%s]', data)

        if ('svc_url' not in data
                or 'deployment' not in data
                or 'host_machine' not in data):
            raise Exception('Failed to get the required data from the setup operation.')

        self.setup_data = data
        self.svc_url = self.setup_data.get('svc_url')

        self.log.info('Working with service URL [%s]', self.svc_url)

        return data

    def set_host_machine(self, machine_name=None):
        """Creates the host machine's client and machine object

            Args:
                machine_name        (str/None)      --      The name of the host machine. Pass None to pick from setup

        """

        if machine_name is None and self.setup_data is not None:
            machine_name = self.setup_data.get('host_machine')

        self.log.info('Setting up host machine objects for [%s]', machine_name)
        self.host_cl = self.commcell.clients.get(machine_name)
        self.host_machine = Machine(self.host_cl)

    def exec(self, command):
        """Executes the command on the host machine

            Args:
                command     (str)   --      The command to execute

            Returns:
                The output formatter class

        """

        self.log.info('Command [%s]', command)
        return self.host_machine.execute_command(command)

    def request(self, method, route, json=None, data=None, params=None, headers=None):
        """Sends an HTTP request

            Args:
                method          (str)   --      The HTTP method

                route           (str)   --      The path to send request to

                json            (dict)  --      The JSON data to send

                data            (dict)  --      The form data to send

                params          (dict)  --      The parameters to pass

                headers         (dict)  --      The headers to set in the request

            Returns:
                request.Response object

        """

        url = f'{self.svc_url}/{route}'
        method = method.lower()
        headers = {'accept': 'application/json'} if headers is None else headers
        content_type = None

        if json:
            content_type = 'JSON'
        elif isinstance(data, dict):
            content_type = 'FORM DATA'
        elif isinstance(data, str):
            content_type = 'XML'

        self.log.info(
            '***** %s %s Content [%s] Accept [%s] Params [%s] *****',
            method.upper(), url, content_type, headers['accept'], params
        )

        response = getattr(requests, method)(url, json=json, data=data, headers=headers, params=params)

        return response

    def verify(self, response, status=200, content_type='application/json'):
        """Verifies the response received based on the args passed

            Args:
                response        (obj)   --  The request.Response object

                status          (int)   --  The status code to verify

                content_type    (str)   --  The content type to verify

            Returns:
                None, raises exception when verification failed.

        """

        try:
            self.log.info('Received response. Status code [%s] Response [%s]', response.status_code, response.text)
            assert response.status_code == status, f'Status code is not [{status}]. Got [{response.status_code}]'
            assert content_type in response.headers.get('Content-Type', ''), f'Content type is not [{content_type}]'
        except Exception as e:
            self.log.error('Got exception [%s]', e)
            self.log.error(response.headers)
            raise Exception(e)

    def populate_random_data(self):
        """Populates random data on the CVDNC test service"""

        self.log.info('***** Populating random data *****')
        random_data = []
        for _ in range(5):
            json = {
                'comment': self.random_sentence(),
                'userGuid': self.random_guid()
            }
            response = self.request('POST', 'CRUD', json=json)
            self.verify(response)
            random_data.append(json)
            time.sleep(1)

        response = self.request('GET', 'CRUD')
        for data in random_data:
            user_guid = data['userGuid']
            if user_guid not in response.text:
                raise Exception('Item with GUID not found in the response [%s]', user_guid)

        return random_data

    @staticmethod
    def random_sentence(word_count=5):
        """Returns a random sentence

            Args:
                word_count      (int)   --  The number of words in the sentence

            Returns:
                The random sentence

        """

        words = []
        for _word in range(word_count):
            word = ''
            for _ in range(random.randint(3, 8)):
                character = chr(random.randint(97, 122))
                word += character
            words.append(word)

        return ' '.join(words)

    @staticmethod
    def random_guid():
        """Returns a random GUID"""
        return str(uuid.uuid4())
