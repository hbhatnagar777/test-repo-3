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
        self.name = "[Cloud Laptop]: Validate Addition of content after backup"
        self.applicable_os = self.os_list.WINDOWS
        self.slash_format = None

    # PRE-REQUISITES OF THE TESTCASE
    # --- When Automation client installed for the first time below steps need to be performed
    #     - disassociate the client from plan [backupset -->rc---> subclient policy-->None]
    #     - Use same storage policy from plan or assigen new storage policy [As testcase not associating any storage policy]
    #     - Use same schedule policy from plan or assign new schedule policy [As testcase not creating schedule policies]
    #     - Change the default interval to minutes [ for ex: 3 min] , otherwise testcase will wait for 8 hours

    def run(self):
        """Main function for test case execution"""
        try:
            self.tcinputs.update(LaptopHelper.set_inputs(self, 'Commcell'))
            # -------------------------------------------------------------------------------------
            #    SCENARIO-1:
            #       - Documents moniker validation with new data
            #    SCENARIO-2:
            #       - Add absolute path as content and validate the new data
            #    SCENARIO-3:
            #       - Validate default Library filter
            # -------------------------------------------------------------------------------------

            server_obj = serverhelper.ServerTestCases(self)
            cloud_object = cloudlaptophelper.CloudLaptopHelper(self)
            utility = cloud_object.utility
            machine_object = utility.get_machine_object(self.tcinputs['ClientName'])
            utils = cloud_object.utils
            laptop_utils = LaptopUtils(self)
            subclient_object = utils.get_subclient(self.tcinputs['ClientName'])
            subclient_id = subclient_object.subclient_id
            test_path = utility.create_directory(machine_object)

            if self.tcinputs['os_type']=='Mac':
                self.slash_format='/'
                subclient_content = ['/%Documents%', '/%Desktop%', '/%Pictures%', '/%Music%', '/%MigrationAssistant%']
                filter_content = ["<WKF,Library>", "/%Temporary Files (Mac)%"]
                documents_path = laptopconstants.MAC_DOCUMENTS_PATH
                abs_path = test_path + "/" + "abscontent"
                library_path = laptopconstants.MAC_LIBRARY_PATH  
                libraryfile_path = library_path + "/" + "file3.txt"
                utility.create_directory(machine_object, library_path)
                utility.create_directory(machine_object, documents_path)
                command = "chown -R root:admin "+documents_path
                machine_object.execute_command(command)
                command = "chown -R root:admin "+library_path
                machine_object.execute_command(command)
                command = "chown -R root:admin "+abs_path
                machine_object.execute_command(command)


            
            else:
                self.slash_format='\\'
                subclient_content = [r'\%Documents%', r'\%Desktop%', r'\%Pictures%',
                                     r'\%Music%', r'\%Office%', r'\%MigrationAssistant%']
                filter_content = ["<WKF,AppData>", r"\%Temporary Files (Windows)%", r"C:\Program Files",
                                  r"C:\Program Files (x86)", r"C:\Windows", "*.drivedownload"]

                documents_path = laptopconstants.DOCUMENTS_PATH
                abs_path = test_path + "\\" + "abscontent"
                library_path = laptopconstants.LIBRARY_PATH
                libraryfile_path = library_path + "//" + "file3.txt"
                utility.create_directory(machine_object, abs_path)
                utility.create_directory(machine_object, library_path)


            subclient_object.content = subclient_content
            subclient_object.filter_content = filter_content
            subclient_object.exception_content = ['*.M4U']

            self.temp_directory_list = [documents_path, library_path, abs_path]

            # -------------------------------------------------------------------------------------
            server_obj.log_step("""
                SCENARIO-1:
                    - Add new content under Documents path
                    - Verify backup triggered after newcontent added and backup completed successfully
                    - Restore the data verify new content backed up or not
 
                """, 100)
 
            job_regkey_path = "LaptopCache" + str(self.slash_format)+(subclient_id)
            _ = utility.is_regkey_set(machine_object, job_regkey_path, "RunStatus", 10, 30, True, 0)
 
            self._log.info("Adding data under Documents path: %s", str(documents_path))
            laptop_utils.create_file(machine_object, documents_path, files=5)
            cloud_object.wait_for_incremental_backup(machine_object, os_type=self.tcinputs['os_type'])
            cloud_object.source_dir = documents_path
            cloud_object.subclient_content_dir = documents_path
            cloud_object.out_of_place_restore(machine_object, subclient_object, cleanup=False)
            self._log.info("***** Validation of backup with new content completed successfully *****")

            # -------------------------------------------------------------------------------------
            server_obj.log_step("""
                SCENARIO-2:
                    - Add absolute path in content
                    - Verify backup triggered after files modified and backup completed successfully
                    - Restore the data verify modified data backed up or not

                """, 100)
            job_regkey_path = "LaptopCache" + str(self.slash_format)+(subclient_id)
            _ = utility.is_regkey_set(machine_object, job_regkey_path, "RunStatus", 10, 30, True, 0)
            self._log.info("Adding data under absolute path: %s", str(abs_path))
            laptop_utils.create_file(machine_object, abs_path, files=5)
            subclient_content.append(abs_path)
            subclient_object.content = subclient_content
            cloud_object.wait_for_incremental_backup(machine_object, os_type=self.tcinputs['os_type'])
            cloud_object.source_dir = abs_path
            cloud_object.subclient_content_dir = abs_path
            cloud_object.out_of_place_restore(machine_object, subclient_object, cleanup=False)
            self._log.info("***** Validation of backup with absolute path in content completed successfully *****")

            # -------------------------------------------------------------------------------------
            server_obj.log_step("""
            SCENARIO-3:
                - Add text file under Library filter path
                - Verify backup triggered after files added and backup completed successfully
                - Restore the data verify added data is not backed up

            """, 100)

            job_regkey_path = "LaptopCache" + str(self.slash_format)+(subclient_id)
            _ = utility.is_regkey_set(machine_object, job_regkey_path, "RunStatus", 10, 30, True, 0)
            self._log.info('Verify whether job is not triggered for text file in Library path')

            machine_object.create_file(libraryfile_path, "test")
            cloud_object.wait_for_incremental_backup(machine_object, os_type=self.tcinputs['os_type'])
            cloud_object.source_dir = library_path
            cloud_object.subclient_content_dir = library_path
            data_path_leaf = ntpath.basename(str(cloud_object.source_dir))
            dest_dir = utility.create_directory(machine_object)
            dest_path = machine_object.os_sep.join([dest_dir, data_path_leaf + "_restore"])
            restorejob_object = utils.subclient_restore_out_of_place(
                dest_path,
                [cloud_object.subclient_content_dir],
                client=self.tcinputs['ClientName'],
                subclient=subclient_object,
                wait=False
            )
            utility.sleep_time(60, "sleep until restore goes to pending")
            self._log.info(restorejob_object.delay_reason)
            if not "nothing to restore" in restorejob_object.delay_reason:
                raise Exception("file under Library path has been backedup")
            self._log.info("***** Validation of backup with Library filter successfully *****")

        except Exception as excp:
            server_obj.fail(excp)
            self.log.error("Testcase failed with exception [{0}]".format(str(excp)))
        finally:
            utils.cleanup_dir()
