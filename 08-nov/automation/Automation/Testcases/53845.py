# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

Test cases to Validate restore functionality of a CloudLaptop.

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()                  --  initialize TestCase class

    run()                       --  run function of this test case

"""

import ntpath
from Server import serverhelper
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.options_selector import OptionsSelector
from AutomationUtils.idautils import CommonUtils
from AutomationUtils import machine
from Laptop.CloudLaptop import cloudlaptophelper


class TestCase(CVTestCase):
    """Class for executing this test case"""
    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Validate restore functionality of a CloudLaptop"
        self.show_to_user = True
        self.machin = None
        self._utility = None
        self.serverbase = None
        self.server_obj = None
        self.tcinputs = {
            "TESTPATH": None
        }

    def run(self):
        """Main function for test case execution"""
        try:
            self._log.info("Started executing {0} testcase".format(self.id))
            subclient_obj = self.subclient
            self.serverbase = CommonUtils(self.commcell)
            self._utility = OptionsSelector(self._commcell)
            self.server_obj = serverhelper.ServerTestCases(self)
            self.machin = machine.Machine(self.client, self.commcell)
            cloud_object = cloudlaptophelper.CloudLaptopHelper(self)
            compare_source = self.tcinputs['TESTPATH']
            new_folder_name = compare_source+"_rename"
            tmp_path = None

            # -------------------------------------------------------------------------------------
            self.server_obj.log_step("""
                1. Out-of-place restore
                    1.a Run Out-of-place restore job to restore files and folders
                           by restoring to the same client but different path by selecting
                           default options of restore
                    1.b verify / Validate that files gets restored correctly.

                2. In-place restore
                    2.a rename the data path "__rename"
                    2.b Restore files and folders by restoring to the same client
                            to same folder by selecting default options of restore
                    2.c verify / Validate that files gets restored correctly by comparing
                            with renamed file "__rename"
            """, 200)

            # -------------------------------------------------------------------------------------
            # -------------------------------------------------------------------------------------
            self.server_obj.log_step("""
                1. Out-of-place restore of subclient:
                    1.a Run Out-of-place restore job to restore files and folders
                            by restoring to the same client but different path by selecting
                            default options of restore
                    1.b verify / Validate that files gets restored correctly.
            """, 200)
            # -------------------------------------------------------------------------------------

            if tmp_path is None:
                tmp_path = self._utility.create_directory(self.machin)

            data_path_leaf = ntpath.basename(str(compare_source))

            dest_path = self.machin.os_sep.join([tmp_path, data_path_leaf + "_restore"])
            # out-of-Place restore
            if len(subclient_obj.content) is 0:
                _paths = [each['subclientPolicyPath'] for each in subclient_obj._content]
            else:
                _paths = subclient_obj.content
            self._utility.sleep_time(120, "Wait for index play back to finish'")
            self.serverbase.subclient_restore_out_of_place(
                dest_path, _paths, client=self.client.client_name, subclient=subclient_obj, wait=True
            )
            self._log.info("subclient Out-Of-Place Restore Job completed successfully")
            compare_destination = self.machin.os_sep.join([dest_path, data_path_leaf])
            # validation of restore data
            cloud_object.validate_restore(self.machin, compare_source, compare_destination)

            # -------------------------------------------------------------------------------------
            self.server_obj.log_step("""
                2. In-place restore of subclient

                    2.a rename the data path
                    2.b Restore files and folders by restoring to the same client
                            to same folder by selecting default options of restore
                    2.c verify / Validate restored files metadata and checksum by comparing
                            with renamed file metadata and checksum information
            """, 200)
            # -------------------------------------------------------------------------------------

            self.machin.rename_file_or_folder(compare_source, new_folder_name)
            # in-Place restore
            self.serverbase.subclient_restore_in_place(_paths, subclient=subclient_obj)
            self._log.info("Subclient in Place Restore Job completed successfully")
            # validation of restore data
            cloud_object.validate_restore(self.machin, compare_source, compare_destination)
            self._log.info("***TEST CASE COMPLETED SUCCESSFULLY AND PASSED***")

        except Exception as exp:
            self.server_obj.fail(exp)

        finally:
            self._utility.remove_directory(self.machin, dest_path)
            if self.machin.check_directory_exists(compare_source):
                self._utility.remove_directory(self.machin, new_folder_name)
            else:
                self.machin.rename_file_or_folder(new_folder_name, compare_source)
