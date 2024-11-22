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
from Laptop.laptophelper import LaptopHelper


class TestCase(CVTestCase):
    """Class for executing this test case"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "[Cloud Laptop]: Validate addition of filter after backup  "
        self.applicable_os = self.os_list.WINDOWS
        self.slash_format = None

    # PRE-REQUISITES OF THE TESTCASE
    # --- When Automation client installed for the first time below steps need to be performed
    #     - disassociate the client from plan [backupset -->rc---> subclient policy-->None]
    #     - Use same storage policy from plan or assigen new storage policy [As testcase not associating any storage policy]
    #     - Use same schedule policy from plan or assign new schedule policy [As testcase not creating schedule policies]
    #     - Change the default interval to minutes [ for ex: 3 min] , otherwise testcase will wait for 8 hours

    def filter_validate(self, src_path, filterfile):
        """ validates the backup with wildcard content and exceptions
        Args:
            srcpath      (str)   --  Path where data needs to be validated on client
            filterfile   (str)   --  Filter that needs to be validated
        Raises:
            Exception(Exception_Code, Exception_Message):
                if failed to validated the backup with filters/exception
        """
        data_path_leaf = ntpath.basename(str(src_path))
        dest_dir = self.utility.create_directory(self.machine_object)
        dest_path = self.machine_object.os_sep.join([dest_dir, data_path_leaf + "_restore"])
        self.utils.subclient_restore_out_of_place(
            dest_path,
            [src_path],
            client=self.tcinputs['ClientName'],
            subclient=self.subclient_object,
            wait=True
        )

        #restore_file_list = self.machine_object.get_files_and_directory_path(dest_path)
        temp_path = dest_path + str(self.slash_format) + data_path_leaf
        restore_file_list = self.machine_object.get_folder_or_file_names(temp_path)

        self._log.info(restore_file_list)


        filterlist_count = restore_file_list.count(filterfile)
        if filterlist_count > 1:
            raise Exception("Job backedup files which didn't honor the filter")
        self._log.info("Files didnt backup the filter files")

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
                self.subclient_content = ['/%Documents%', '/%Desktop%']
                documents_path = laptopconstants.MAC_DOCUMENTS_PATH
                self.utility.create_directory(self.machine_object, documents_path)
                command = "chown -R root:admin "+documents_path
                self.machine_object.execute_command(command)


            else:
                self.slash_format='\\'
                job_regkey_path = "LaptopCache\\" + str(subclient_id)
                self.subclient_content = [r'\%Documents%', r'\%Desktop%']
                documents_path = laptopconstants.DOCUMENTS_PATH

            self.filter_content = ["*.txt"]

            self.subclient_object.content = self.subclient_content
            self.subclient_object.filter_content = ['*.M4U']
            self.subclient_object.exception_content = ['*.M4U']
            self._log.info("Started executing {0} testcase".format(self.id))

        # -------------------------------------------------------------------------------------
        #
        #    SCENARIO-1:
        #       - Addition of filter after backup validation

        # -------------------------------------------------------------------------------------
            self.temp_directory_list = [documents_path]
            self.server_obj.log_step("""

            SCENARIO-1:
                - Add new content under data path with txt files, doc files, log files
                - Add filter as *.txt and add text files in content, next backup should not backup those text files

            """, 100)

            # ------ read the registry to check the run status of previous run ---- #
            _ = self.utility.is_regkey_set(self.machine_object, job_regkey_path, "RunStatus", 10, 30, True, 0)

            self._log.info("Generating testdata for filter addition case under: %s", str(documents_path))
            

            for i in range(0,5):
                text_file_path = documents_path + str(self.slash_format) + 'file'+str(i)+".txt"
                doc_file_path = documents_path + str(self.slash_format) + 'file'+str(i)+".doc"
                self.machine_object.create_file(text_file_path, "Validation of addition of filter after backup of the text file")
                self.machine_object.create_file(doc_file_path, "Validation of addition of filter after backup of doc file")

            cloud_object.wait_for_incremental_backup(self.machine_object, os_type=self.tcinputs['os_type'])
            cloud_object.source_dir = documents_path
            cloud_object.subclient_content_dir = documents_path
            cloud_object.out_of_place_restore(self.machine_object, self.subclient_object, cleanup=False)
            self._log.info("----Adding *.txt as filter to content and validate the backup-----")
            self.subclient_object.filter_content = self.filter_content
            self.machine_object.modify_test_data(documents_path, modify=True)

            cloud_object.wait_for_incremental_backup(self.machine_object, os_type=self.tcinputs['os_type'])
            self.utility.sleep_time(300, "sleep Before restore for cloud laptop")

            self.filter_validate(documents_path, ".txt")
            self.temp_directory_list = [documents_path]

            self._log.info("***** Validation of filter with new filter added completed successfully *****")

        except Exception as excp:
            self.server_obj.fail(excp)
            self.log.error("Testcase failed with exception [{0}]".format(str(excp)))

        finally:
            self.utils.cleanup_dir()
