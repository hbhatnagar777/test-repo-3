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
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils import constants
from Application.Exchange.ExchangeMailbox.exchange_mailbox import ExchangeMailbox
from Application.Exchange.ExchangeMailbox.data_generation import TestData
from Application.Exchange.ExchangeMailbox.constants import (
    ARCHIVE_POLICY_DEFAULT)
from Application.Exchange.ExchangeMailbox.pstingestion_helper import PSTIngestion


class TestCase(CVTestCase):
    """PST Ingestion: Basic Test of pst archive and restore with mailbox data"""

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
        self._subclient = None
        self.file_owner = None
        self._client = None
        self.name = "PST Ingestion: Basic Test of pst archive and restore with mailbox data"
        self.show_to_user = True
        self.smtp_list = []
        self.mailboxes_list = []
        self.exmbclient_object = None
        self.tcinputs = {
            "SubclientName": None,
            "BackupsetName": None,
            "IndexServer": None,
            "StoragePolicyName": None,
            "PSTPath": None,
            "JobResultDirectory": None,
            "DomainName": None,
            "ProxyServers": None,
            "ExchangeServerName": None,
            "ExchangeCASServer": None,
            "EnvironmentType": None,
            "pstIngestionDetails": None
        }
        self.archive_policy_default = None
        self.test_data = None

    def setup(self):
        """Setup function of this test case"""
        self.exmbclient_object = ExchangeMailbox(self)
        self.log.info(
            "========================== TEST DATA =========================="
        )
        test_data = TestData(self.exmbclient_object)
        self.test_data = test_data
        self.mailboxes_list = test_data.create_mailbox()
        self.smtp_list = test_data.import_pst()
        self.file_owner = self.tcinputs[
            'pstIngestionDetails']['fileOwnerMbxName'].split("\\")[-1]
        test_data.clean_onprem_mailbox_contents([self.file_owner])
        self.test_data.powershell_object.import_pst(self.file_owner,
                                                    self.exmbclient_object.pst_path)
        self.exmbclient_object.users = self.smtp_list

        self._client = self.exmbclient_object.cvoperations.add_exchange_client()
        self._subclient = self.exmbclient_object.cvoperations.subclient
        ewsURL = self.tcinputs.get("EWSServiceURL", None)
        if ewsURL:
            self.exmbclient_object.cvoperations.enableEWSSupport(service_url=ewsURL)
        archive_policy_default = ARCHIVE_POLICY_DEFAULT % self.id
        self.archive_policy_default = self.exmbclient_object.cvoperations.add_exchange_plan(
            plan_name=archive_policy_default)

    def run(self):
        """Run function of this test case"""
        try:
            self.log.info(
                "========================== CREATE ASSOCIATION ==========================")
            subclient_content = {
                'mailboxNames': [self.mailboxes_list[0], self.mailboxes_list[1],
                                 self.mailboxes_list[2], self.mailboxes_list[3]],
                'plan_name': self.archive_policy_default.plan_name
            }
            pst_ingestion_contents = self.tcinputs['pstIngestionDetails']
            active_directory = self.exmbclient_object.active_directory
            before_backup_object = self.exmbclient_object.exchange_lib
            before_backup_object.mail_users = [self.smtp_list[0].lower(),
                                               self.smtp_list[1].lower(),
                                               self.smtp_list[2].lower(),
                                               self.smtp_list[3].lower()]
            before_backup_object.get_mailbox_prop()
            pstingestion_obj = PSTIngestion(self.exmbclient_object, self.test_data,
                                            fix_mbx=[pst_ingestion_contents["fileOwnerMbxName"].lower()])
            import_to_mbx = self.mailboxes_list[len(self.mailboxes_list) - 2]
            owner_values = pstingestion_obj.get_all_pst_owners()
            for key, value in owner_values.items():
                self.log.info("Values for %s:" % key)
                self.log.info("File Name: %s | | Owner: %s" % (value[0], value[1]))

            db = (f'{self.test_data.json_value.Mailbox[0].DATABASE}_'
                  f'{self.exmbclient_object.exchange_server[0]}_{self.test_data.testcase_id}')
            pstingestion_obj.merge_backup_properties(before_backup_object, import_to_mbx,
                                                     owner_values, db)

            active_directory.set_user_assocaitions(subclient_content, False)
            for pst_sub_content in pst_ingestion_contents['details']:
                active_directory.set_pst_associations(pst_sub_content)
            self.log.info(
                "======================= RUNNING BACKUP AND PST INGESTION =======================")
            self.exmbclient_object.cvoperations.run_backup()
            job = self.exmbclient_object.cvoperations.run_pst_ingestion()
            response = job.advanced_job_details(job.ADVANCED_JOB_DETAILS.BKUP_INFO)
            if 'bkpInfo' in response:
                if response['bkpInfo']:
                    advanced_details = response['bkpInfo']['exchMbInfo']
                else:
                    raise Exception('Job Details is empty')
            else:
                raise Exception("Backup info not present in response")

            self.log.info(
                """======================== VERIFYING OWNER VALUES  ========================""")

            pstingestion_obj.verify_owners(owner_values, advanced_details['SourceMailboxStats'])
            self.log.info(
                """========================== OWNER VALUES VERIFIED ==========================""")

            self.log.info(
                "========================== RUNNING RESTORE ==========================")

            mailbox_restore_name = self.mailboxes_list[len(self.mailboxes_list) - 1]
            self.exmbclient_object.cvoperations.run_restore(
                oop=True,
                destination_mailbox=mailbox_restore_name
            )
            self.log.info(
                "========================== RESTORE JOB COMPLETED ==========================")
            self.log.info(
                "====================== GETTING PROPERTIES AFTER RESTORE ======================")
            mailbox_restore_name = f'{mailbox_restore_name}@{ self.tcinputs["DomainName"]}'
            after_restore_object = self.exmbclient_object.exchange_lib
            after_restore_object.mail_users = [mailbox_restore_name]
            after_restore_object.get_mailbox_prop()
            restore = self.exmbclient_object.restore

            self.log.info(
                """========================== COMPARING PROPERTIES ==========================""")

            restore.compare_mailbox_for_pst_ingestion(before_backup_object.mailbox_prop,
                                                      after_restore_object.mailbox_prop[
                                                          mailbox_restore_name].folders)
            self.log.info(
                """==================== PROPERTIES VERIFIED SUCCESSFULLY ====================""")

        except Exception as ex:
            self.log.error('Error {} on line {}. Error {}'.format(
                type(ex).__name__, sys.exc_info()[-1].tb_lineno, ex))
            self.result_string = str(ex)
            self.status = constants.FAILED
