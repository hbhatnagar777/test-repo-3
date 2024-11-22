# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

This testdata verified that testdata with multiple components/mount points are working
successfully during index playback, browse, synthetic full, restore

TestCase:
    __init__()                  --  Initializes the TestCase class

    setup()                     --  All testcase objects are initializes in this method

    run()                       --  Contains the core testcase logic and it is the one executed

    create_mount_points()       -- Creates new testdata for the subclient

    tear_down()                 --  Cleans the data created for Indexing validation

"""

import traceback
import os

from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine

from Indexing.testcase import IndexingTestcase
from Indexing.helpers import IndexingHelpers


class TestCase(CVTestCase):
    """This testdata verified that testdata with multiple components/mount points are working
    successfully during index playback, browse, synthetic full, restore"""

    def __init__(self):
        """Initializes test case class object"""

        super(TestCase, self).__init__()
        self.name = 'Indexing - Multiple components testdata'
        self.show_to_user = False

        self.tcinputs = {
            'StoragePolicyName': None
        }

        self.backupset = None
        self.subclient = None

        self.cl_machine = None
        self.idx_tc = None
        self.idx_help = None

        self.src_mount_path = '/auto_mount_src'
        self.dst_mount_path = '/auto_mount_dst'

    def setup(self):
        """All testcase objects are initializes in this method"""

        try:

            self.backupset_name = self.tcinputs.get('Backupset', 'multiple_components_auto')
            self.subclient_name = self.tcinputs.get('Subclient', self.id)
            self.storagepolicy_name = self.tcinputs.get('StoragePolicyName')

            if 'unix' not in self.client.os_info.lower():
                raise Exception(
                    'This testcase is applicable only for Unix clients. Please change '
                    'storage policy to change IndexServer MA')

            self.cl_machine = Machine(self.client, self.commcell)

            self.idx_tc = IndexingTestcase(self)
            self.idx_help = IndexingHelpers(self.commcell)

            self.backupset = self.idx_tc.create_backupset(self.backupset_name)

            self.subclient = self.idx_tc.create_subclient(
                name=self.subclient_name,
                backupset_obj=self.backupset,
                storage_policy=self.storagepolicy_name,
                content=[self.dst_mount_path]
            )

        except Exception as exp:
            self.log.error(str(traceback.format_exc()))
            raise Exception(exp)

    def run(self):
        """Contains the core testcase logic and it is the one executed

            Steps:
                - Create mount paths in unix machine
                - Run FULL => INC => SFULL => INC => SFULL
                - Validate job based browse after every job
                - Validate find and restore after every cycle
        """

        try:
            self.log.info("Started executing {0} testcase".format(self.id))

            testdata_to_modify = [
                self.dst_mount_path + '/mnt1/dnd_testdata1',
                self.dst_mount_path + '/mnt2/dnd_testdata2'
            ]

            self.create_mount_points(200, 10)

            self.log.info('Creating some data to edit in the destination dir')
            self.idx_tc.new_testdata(testdata_to_modify, hlinks=False, slinks=False)
            self.idx_tc.run_backup(self.subclient, 'Full')

            self.log.info('Editing testdata in destination directory')
            self.idx_tc.edit_testdata(testdata_to_modify)
            self.idx_tc.run_backup(self.subclient, 'incremental')

            self.log.info('********** VERIFICATION 1 - Find operation - Cycle 1 **********')

            self.idx_tc.verify_browse_restore(self.backupset, {
                'subclient': self.subclient_name,
                'operation': 'find',
                'path': '/**/*',
                'restore': {
                    'do': True,
                    'source_items': ['/']
                }
            })

            self.idx_tc.run_backup(self.subclient, 'synthetic_full', restore=True)

            self.log.info('Editing testdata in destination directory')
            self.idx_tc.edit_testdata(testdata_to_modify)
            self.idx_tc.run_backup(self.subclient, 'incremental')

            self.log.info('********** VERIFICATION 2 - Find operation - Cycle 2 **********')

            self.idx_tc.verify_browse_restore(self.backupset, {
                'subclient': self.subclient_name,
                'operation': 'find',
                'show_deleted': True,
                'path': '/**/*',
                'restore': {
                    'do': True,
                    'source_items': ['/']
                }
            })

            self.idx_tc.run_backup(self.subclient, 'synthetic_full', restore=True)

        except Exception as exp:
            self.log.error('Test case failed with error: ' + str(exp))
            self.result_string = str(exp)
            self.status = constants.FAILED
            self.log.error(str(traceback.format_exc()))

    def create_mount_points(self, mountpoints=10, files=20):
        """Creates new testdata for the subclient"""

        self.log.info(
            'Creating mount points for source dir [{0}] and destination dir [{1}]'.format(
                self.src_mount_path, self.dst_mount_path
            ))

        # This script create two directories (source and destination) and mounts the sub-dirs in
        # the source directory to the sub-dirs in the destination directory

        script = """#!/bin/bash
            mountsrc='{0}'
            mountdst='{1}'
            amountOfMount={2}
            amountOfFiles={3}
            
            umount -f $mountdst/mnt* > /dev/null
            
            rm -r -f $mountsrc
            rm -r -f $mountdst
            
            mkdir $mountsrc
            mkdir $mountdst
            
            for n in `seq 1 $amountOfMount`
            do
            
                csrc="$mountsrc/mnt$n"
                cdst="$mountdst/mnt$n"
            
                mkdir $csrc
                mkdir $cdst

                mount --bind $csrc $cdst

                for i in `seq 1 $amountOfFiles`
                do
                    fvar=$( cat /dev/urandom| tr -cd 'a-f0-9' | head -c 32 )
                    echo "$fvar" > "$csrc/$fvar"
                done
            done""".format(self.src_mount_path, self.dst_mount_path, mountpoints, files)

        script_path = os.path.join(constants.AUTOMATION_DIRECTORY, 'create_mount_path.bash')
        with open(script_path, 'w+') as file_obj:
            file_obj.write(script)

        self.log.info('Executing create mount path script [{0}]'.format(script_path))
        self.cl_machine.execute(script_path)

        os.remove(script_path)

    def tear_down(self):
        """Cleans the data created for Indexing validation"""

        self.backupset.idx.cleanup()

        self.log.info('Deleting mount points created')
        #self.cl_machine.execute_command('umount {0}/mnt* -f'.format(self.dst_mount_path))
        #self.cl_machine.execute_command('rm {0} -r -f'.format(self.src_mount_path))
        #self.cl_machine.execute_command('rm {0} -r -f'.format(self.dst_mount_path))
