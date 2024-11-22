# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()      --  initialize TestCase class

    setup()         --  setup function of this test case

    run()           --  run function of this test case

    runvatool()     -- function to run vatool


"""


from AutomationUtils.cvtestcase import CVTestCase
from FileSystem.FSUtils.onepasshelper import cvonepas_helper
from AutomationUtils import constants, windows_machine
from MediaAgents.MAUtils.mahelper import MMHelper
from AutomationUtils.machine import Machine
import time


class TestCase(CVTestCase):
    """Class for basic Acceptance Test for File Archiving System"""

    def __init__(self):
        """Initializes test case class object

            Properties to be initialized:

                name            (str)       --  name of this test case

                tcinputs        (dict)      --  test case inputs with input name as dict key
                                                and value as input type"""
        super(TestCase, self).__init__()
        self.name = "Basic Acceptance Test for vatool  File Archiving System"
        self.show_to_user = True
        self.base_folder_path = None
        self.origin_folder_path = None

        self.UNC_base_folder_path = None
        self.UNC_origin_folder_path = None
        self.is_nas_turbo_type = False
        self.sp = None
        self.primary_copy = None
        self.OPHelper = None
        self.tcinputs = {
            "TestPath": None,
            "StoragePolicyName": None,
            "PrimaryMAName": None,
            "PrimaryCopyLibraryName": None
        }

    def setup(self):
        """Setup function of this test case"""
        self.OPHelper = cvonepas_helper(self)
        self.MAHelper = MMHelper(self)
        self.OPHelper.populate_inputs()

        self.log.info("Test inputs populated successfully.")


        if self.OPHelper.nas_turbo_type.lower() == 'networkshare':
            self.is_nas_turbo_type = True

        self.OPHelper.test_file_list = [("test1.txt", True), ("test2.txt", True), ("test3.txt", True),
                                        ("test4.txt", True)]

        self.base_folder_path = self.OPHelper.access_path + '{0}{1}_{2}_data'.format(
                            self.OPHelper.slash_format, str(self.OPHelper.testcase.id), "OPTIMIZED")

        if self.is_nas_turbo_type:
            self.UNC_base_folder_path = self.base_folder_path[2:]
            self.UNC_base_folder_path = "\\UNC-NT_" + self.UNC_base_folder_path
            self.UNC_origin_folder_path = self.OPHelper.client_machine.join_path(self.UNC_base_folder_path, 'origin')

        self.origin_folder_path = self.OPHelper.client_machine.join_path(self.base_folder_path, 'origin')


        self.OPHelper.prepare_turbo_testdata(
            self.origin_folder_path,
            self.OPHelper.test_file_list,
            size1=10 * 1024, size2=10 * 1024
        )

        self.OPHelper.org_hashcode = self.OPHelper.client_machine.get_checksum_list(self.origin_folder_path)
        self.log.info("Test data populated successfully.")
        self.MAHelper.configure_storage_policy(storage_policy_name=self.tcinputs.get('StoragePolicyName'),library_name=self.tcinputs.get('PrimaryCopyLibraryName'),ma_name=self.tcinputs.get('PrimaryMAName'))
        self.sp = self.commcell.storage_policies.get(self.tcinputs.get('StoragePolicyName'))
        self.primary_copy = self.sp.get_copy(self.tcinputs.get('PrimaryCopyName', 'Primary'))
        self.OPHelper.create_archiveset(delete=True, is_nas_turbo_backupset=self.is_nas_turbo_type)
        self.OPHelper.create_subclient(delete=True, content=[self.origin_folder_path])

        if self.is_nas_turbo_type:
            update_properties = self.OPHelper.testcase.subclient.properties
            update_properties['fsSubClientProp']['scanOption'] = 1
            update_properties['fsSubClientProp']['enableNetworkShareAutoMount'] = True
            update_properties['fsSubClientProp']['checkArchiveBit'] = True
            update_properties['fsSubClientProp']['preserveFileAccessTime'] = True
            update_properties['impersonateUser']['password'] = self.tcinputs.get("ImpersonatePassword")
            update_properties['impersonateUser']['userName'] = self.tcinputs.get("ImpersonateUser")
            self.OPHelper.testcase.subclient.update_properties(update_properties)

        _disk_cleanup_rules = {
            "useNativeSnapshotToPreserveFileAccessTime": False,
            "fileModifiedTimeOlderThan": 0,
            "fileSizeGreaterThan": 8,
            "stubPruningOptions": 0,
            "afterArchivingRule": 1,
            "stubRetentionDaysOld": 365,
            "fileCreatedTimeOlderThan": 0,
            "maximumFileSize": 0,
            "fileAccessTimeOlderThan": 0,
            "startCleaningIfLessThan": 100,
            "enableRedundancyForDataBackedup": False,
            "patternMatch": "",
            "stopCleaningIfupto": 100,
            "rulesToSatisfy": 1,
            "enableArchivingWithRules": True
        }

        self.OPHelper.testcase.subclient.archiver_retention = True
        self.OPHelper.testcase.subclient.archiver_retention_days = 1
        self.OPHelper.testcase.subclient.backup_retention = False
        self.OPHelper.testcase.subclient.disk_cleanup = True
        self.OPHelper.testcase.subclient.disk_cleanup_rules = _disk_cleanup_rules
        self.OPHelper.testcase.subclient.backup_only_archiving_candidate = True

    def delete_job(self,jobid):
        """
        deletes jobid sent as arg
        Args:
            job (int) jobid to be deleted
        Returns:
            None
        """

        if isinstance(jobid,str):
            self.log.info("deleting job %s ", jobid)
            self.primary_copy.delete_job(jobid)

    def runvatool(self, path, contentpath, sid, noofprotectedfiles):
        _desc =""" Function to run vatool
            Raises exception if failed to run vatool cmd

        """
        try:
            log = self.log
            output = None
            log.info("Running vatool cmd at %s for id %s for contentpath %s and protected files %s" % (path, sid, contentpath, noofprotectedfiles))
            path1 = path.replace(" ","' '")
            path2 = path1+"\\Base\\cvVerifyArchive.exe"
            path3 = path+"\\Base\\temp"
            log.info("Running vatool cmd at final path %s" % path2)

            if self.is_nas_turbo_type:
                client1 = self.tcinputs.get("ProxyClient")
                cmd = (path2 + ' -clientName ' + client1 + ' -instanceName Instance001 -outCSVPath "' + path3 + '" -appId ' + sid + ' -path ' + contentpath)
            else:
                client1 = self.tcinputs.get("ClientName")
                cmd = (path2 + ' -clientName ' + client1 + ' -instanceName Instance001 -outCSVPath "' + path3 + '" -appId ' + sid + ' -path ' + contentpath)
            log.info("Client where vatool should run %s" % client1)
            log.info("Client where vatool should run %s" % self.OPHelper.client_machine)
            log.info("Command used for vatool {}".format(cmd))
            if self.OPHelper.client_machine.os_info == "WINDOWS":
                output = self.OPHelper.client_machine.execute_command(cmd)
                log.info(str(output.output))
                if str(output.output).find("fail") >= 0 or output.exit_code != 0:
                    raise Exception("Error while executing exe %s" % str(output.output))
                elif str(output.output).find(noofprotectedfiles) >= 0 and output.exit_code == 0:
                    log.info("vatool exe executed successfully and verified all stubs as expected")
                else:
                    raise Exception("vatool exe not executed successfully as protected count %s did not match:%s" %(noofprotectedfiles,str(output.output)))
            else:
                raise Exception("Exception raised with unknown reason :%s" %str(output))

        except Exception as err:
            raise Exception('Failed to execute vatool with error %s' %str(err))


    def run(self):
        """Run function of this test case"""

        _desc = """
        1. Archive test data.
        2. Stub the test data, backup stubs and verify stubs using vatool shown as protected.
        3. Age job manually and then run vatool and confirm vatool result showing dangling stubs
        
        """

        try:

            if self.is_nas_turbo_type:
                client2 = Machine(machine_name=self.tcinputs.get("ProxyClient"), commcell_object=self.commcell)
                path = client2.client_object.install_directory
            else:
                path = self.client.install_directory
            self.log.info("Client path where vatool should run -- %s" % path)
            cpath = self.origin_folder_path
            sid = self.subclient.subclient_id
            self.runvatool(path, cpath, sid,"0")
            job_list = self.OPHelper.run_archive(repeats=1)
            time.sleep(10)
            self.OPHelper.verify_stub(path=self.origin_folder_path, is_nas_turbo_type=self.is_nas_turbo_type)
            time.sleep(10)
            self.runvatool(path, cpath, sid,"4")
            self.OPHelper.run_archive(repeats=1)
            self.runvatool(path, cpath, sid, "4")



            for job in job_list:
                self.log.info("Job Id to be deleted so data version is deleted from index: " + job.job_id)
                self.delete_job(job.job_id)
                time.sleep(10)
            #self.commcell.run_data_aging().wait_for_completion()
            time.sleep(200)
            #self.OPHelper.run_archive(repeats=1) This job prunes the stubs so do not run incr
            self.runvatool(path, cpath, sid, "[4/4] archived files were not protected in archive")



            self.log.info('Basic Acceptance tests for Vatool passed')
            self.log.info('Test case executed successfully.')
            self.status = constants.PASSED

        except Exception as exp:
            self.log.error('Basic Acceptance tests failed with error: %s', exp)
            self.result_string = str(exp)
            self.log.info('Test case failed')
            self.status = constants.FAILED
