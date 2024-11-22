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
    __init__()                      --  initialize TestCase class

    setup()                         --  setup function of this test case

    remove_index_server_directory() --  deletes and recreates the index directory of data source core

    run()                           --  run function of this test case

    tear_down()                     --  tear down function of this test case

"""

import sys
import time
from cvpysdk.datacube.constants import IndexServerConstants as index_constants
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils import constants
from AutomationUtils.machine import Machine
from dynamicindex.utils import constants as dynamic_constants
from dynamicindex.index_server_helper import IndexServerHelper
from Application.Exchange.ExchangeMailbox.exchange_mailbox import ExchangeMailbox
from Application.Exchange.ExchangeMailbox.data_generation import TestData
from Application.Exchange.ExchangeMailbox.solr_helper import SolrHelper
from Application.Exchange.ExchangeMailbox.constants import (
    ARCHIVE_POLICY_ATTACHMENTS,
    ARCHIVE_POLICY_LARGER_THAN,
    ARCHIVE_POLICY_OLDER_THAN,
    ARCHIVE_POLICY_DEFAULT
)


class TestCase(CVTestCase):
    """Class for executing Basic acceptance test of Exchange
    User Mailbox Onpremise backup and restore"""

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

        """
        super(TestCase, self).__init__()
        self.name = "Exchange Mailbox - Validate Reconstruction"
        self.show_to_user = True
        self.smtp_list = []
        self.mailboxes_list = []
        self.exmbclient_object = None
        self.tcinputs = {
            "IndexServer": None,
            "StoragePolicyName": None,
            "JobResultDirectory": None,
            "DomainName": None,
            "ProxyServers": None,
            "ExchangeServerName": None,
            "ExchangeCASServer": None,
            "EnvironmentType": None,
            "cvsolr": None
        }
        self.data_source_obj = None
        self.index_server_helper = None
        self.index_server_obj = None
        self.solr_helper = None
        self.index_server_helper = None
        self.index_server_roles = [index_constants.ROLE_EXCHANGE_INDEX]

    def setup(self):
        """Setup function of this test case"""
        self.exmbclient_object = ExchangeMailbox(self)
        self.log.info(
            "--------------------------TEST DATA-----------------------------------"
        )

        testdata = TestData(self.exmbclient_object)

        self.mailboxes_list = testdata.create_mailbox()
        self.smtp_list = testdata.import_pst()
        self.exmbclient_object.users = self.smtp_list

        self._client = self.exmbclient_object.cvoperations.add_exchange_client()
        self._subclient = self.exmbclient_object.cvoperations.subclient

        archive_policy_default = ARCHIVE_POLICY_DEFAULT % (self.id)
        archive_policy_attachments = ARCHIVE_POLICY_ATTACHMENTS % (self.id)
        archive_policy_msg_larger_than = ARCHIVE_POLICY_LARGER_THAN % (self.id)
        archive_policy_msg_older_than = ARCHIVE_POLICY_OLDER_THAN % (self.id)

        self.archive_policy_default = self.exmbclient_object.cvoperations.add_exchange_policy(
            self.exmbclient_object.cvoperations.get_policy_object
            (archive_policy_default, "Archive"))

        archive_policy_object = self.exmbclient_object.cvoperations.get_policy_object(
            archive_policy_attachments, "Archive")
        archive_policy_object.include_messages_with_attachements = True
        self.archive_policy_attachments = (
            self.exmbclient_object.cvoperations.add_exchange_policy(archive_policy_object))

        archive_policy_object = self.exmbclient_object.cvoperations.get_policy_object(
            archive_policy_msg_older_than, "Archive")
        archive_policy_object.include_messages_older_than = 30
        self.archive_policy_msg_older_than = (
            self.exmbclient_object.cvoperations.add_exchange_policy(archive_policy_object))

        archive_policy_object = self.exmbclient_object.cvoperations.get_policy_object(
            archive_policy_msg_larger_than, "Archive")
        archive_policy_object.include_messages_larger_than = 10
        self.archive_policy_msg_larger_than = (
            self.exmbclient_object.cvoperations.add_exchange_policy(archive_policy_object))

        if not self.tcinputs['cvsolr']:
            self.solr_helper = SolrHelper(self.exmbclient_object)
        else:
            self.solr_helper = SolrHelper(self.exmbclient_object, None, True)

        self.index_server_helper = IndexServerHelper(self.commcell,
                                                     self.tcinputs['IndexServerName'])
        self.log.info("Index server helper intialized")
        self.index_server_helper.update_roles(index_server_roles=self.index_server_roles)
        self.index_server_obj = self.index_server_helper.index_server_obj
        self.index_server_helper.init_subclient()

    def remove_index_server_directory(self):
        """deletes and recreates the index directory of data source core"""

        src_machine_obj = Machine(machine_name=self.index_server_obj.client_name[0],
                                  commcell_object=self.commcell)

        analytics_dir = src_machine_obj.get_registry_value(
            commvault_key=dynamic_constants.ANALYTICS_REG_KEY,
            value=dynamic_constants.ANALYTICS_DIR_REG_KEY)
        self.log.info("Index server Index directory is : %s", analytics_dir)
        self.log.info("Stopping the index server process")
        dest_client_obj = self.commcell.clients.get(self.index_server_obj.client_name[0])
        dest_client_obj.stop_service(service_name=dynamic_constants.ANALYTICS_SERVICE_NAME)
        self.log.info("Wait two minute for solr to go down")
        time.sleep(120)
        dir_to_remove = f"{analytics_dir}\\{self.data_source_obj.computed_core_name}"
        self.log.info("Remove the index dir of open data source code : %s", dir_to_remove)
        src_machine_obj.remove_directory(directory_name=dir_to_remove)
        self.log.info("Starting the index server process")
        dest_client_obj.start_service(service_name=dynamic_constants.ANALYTICS_SERVICE_NAME)
        self.log.info("Wait two minute for solr to come up")
        time.sleep(120)

    def run(self):
        """Run function of this test case"""
        try:

            subclient_content_1 = {
                'mailboxNames': [self.mailboxes_list[0], self.mailboxes_list[1]],
                'archive_policy': self.archive_policy_default,
            }
            subclient_content_2 = {
                'mailboxNames': [self.mailboxes_list[2], self.mailboxes_list[3]],
                'archive_policy': self.archive_policy_attachments,
            }
            subclient_content_3 = {
                'mailboxNames': [self.mailboxes_list[4], self.mailboxes_list[5]],
                'archive_policy': self.archive_policy_msg_larger_than,
            }
            subclient_content_4 = {
                'mailboxNames': [self.mailboxes_list[6], self.mailboxes_list[7]],
                'archive_policy': self.archive_policy_msg_older_than,
            }

            self.log.info("----------------CREATE USER ASSOCAITION----------------")
            active_directory = self.exmbclient_object.active_directory

            active_directory.set_user_assocaitions(subclient_content_1)

            active_directory.set_user_assocaitions(subclient_content_2)

            active_directory.set_user_assocaitions(subclient_content_3)

            active_directory.set_user_assocaitions(subclient_content_4)

            self.log.info("------------READING MAILBOX PROPERTIES BEFORE BACKUP------------")

            before_backup_object = self.exmbclient_object.exchange_lib
            before_backup_object.get_mailbox_prop()

            self.log.info("----------RUNNING EXCHANGE DATA FIRST BACKUP-------------")
            exch_bckp_jobid = self.exmbclient_object.cvoperations.run_backup()
            if exch_bckp_jobid is None:
                raise Exception("Exchange Backup job id not generated")
            self.solr_helper.check_all_items_played_successfully(exch_bckp_jobid, None)

            self.log.info("-----------RUNNING EXCHANGE DATA SECOND BACKUP------------")
            exch_bckp_jobid = self.exmbclient_object.cvoperations.run_backup()
            if exch_bckp_jobid is None:
                raise Exception("Exchange Backup job id not generated")
            self.solr_helper.check_all_items_played_successfully(exch_bckp_jobid, None)

            before_reconsturction = self.solr_helper.get_user_sum_of_results_count()

            self.remove_index_server_directory()

            self.log.info("--------------RUNNING BACKUP FOR RECONSTRUCTION---------------")
            self.exmbclient_object.cvoperations.run_backup()

            after_reconsturction = self.solr_helper.get_user_sum_of_results_count()

            self.log.info("Validating the items from source and destination")
            if before_reconsturction == after_reconsturction:
                self.log.info("The items are correctly restored in the destination")
            else:
                raise Exception("The items are not correctly restored in the destination")

        except Exception as ex:
            self.log.error('Error %s on line %s. Error %s', type(ex).__name__,
                           sys.exc_info()[-1].tb_lineno, ex)
            self.result_string = str(ex)
            self.status = constants.FAILED

    def tear_down(self):
        """Tear down function of this test case"""
        if self.status == constants.PASSED:
            self.log.info("51253 TC passed")
