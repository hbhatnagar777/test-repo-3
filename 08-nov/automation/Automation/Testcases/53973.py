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

import os

from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine

from Application.CloudApps import cloud_connector

from Application.CloudApps import constants as ca_constants


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

                proxy_machine   (object)    --  Object of machine class for OneDrive proxy machine

        """
        super(TestCase, self).__init__()
        self.name = "Filesystem data restore to OneDrive verification"
        self.applicable_os = self.os_list.WINDOWS
        self.product = self.products_list.CLOUDCONNECTOR
        self.feature = self.features_list.DATAPROTECTION
        self.show_to_user = True
        self.tcinputs = {
            "application_id": "",
            "application_key_value": "",
            "azure_directory_id": "",
            "destination_user": ""
        }
        self.cvcloud_object = None
        self.proxy_machine = None

    def setup(self):
        """Setup function of this test case"""

        self.cvcloud_object = cloud_connector.CloudConnector(self)
        self.cvcloud_object.cvoperations.cleanup()
        folder_id = self.cvcloud_object.one_drive.get_folder_id_from_graph(
            user_id=self.tcinputs.get("destination_user", ""), folder=ca_constants.TEST_DATA_PATH.split('\\')[-1])
        if folder_id is not None:
            self.cvcloud_object.one_drive.delete_folder(
                user_id=self.tcinputs.get("destination_user", ""),
                folder_name=ca_constants.TEST_DATA_PATH.split('\\')[-1],
                folder_id=folder_id)
        self.proxy_client_object = self.commcell.clients.get(self.instance.proxy_client)
        self.proxy_client_object.reconfigure_client()

    def run(self):
        """Run function of this test case"""
        try:
            # generate test data
            self.proxy_machine = Machine(self.instance.proxy_client, self.commcell)
            self.proxy_machine.generate_test_data(file_path=ca_constants.TEST_DATA_PATH,
                                                  dirs=0,
                                                  files=5,
                                                  file_size=100,
                                                  levels=0)
            self.cvcloud_object.cvoperations.create_subclient(
                name=ca_constants.SUBCLIENT_NAME, content=[
                    ca_constants.TEST_DATA_PATH])
            # Run full backup

            backup_level = 'FULL'
            self.cvcloud_object.cvoperations.check_job_status(
                job=self.cvcloud_object.cvoperations.fs_subclient.backup(
                    backup_level=backup_level), backup_level_tc=backup_level)

            # Browse and Restore
            path = self.cvcloud_object.cvoperations.fs_subclient.browse()
            path1 = self.cvcloud_object.cvoperations.fs_subclient.browse(path=path[0][0])
            dest_path = self.tcinputs.get("destination_user", "")
            if not dest_path:
                raise Exception('Destination user not found in input json.')
            self.cvcloud_object.cvoperations.check_job_status(
                job=self.cvcloud_object.cvoperations.restore_fs_to_od(
                    source_path=path1[0], destination_path=dest_path), backup_level_tc='RESTORE')
            folder_name = ca_constants.TEST_DATA_PATH.split('\\')[-1]
            self.log.info('folder name on one drive: %s', folder_name)
            self.cvcloud_object.one_drive.get_file_properties(user=dest_path, folder=folder_name)
            self.cvcloud_object.one_drive.download_files(user=dest_path)

            # Comparison
            source_path = os.path.join(ca_constants.ONEDRIVE_DOWNLOAD_DIRECTORY, dest_path)

            self.log.info('destination path on proxy client: %s', ca_constants.TEST_DATA_PATH)
            machine = Machine()
            diff = machine.compare_folders(destination_machine=self.proxy_machine,
                                           source_path=source_path,
                                           destination_path=ca_constants.TEST_DATA_PATH)

            if diff:
                self.log.info('Following files are not matching after restore', diff)
                raise Exception('File comparison is not matching')
            self.log.info('File hashes are matching after disk restore')

        except Exception as exp:
            self.log.error('Failed with error: %s', str(exp))
            self.result_string = str(exp)
            self.status = constants.FAILED

    def tear_down(self):
        # delete generated data on proxy client, delete subclient
        self.proxy_machine.remove_directory(ca_constants.TEST_DATA_PATH)
        self.cvcloud_object.one_drive.delete_folder(
            user_id=self.tcinputs.get("destination_user", ""), folder_name=ca_constants.TEST_DATA_PATH.split('\\')[-1])
        self.cvcloud_object.cvoperations.cleanup()
        self.cvcloud_object.cvoperations.subclients_object.delete(ca_constants.SUBCLIENT_NAME)
        del self.cvcloud_object
