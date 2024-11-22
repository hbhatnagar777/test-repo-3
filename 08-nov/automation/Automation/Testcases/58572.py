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
from cvpysdk.datacube.constants import IndexServerConstants
from AutomationUtils.cvtestcase import CVTestCase
from Application.Exchange.ExchangeMailbox.exchange_mailbox import ExchangeMailbox
from Application.Exchange.ExchangeMailbox.data_generation import TestData
from Application.Exchange.ExchangeMailbox.solr_helper import SolrHelper
from Application.Exchange.ExchangeMailbox.constants import (
    ARCHIVE_POLICY_DEFAULT
)
from dynamicindex.index_server_helper import IndexServerHelper


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
        self.name = "Backup and in place restore of Index server data"
        self.show_to_user = True
        self.tcinputs = {
            "IndexServer": None,
            "source_client": None,
            "StoragePolicyName": None,
            "JobResultDirectory": None,
            "DomainName": None,
            "ProxyServers": None,
            "ExchangeServerName": None,
            "ExchangeCASServer": None,
            "EnvironmentType": None,
        }
        self.exmbclient_object = None
        self.smtp_list = []
        self.mailboxes_list = []
        self.solr_helper = None
        self.index_server_helper = None
        self.index_server_roles = [IndexServerConstants.ROLE_EXCHANGE_INDEX]

    def setup(self):
        """Setup function of this test case"""

        self.exmbclient_object = ExchangeMailbox(self)

        self.log.info("--------------------TEST DATA--------------------")
        testdata = TestData(self.exmbclient_object)

        self.mailboxes_list = testdata.create_mailbox()
        self.smtp_list = testdata.import_pst()
        self.exmbclient_object.users = self.smtp_list

        self._client = self.exmbclient_object.cvoperations.add_exchange_client()
        self._subclient = self.exmbclient_object.cvoperations.subclient

        archive_policy_default = ARCHIVE_POLICY_DEFAULT % (self.id)
        self.archive_policy_default = self.exmbclient_object.cvoperations.add_exchange_policy(
            self.exmbclient_object.cvoperations.get_policy_object
            (archive_policy_default, "Archive"))

        self.index_server_helper = IndexServerHelper(self.commcell, self.tcinputs['IndexServer'])
        self.log.info("Index server helper intialized")
        self.index_server_helper.init_subclient()

    def run(self):
        """Run function of this test case"""
        try:
            self.log.info("-------Creating Subclient content and associate to User-------")
            subclient_content = {
                'mailboxNames': [self.mailboxes_list[0]],
                'archive_policy': self.archive_policy_default,
            }
            active_directory = self.exmbclient_object.active_directory
            active_directory.set_user_assocaitions(subclient_content)

            self.log.info("------------RUNNING EXCHANGE DATA BACKUP--------------------")
            exch_bckp_jobid = self.exmbclient_object.cvoperations.run_backup()
            if exch_bckp_jobid is None:
                raise Exception("Exchange Backup job id not generated")

            self.solr_helper = SolrHelper(self.exmbclient_object)
            num_found_src = self.solr_helper.get_user_sum_of_results_count()
            self.log.info("Number of items in Source Index server that are backedup: %d", num_found_src)

            self.log.info("------------Preparing for Index server Backup------------")
            self.index_server_helper.subclient_obj.configure_backup(
                storage_policy=self.tcinputs['StoragePolicyName'],
                role_content=self.index_server_roles)
            self.index_server_helper.run_full_backup()

            self.log.info(
                "In-place restore of index server for role : %s",
                self.index_server_roles)

            job_obj = self.index_server_helper.subclient_obj.do_restore_in_place(
                roles=self.index_server_roles)
            if job_obj is None:
                raise Exception("Issue with in place restore jobId")
            self.index_server_helper.monitor_restore_job(job_obj=job_obj)

            num_found_dest = self.solr_helper.get_user_sum_of_results_count()
            self.log.info("Number of items in Source Index server after restore: %d", num_found_dest)

            self.log.info("Validating the items from source and destination")
            if num_found_src == num_found_dest:
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
            self.log.info("58572 TC passed")
