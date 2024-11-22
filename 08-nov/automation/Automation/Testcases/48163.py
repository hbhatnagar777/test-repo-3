# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

This test verifies acceptance testcase for reference copy testcase

TestCase:
    __init__()                  --  Initializes the TestCase class

    setup()                     --  All testcase objects are initializes in this method

    run()                       --  Contains the core testcase logic and it is the one executed

    edit_testdata()             --  Edits the testdata for the subclient

    verify_restore()            --  Starts restore for the reference copy subclient and verifies the restore result.

    do_setup()                  --  Creates fresh reference copy and source subclients and runs FULL backup.

    create_source_entities()    --  Creates backupset and subclient for the source client

    create_reference_copy_entities()    --  Creates backupset and subclient for the reference copy client

    set_reference_copy_content()    --  Sets the content for the reference copy subclient

    set_reference_copy_association()    --  Sets the association for the reference copy subclient

    get_random_file()           --  Gets a random file from the given path

    get_file_names()            --  Scans the directory and returns a list of file with only the filename

"""

import random
import os

from AutomationUtils import logger
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine
from AutomationUtils import commonutils

from Indexing.testcase import IndexingTestcase


class TestCase(CVTestCase):
    """This test verifies acceptance testcase for reference copy testcase

        Steps:
            In Setup mode:
            1) Create reference copy source subclient
            2) Run FULL backup
            3) Create reference copy subclient
            4) Associate the source subclient
            5) Set the reference copy content
            6) Run FULL backup

            In Test mode:
            1) Add, edit and delete a file in the source subclient
            2) Run INC backup on source
            3) Run INC backup on reference copy subclient
            4) Verify browse and restore
            5) Run synthetic full job on source and reference copy subclient
            6) Verify browse and restore

    """

    def __init__(self):
        """Initializes test case class object"""

        super(TestCase, self).__init__()
        self.name = 'Indexing - Reference copy'

        self.tcinputs = {
            'ClientName': None,  # Name of the source client
            'StoragePolicy': None,
            'ReferenceCopyClientName': None,
            'RestorePath': None,
            'Mode': None  # Supported values are 'Setup' and 'Test'
        }

        self.cl_machine = None
        self.idx_tc = None
        self.src_backupset_name = 'ref_copy_src'
        self.src_subclient_name = 'ref_copy_sc'
        self.rc_backupset_name = 'ref_copy_auto_bkset'
        self.rc_subclient_name = 'ref_copy_auto_sc'
        self.rc_client = None
        self.rc_agent = None
        self.rc_backupset = None
        self.rc_subclient = None

    def setup(self):
        """All testcase objects are initialized in this method"""

        self.cl_machine = Machine(self.client)
        self.idx_tc = IndexingTestcase(self)

        self.mode = self.tcinputs.get('Mode').lower()
        self.storage_policy = self.tcinputs.get('StoragePolicy')
        self.rc_client = self.commcell.clients.get(self.tcinputs.get('ReferenceCopyClientName'))
        self.rc_agent = self.rc_client.agents.get('File System')

        track_folder = os.path.join(logger.get_log_dir(), 'Indexing', 'reference_copy')
        if not os.path.exists(track_folder):
            os.makedirs(track_folder)

        self.deleted_files = os.path.join(
            track_folder,
            f'{self.client.client_name}_{self.src_subclient_name}_deleted_files.txt'
        )
        self.log.info(f'***** File to track deletions [{self.deleted_files}] *****')

        if self.mode == 'setup':
            self.do_setup()
            return

        if not self.rc_backupset:
            self.rc_backupset = self.rc_agent.backupsets.get(self.rc_backupset_name)

        if not self.rc_subclient:
            self.rc_subclient = self.rc_backupset.subclients.get(self.rc_subclient_name)

        if not self._backupset:
            self.backupset = self.agent.backupsets.get(self.src_backupset_name)

        if not self._subclient:
            self.subclient = self.backupset.subclients.get(self.src_subclient_name)

    def run(self):
        """Contains the core testcase logic"""

        if self.mode == 'setup':
            self.log.info('In Setup mode, not running tests')
            return

        self.log.info('***** Editing testdata *****')
        self.edit_testdata()

        self.log.info('***** Running INC on SOURCE client *****')
        self.idx_tc.run_backup(self.subclient, backup_level='incremental')

        self.log.info('***** Running INC on REFERENCE COPY client *****')
        self.idx_tc.run_backup(self.rc_subclient, backup_level='incremental')

        self.verify_restore()

        self.log.info('***** Running SFULL on SOURCE client *****')
        self.idx_tc.run_backup(self.subclient, backup_level='synthetic_full')

        self.log.info('***** Running SFULL on REFERENCE COPY client *****')
        self.idx_tc.run_backup(self.rc_subclient, backup_level='synthetic_full')

        self.verify_restore()

        self.log.info('Testcase completed successfully')

    def edit_testdata(self):
        """Edits the testdata for the subclient"""

        sc_content = self.subclient.content

        for path in sc_content:
            to_delete_file = self.get_random_file(path)
            self.cl_machine.delete_file(to_delete_file['path'])

            with open(self.deleted_files, 'a') as deleted_files:
                line = [to_delete_file['path'], to_delete_file['size'], to_delete_file['mtime']]
                line = ','.join(line)
                deleted_files.write(f'{line}\n')
                self.log.info(f'Recorded the deleted file information [{line}]')

            to_edit_file = self.get_random_file(path)
            self.log.info(f'Editing file [{to_edit_file["path"]}]')
            self.cl_machine.append_to_file(to_edit_file['path'], str(random.randint(0, 9))*10)

            self.log.info('Creating files')
            rand_id = commonutils.get_random_string(length=4)
            self.idx_tc.create_only_files(path, count=2, name=f'file-{rand_id}', extensions=['txt'])
            self.idx_tc.create_only_files(path, count=2, name=f'file-{rand_id}', extensions=['ini'])

    def verify_restore(self):
        """Starts restore for the reference copy subclient and verifies the restore result."""

        self.log.info('***** Running RESTORE on REFERENCE COPY client')

        restore_path = self.cl_machine.join_path(self.tcinputs.get('RestorePath'), 'r')

        try:
            self.cl_machine.remove_directory(restore_path)
        except Exception as e:
            self.log.error('Failed to delete the existing restore directory')

        self.idx_tc.cv_ops.subclient_restore_out_of_place(
            client=self.client,
            subclient=self.rc_subclient,
            destination_path=restore_path,
            paths=['\\']
        )

        # We verify the restore results by taking the name of the file only instead of full path
        actual_items = self.get_file_names(restore_path)
        self.log.info(f'=> Actual items [{actual_items}]')

        expected_items = {}
        for path in self.subclient.content:
            items = self.get_file_names(path, do_filter=True)
            expected_items.update(items)

        with open(self.deleted_files, 'r') as deleted_files:
            for line in deleted_files:
                line = line.strip()
                if not line:
                    continue
                file_data = line.split(',')
                file_name = file_data[0].split(self.cl_machine.os_sep)[-1]
                expected_items[file_name] = {
                    'size': file_data[1],
                    'modified': file_data[2]
                }

        self.log.info(f'=> Expected items [{expected_items}]')

        if actual_items != expected_items:
            diff = commonutils.get_dictionary_difference(actual_items, expected_items)
            self.log.error(f'=> Added [{diff[0]}]')
            self.log.error(f'=> Removed [{diff[1]}]')
            self.log.error(f'=> Modified [{diff[2]}]')
            raise Exception('Mismatch in actual and expected results after restore')

        self.log.info('***** Restore results are verified *****')

    def do_setup(self):
        """Creates fresh reference copy and source subclients and runs FULL backup."""

        self.log.info('***** In SETUP mode *****')
        self.log.info('***** Creating reference copy source client *****')

        self.create_source_entities()

        self.create_reference_copy_entities()

        self.log.info('***** Creating testdata *****')
        for path in self.subclient.content:
            rand_id = commonutils.get_random_string(length=4)
            self.idx_tc.create_only_files(path, count=3, name=f'root-file-{rand_id}', extensions=['txt'])
            self.idx_tc.create_only_files(path, count=2, name=f'root-file-{rand_id}', extensions=['ini'])
            self.idx_tc.create_only_files(path, count=3, base_dir='dir', name=f'dir-file-{rand_id}', extensions=['txt'])
            self.idx_tc.create_only_files(path, count=2, base_dir='dir', name=f'dir-file-{rand_id}', extensions=['ini'])

        self.log.info('***** Running backup on SOURCE client *****')
        self.idx_tc.run_backup(self.subclient, backup_level='full')

        self.log.info('***** Running backup on REFERENCE COPY client *****')
        self.idx_tc.run_backup(self.rc_subclient, backup_level='full')

        self.log.info('***** Deleting TRACK DELETIONS file *****')
        try:
            os.remove(self.deleted_files)
        except Exception as e:
            self.log.error(f'Failed to delete file [{e}]')

        self.log.info('Setup completed successfully')

    def create_source_entities(self):
        """Creates backupset and subclient for the source client"""

        self.backupset = self.idx_tc.create_backupset(self.src_backupset_name, for_validation=False)

        self.subclient = self.idx_tc.create_subclient(
            name=self.src_subclient_name,
            backupset_obj=self.backupset,
            storage_policy=self.storage_policy
        )

        for path in self.subclient.content:
            self.log.info(f'Creating subclient content directory [{path}]')
            self.cl_machine.create_directory(path)

    def create_reference_copy_entities(self):
        """Creates backupset and subclient for the reference copy client"""

        if self.rc_agent.backupsets.has_backupset(self.rc_backupset_name):
            self.rc_agent.backupsets.delete(self.rc_backupset_name)

        self.rc_backupset = self.rc_agent.backupsets.add(self.rc_backupset_name)
        self.rc_subclient = self.rc_backupset.subclients.add(self.rc_subclient_name, storage_policy=self.storage_policy)

        if not self.rc_subclient.subclient_id:
            raise Exception('Cannot get reference copy subclient ID')

        self.log.info('Setting reference copy subclient type')
        self.idx_tc.options_help.update_commserve_db(f"""
            update APP_Application set subclientStatus = 65536 where id = '{self.rc_subclient.subclient_id}' 
        """)

        self.set_reference_copy_content()
        self.set_reference_copy_association()

    def set_reference_copy_content(self):
        """Sets the content for the reference copy subclient"""

        self.log.info('***** Setting reference copy content *****')

        xml = f"""<databrowse_SetReferenceCopyContents>
            <contents fromTime="1600000000" toTime="0" useLatestCycle="0">
                <criterias filterName="">
                    <filteredBrowseCriteriaValue field="0" selectAll="1">
                        <values val="*.txt"/>
                    </filteredBrowseCriteriaValue>
                </criterias>
                <timeZone TimeZoneID="42" TimeZoneName="(UTC+05:30) Chennai, Kolkata, Mumbai, New Delhi" _type_="55"/>
            </contents>
            <entity _type_="7"
            backupsetId="{self.rc_backupset.backupset_id}" backupsetName="{self.rc_backupset.backupset_name}"
            clientId="0" clientName="{self.rc_client.client_name}" 
            instanceId="1" instanceName=""
            subclientId="{self.rc_subclient.subclient_id}" subclientName="{self.rc_subclient.subclient_name}"/>
        </databrowse_SetReferenceCopyContents>
        """

        response = self.commcell.execute_qcommand('qoperation execute', xml)

        if response.status_code != 200:
            raise Exception('Unable to set reference copy content')

        self.log.info('Successfully set reference copy content')

    def set_reference_copy_association(self):
        """Sets the association for the reference copy subclient"""

        self.log.info('***** Setting reference copy association *****')

        xml = f"""<databrowse_SetReferenceCopyAsociationResp>
            <refCopyAssociations>
                <associations _type_="7" appName="Windows File System" applicationId="33" 
                backupsetId="{self.backupset.backupset_id}" backupsetName="{self.backupset.backupset_name}"
                clientId="{self.client.client_id}" clientName="{self.client.client_name}"
                commCellId="2" commCellName="{self.commcell.commserv_name}"
                instanceId="1" instanceName="DefaultInstanceName"
                subclientId="{self.subclient.subclient_id}" subclientName="{self.subclient.subclient_name}"/>
            </refCopyAssociations>
            <entity _type_="7"
            backupsetId="{self.rc_backupset.backupset_id}" backupsetName="{self.rc_backupset.backupset_name}"
            clientId="0" clientName="{self.rc_client.client_name}" 
            instanceId="1" instanceName=""
            subclientId="{self.rc_subclient.subclient_id}" subclientName="{self.rc_subclient.subclient_name}"/>
        </databrowse_SetReferenceCopyAsociationResp>"""

        response = self.commcell.execute_qcommand('qoperation execute', xml)

        if response.status_code != 200:
            raise Exception('Unable to set reference copy subclient association')

        self.log.info('Successfully set reference copy association')

    def get_random_file(self, path):
        """Gets a random file from the given path

            Args:
                path        (str)       --      The path of the folder to get a random file

            Returns:
                (dict)      --  Dict of the file properties like path, size, mtime

        """

        all_files = self.cl_machine.scan_directory(path, filter_type='file')
        random.shuffle(all_files)

        for file in all_files:
            if '.txt' in file['path']:
                return file

    def get_file_names(self, path, do_filter=False):
        """Scans the directory and returns a list of file with only the filename

            Args:
                path        (str)   --      The path of the folder to get filenames

                do_filter   (bool)  --      Skips files without the txt extension

            Returns:
                (list)      --      List of filename with their size and mtime

        """

        files = {}
        files_raw = self.cl_machine.scan_directory(path, filter_type='file')

        for file in files_raw:
            path = file['path']
            file_name = path.split(self.cl_machine.os_sep)[-1]

            if do_filter:
                if '.txt' not in file_name:
                    continue

            files[file_name] = {
                'size': file['size'],
                'modified': file['mtime']
            }

        return files
