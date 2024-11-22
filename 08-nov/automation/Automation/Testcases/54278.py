# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
""""
Main file for executing this test case
TestCase is the only class definied in this file
TestCase: Class for executing this test case

TestCase:
    __init__()             --  Initialize TestCase class

    run()                  --  run function of this test case
"""

from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from FileSystem.SNAPUtils.unixsnaphelper import UnixSnapHelper
from AutomationUtils.constants import backup_level



class TestCase(CVTestCase):
    """ Unix snap"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = 'Snap Backup - LVM testing scenario --with Filters enabled on the subclient'
        self.tcinputs = {
            "SubclientContent": None,
            "ScanType": None,
            "MediaAgentName": None,
            "RestoreLocation": None,
            "DiskLibLocation": None,
            "SnapEngine": None
            }

    def run(self):
        """Main function for test case execution"""
        log = self.log

        try:
            file_extentsion_list = ['.doc', '.txt', '.xml']
            log.info("Started executing %s testcase", format(self.id))
            snap_helper = UnixSnapHelper(self.commcell, self.client, self.agent, self.tcinputs)
            snap_helper.setup_snap_environment()
            self.generate_testdata(file_extentsion_list, snap_helper.test_data_paths, 5)
            snap_helper.snap_backup(backup_level.FULL, True)
            snap_helper.backup_copy()
            snap_helper.validate_filters(self.tcinputs['Filter_content'].split(','))
            self.log.info("*" * 20 + "Filters validation completed successfully" + "*" * 20)
            snap_helper.status = constants.PASSED
        except Exception as excp:
            log.error('Failed with error: [%s]', str(excp))
            self.result_string = str(excp)
            self.status = constants.FAILED
        finally:
            snap_helper.cleanup()

    def generate_testdata(self, file_extensions, path=None, no_of_files=5):
        """Creates files with the specified extensions

        Args:
            file_extensions   (list)    --  List of all the extensions
            path               (str)    --  Source path to create files on
            no.of files        (int)    --  File count to create in destination


        """

        for content_path in path:
            self.slash_format = '/'
            snap_helper = UnixSnapHelper(self.commcell, self.client, self.agent, self.tcinputs)
            if snap_helper.client_machine.check_directory_exists(content_path):
                self.log.info("Deleting the existing folder")
                snap_helper.client_machine.remove_directory(content_path)

            snap_helper.client_machine.create_directory(content_path)
            for each_extension in file_extensions:
                for i in range(1, no_of_files):
                    file_name = "{0}{1}{2}{3}".format(content_path, self.slash_format, str(i), each_extension)
                    data_to_file = str("My File Data {0}".format(file_name))
                    snap_helper.client_machine.create_file(file_name, data_to_file)
