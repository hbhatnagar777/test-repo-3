# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""Main file for executing this test case

TestCase: Class for executing this test case

TestCase:
    __init__()                               --  initialize TestCase class

    setup()                                  --  setup function of this test case

    run()                                    --  run function of this test case

    if_rfc_files_exist()                     --  verifies if RFC files exist on the server

    get_rfc_server_machine()                 --  Fetches RFC server machine for given Job id

    change_access_time()                     --  Changes the access time at given statefile xml path

"""
import datetime
import time
import xmltodict
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine
from Indexing.helpers import IndexingHelpers
from Indexing.database import index_db
from Indexing.testcase import IndexingTestcase


class TestCase(CVTestCase):
    """
    This testcase verifies the RFC cleanup should happen if the folder is older than a week.

    Steps:
     1) Run a few jobs -> Full, Inc, Sfull and Inc.
     2) Check if RFC files are created for the jobs
     3) Change the access time in statefile in Full and Sfull folders to before 7 days.
     4) Change the access time in statefile in one of the folders to before 5 days.
     5) Restart services on the RFC server.
     6) Verify that the folder which time was changed to a date 7 days ago is deleted or cleaned up.
     7) Verify that the other folder with 5 days change is still present in cache.

"""

    def __init__(self):
        """Initializes test case class object"""
        super().__init__()
        self.name = 'Indexing - Verify RFC cleanup'
        self.tcinputs = {
            'StoragePolicy': None
        }
        self.backupset = None
        self.subclient = None
        self.cl_machine = None
        self.idx_db = None
        self.rfc_servers = {}
        self.idx_help = None
        self.idx_tc = None
        self.statepaths = {}

    def setup(self):
        """All testcase objects have been initialized in this method"""

        self.cl_machine = Machine(self.client)
        self.idx_tc = IndexingTestcase(self)
        self.backupset = self.idx_tc.create_backupset(
            name='70636_rfc_cleanup',
            for_validation=True)

        self.subclient = self.idx_tc.create_subclient(
            name='rfc_cleanup_sc',
            backupset_obj=self.backupset,
            storage_policy=self.tcinputs['StoragePolicy'],
            register_idx=True
        )
        self.idx_help = IndexingHelpers(self.commcell)

    def run(self):
        """Contains the core testcase logic, and it is the one executed"""
        try:
            if 'windows' not in self.client.os_info.lower():
                raise Exception('RFC cleanup verificaton testcase is applicable only for windows, '
                                'Unix/linux clients don\'t create RFC')

            self.log.info('************* Running backup jobs *************')

            jobs_sequence = self.idx_tc.run_backup_sequence(
                subclient_obj=self.subclient,
                steps=['New', 'Full', 'Edit', 'Incremental', 'Synthetic_full', 'Edit',
                       'Incremental'])
            self.log.info('Backup Jobs completed successfully')

            indexing_level = self.idx_help.get_agent_indexing_level(self.agent)
            self.idx_db = index_db.get(self.subclient if indexing_level == 'subclient' else
                                       self.backupset)

            self.log.info('Getting RFC server for Full job')
            rfc_server_full = self.get_rfc_server_machine(job_id=jobs_sequence[0].job_id)
            if self.if_rfc_files_exist(job_id=jobs_sequence[0].job_id,
                                       rfc_server_machine=rfc_server_full):
                state_file_path_full = self.statepaths[jobs_sequence[0].job_id]
            else:
                raise Exception('Verification of RFC failed, no files in RFC folder for Full job.')
            self.log.info('State-file path for Full job is------ %s', state_file_path_full)

            self.log.info('** Changing Access Time by -7 days in the rfc statefile for full job **')
            # Since we are moving access time by 7 days, the rfc folder should be deleted.
            self.change_access_time(file_path=state_file_path_full,
                                    rfc_server_machine=rfc_server_full, days=7)

            rfc_server_inc = self.get_rfc_server_machine(job_id=jobs_sequence[1].job_id)
            if self.if_rfc_files_exist(job_id=jobs_sequence[1].job_id,
                                       rfc_server_machine=rfc_server_inc):
                state_file_path_inc = self.statepaths[jobs_sequence[1].job_id]
            else:
                raise Exception('Verification of RFC failed, '
                                'no files in the RFC folder for Inc job.')
            self.log.info('State-file path for Incremental job is------ %s', state_file_path_inc)

            self.log.info('** Changing Access Time by -5 days in the rfc statefile for incremental '
                          'job **')
            # Since we are moving access time by 5 days, the rfc folder shouldn't be deleted.
            self.change_access_time(file_path=state_file_path_inc,
                                    rfc_server_machine=rfc_server_inc, days=5)

            if self.if_rfc_files_exist(job_id=jobs_sequence[2].job_id,
                                       rfc_server_machine=rfc_server_inc):
                state_file_path_syn = self.statepaths[jobs_sequence[2].job_id]
            else:
                raise Exception('Verification of RFC failed, no files in RFC folder for Syn job.')
            self.log.info('State-file path for Synthetic Full job is------ %s', state_file_path_syn)

            self.log.info('** Changing Access Time by -7 days in the rfc statefile for sfull job **'
                          )
            # Since we are moving access time by 7 days, the rfc folder should be deleted.
            self.change_access_time(file_path=state_file_path_syn,
                                    rfc_server_machine=rfc_server_inc, days=7)

            # Restarts the services
            self.log.info('Restarting Commvault Services on RFC servers')
            for rfc_server_name in self.rfc_servers:
                self.log.info('Restarting services on %s', rfc_server_name)
                rfc_client = self.commcell.clients.get(rfc_server_name)
                rfc_client.restart_services()
                self.log.info('Services Restarted Successfully on %s', rfc_server_name)
            self.log.info(' Waiting after service restart for the cleanup to initiate')
            time.sleep(120)

            self.log.info('Verifying Cleanup for Full job')
            if not self.if_rfc_files_exist(job_id=jobs_sequence[0].job_id,
                                           rfc_server_machine=rfc_server_full):
                self.log.info('Cleanup of RFC files is successfull for Full job')
            else:
                raise Exception('Cleanup of RFC files failed for Full Job.')

            self.log.info('Verifying Cleanup for Incremental job')
            if self.if_rfc_files_exist(job_id=jobs_sequence[1].job_id,
                                       rfc_server_machine=rfc_server_inc):
                self.log.info('No cleanup happened and RFC is present for Incremental Job.')
            else:
                raise Exception('Cleanup of RFC files is successfull for Incremental Job which is '
                                'UNEXPECTED.')

            self.log.info('Verifying Cleanup for Synthetic Full job')
            if not self.if_rfc_files_exist(job_id=jobs_sequence[2].job_id,
                                           rfc_server_machine=rfc_server_inc):
                self.log.info('Cleanup of RFC files is successfull for Synthetic Full job.')
            else:
                raise Exception('Cleanup of RFC files failed for Synthetic full Job.')

        except Exception as exp:
            self.log.error('Failed to execute test case with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED

    def get_rfc_server_machine(self, job_id):
        """ Fetches the RFC server machine for a given Job id

                    Args:
                            job_id    (str)   --   Job ID of the job for which RFC server is needed

                        """
        rfc_server = self.idx_help.get_rfc_server(job_id=job_id)
        rfc_server_name = rfc_server.name
        self.log.info('RFC server for the job id: %s is %s', job_id, rfc_server_name)
        if rfc_server_name in self.rfc_servers:
            return self.rfc_servers.get(rfc_server_name)
        rfc_server_machine = Machine(rfc_server_name, self.commcell)
        self.rfc_servers[rfc_server_name] = rfc_server_machine
        return rfc_server_machine

    def if_rfc_files_exist(self, job_id, rfc_server_machine):
        """ verifies the RFC files on the server

            Args:
                    job_id    (str)   --   Job ID of the job for which RFC upload has to be verified

                    rfc_server_machine   (obj)    --  RFC server of machine

                """
        self.log.info(' Verifying if RFC exist for Job: %s', job_id)
        rfc_folder = self.idx_db.get_rfc_folder_path(rfc_server_machine=rfc_server_machine,
                                                     job_id=job_id)
        self.log.info('RFC folder path for the job: %s is %s', job_id, rfc_folder)

        self.log.info('***** Checking if RFC Folder exists ******')
        if rfc_server_machine.check_directory_exists(rfc_folder):
            rfc_files = rfc_server_machine.get_files_in_path(rfc_folder, recurse=False)
            self.log.info('RFC files under %s are %s', rfc_folder, rfc_files)
            if len(rfc_files) != 0:
                self.log.info('RFC files are verified at %s', rfc_folder)
                statefile_path = [i for i in rfc_files if 'STATEFILE' in i]
                if len(statefile_path) != 0:
                    self.statepaths[job_id] = statefile_path[0]
                else:
                    raise Exception('No state file path present in RFC folder.')
                return True

            return False
        return False

    def change_access_time(self, file_path, rfc_server_machine, days):
        """ Changes the Access time in statefile of the RFC Folder by given days

                Args:
                        file_path         (str)    --  path of the RFC state file
                        rfc_server_machine (obj)    -- rfc server machine of the job
                        days              (int)    --  Number of days by access time has to be moved

                        """

        content = rfc_server_machine.read_file(file_path)
        self.log.info('Getting content from statefile as %s', content)
        xml_content = xmltodict.parse(content)
        access_time = int(xml_content['Indexing_RFCStateFile']['@accessTime'])
        self.log.info(' Original Access Time is- %s', datetime.date.fromtimestamp(access_time))
        changed_time = access_time - (days * 86400)
        self.log.info(' Changed Access Time is- %s', datetime.date.fromtimestamp(changed_time))
        xml_content['Indexing_RFCStateFile']['@accessTime'] = str(changed_time)
        edited_content = xmltodict.unparse(xml_content)
        rfc_server_machine.create_file(file_path, edited_content)
        changed_access = xmltodict.parse(rfc_server_machine.find_lines_in_file(file_path,
                                                                               ['accessTime'])[0])
        changed_access = changed_access['Indexing_RFCStateFile']['@accessTime']
        if changed_access == str(changed_time):
            self.log.info('The access time is changed successfully by %s days', days)
        else:
            raise Exception('Error while changing access time in statefile of the RFC.')
