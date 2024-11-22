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
from Laptop.laptoputils import LaptopUtils
from Laptop import laptopconstants
from Laptop.laptophelper import LaptopHelper

class TestCase(CVTestCase):
    """Class for executing this test case"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "[Cloud Laptop]: DropBox moniker backup"
        self.applicable_os = self.os_list.WINDOWS

    # PRE-REQUISITES OF THE TESTCASE
    # --- When Automation client installed for the first time below steps need to be performed
    #     - disassociate the client from plan [backupset -->rc---> subclient policy-->None]
    #     - Use same storage policy from plan or assigen new storage policy
    #     - Use same schedule policy from plan or assign new schedule policy
    #     - Change the default interval to minutes

    def run(self):
        """Main function for test case execution"""
        try:

            self.tcinputs.update(LaptopHelper.set_inputs(self, 'Commcell'))
            self.server_obj = serverhelper.ServerTestCases(self)
            cloud_object = cloudlaptophelper.CloudLaptopHelper(self)
            utility = cloud_object.utility
            machine_object = utility.get_machine_object(self.tcinputs['ClientName'])
            self.utils = cloud_object.utils
            laptop_utils = LaptopUtils(self)
            subclient_object = self.utils.get_subclient(self.tcinputs['ClientName'])
            subclient_id = subclient_object.subclient_id

            
            if self.tcinputs['os_type']=='Mac':
                self.slash_format='/'
                subclient_content = ['/%Documents%', '/%Desktop%', '/%Pictures%', '/%Dropbox%']
                filter_content = ["/Library", "<WKF,Library>", "/%Temporary Files (Mac)%"]
                test_folder = laptopconstants.MAC_DROPBOX_PATH
                data_folder = test_folder + self.slash_format + "Inc1"    
                command = "chown -R root:admin "+test_folder
                machine_object.execute_command(command)

            else:
                self.slash_format='\\'
                test_folder = laptopconstants.DROPBOX_PATH
                data_folder = test_folder + self.slash_format + "Inc1"    
                subclient_content = [r'\%Documents%', r'\%Desktop%', r'\%Pictures%', r'\%DropBox%']
                filter_content = ["<WKF,AppData>", r"\%Temporary Files (Windows)%", r"C:\Program Files",
                              r"C:\Program Files (x86)", r"C:\Windows", "*.drivedownload"]
            subclient_object.content = subclient_content
            subclient_object.filter_content = filter_content
            subclient_object.exception_content = ['*.M4U']

            self._log.info("Started executing {0} testcase".format(self.id))
            job_regkey_path = "LaptopCache" + str(self.slash_format)+(subclient_id)

            # -------------------------------------------------------------------------------------
            #
            #    SCENARIO-1:
            #       - Add wild card content and validate if it backedup as expected
            # -------------------------------------------------------------------------------------
            self.server_obj.log_step("""

            SCENARIO-1:
                - Add new content under dropBox path with txt files, doc files, xml files, docx files
                - Files needs to be backedup as respectively with OneDrive moniker content
 
            """, 100)

            # -------------------------------------------------------------------------------------
            _ = utility.is_regkey_set(machine_object, job_regkey_path, "RunStatus", 10, 30, True, 0)

            self._log.info("Generating test data for DropBox under path: %s", str(test_folder))
            utility.create_directory(machine_object, data_folder)
            laptop_utils.create_file(machine_object, data_folder, files=5)

            cloud_object.wait_for_incremental_backup(machine_object, os_type=self.tcinputs['os_type'])
            cloud_object.source_dir = data_folder
            cloud_object.subclient_content_dir = data_folder
            cloud_object.out_of_place_restore(machine_object, subclient_object)
            self._log.info("New content under DropBox moniker verification completed")
            self._log.info("If there is no change ontent, verify if it is not backing up anything")
            cloud_object.wait_for_incremental_backup(machine_object, os_type=self.tcinputs['os_type'])
            data_path_leaf = ntpath.basename(str(cloud_object.source_dir))
            dest_dir = utility.create_directory(machine_object)
            dest_path = machine_object.os_sep.join([dest_dir, data_path_leaf + "_restore"])
            utility.sleep_time(300, "sleep Before restore for cloud laptop")
            restorejob_object = self.utils.subclient_restore_out_of_place(
                dest_path,
                [data_folder],
                client=self.tcinputs['ClientName'],
                subclient=subclient_object,
                wait=False
            )
            utility.sleep_time(60, "sleep until restore goes to pending")
            self._log.info(restorejob_object.delay_reason)
            if not "nothing to restore" in restorejob_object.delay_reason:
                raise Exception("Backup started without any changes in files")
            self._log.info("***** Validation of Dropbox moniker backup completed successfully *****")

        except Exception as excp:
            self.server_obj.fail(excp)
            self.log.error("Testcase failed with exception [{0}]".format(str(excp)))

        finally:
            self.utils.cleanup_dir()
