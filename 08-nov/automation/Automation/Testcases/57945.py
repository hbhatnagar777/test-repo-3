# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()      --  initialize TestCase class

    setup()         --  setup function of this test case

    run()           --  run function of this test case

    tear_down()     --  tear down function of this test case
"""
import sys
import collections
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from Application.Exchange.ExchangeMailbox.exchange_mailbox import ExchangeMailbox
from Application.Exchange.exchange_sqlite_helper import SQLiteHelper
from Application.Exchange.ExchangeMailbox.constants import GET_INDEXED_GUIDS_QUERY


class TestCase(CVTestCase):
    """Class for executing test case of discovery, association
    and disassociation of Exchange Online Mailbox Groups

        Example for test case inputs:
        "57945":
        {
        "ClientName": <Exchange Online Client Name>
        "AgentName": "Exchange Mailbox",
        "InstanceName": "defaultInstanceName",
        "BackupsetName": "User Mailbox",
        "EnvironmentType":4,
        "SubClientName":"usermailbox",
        "PlanName": "<Plan-name>>",
        "NewSharedPathDetails": {
          "Path": <unc-path-of-shared-job-results-directory or local-path-of-proxy-server>
          "Username":
            if local_path then None
            else if UNC Path then Job Result Directory machine username
          ,
          "Password":
          if local_path then None
          else if UNC Path then the Job Results Directory machine password
        },
        "ProxyServerDetails":
          {
            "Name": "<Name-of-exchange-IDA-Machine>",
            "IpAddress": "<IP Address-of-Exchange-IDA-Machine>",
            "Username": "<Username-Of-Exchange-IDA>",
            "Password": "<Password-Of-Exchange-IDA>"
          }

      }
      """

    def __init__(self):
        """Initializes test case class object

            Properties to be initialized:
                name            (str)       --  name of this test case


                show_to_user    (bool)      --  test case flag to determine if the test case is
                                                    to be shown to user or not
                    Accept:
                        True    -   test case will be shown to user from commcell gui

                        False   -   test case will not be shown to user

                    default: False

                tcinputs    (dict)      --  dict of test case inputs with input name as dict key
                                                and value as input type

                        Ex: {

                             "MY_INPUT_NAME": None

                        }

                exmbclient_object      (object)    --  Object of ExchangeMailbox class

                query                   (str)      --  The query that would be executed on the Dat file


        """
        super(TestCase, self).__init__()
        self.exmb_sqlite_helper = None
        self.name = "Basic Acceptance Test for Moving Job Results Directory"
        self.show_to_user = True
        self.product = self.products_list.EXCHANGEMB
        self.exmbclient_object = None
        self.query = GET_INDEXED_GUIDS_QUERY
        self.tcinputs = {
            "NewSharedPathDetails": None
        }

    def setup(self):
        """ Setup Function for this Test Case"""
        self.exmbclient_object = ExchangeMailbox(self)
        self.log.info('Exchange Mailbox Object Created')

        self._client = self.exmbclient_object.cvoperations.add_exchange_client(
        )
        self.log.info('Created Exchange Online Client')
        self._subclient = self.exmbclient_object.cvoperations.subclient
        self.log.info('Associated Exchange Online Sub Client')

        self.log.info('Client associated with Exchange Mailbox Object')

        self.exmb_sqlite_helper = SQLiteHelper(self)

    def run(self):
        """ Run function of this test case"""
        try:
            self.subclient.enable_auto_discover_association(association_name="All Public Folders",
                                                            plan_name=self.tcinputs["ExchangePlan"])
            self.log.info('Associated the Public Folders')

            self.log.info('Starting Public Folder backup')
            self.exmbclient_object.cvoperations.backup_public_folders()
            self.log.info('Backup Job completed')
            job_results_dir = self.exmbclient_object.get_job_results_dir
            self.log.info(
                'Job Result Directory is: {}'.format(job_results_dir))
            sqlite_res = self.exmb_sqlite_helper.execute_dat_file_query(job_results_dir,
                                                                        file_name="ExMBJobInfo.dat",
                                                                        query=self.query)
            sqlite_guids_initial = list()
            for i in sqlite_res:
                sqlite_guids_initial.append(i[0].upper())

            shared_path_details = self.tcinputs.get('NewSharedPathDetails', {})
            self.client.change_o365_client_job_results_directory(
                new_directory_path=shared_path_details["Path"],
                username=shared_path_details.get('Username', None),
                password=shared_path_details.get('Password', None))
            self.log.info('Job Result Directory changed successfully')

            self.client.refresh()
            self.log.info('Refreshed the client object')

            job_results_dir = self.exmbclient_object.get_job_results_dir
            self.log.info(
                'New Job Result Directory is: {}'.format(job_results_dir))

            self.log.info('Initiating a new backup job')
            self.exmbclient_object.cvoperations.backup_public_folders()
            self.log.info('Backup job complete')

            sqlite_res = self.exmb_sqlite_helper.execute_dat_file_query(job_results_dir,
                                                                        file_name="ExMBJobInfo.dat",
                                                                        query=self.query)

            sqlite_guids_final = list()
            for i in sqlite_res:
                sqlite_guids_final.append(i[0].upper())

            if collections.Counter(sqlite_guids_final) != collections.Counter(
                    sqlite_guids_initial):
                self.log.error('The two lists do not match')
                raise Exception('Indexed Lists do not match')

            self.log.info('Two lists matched')
            self.log.info('All the items were indexed')
            self.log.info('Test Case Successful!!!')
        except Exception as ex:
            self.log.error('Error %s on line %s. Error %s', type(ex).__name__,
                           sys.exc_info()[-1].tb_lineno, ex)
            self.result_string = str(ex)
            self.status = constants.FAILED
