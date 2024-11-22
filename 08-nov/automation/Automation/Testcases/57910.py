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

import time
import sys
from AutomationUtils import machine, constants
from AutomationUtils.cvtestcase import CVTestCase
from Application.Exchange.ExchangeMailbox.exchange_mailbox import ExchangeMailbox
from Application.Exchange.exchange_sqlite_helper import SQLiteHelper
from Application.Exchange.exchangepowershell_helper import ExchangePowerShell
from Application.Exchange.ExchangeMailbox.constants import (
    GET_INDEXED_GUIDS_QUERY
)


class TestCase(CVTestCase):
    """
        Exchange Online Public Folder Discovery Validation test Case

        Example for test case inputs:
            "57910":
            {

            "AgentName": "Exchange Mailbox",
            "InstanceName": "defaultInstanceName",
            "BackupsetName": "User Mailbox",
            "ProxyServers": [
              <proxy server name>
            ],
            "EnvironmentType":4,
            "JobResultDirectory":"<either-empty-or-the-UNC-Path>",
            "RecallService":"",
            "StoragePolicyName":"Exchange Plan",
            "IndexServer":"<index-server name>",
            "GroupName":"<name-of-group-to-be-discovered>",
            "azureAppKeySecret": "<azure-app-key-secret-from-Azure-portal>",
            "azureAppKeyID":"<App-Key-ID-from-Azure-portal>",
            "azureTenantName": "<Tenant-Name-from-Azure-portal>",
            "SubClientName":"usermailbox",
            "RestorePath": <complete-path-of-the-local-directory-of-proxy-server>
            "PlanName": "<Plan-name>>",
            "ServiceAccountDetails": [
              {
                "ServiceType": 2,
                "Username": "<username>",
                "Password": "<password>>"
              }
            ],
            "ProxyServerDetails":
              {
                "IpAddress": "<IP Address-of-Exchange-Proxy Server-Machine>",
                "Username": "<Username-Of-Exchange-Proxy-Server>",
                "Password": "<Password-Of-Exchange-Proxy-Server>"
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


                machine                (object)    --  Object of Machine class for the local machine

                powershell             (object)    --   Object of Exchange PowerShell

                sqlite_helper         (object)      --   Object of SQLite Helper class

                query                   (str)      --   The query that would be executed to get the
                                                        list of GUIDs from the SQLIte DAT file

        """
        super(TestCase, self).__init__()

        self.name = "Exchange Online Public Folder " \
                    "Discovery, Backup and Restore Validation"
        self.show_to_user = True
        self.product = self.products_list.EXCHANGEMB
        self.exmbclient_object = None
        self.machine = None
        self.powershell = None
        self.sqlite_helper = None
        self.query = GET_INDEXED_GUIDS_QUERY
        self._utility = None

    def setup(self):
        """
        Set up function for this test case
        """
        self.exmbclient_object = ExchangeMailbox(self)

        self._client = self.exmbclient_object.cvoperations.add_exchange_client()
        self.log.info('Created Exchange Online Client')
        self._subclient = self.exmbclient_object.cvoperations.subclient
        self.log.info('Associated Exchange Online SubClient')

        self.sqlite_helper = SQLiteHelper(self)
        self.machine = machine.Machine()

        self.powershell = ExchangePowerShell(ex_object=self.exmbclient_object, cas_server_name=None,
                                             exchange_server=None,
                                             exchange_adminname=self.exmbclient_object.exchange_online_user,
                                             exchange_adminpwd=self.exmbclient_object.exchange_online_password,
                                             server_name=self.exmbclient_object.server_name)

    def run(self):
        """Run function for this test case"""
        try:
            folder_name = self.powershell.exch_online_public_folder_ops(op_type="CreatePF")
            self.log.info('Created the Public Folder')

            folder_smtp_address = self.powershell.exch_online_public_folder_ops(
                op_type="MailEnable",
                public_folder_name=folder_name)
            self.log.info('Mail enabled the Public Folder with SMTP Address: {}'.format(
                folder_smtp_address))

            self.exmbclient_object.exchange_lib.send_email(
                mailbox_list=[folder_smtp_address])
            self.log.info('Populated the Public Folder with E-Mails')

            time.sleep(50)
            # It takes these many seconds on an average for all the emails to
            # show up in the Public Folder

            item_count = self.powershell.exch_online_public_folder_ops(
                op_type="ItemCount",
                public_folder_name=folder_name)
            self.log.info(
                'Item Count from Exchange PowerShell: {}'.format(item_count))

            self.subclient.enable_auto_discover_association(association_name="All Public Folders",
                                                            plan_name=self.tcinputs["Office365Plan"])
            self.log.info('Associated the Public Folders')

            self.log.info('Starting Public Folder backup')
            self.exmbclient_object.cvoperations.backup_public_folders()
            self.log.info('Backup Job completed')

            self.log.info('Getting the Public Folders using PowerShell')
            hash_prop_dict = {
                "hash_algo": 'sha256',
                "attribute": 'EntryId'
            }
            folder_guids = self.powershell.exch_online_public_folder_ops(
                op_type="GetFolderIDs",
                prop_dict=hash_prop_dict
            )
            self.log.info(folder_guids)
            self.log.info(
                'Got the GUIDs of Exchange Online Folders from PowerShell')

            self.log.info('Copying the file from Proxy server to Test machine')
            job_results_dir = self.exmbclient_object.get_job_results_dir
            self.log.info(
                'Job Result Directory is: {}'.format(job_results_dir))

            sqlite_res = self.sqlite_helper.execute_dat_file_query(job_results_dir,
                                                                   file_name="ExMBJobInfo.dat",
                                                                   query=self.query)
            self.log.info(
                'Successfully copied the file to the machine and got the GUIDs')

            sqlite_guids = list()
            for i in sqlite_res:
                sqlite_guids.append(i[0].upper())
            self.log.info('Got the GUIDs from the dat file')

            self.log.info('Comparing the two lists')
            for entry in folder_guids:
                if entry.upper() not in sqlite_guids:
                    self.log.info(
                        "Folder GUID not found: Folder ID: %s", entry)
                    raise Exception('Public Folder ID not found in the DB')

            self.log.info('All the public folders have been backed up')

            public_folder_guid = self.exmbclient_object.csdb_helper.get_public_folder_guid()
            self.log.info('Got the Public Folder GUID %s', public_folder_guid)

            restore_path = ["\\MB\\{", public_folder_guid, "}\\", folder_name]
            restore_path = ''.join(restore_path)
            self.log.info('Restore Path: %s', restore_path)

            self.log.info('Starting Restore Job')
            restore_dir = self.tcinputs.get("RestorePath", r"C:\\tmp")
            restore_job = self.subclient.disk_restore(
                paths=[restore_path],
                destination_path=restore_dir,
                destination_client=self.exmbclient_object.server_name,
            )
            self.log.info(
                "Restore Job Started with JOB ID: {}".format(
                    restore_job.job_id))
            restore_job.wait_for_completion()
            self.log.info('Restore Job completed')

            restore_job_item_count = restore_job.details["jobDetail"]["detailInfo"]["numOfObjects"]
            self.log.info('Items restored: {}'.format(restore_job_item_count))

            if restore_job_item_count != item_count:
                self.log.info(
                    'Restore Item Count:{}'.format(restore_job_item_count))
                self.log.info(
                    'Public Folder Item Count: {}'.format(item_count))
                raise Exception('Item Count Mismatch')

            self.log.info('Count matched')
            self.log.info('Test Case Completed!!!')

            self.log.info('Performing Cleanup')
            self.commcell.clients.delete(self.client.client_name)

            delete_public_folder_dict = {
                "mail_enabled": True
            }
            self.powershell.exch_online_public_folder_ops(
                op_type="Delete",
                public_folder_name=folder_name,
                prop_dict=delete_public_folder_dict)
            self.log.info('Deleted the CLIENT')

        except Exception as ex:
            self.log.error('Error %s on line %s. Error %s', type(ex).__name__,
                           sys.exc_info()[-1].tb_lineno, ex)
            self.result_string = str(ex)
            self.status = constants.FAILED
