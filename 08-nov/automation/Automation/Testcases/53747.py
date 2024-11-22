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
    __init__()      --  initialize TestCase class

    setup()         --  setup function of this test case

    run()           --  run function of this test case

    tear_down()     --  tear down function of this test case
"""

from AutomationUtils import constants

from Application.CloudApps import cloud_connector
from AutomationUtils.cvtestcase import CVTestCase


class TestCase(CVTestCase):
    """Class for executing Basic acceptance test of Cloud Apps backup and Restore test case"""

    def __init__(self):
        """Initializes test case class object

            Properties to be initialized:
                name            (str)       --  name of this test case

                applicable_os   (str)       --  applicable os for this test case
                    Ex: self.os_list.WINDOWS

                product         (str)       --  applicable product for this test case
                    Ex: self.products_list.FILESYSTEM

                features        (str)       --  qcconstants feature_list item
                    Ex: self.features_list.DATAPROTECTION

                show_to_user    (bool)      --  test case flag to determine if the test case is
                                                    to be shown to user or not
                    Accept:
                        True    -   test case will be shown to user from commcell gui

                        False   -   test case will not be shown to user
                    default: False

                tcinputs    (dict)      --  dict of test case inputs with input name as dict key
                                                and value as input type
                        Ex: {
                             "MY_INPUT_NAME": None
                        }

                cvcloud_object      (object)    --  Object of CloudConnector class

                log     (object)    --  Object of the logger module
        """
        super(TestCase, self).__init__()
        self.name = "Point in time restore verification for GDrive"
        self.applicable_os = self.os_list.WINDOWS
        self.product = self.products_list.CLOUDCONNECTOR
        self.feature = self.features_list.DATAPROTECTION
        self.show_to_user = True
        self.tcinputs = {
            "application_email_address": "",
            "private_key_file_path": None
        }
        self.cvcloud_object = None

    def setup(self):
        """Setup function of this test case"""

        self.cvcloud_object = cloud_connector.CloudConnector(self)
        self.cvcloud_object.cvoperations.cleanup()

    def run(self):
        """Run function of this test case"""

        try:
                            
            self.cvcloud_object.gdrive.delete_folder()
            self.cvcloud_object.gdrive.create_files(
                unicode_data=False, pdf=True, google_docs=True, new_folder=True, attempt='full')
            self.cvcloud_object.gdrive.get_file_properties()
            backup_level = 'FULL'
            self.cvcloud_object.cvoperations.check_job_status(self.subclient.backup(backup_level),
                                                              backup_level_tc=backup_level)
            self.cvcloud_object.gdrive.create_files(
                unicode_data=False, pdf=True, google_docs=True, new_folder=False, attempt='Incremental')
            self.cvcloud_object.gdrive.get_file_properties()
            backup_level = 'INCREMENTAL'
            self.cvcloud_object.cvoperations.check_job_status(self.subclient.backup(backup_level),
                                                              backup_level_tc=backup_level)
            self.cvcloud_object.gdrive.delete_files()
            self.cvcloud_object.cvoperations.restore_subclient(incremental=True)
            self.cvcloud_object.gdrive.compare_file_properties(incremental=True)

        except Exception as exp:
            self.log.error('Failed with error: ' + str(exp))
            self.result_string = str(exp)
            self.status = constants.FAILED

    def tear_down(self):
        # delete subclient here
        # delete docs folder, label dict folder and message property folder
        if self.status == constants.PASSED:
            self.cvcloud_object.gdrive.delete_folder()
            self.cvcloud_object.cvoperations.cleanup()
        del self.cvcloud_object
