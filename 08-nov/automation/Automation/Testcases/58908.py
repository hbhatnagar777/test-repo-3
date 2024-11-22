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
        self.name = "[Cloud Laptop]: Wildcard Filter and Exception Verification"
        self.applicable_os = self.os_list.WINDOWS

    # PRE-REQUISITES OF THE TESTCASE
    # --- When Automation client installed for the first time below steps need to be performed
    #     - disassociate the client from plan [backupset -->rc---> subclient policy-->None]
    #     - Use same storage policy from plan or assigen new storage policy [As testcase not associating any storage policy]
    #     - Use same schedule policy from plan or assign new schedule policy [As testcase not creating schedule policies]
    #     - Change the default interval to minutes [ for ex: 3 min] , otherwise testcase will wait for 8 hours

    def wilcard_filter_validate(self, operation="FILTER"):
        """ validates the backup with wildcard filter and exceptions
        Args:
            operation    (str)   --  operation which needs to be validated
                                    supported are FILTER and EXCEPTION

        Raises:
            Exception(Exception_Code, Exception_Message):
                if failed to validated the backup with filters/exception

        """
        self.utility.sleep_time(300, "Wait for index play back to finish")
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

        restore_folder_path=self.dest_path + str(self.slash_format) + data_path_leaf
        restore_file_list = self.machine_object.get_folder_or_file_names(restore_folder_path)
        if not self.tcinputs['os_type']=='Mac':
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
        if operation == 'FILTER':
            if not (docfilecount == 2 and txtfilecount == 3 and docxfilecount == 0 and xmlfilecount == 0):
                raise Exception("Wildcard filter content is not honored  and backedup correctly")
        elif operation == "EXCEPTION":
            if not (docfilecount == 3 and txtfilecount == 2 and docxfilecount == 5 and xmlfilecount == 5):
                raise Exception("Wildcard exception content is not honored  and backedup correctly")

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
                self.data_folder = self.test_folder + str(self.slash_format) + "TC_58908"
                command = "chown -R root:admin "+self.data_folder
                self.machine_object.execute_command(command)

            else:
                self.slash_format='\\'
                self.test_folder = laptopconstants.TEST_DATA_PATH
                job_regkey_path = "LaptopCache\\" + str(subclient_id)
                self.data_folder = self.test_folder + str(self.slash_format) + "TC_58908"
                
            self.utility.create_directory(self.machine_object, self.data_folder)
            self.filter_content = [self.data_folder + str(self.slash_format) + '[a-c]file1.doc', 
                                    self.data_folder + str(self.slash_format) + 'file?1.xml', 
                                    self.data_folder + str(self.slash_format) + 'file[!1-3]1.txt', 
                                    self.data_folder + str(self.slash_format) + '*.docx']
            self.subclient_object.content = [self.data_folder]
            self.subclient_object.filter_content = self.filter_content
            self.subclient_object.exception_content = ['*.M4U']

            self._log.info("Started executing {0} testcase".format(self.id))

        # -------------------------------------------------------------------------------------
        #
        #    SCENARIO-1:
        #       - Validate wildcard filter in the content
        #    SCENARIO-2:
        #       - Validate wildcard Exception in the content
        # -------------------------------------------------------------------------------------
            self.server_obj.log_step("""

            SCENARIO-1:
                - Add content as C:\selftestdata and filters with wildcard content
                - Backup should honor the wild card filters and backup expected files.
                - Validate whether job backedup expected files or not
              
            """, 100)

            _ = self.utility.is_regkey_set(self.machine_object, job_regkey_path, "RunStatus", 10, 30, True, 0)
            self._log.info("Generation test data for wild card filter case under: %s", str(self.data_folder))
            for i in range(0,5):
                text_file_path = self.data_folder + str(self.slash_format) + 'file'+str(i)+str(1)+".txt"
                doc_file_path = self.data_folder + str(self.slash_format) + chr(97 + i)+ 'file'+str(1)+".doc"
                docx_file_path = self.data_folder + str(self.slash_format) + str(i)+'file'+str(1)+".docx"
                xml_file_path = self.data_folder + str(self.slash_format) + 'file'+chr(97 + i)+ str(1)+".xml"
  
                self.machine_object.create_file(text_file_path, "Validation of wildcard content with text file")
                self.machine_object.create_file(doc_file_path, "Validation of wildcard content with with doc file")
                self.machine_object.create_file(docx_file_path, "Validation of wildcard content with with docx file")
                self.machine_object.create_file(xml_file_path, "Validation of wildcard content with xml file")
 
            cloud_object.wait_for_incremental_backup(self.machine_object, os_type=self.tcinputs['os_type'])
            self.wilcard_filter_validate(operation="FILTER")
            self._log.info("***** Validation of wild card filter content completed successfully *****")

            # -------------------------------------------------------------------------------------
            self.server_obj.log_step("""

            SCENARIO-2:
                - Add content as C:\selftestdata and filter as C:\selftestdata\files_with_custom_names
                    and exception with wildcard content
                - Backup should honor the wild card exception and backup expected files.
                - Validate whether job backedup expected files or not
            """, 100)

            # -------------------------------------------------------------------------------------
            _ = self.utility.is_regkey_set(self.machine_object, job_regkey_path, "RunStatus", 10, 30, True, 0)

            self._log.info("Add wild card content as exception")
            self.filter_content = [self.data_folder]
            self.subclient_object.filter_content = self.filter_content
            
            self.exception_content = [self.data_folder + str(self.slash_format) + '[a-c]file1.doc', 
                                      self.data_folder + str(self.slash_format) + 'file?1.xml', 
                                      self.data_folder + str(self.slash_format) + 'file[!1-3]1.txt', 
                                      self.data_folder + str(self.slash_format)+ '*.docx']
            self.subclient_object.exception_content = self.exception_content
            self._log.info("Generating test data for wild card exception case under: %s", str(self.data_folder))
            self.machine_object.modify_test_data(self.data_folder, modify=True)
            cloud_object.wait_for_incremental_backup(self.machine_object, os_type=self.tcinputs['os_type'])
            self.wilcard_filter_validate(operation="EXCEPTION")
            self.temp_directory_list = [self.data_folder, self.dest_path]

            self._log.info("***** Validation of wild card exception content completed successfully *****")

        except Exception as excp:
            self.server_obj.fail(excp)
            self.log.error("Testcase failed with exception [{0}]".format(str(excp)))

        finally:
            self.utils.cleanup_dir()
