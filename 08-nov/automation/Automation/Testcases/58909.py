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
    __init__()            --  initialize TestCase class


    setup()               --  setup function of this test case

    run()                 --  run function of this test case

"""
import ntpath, re
from AutomationUtils.cvtestcase import CVTestCase
from Server import serverhelper
from Laptop.CloudLaptop import cloudlaptophelper
from Laptop import laptopconstants
from Laptop.laptophelper import LaptopHelper


class TestCase(CVTestCase):
    """Class for executing this test case"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "[Cloud Laptop]: Validate addition of exception after backup"
        self.applicable_os = self.os_list.WINDOWS
        self.slash_format=None

    # PRE-REQUISITES OF THE TESTCASE
    # --- When Automation client installed for the first time below steps need to be performed
    #     - disassociate the client from plan [backupset -->rc---> subclient policy-->None]
    #     - Use same storage policy from plan or assigen new storage policy
    #     - Use same schedule policy from plan or assign new schedule policy
    #     - Change the default interval to minutes

    def exception_validate(self, operation="ADD"):
        """ validates the backup with wildcard filter and exceptions
        Args:
            operation    (str)   --  operation which needs to be validated
                                    supported are ADD and REMOVE

        Raises:
            Exception(Exception_Code, Exception_Message):
                if failed to validated the backup with filters/exception

        """
        self.utility.sleep_time(300, "Wait for index play back to finish")
        data_path_leaf = ntpath.basename(str(self.data_folder))
        dest_dir = self.utility.create_directory(self.machine_object)
        docfilecount = 0
        txtfilecount = 0
        self.dest_path = self.machine_object.os_sep.join([dest_dir, data_path_leaf + "_restore"])
        self.utils.subclient_restore_out_of_place(
            self.dest_path,
            [self.data_folder],
            client=self.tcinputs['ClientName'],
            subclient=self.subclient_object,
            wait=True
        )
        temp_path = self.dest_path + str(self.slash_format) + data_path_leaf
        restore_file_list = self.machine_object.get_folder_or_file_names(temp_path)
        if not self.tcinputs['os_type']=='Mac':
            restore_file_list = ' '.join(restore_file_list.splitlines()).split()[2:]
        for file in restore_file_list:
            wildcard = "doc$"
            found = re.findall(wildcard, file)
            if not len(found) == 0:
                docfilecount = docfilecount + 1
            wildcard = ".*txt"
            found = re.findall(wildcard, file)
            if not len(found) == 0:
                txtfilecount = txtfilecount + 1

        self._log.info(str(docfilecount) + " " + str(txtfilecount))
        if operation == 'ADD':
            if not (docfilecount == 5 and txtfilecount == 5):
                raise Exception("Exception content is not honored  and backedup correctly")
        elif operation == "REMOVE":
            if not (docfilecount == 0 and txtfilecount == 0):
                raise Exception("Exception content is not honored  and backedup correctly")

    def run(self):
        """Main function for test case execution"""
        try:

            self.tcinputs.update(LaptopHelper.set_inputs(self, 'Commcell'))
            self.server_obj = serverhelper.ServerTestCases(self)
            cloud_object = cloudlaptophelper.CloudLaptopHelper(self)
            self.utility = cloud_object.utility
            self.machine_object = self.utility.get_machine_object(self.tcinputs['ClientName'])
            self.utils = cloud_object.utils
            self.subclient_object = self.utils.get_subclient(self.tcinputs['ClientName'])
            subclient_id = self.subclient_object.subclient_id
            if self.tcinputs['os_type']=='Mac':
                self.slash_format='/'
                job_regkey_path = "LaptopCache/" + str(subclient_id)
                self.test_folder = laptopconstants.MAC_TEST_DATA_PATH
                self.data_folder = self.test_folder + "/test"
                command = "chown -R root:admin "+self.data_folder
                self.machine_object.execute_command(command)

            else:
                self.slash_format='\\'
                job_regkey_path = "LaptopCache\\" + str(subclient_id)
                self.test_folder = laptopconstants.TEST_DATA_PATH
                self.data_folder = self.test_folder + "\\test"

            self.utility.create_directory(self.machine_object, self.data_folder)
            self.filter_content = [self.data_folder]
            self.subclient_object.content = [self.test_folder]
            self.subclient_object.filter_content = self.filter_content
            self.subclient_object.exception_content = ['*M4U']
            self._log.info("Started executing {0} testcase".format(self.id))
            
            _ = self.utility.is_regkey_set(self.machine_object, job_regkey_path, "RunStatus", 10, 30, True, 0)

            self._log.info("Generation test data for wild card filter case under: %s", str(self.test_folder))
            for i in range(0,5):
                text_file_path = self.data_folder + str(self.slash_format) + 'file'+str(i)+".txt"
                doc_file_path = self.data_folder + str(self.slash_format) + 'file'+str(i)+".doc"
                self.machine_object.create_file(text_file_path, "Validation of filter of the backup with text file")
                self.machine_object.create_file(doc_file_path, "Validation of filter of the backup with doc file")

            cloud_object.wait_for_incremental_backup(self.machine_object, os_type=self.tcinputs['os_type'])

            data_path_leaf = ntpath.basename(str(self.data_folder))
            dest_dir = self.utility.create_directory(self.machine_object)
            dest_path = self.machine_object.os_sep.join([dest_dir, data_path_leaf + "_restore"])
            self.temp_directory_list = [self.test_folder, dest_path]
            self.utility.sleep_time(300, "sleep Before restore for cloud laptop")
            restorejob_object = self.utils.subclient_restore_out_of_place(
                dest_path,
                [self.data_folder],
                client=self.tcinputs['ClientName'],
                subclient=self.subclient_object,
                wait=False
            )
            self.utility.sleep_time(60, "sleep till restore job goes to pending")
            self._log.info(restorejob_object.delay_reason)
            if not "nothing to restore" in restorejob_object.delay_reason:
                raise Exception("files has been backedup without honoring filter")

            self._log.info("******Add Exception as *.txt , *.doc and validate backup******")
            self.subclient_object.exception_content = ["*.txt", "*.doc"]

            cloud_object.wait_for_incremental_backup(self.machine_object, os_type=self.tcinputs['os_type'])
            self.exception_validate(operation="ADD")
            self._log.info("***** Validation of addition of exception content completed successfully *****")

        except Exception as excp:
            self.server_obj.fail(excp)
            self.log.error("Testcase failed with exception [{0}]".format(str(excp)))

        finally:
            self.utils.cleanup_dir()
