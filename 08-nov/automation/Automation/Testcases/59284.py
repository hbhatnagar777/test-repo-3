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
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.mailer import Mailer
from Server import serverhelper
from Laptop.CloudLaptop import cloudlaptophelper
from Laptop import laptopconstants


class TestCase(CVTestCase):
    """Class for executing this test case"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "[Cloud Laptop]: Email moniker backup"
        self.applicable_os = self.os_list.WINDOWS

    # PRE-REQUISITES OF THE TESTCASE
    # --- When Automation client installed for the first time below steps need to be performed
    #     - disassociate the client from plan [backupset -->rc---> subclient policy-->None]
    #     - Use same storage policy from plan or assigen new storage policy
    #     - Use same schedule policy from plan or assign new schedule policy
    #     - Change the default interval to minutes

    def pstfile_validation(self, validate=True):
        """ Verifies whetehr pst file evaluation is done """

        job_result = r"CV_JobResults\iDataAgent\FileSystemAgent" if self.machine_object.os_info == "WINDOWS" else ""
        collect_file_path = self.machine_object.join_path(
            self.client.job_results_directory,
            job_result,
            "2",
            self.subclient_id,
            "NumColInc1.cvf"
            )

        self.log.info("Get files that are picked for backup from collect file")
        collect_contents = self.machine_object.read_file(collect_file_path)
        collect_contents = collect_contents.splitlines()
        collect_contents = [content.split("|")[0].replace("*??", "") for content in collect_contents]

        self.log.info(collect_contents)

        source_contents = self.machine_object.get_files_in_path(self.test_folder)
        source_contents = [content.replace("\\\\", "\\") for content in source_contents]

        self.log.info(source_contents)
        if validate == True:
            if not collect_contents == None:
                if source_contents in collect_contents:
                    raise Exception("Files again abckedup")
        else:
            return collect_contents, source_contents

    def run(self):
        """Main function for test case execution"""
        try:

            self.server_obj = serverhelper.ServerTestCases(self)
            cloud_object = cloudlaptophelper.CloudLaptopHelper(self)
            utility = cloud_object.utility
            self.machine_object = utility.get_machine_object(self.tcinputs['ClientName'])
            self.utils = cloud_object.utils
            subclient_object = self.utils.get_subclient(self.tcinputs['ClientName'])
            self.test_folder = laptopconstants.PST_FILE_PATH
            emailId = laptopconstants.EMAIL_ID
            subclient_content = [r'\%Documents%', r'\%Desktop%', r'\%Pictures%',
                                 r'\%Music%', r'\%Email Files%']
            filter_content = ["<WKF,AppData>", r"\%Temporary Files (Windows)%", r"C:\Program Files",
                              r"C:\Program Files (x86)", r"C:\Windows", "*.drivedownload"]
            subclient_object.content = subclient_content
            subclient_object.filter_content = filter_content
            subclient_object.exception_content = [" "]

            self._log.info("Started executing {0} testcase".format(self.id))
            self.subclient_id = subclient_object.subclient_id
            job_regkey_path = "LaptopCache\\" + str(self.subclient_id)

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
            _ = utility.is_regkey_set(self.machine_object, job_regkey_path, "RunStatus", 10, 30, True, 0)

            mail = Mailer({'receiver':emailId}, commcell_object=self.commcell)
            mail.mail("test cloud PST Evaluation", "This is a test email")
            cloud_object.wait_for_incremental_backup(self.machine_object)
            cloud_object.source_dir = self.test_folder
            cloud_object.subclient_content_dir = self.test_folder
            collect_contents, source_contents = self.pstfile_validation(validate=False)
            if not set(source_contents).issubset(set(collect_contents)):
                raise Exception("Pst file is not backedup")
            self._log.info("Email moniker backup is validated")

            self.log.info('Send email in such a way that , it goes to the pst file that is opened in outlook file')
            self.log.info('Sending email with subject Test PST evaluation')

            mail = Mailer({'receiver':emailId}, commcell_object=self.commcell)
            mail.mail("test cloud PST Evaluation", "This is a test email")

            self.log.info('Verify whether backup triggered for the pst file modification')
            cloud_object.wait_for_incremental_backup(self.machine_object)
            collect_contents, source_contents = self.pstfile_validation(validate=False)
            if not set(source_contents).issubset(set(collect_contents)):
                raise Exception("Pst file is not backedup")
            self.log.info('Modification in pst file is verified')

            self._log.info("If there is no change content, verify if it is not backing up anything")
            cloud_object.wait_for_incremental_backup(self.machine_object)

            self.pstfile_validation()
            self._log.info("***** Validation of Email moniker backup completed successfully *****")

        except Exception as excp:
            self.server_obj.fail(excp)
            self.log.error("Testcase failed with exception [{0}]".format(str(excp)))
