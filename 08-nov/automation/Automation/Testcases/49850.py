# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

TestCase is the only class definied in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()      --  initialize TestCase class

    run()           --  run function of this test case
"""

import os
from cvpysdk.exception import SDKException
from Server.Alerts.alert_helper import AlertHelper
from Application.SQL.sqlhelper import SQLHelper
from AutomationUtils import constants
from AutomationUtils.machine import Machine
from AutomationUtils.cvtestcase import CVTestCase


# Class of Testcase is named as TestCase which inherits from CVTestCase
class TestCase(CVTestCase):
    """ Class for executing test case for Agent Based Alert verification"""

    # Constructor for the testcase
    def __init__(self):
        """Initializes the testcase object"""
        super(TestCase, self).__init__()
        self.name = 'Testcase for Agent Based Alert Verification'
        self.cache = None
        self.cache1 = None
        self.sql_helper = None

    def setup_entities(self):
        """Sets up subclient entities required for testcase"""
        self.log.info("=============================")
        self.log.info("Settting up Testcase Entities")
        self.sql_helper = SQLHelper(_tcobject=self,
                                    _sqlclient=self.commcell.webconsole_hostname,
                                    _sqlinstance=self.commcell.webconsole_hostname + '\\' + self.tcinputs["InstanceName"].split('\\')[1],
                                    _sqluser=self.tcinputs["SQLUsername"],
                                    _sqlpass=self.tcinputs["SQLPassword"])
        # Setup SQL Server helper
        self.sql_helper.sql_setup(noof_dbs=1,
                                  noof_ffg_db=1,
                                  noof_files_ffg=1,
                                  noof_tables_ffg=1,
                                  noof_rows_table=10)
        self.log.info("Entities Setup Completed")
        self.log.info("=============================")

    def cleanup_entities(self):
        """Cleans up different entities created for the testcase"""
        self.log.info("Cleaning Up Testcase Entities")
        # Delete the subclient
        self.instance.subclients.delete(self.sql_helper.subclient.subclient_name)
        # Delete generated Database
        try:
            self.sql_helper.dbinit.drop_databases(databasename=self.sql_helper.dbname)
        except Exception as e:
            print(str(e))
        # Cleanup created directories on both Local machine and Client machine
        sqlmachine = Machine(self.client)
        localmachine = Machine()
        sqlmachine.remove_directory(self.sql_helper.tcdir)
        localmachine.remove_directory(
            os.path.join(self.log_dir, os.path.basename(os.path.normpath(self.sql_helper.tcdir)))
        )
        self.log.info("Testcase Entities Cleaned")

    def add_additional_setting(self):
        """
            Used for adding appropriate additional settings to trigger the alert situation
        """
        self.log.info('Adding Additional Setting')
        self.commcell.add_additional_setting(category='CommServDB.GxGlobalParam',
                                             key_name='client Offline Alert Notification Interval',
                                             data_type='INTEGER',
                                             value='0')
        self.log.info('Setting added Successfully')

    def misc_cleanup(self):
        """
            Used for removing the additional settings that were added for triggering alert situation
        """
        self.log.info('Removing Additional Setting')
        self.commcell.delete_additional_setting(category='CommServDB.GxGlobalParam',
                                                key_name='client Offline Alert Notification Interval')
        self.log.info('Setting Removed Successfully')

    def get_backup_objects(self, client_name, agent_name, backupset_name, subclient_name):
        """Used for getting client and subclient objects required for triggering alert situation

            Args:
                client_name (string)  -  Client Name
                agent_name (string) - Agent Name
                backupset_name (string) - Backupset Name
                subclient_name (string) - Subclient Name

            Returns:
                (tuple) - Tuple of client, subclient objects
        """
        client_obj = self.commcell.clients.get(client_name)
        subclient_obj = client_obj.agents.get(agent_name).backupsets.get(backupset_name).subclients.get(subclient_name)
        return client_obj, subclient_obj

    def run(self):
        """Main function for test case execution"""
        try:
            # Setup testcase entities
            self.setup_entities()
            # Initialize alerts object
            self.add_additional_setting()
            self.log.info('Initializing Alerts')
            alert_helper = AlertHelper(commcell_object=self.commcell,
                                       category='Job Management',
                                       alert_type='Data Protection')

            # Creating Alert of given type
            # Feed alert data to create the right format
            alert_data = alert_helper.get_alert_xml(name='Test Backup Restore Job - SQL Server',
                                                    notif_type=['Email'],
                                                    entities={'clients': self.tcinputs['ClientName']},
                                                    criteria=1,
                                                    mail_recipent=["TestAutomation3@commvault.com"],
                                                    ida_types=["SQL Server"])
            # Initialize Mailbox object
            alert_helper.initialize_mailbox(set_unread_only=False)

            self.log.info('Creating Alert %s for testcase %s', alert_data.get("alert_name"), self.id)
            alert_helper.create_alert_from_xml()

            # Trigger Alert Situation
            self.cache = alert_helper.alert_situations.backup_job(client=self.client,
                                                                  subclient=self.sql_helper.subclient,
                                                                  backup_type=self.tcinputs['BackupType'])

            # Function to read email and confirmation alert notification
            try:
                alert_helper.check_if_alert_mail_received(short_interval=10, patterns=[self.cache.get("job_id"),
                                                                                       self.sql_helper.subclient.name,
                                                                                       self.tcinputs["AgentName"]])
                self.log.info('============================================================')
                self.log.info('Received Alert Notification Mail  for Agent : %s', self.tcinputs["AgentName"])
                self.log.info('============================================================')
            except Exception as mail_excp:
                self.log.error('Didn\'t receive mail for Agent : %s', self.tcinputs["AgentName"])
                self.log.error('Encountered exception %s', str(mail_excp))
                raise SDKException('Alert', '102', 'Alert notification was expected')

            # Now Run Backup Job using Windows File System Agent
            client1, subclient1 = self.get_backup_objects(client_name=self.tcinputs['ClientName1'],
                                                          agent_name=self.tcinputs['AgentName1'],
                                                          backupset_name=self.tcinputs['BackupsetName1'],
                                                          subclient_name=self.tcinputs['SubclientName1'])
            self.cache1 = alert_helper.alert_situations.backup_job(client=client1,
                                                                   subclient=subclient1,
                                                                   backup_type=self.tcinputs['BackupType1'])
            # Function to read email and confirmation alert notification
            try:
                alert_helper.check_if_alert_mail_received(short_interval=20, patterns=[self.cache1.get("job_id"),
                                                                                       self.tcinputs["BackupsetName1"],
                                                                                       self.tcinputs["SubclientName1"]])
                raise SDKException('Alert', '102', 'Alert notification wasn\'t expected')
            except Exception as mail_excp:
                self.log.error('Didn\'t receive mail for Agent : %s', self.tcinputs["AgentName1"])
                self.log.error('Encountered exception %s', str(mail_excp))

        except Exception as excp:
            self.log.error('Failed with error %s', str(excp))
            # Set the Test-Case params : result_string, status
            self.result_string = str(excp)
            self.status = constants.FAILED
        finally:
            # Cleanup phase
            if self.cache:
                self.log.info('Will try to disconnect from the machine')
                self.cache['client_machine'].disconnect()
                self.log.info('Disconnected from the machine successfully')

            alert_helper.cleanup()
            self.cleanup_entities()
            self.misc_cleanup()
