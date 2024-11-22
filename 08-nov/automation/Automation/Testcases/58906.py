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
import ntpath
from AutomationUtils.cvtestcase import CVTestCase
from Server import serverhelper
from Laptop.CloudLaptop import cloudlaptophelper
from Laptop import laptopconstants


class TestCase(CVTestCase):
    """Class for executing this test case"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "[Cloud Laptop]: Validate removal of filter after backup"

    # PRE-REQUISITES OF THE TESTCASE
    # --- When Automation client installed for the first time below steps need to be performed
    #     - disassociate the client from plan [backupset -->rc---> subclient policy-->None]
    #     - Use same storage policy from plan or assigen new storage policy [As testcase not associating any storage policy]
    #     - Use same schedule policy from plan or assign new schedule policy [As testcase not creating schedule policies]
    #     - Change the default interval to minutes [ for ex: 3 min] , otherwise testcase will wait for 8 hours

    def filter_validate(self, src_path, filterfile, operation):
        """ validates the backup with wildcard content and exceptions
        Args:        
            srcpath      (str)   --  Path where data needs to be validated on client        
            filterfile   (str)   --  Filter that needs to be validated  
            operation    (str)   --  Operation which needs to be validated
                                    supported are ADD and REMOVE

        Raises:
            Exception(Exception_Code, Exception_Message):
                if failed to validated the backup with filters/exception

        """
        self.utility.sleep_time(60, "Wait for index play back to finish")
        data_path_leaf = ntpath.basename(str(src_path))
        dest_dir = self.utility.create_directory(self.machine_object)
        self.dest_path = self.machine_object.os_sep.join([dest_dir, data_path_leaf + "_restore"])
        self.utils.subclient_restore_out_of_place(
            self.dest_path,
            [src_path],
            client=self.tcinputs['ClientName'],
            subclient=self.subclient_object,
            wait=True
        )

        restore_file_list = self.machine_object.get_files_and_directory_path(self.dest_path)
        filterlist_count = restore_file_list.count(filterfile)
        if operation in "ADD":
            if filterlist_count > 1:
                raise Exception("Job backedup files which didn't honor the filter")
        elif operation in "REMOVE":
            if not filterlist_count == 5:
                raise Exception("Job didnt backup files which didn't honor the filter")
        self._log.info("Files backup the filter files honorng the filter type")

    def run(self):
        """Main function for test case execution"""
        try:

            self.server_obj = serverhelper.ServerTestCases(self)
            cloud_object = cloudlaptophelper.CloudLaptopHelper(self)
            self.utility = cloud_object.utility
            self.machine_object = self.utility.get_machine_object(self.tcinputs['ClientName'])
            self.utils = cloud_object.utils
            self.subclient_object = self.utils.get_subclient(self.tcinputs['ClientName'])
            self.subclient_content = [r'\%Documents%', r'\%Desktop%']
            self.filter_content = ["*.txt"]
            self.subclient_object.content = self.subclient_content
            self.subclient_object.filter_content = self.filter_content
            self.subclient_object.exception_content = [" "]

            self._log.info("Started executing {0} testcase".format(self.id))
            subclient_id = self.subclient_object.subclient_id
            job_regkey_path = "LaptopCache\\" + str(subclient_id)

        # -------------------------------------------------------------------------------------
        #
        #    SCENARIO-1:
        #       - Add filter as *.txt and backup the files which will backup other than text files
        #       - Remove the filter and backup,  which will backup the text files back.
        # -------------------------------------------------------------------------------------
            documents_path = laptopconstants.DOCUMENTS_PATH
            # -------------------------------------------------------------------------------------
            self.server_obj.log_step("""

            SCENARIO-1:
                - Add new content under data path with txt files, doc files, log files
                - Add filter as *.txt and add text files in content, next backup should not backup those text files
                - Remove the filter and add some text files in content, next backup should backup the text files again.
            """, 100)

            _ = self.utility.is_regkey_set(self.machine_object, job_regkey_path, "RunStatus", 10, 30, True, 0)

            self._log.info("Generating test data for removal filter case under path: %s", str(documents_path))
            self.machine_object.generate_test_data(documents_path, 0, 5, custom_file_name="file.txt")
            self.machine_object.generate_test_data(documents_path, 0, 5, custom_file_name="file.doc")

            cloud_object.wait_for_incremental_backup(self.machine_object)
            self.filter_validate(documents_path, ".txt", "ADD")

            self._log.info("Removing filter *.txt from filter content")
            self.subclient_object.filter_content = [" "]
            self.machine_object.modify_test_data(documents_path, modify=True)

            cloud_object.wait_for_incremental_backup(self.machine_object)
            self.filter_validate(documents_path, ".txt", "REMOVE")
            self.temp_directory_list = [documents_path, self.dest_path]

            self._log.info("***** Validation of removal of filter completed successfully *****")

        except Exception as excp:
            self.server_obj.fail(excp)
            self.log.error("Testcase failed with exception [{0}]".format(str(excp)))

        finally:
            self.utils.cleanup_dir()
