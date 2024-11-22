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
import os

from AutomationUtils import logger, constants
from AutomationUtils.cvtestcase import CVTestCase
from VirtualServer.VSAUtils import VirtualServerHelper, OptionsHelper
from Application.SQL.sqlhelper import SQLHelper


class TestCase(CVTestCase):
    """Class for executing Basic acceptance Test of NDMP backup and Restore test case"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "VSA VMWare SQL AppAware Basic with NO Existing SQL Instance"
        self.product = self.products_list.VIRTUALIZATIONVMWARE
        self.feature = self.features_list.DATAPROTECTION
        self.show_to_user = False
        self.sqlhelper = None
        self.tcinputs = {
            "BackupVMName": None,
            "SQLInstance": None,
            "SQLUserName": None,
            "SQLPassword": None
        }

    def run(self):
        """Main function for test case execution"""

        self.log = logger.get_log()

        try:
            self.log.info("Started executing %s testcase", self.id)

            self.log.info("*" * 10 + " Initialize helper objects " + "*" * 10)
            auto_commcell = VirtualServerHelper.AutoVSACommcell(self.commcell, self.csdb)
            auto_client = VirtualServerHelper.AutoVSAVSClient(auto_commcell, self.client)
            auto_instance = VirtualServerHelper.AutoVSAVSInstance(
                auto_client, self.agent, self.instance)
            auto_backupset = VirtualServerHelper.AutoVSABackupset(auto_instance, self.backupset)
            auto_subclient = VirtualServerHelper.AutoVSASubclient(auto_backupset, self.subclient)
            vm = self.tcinputs["BackupVMName"]

            if vm not in auto_subclient.vm_list:
                raise Exception("Given Backup vm not found in subclient list")

            self.log.info("Working on VM - " + str(vm))

            self.log.info("Reverting VM to snap named Fresh if it exists")
            auto_subclient.hvobj.VMs[vm].revert_snap()
            try:
                self.log.info("Deleting the client from commcell if it exists")
                auto_commcell.commcell.clients.delete(vm)

            except Exception as e:
                self.log.info("The Instance is already cleared so just proceeding %s", e)

            auto_subclient.hvobj.VMs[vm].update_vm_info("All", True)

            sql_machine_user = auto_subclient.hvobj.VMs[vm].user_name
            sql_machine_pass = auto_subclient.hvobj.VMs[vm].password
            sql_instance = self.tcinputs["SQLInstance"]
            sql_user = self.tcinputs["SQLUserName"]
            sql_pass = self.tcinputs["SQLPassword"]

            # Get SQL helper object.  User & Pw is required as the vm doesnt have CV software yet.
            self.sqlhelper = SQLHelper(self,
                                       auto_subclient.hvobj.VMs[vm].ip,
                                       sql_instance,
                                       sql_user,
                                       sql_pass,
                                       _app_aware=True,
                                       _machine_user=sql_machine_user,
                                       _machine_pass=sql_machine_pass)

            self.sqlhelper.sql_setup(noof_dbs=1,
                                     noof_ffg_db=2,
                                     noof_files_ffg=2,
                                     noof_tables_ffg=3,
                                     noof_rows_table=10
                                     )

            sqldump_file1 = "before_backup_full.txt"
            sqldump_file2 = "after_restore.txt"

            # get table shuffled list
            returnstring, list1, list2, list3 = self.sqlhelper.dbvalidate.get_random_dbnames_and_filegroups(
                100,
                self.sqlhelper.noof_dbs,
                self.sqlhelper.noof_ffg_db,
                self.sqlhelper.noof_tables_ffg
            )
            if not returnstring:
                raise Exception("Error in while generating the random number.")

            # write the original database to file for comparison
            if not self.sqlhelper.dbvalidate.dump_db_to_file(
                    os.path.join(self.sqlhelper.tcdir, sqldump_file1),
                    self.sqlhelper.dbname, list1, list2, list3, 'FULL'):
                raise Exception("Failed to write database to file.")

            self.log.info("*" * 10 + " Backup " + " *" * 10)
            backup_options = OptionsHelper.BackupOptions(auto_subclient)
            backup_options.Application_aware = True
            auto_subclient.backup(backup_options)

            self.log.info("*" * 10 + " Run SQL Restore and Validate it " + "*" * 10)

            # run restore in place job
            auto_commcell.commcell.clients.refresh()
            client = auto_commcell.commcell.clients.get(vm)
            agent = client.agents.get('SQL Server')
            instance = agent.instances.get(sql_instance)
            subclient = instance.subclients.get("default")
            self.client = client
            self.instance = instance
            self.subclient = subclient

            sqlhelper_client = SQLHelper(self, client.client_name, instance.instance_name, sql_user, sql_pass)

            self.log.info("*" * 10 + " Run Restore in place " + "*" * 10)
            if not sqlhelper_client.sql_restore(self.sqlhelper.subcontent):
                raise Exception("Restore was not successful!")

            # write the restored database to file for comparison
            if not sqlhelper_client.dbvalidate.dump_db_to_file(
                    os.path.join(self.sqlhelper.tcdir, sqldump_file2),
                    self.sqlhelper.dbname, list1, list2, list3, 'FULL'):
                raise Exception("Failed to write database to file.")

            # compare original and restored databases
            self.log.info("*" * 10 + " Validating content " + "*" * 10)
            if not sqlhelper_client.dbvalidate.db_compare(os.path.join(self.sqlhelper.tcdir, sqldump_file1),
                                                          os.path.join(self.sqlhelper.tcdir, sqldump_file2)):
                raise Exception("Failed to compare both files.")

            self.log.info("*" * 10 + " TestCase {0} successfully completed! ".format(self.id) + "*" * 10)
            self.status = constants.PASSED

        except Exception as exp:
            self.log.error('Failed with error: ' + str(exp))
            self.result_string = str(exp)
            self.status = constants.FAILED

        finally:
            self.sqlhelper.sql_teardown()
