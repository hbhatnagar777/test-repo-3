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
    __init__()          --  initialize TestCase class

    run()               --  run function of this test case calls SnapHelper Class to execute
                            and Validate Below Operations.
                            Intellisnap test case for data modification.

        Test Case JOSN inputs:
            "AgentName":                "name of the agent eg: File System",
            "ArrayName":                "name of the Array",
            "ArrayPassword":            "user name of the Array",
            "ArrayUserName":            "password of the Array",
            "ClientName":               "name of the Client",
            "InstanceName":             "name of the Instance eg: DefaultInstanceName",
            "MediaAgent":               "Media Agent Name",
            "SnapAutomationOutput":     "Output location eg: C:\\automationoutput",
            "SnapEngineAtArray":        "Snap Engine name eg: NetApp",
            "SnapEngineAtSubclient":    "Snap Vendor Name eg: NetApp",
            "SubclientContent":         "Subclient Content eg: H:\\",
            "BackendArrayName1":        "name of the Backend Array",
            "BackendArrayUserName1":    "user name of the Backend Array",
            "BackendArrayPassword1":    "password of the Backend Array",
            "BackendArrayControlHost1": "Backend Array ControlHost",
            "BackendSnapEngineAtArray": "Backend Snap Engine name",
            "BackendArrayName2":        "name of the second Backend Array",
            "BackendArrayUserName2":    "user name of the second Backend Array",
            "BackendArrayPassword2":    "password of the second Backend Array",
            "BackendArrayControlHost2": "second Backend Array ControlHost",
"""

import os
from base64 import b64encode
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from FileSystem.SNAPUtils.snapconstants import SNAPConstants
from FileSystem.SNAPUtils.snaphelper import SNAPHelper


class TestCase(CVTestCase):
    """Class for executing Basic acceptance test of IntelliSnap backup and Restore test case
    for Netapp Array"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.snapconstants = None
        self.snaphelper = None
        self.tcinputs = {
            "MediaAgent": None,
            "SubclientContent": None,
            "SnapAutomationOutput": None,
            "SnapEngineAtArray": None,
            "SnapEngineAtSubclient": None
            }
        self.name = """Automation : Basic Acceptance Test for IntelliSnap Data Modification
                    for All Vendors"""


    def run(self):
        """Main function for test case execution
        """

        try:
            self.snapconstants = SNAPConstants(self.commcell, self.client, self.agent, self.tcinputs)
            self.snaphelper = SNAPHelper(self.commcell, self.client, self.agent, self.tcinputs, self.snapconstants)
            self.log.info("*" * 20 + "Adding Arrays" + "*" * 20)
            self.snaphelper.add_array()
            if self.snapconstants.snap_engine_at_array in ["Dell EMC VNX / CLARiiON", "Fujitsu ETERNUS AF / DX"]:
                self.snapconstants.config_update_level = "subclient"
            if self.snapconstants.config_update_level == "array":
                if self.snapconstants.source_config is not None:
                    self.snaphelper.edit_array(self.snapconstants.arrayname,
                                               self.snapconstants.source_config,
                                               self.snapconstants.config_update_level,
                                               array_access_node=self.snapconstants.array_access_nodes_to_edit)

            if self.snapconstants.vplex_engine is True:
                """ Adding First Backeend arrays """
                self.log.info("*" * 20 + "Adding backend array for Snap Engine: {0}".format(
                    self.tcinputs['BackendSnapEngineAtArray']))
                self.snapconstants.arrayname = self.tcinputs['BackendArrayName1']
                self.snapconstants.username = self.tcinputs['BackendArrayUserName1']
                self.snapconstants.password = b64encode(
                    self.tcinputs['BackendArrayPassword1'].encode()).decode()
                self.snapconstants.controlhost = self.tcinputs.get('BackendArrayControlHost1', None)
                self.snapconstants.snap_engine_at_array = self.tcinputs['BackendSnapEngineAtArray']
                self.snaphelper.add_array()

                """ Adding Second Backend array """
                self.log.info("*" * 20 + "Adding Second backend array for Snap Engine: {0}".format(
                    self.tcinputs['BackendSnapEngineAtArray']))
                self.snapconstants.arrayname = self.tcinputs['BackendArrayName2']
                self.snapconstants.username = self.tcinputs['BackendArrayUserName2']
                self.snapconstants.password = b64encode(
                    self.tcinputs['BackendArrayPasswd2'].encode()).decode()
                self.snapconstants.controlhost = self.tcinputs.get('BackendControlHost2', None)
                self.snaphelper.add_array()

            """ Re-Set arrayname and engine Name as primary """
            self.snapconstants.arrayname = self.tcinputs['ArrayName']
            self.snapconstants.snap_engine_at_array = self.tcinputs['SnapEngineAtArray']
            self.log.info("*" * 20 + "Setup of Intellisnap Entities" + "*" * 20)
            self.snaphelper.setup()
            self.snaphelper.add_test_data_folder()
            if self.snapconstants.config_update_level == "subclient":
                if self.snapconstants.source_config is not None:
                    self.snaphelper.edit_array(self.snapconstants.arrayname,
                                               self.snapconstants.source_config,
                                               self.snapconstants.config_update_level,
                                               int(self.snapconstants.subclient.subclient_id),
                                               array_access_node=self.snapconstants.array_access_nodes_to_edit)

            """Full job"""
            self.snaphelper.update_test_data(mode='add', path=self.snapconstants.test_data_path)
            self.log.info("*" * 20 + "Running FULL Snap Backup job" + "*" * 20)
            full1_job = self.snaphelper.snap_backup()
            """ add new files under Testdata, delete folder (dir1) inside Full folder """
            count = 0
            path1 = []
            path2 = []
            for path in self.snapconstants.test_data_path:
                filepath1 = os.path.join(self.snapconstants.test_data_path[count], 'newfile1.txt')
                self.snaphelper.client_machine.create_file(filepath1, 'new test file1', file_size=500)
                path1.append(filepath1)
                filepath2 = os.path.join(self.snapconstants.test_data_path[count], 'newfile2.txt')
                self.snaphelper.client_machine.create_file(filepath2, 'new test file2', file_size=500)
                path2.append(filepath2)
                #copy data before deleting
                self.snaphelper.update_test_data(mode='copy', path=self.snapconstants.test_data_path)
                #delete dir1 folder from Full
                test_path = os.path.join(self.snapconstants.test_data_folder[count], 'dir1')
                self.snaphelper.client_machine.remove_directory(test_path)
                count = count + 1
            #INC1
            self.log.info("*" * 20 + "Running INCREMENTAL Snap Backup job" + "*" * 20)
            self.snapconstants.backup_level = 'INCREMENTAL'
            self.snaphelper.update_test_data(mode='add', path=self.snapconstants.test_data_path)
            inc1_job = self.snaphelper.snap_backup()
            #Latest Snap outplace restore with show deleted items. outplace validation
            count = 0
            for path in self.snapconstants.test_data_path:
                self.snapconstants.source_path = [path]
                if self.snapconstants.skip_catalog:
                    self.log.info("*" * 20 + "Running Backup copy from Storage Policy" + "*" * 20)
                    self.snaphelper.backup_copy()
                    self.log.info("*" * 20 + "Running OutPlace Restore from backup copy with\
                            Source Path: {0}".format(path) + "*" * 20)
                    self.snaphelper.tape_outplace(inc1_job.job_id, 2, fs_options=True)
                    self.snaphelper.compare(self.snaphelper.client_machine,
                                            self.snapconstants.windows_restore_client,
                                            self.snapconstants.copy_content_location[count],
                                            self.snapconstants.tape_outplace_restore_location)
                else:
                    self.log.info("*" * 20 + "Running OutPlace Restore from SnapBackup with\
                            Source Path: {0}".format(path) + "*" * 20)
                    self.snaphelper.snap_outplace(1, fs_options=True)
                    self.snaphelper.compare(self.snaphelper.client_machine,
                                            self.snaphelper.client_machine,
                                            self.snapconstants.copy_content_location[count],
                                            self.snapconstants.snap_outplace_restore_location)
                count = count + 1
            self.log.info("*" * 20 + "Restore of deleted data and Validation is\
                          Successful " + "*" * 20)

            #Empty Incremental INC2
            self.log.info("*" * 20 + "Running INCREMENTAL Snap Backup job" + "*" * 20)
            inc2_job = self.snaphelper.snap_backup()
            #Inplace restore from snap and validate
            self.snapconstants.source_path = self.snapconstants.test_data_path
            self.log.info("*" * 20 + "Running InPlace Restore from Snap Backup job" + "*" * 20)
            self.snaphelper.update_test_data(mode='copy', path=self.snapconstants.test_data_path)
            self.snaphelper.snap_inplace(1)
            self.snaphelper.inplace_validation(inc2_job.job_id,
                                               self.snapconstants.snap_copy_name,
                                               self.snapconstants.test_data_path)
            count = 0
            for path in self.snapconstants.test_data_path:
                #modify a file from root dir
                self.snaphelper.client_machine.modify_content_of_file(path2[count])
                #add new file under E:\TestData\INC\dir2
                filepath3 = os.path.join(self.snapconstants.test_data_folder[count+1], 'dir2', 'newfile3.txt')
                self.snaphelper.client_machine.create_file(filepath3, 'new test file3', file_size=500)
                self.snaphelper.update_test_data(mode='copy', path=self.snapconstants.test_data_path)
                #delete a file from root dir
                self.snaphelper.client_machine.delete_file(path1[count])
                count = count + 1
            #INC3 job
            self.log.info("*" * 20 + "Running INCREMENTAL Snap Backup job" + "*" * 20)
            inc3_job = self.snaphelper.snap_backup()
            #Latest Snap outplace restore with show deleted items. outplace validation
            count = 0
            for path in self.snapconstants.test_data_path:
                self.snapconstants.source_path = [path]
                if self.snapconstants.skip_catalog:
                    self.log.info("*" * 20 + "Running Backup copy from Storage Policy" + "*" * 20)
                    self.snaphelper.backup_copy()
                    self.log.info("*" * 20 + "Running OutPlace Restore from backup copy with\
                            Source Path: {0}".format(path) + "*" * 20)
                    self.snaphelper.tape_outplace(inc3_job.job_id, 2, fs_options=True)
                    self.snaphelper.compare(self.snaphelper.client_machine,
                                            self.snapconstants.windows_restore_client,
                                            self.snapconstants.copy_content_location[count],
                                            self.snapconstants.tape_outplace_restore_location)
                else:
                    self.log.info("*" * 20 + "Running OutPlace Restore from SnapBackup with\
                            Source Path: {0}".format(path) + "*" * 20)
                    self.snaphelper.snap_outplace(1, fs_options=True)
                    self.snaphelper.compare(self.snaphelper.client_machine,
                                            self.snaphelper.client_machine,
                                            self.snapconstants.copy_content_location[count],
                                            self.snapconstants.snap_outplace_restore_location)
                count = count + 1
            self.log.info("*" * 20 + "Restore of deleted data and Validation is\
                          Successful " + "*" * 20)
            #Backup Copy
            self.log.info("*" * 20 + "Running Backup copy from Storage Policy" + "*" * 20)
            self.snaphelper.backup_copy()
            #Latest Tape outplace restore with show deleted items. outplace validation
            self.log.info("*" * 20 + "Running OutPlace Restore from Backup Copy" + "*" * 20)
            self.snapconstants.source_path = self.snapconstants.test_data_path
            self.snaphelper.tape_outplace(inc3_job.job_id, 2, fs_options=True)
            self.snaphelper.outplace_validation(self.snapconstants.tape_outplace_restore_location,
                                                self.snapconstants.windows_restore_client)
            self.snaphelper.update_test_data(mode='copy', path=self.snapconstants.test_data_path)
            #delete files inside directories.
            count = 0
            for path in self.snapconstants.test_data_path:
                for num in range(1, 4):
                    filepath4 = os.path.join(self.snapconstants.test_data_folder[count], 'dir3', 'acls', f'aclfile{num}')
                    self.snaphelper.client_machine.delete_file(filepath4)
                count = count + 1

            #INC4 job
            self.log.info("*" * 20 + "Running INCREMENTAL Snap Backup job" + "*" * 20)
            inc4_job = self.snaphelper.snap_backup()
            #Latest Snap outplace restore with show deleted items. outplace validation
            count = 0
            for path in self.snapconstants.test_data_path:
                self.snapconstants.source_path = [path]
                if self.snapconstants.skip_catalog:
                    self.log.info("*" * 20 + "Running Backup copy from Storage Policy" + "*" * 20)
                    self.snaphelper.backup_copy()
                    self.log.info("*" * 20 + "Running OutPlace Restore from backup copy with\
                            Source Path: {0}".format(path) + "*" * 20)
                    self.snaphelper.tape_outplace(inc4_job.job_id, 2, fs_options=True)
                    self.snaphelper.compare(self.snaphelper.client_machine,
                                            self.snapconstants.windows_restore_client,
                                            self.snapconstants.copy_content_location[count],
                                            self.snapconstants.tape_outplace_restore_location)
                else:
                    self.log.info("*" * 20 + "Running OutPlace Restore from SnapBackup with\
                            Source Path: {0}".format(path) + "*" * 20)
                    self.snaphelper.snap_outplace(1, fs_options=True)
                    self.snaphelper.compare(self.snaphelper.client_machine,
                                            self.snaphelper.client_machine,
                                            self.snapconstants.copy_content_location[count],
                                            self.snapconstants.snap_outplace_restore_location)
                count = count + 1
            self.log.info("*" * 20 + "Restore of deleted data and Validation is\
                          Successful " + "*" * 20)
            #Backup Copy
            self.log.info("*" * 20 + "Running Backup copy from Storage Policy" + "*" * 20)
            self.snaphelper.backup_copy()
            #Latest Tape outplace restore with show deleted items. outplace validation
            self.log.info("*" * 20 + "Running OutPlace Restore from Backup Copy" + "*" * 20)
            self.snapconstants.source_path = self.snapconstants.test_data_path
            self.snaphelper.tape_outplace(inc4_job.job_id, 2, fs_options=True)
            self.snaphelper.outplace_validation(self.snapconstants.tape_outplace_restore_location,
                                                self.snapconstants.windows_restore_client)
            self.log.info("*" * 20 + "Cleanup of Snap Entities" + "*" * 20)
            self.snaphelper.cleanup()
            self.log.info("*" * 20 + "Deletion of Arrays" + "*" * 20)
            self.snaphelper.delete_array()
            if self.snapconstants.vplex_engine is True:
                """ Deleting Vplex arrays"""
                self.snapconstants.arrayname = self.tcinputs['BackendArrayName1']
                self.snaphelper.delete_array()
                self.snapconstants.arrayname = self.tcinputs['BackendArrayName2']
                self.snaphelper.delete_array()
            self.log.info("*" * 20 + "SUCCESSFULLY COMPLETED THE TEST CASE" + "*" * 20)


        except Exception as excp:
            self.log.error('Failed with error: ' + str(excp))
            self.result_string = str(excp)
            self.status = constants.FAILED
