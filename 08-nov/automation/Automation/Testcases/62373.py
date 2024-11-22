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

    run()           --  run function of this test case
"""

from AutomationUtils.cvtestcase import CVTestCase
from VirtualServer.VSAUtils import OptionsHelper, VirtualServerUtils
from AutomationUtils import constants

class TestCase(CVTestCase):
    """Class for executing Basic acceptance Test of VSA backup and Agent less restore case"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Automation- SMB restore performance check"
        self.product = self.products_list.VIRTUALIZATIONVMWARE
        self.feature = self.features_list.DATAPROTECTION
        self.test_individual_status = True
        self.test_individual_failure_message = ""
        self.tcinputs = {}
    def run(self):
        """Main function for test case execution"""

        try:
            auto_subclient = VirtualServerUtils.subclient_initialize(self)
            VirtualServerUtils.decorative_log("Backup")
            backup_options = OptionsHelper.BackupOptions(auto_subclient)
            backup_options.backup_type = "INCREMENTAL"
            auto_subclient.backup(backup_options)
            try:
                VirtualServerUtils.decorative_log("Agentless file restores")
                file_restore_options = OptionsHelper.FileLevelRestoreOptions(auto_subclient)
                file_restore_options.smbrestore = True
                VirtualServerUtils.set_inputs(self.tcinputs, file_restore_options)
                auto_subclient.agentless_file_restore(file_restore_options, "SMBRESTORE", self.tcinputs.get('sourcevm'), self.tcinputs.get('destvm1'), self.tcinputs.get('Indextype'))
                query = "SELECT top 1 duration FROM JMRestoreStatS where srcclientid ="\
                        "(select id from app_client where name = '"+self.tcinputs.get('sourcevm')+"')ORDER BY jobId DESC"
                self.csdb.execute(query)
                jobtime = self.csdb.fetch_all_rows()
                jobtime = jobtime[0][0]
            except Exception as exp:
                self.log.error('Failed with error: '+str(exp))
                raise exp
            try:
                VirtualServerUtils.decorative_log("Agentless file restores")
                file_restore_options = OptionsHelper.FileLevelRestoreOptions(auto_subclient)
                file_restore_options.smbrestore = False
                VirtualServerUtils.set_inputs(self.tcinputs, file_restore_options)
                auto_subclient.agentless_file_restore(file_restore_options, "SMBRESTORE", self.tcinputs.get('sourcevm'), self.tcinputs.get('destvm'), self.tcinputs.get('Indextype'))
                query = "SELECT top 1 duration FROM JMRestoreStatS where srcclientid ="\
                        "(select id from app_client where name = '"+self.tcinputs.get('sourcevm')+"')ORDER BY jobId DESC"
                self.csdb.execute(query)
                jobtime1 = self.csdb.fetch_all_rows()
                jobtime1 = jobtime1[0][0]
            except Exception as exp:
                self.log.error('Failed with error: '+str(exp))
                raise exp
            try:
                if jobtime1 > jobtime:
                    VirtualServerUtils.decorative_log("Performance check passed")
                    self.result_string = str('SMB restore job took less time than guest tools restore approach')
            except Exception as exp:
                self.log.error('Failed with error: '+str("Guest tools restore is faster than SMB restore"))
                raise exp
        except Exception as exp:
            self.log.error('Failed with error: '+str(exp))
            self.result_string = str(exp)
            self.status = constants.FAILED
        finally:
            if auto_subclient and backup_options:
                auto_subclient.cleanup_testdata(backup_options)
            if not self.test_individual_status:
                self.result_string = self.test_individual_failure_message
                self.status = constants.FAILED