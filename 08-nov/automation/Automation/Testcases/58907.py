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


class TestCase(CVTestCase):
    """Class for executing this test case"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "[Cloud Laptop]: Wildcard content Verification"
        self.applicable_os = self.os_list.WINDOWS

    # PRE-REQUISITES OF THE TESTCASE
    # --- When Automation client installed for the first time below steps need to be performed
    #     - disassociate the client from plan [backupset -->rc---> subclient policy-->None]
    #     - Use same storage policy from plan or assigen new storage policy [As testcase not associating 
    #        any storage policy]
    #     - Use same schedule policy from plan or assign new schedule policy [As testcase not creating 
    #    schedule policies]
    #     - Change the default interval to minutes [ for ex: 3 min] , otherwise testcase will wait for 8 hours

    def wilcard_content_validate(self):
        """ validates the backup with wildcard content and exceptions
        Raises:
            Exception(Exception_Code, Exception_Message):
                if failed to validated the backup with filters/exception
        """

        self.utility.sleep_time(60, "Wait for index play back to finish")
        data_path_leaf = ntpath.basename(str(self.data_folder))
        dest_dir = self.utility.create_directory(self.machine_object)
        docfilecount = 0
        txtfilecount = 0
        xmlfilecount = 0
        docxfilecount = 0
        self.dest_path = self.machine_object.os_sep.join([dest_dir, data_path_leaf + "_restore"])
        self.utils.subclient_restore_out_of_place(
            self.dest_path,
            [self.data_folder],
            client=self.tcinputs['ClientName'],
            subclient=self.subclient_object,
            wait=True
        )
        restore_file_list = self.machine_object.get_folder_or_file_names(folder_path=(self.dest_path + "\\" + data_path_leaf), filesonly=True)
        restore_file_list = ' '.join(restore_file_list.splitlines()).split()[2:]
        for file in restore_file_list:
            wildcard = "doc$"
            found = re.findall(wildcard, file)
            if not len(found) == 0:
                docfilecount = docfilecount + 1
            wildcard = ".*xml"
            found = re.findall(wildcard, file)
            if not len(found) == 0:
                xmlfilecount = xmlfilecount + 1
            wildcard = ".*txt"
            found = re.findall(wildcard, file)
            if not len(found) == 0:
                txtfilecount = txtfilecount + 1
            wildcard = ".*docx"
            found = re.findall(wildcard, file)
            if not len(found) == 0:
                docxfilecount = docxfilecount + 1

        self._log.info(str(docfilecount) + " " + str(txtfilecount) + " " + str(docxfilecount) + " " + str(xmlfilecount))
        if not (docfilecount == 3 and txtfilecount == 2 and docxfilecount == 5 and xmlfilecount == 5):
            raise Exception("Wildcard content is not honored  and not backedup correctly")

    def run(self):
        """Main function for test case execution"""
        try:

            self.server_obj = serverhelper.ServerTestCases(self)
            cloud_object = cloudlaptophelper.CloudLaptopHelper(self)
            self.utility = cloud_object.utility
            self.machine_object = self.utility.get_machine_object(self.tcinputs['ClientName'])
            self.utils = cloud_object.utils
            self.subclient_object = self.utils.get_subclient(self.tcinputs['ClientName'])
            self.test_folder = laptopconstants.TEST_DATA_PATH
            self.data_folder = self.test_folder + "\\files_with_custom_name"
            self.subclient_content = [self.data_folder + '\\[a-c]file1.doc', self.data_folder + '\\file?1.xml', self.data_folder + '\\file[!1-3]1.txt', self.data_folder + '\\*.docx']
            self.subclient_object.content = self.subclient_content
            self.subclient_object.filter_content = [" "]
            self.subclient_object.exception_content = [" "]

            self._log.info("Started executing {0} testcase".format(self.id))
            subclient_id = self.subclient_object.subclient_id
            job_regkey_path = "LaptopCache\\" + str(subclient_id)

            # -------------------------------------------------------------------------------------
            #
            #    SCENARIO-1:
            #       - Add wild card content and validate if it backedup as expected
            # -------------------------------------------------------------------------------------
            self.server_obj.log_step("""

            SCENARIO-1:
                - Add new content under data path with txt files, doc files, xml files, docx files
                - Files needs to be backedup as respectively with wild card content
 
            """, 100)

            # -------------------------------------------------------------------------------------
            _ = self.utility.is_regkey_set(self.machine_object, job_regkey_path, "RunStatus", 10, 30, True, 0)

            self._log.info("Generating test data for wild content under path: %s", str(self.test_folder))
            i = 0
            for i in range(5):
                self.machine_object.generate_test_data(self.test_folder, 0, 1, custom_file_name=chr(97 + i) + "file.doc")
                self.machine_object.generate_test_data(self.test_folder, 0, 1, custom_file_name=str(i) + "file.docx")
                self.machine_object.generate_test_data(self.test_folder, 0, 1, custom_file_name="file" + str(i) + ".txt")
                self.machine_object.generate_test_data(self.test_folder, 0, 1, custom_file_name="file" + chr(97 + i) + ".xml")

            cloud_object.wait_for_incremental_backup(self.machine_object)
            self.wilcard_content_validate()
            self.temp_directory_list = [self.test_folder, self.dest_path]

            self._log.info("***** Validation of wild card content completed successfully *****")

        except Exception as excp:
            self.server_obj.fail(excp)
            self.log.error("Testcase failed with exception [{0}]".format(str(excp)))

        finally:
            self.utils.cleanup_dir()
