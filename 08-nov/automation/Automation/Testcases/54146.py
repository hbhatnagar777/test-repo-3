# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

TestCase is the only class definied in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()          --  initialize TestCase class

    setup()             --  setup function of this test case

    run()               --  run function of this test case

    tear_down()         -- teardown function of this test case
"""

import os
import random
from AutomationUtils import constants
from AutomationUtils import idautils
from AutomationUtils.options_selector import CVEntities
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine
from MediaAgents.MAUtils.mahelper import CloudLibrary
from Server import serverhelper


class TestCase(CVTestCase):
    """Class for executing Storage accelerator operations"""

    def __init__(self):
        """Initializes TestCase object"""
        super(TestCase, self).__init__()
        self.name = "Storage accelerator acceptance"
        self.show_to_user = True
        self.tcinputs = {
            "mountpath": None,
            "loginname": None,
            "password": None,
            "server": None,
            "storageaccelerator": None

        }

    def setup(self):
        """Setup function of this test case"""
        storage_accelerator = self.tcinputs['storageaccelerator']
        self.accelerator_client = self.commcell.clients.get(storage_accelerator)
        self.accelerator_machine = Machine(self.accelerator_client)
        self.mediaagent = self.commcell.media_agents.get(self.client.client_name)
        self.mediaagent_machine = Machine(self.client)

    def validatelogs(
            self,
            client_machine,
            validatelog,
            logstrings_to_verify):
        '''
        checks the log for specified string.
        @args
            client_machine (Machine)      -- Client machine object
            validatelog (string)           -- full path of the log to validate
            logstrings_to_verify  (string) -- log string to verify

        '''
        if client_machine.check_file_exists(validatelog):
            qscript = "Select-String -Path {} -Pattern \"{}\"".format(
                validatelog.replace(" ", "' '"), logstrings_to_verify)
            self.log.info("Executing qscript [{0}]".format(qscript))
            response = client_machine.execute_command(qscript)
            return len(response.output.split(logstrings_to_verify))
        else:
            raise Exception("file {} not found".format(validatelog))

    def run(self):
        """Execution method for this test case"""
        try:
            self.log.info("Started executing {0} testcase".format(self.id))
            randomint = str(random.randint(100000, 9999999))
            logfile_to_check = ["cvd.log"]
            string_to_search = "The size of the chunk will"
            hp_library_name = "hp_library_{}".format(randomint)

            hp_libraries = []

            self.clenup_enties = {'storagepolicy': [], 'library': []}
            install_path = self.client.install_directory.split(os.path.sep)[0]
            if not install_path.endswith(os.path.sep):
                install_path += os.path.sep
            restore_location = self.accelerator_machine.join_path(install_path, "Automation_test",
                                                                  "Hp_restore")
            disk_mountpath = self.accelerator_machine.join_path(install_path, "Automation_test")
            disklibraries = self.commcell.disk_libraries
            server = serverhelper.ServerTestCases(self)
            server.rename_remove_logfile(
                self.accelerator_machine,
                logfile_to_check[0],
                templog_dictory="",
                substring='')
            server.rename_remove_logfile(
                self.mediaagent_machine,
                logfile_to_check[0],
                templog_dictory="",
                substring='')
            mountpath = self.tcinputs["mountpath"]
            values = {
                "mountPath": mountpath,
                "serverType": 59,
                "loginName": self.tcinputs["server"] + r"//" + self.tcinputs["loginname"],
                "password": self.tcinputs["password"]}
            library_obj = CloudLibrary(hp_library_name, values)

            if not disklibraries.has_library(library_obj.libraryname):
                library_obj.cloud_library_name = disklibraries.add(
                    library_obj.libraryname,
                    self.mediaagent,
                    library_obj.mountpath,
                    library_obj.loginname,
                    library_obj.secret_accesskey,
                    library_obj.servertype)
                self.log.info(
                    "Created cloud library {} for cloud type {} ".format(
                        library_obj.cloud_library_name, hp_library_name))
            else:
                library_obj.cloud_library_name = disklibraries.get(
                    library_obj.cloud_library_name)
                self.log.info(
                    "HP library {}  already exist ".format(
                        library_obj.cloud_library_name))

                self.clenup_enties["library"].append(library_obj.cloud_library_name.library_name)
                hp_libraries.append(library_obj.cloud_library_name)

            self.idautil = idautils.CommonUtils(self)
            self.entities = CVEntities(self)
            lib_first = library_obj.cloud_library_name.library_name

            all_props = self.entities.create({
                'target':
                    {
                        'client': self.accelerator_client.client_name,
                        'agent': "File system",
                        'instance': "defaultinstancename",
                        'mediaagent': self.mediaagent.media_agent_name,
                        'force': True
                    },
                'backupset': {},
                'subclient': {},
                'storagepolicy': {'library': lib_first}
            })

            self.log.info("Library name is {}".format(lib_first))

            self.subclient_content = all_props["subclient"]["content"][0]
            self.subclient = all_props['subclient']['object']
            for value in range(2):
                if value == 0:
                    option_type = "FULL"
                else:
                    option_type = "INCREMENTAL"

                validatelog = self.mediaagent_machine.join_path(
                    self.client.log_directory, logfile_to_check[0])
                mediacount_before = self.validatelogs(
                    self.mediaagent_machine,
                    validatelog, string_to_search)

                validatelog = self.accelerator_machine.join_path(
                    self.accelerator_client.log_directory, logfile_to_check[0])
                accelerator_before = self.validatelogs(
                    self.accelerator_machine, validatelog, string_to_search)

                self.idautil.subclient_backup(self.subclient, option_type, wait=True)
                validatelog = self.mediaagent_machine.join_path(
                    self.client.log_directory, logfile_to_check[0])
                mediacount_after = self.validatelogs(
                    self.mediaagent_machine,
                    validatelog, string_to_search)
                validatelog = self.accelerator_machine.join_path(
                    self.accelerator_client.log_directory, logfile_to_check[0])
                accelerator_after = self.validatelogs(
                    self.accelerator_machine, validatelog, string_to_search)
                self.accelerator_machine.generate_test_data(self.subclient_content, 1, 1)

                if mediacount_before < mediacount_after and accelerator_before < accelerator_after:
                    self.log.info("Validation is successful")
                    self.log.info("""mediacount_before {} , mediacount_after {}
                    accelerator_before{}, accelerator_after{}""".format(
                        str(mediacount_before),
                        str(mediacount_after),
                        str(accelerator_before),
                        str(accelerator_after)))
                else:
                    self.log.error("Validation failed")

                    self.log.error("""mediacount_before {} , mediacount_after {}
                    accelerator_before{}, accelerator_after{}""".format(
                        str(mediacount_before),
                        str(mediacount_after),
                        str(accelerator_before),
                        str(accelerator_after)))

            restore_job = self.idautil.subclient_restore_out_of_place(
                restore_location, [self.subclient_content], self.accelerator_client.client_name,
                self.subclient)
            restore_job.wait_for_completion()
            difference = self.accelerator_machine.compare_folders(
                self.accelerator_machine, self.subclient_content, restore_location)
            if difference:
                error = ("""difference in source content {} and
                     restored content {}and difference is {} """.format(
                         self.subclient_content, restore_location, difference))
                self.log.error(error)

            try:
                self.accelerator_machine.remove_directory(restore_location)
                self.accelerator_machine.remove_directory(disk_mountpath)
            except Exception as err:
                self._log.info(
                    "Failed to delete Destination dir {0}".format(err))

            self.log.info("Testcase execution completed")
        except Exception as exp:
            self.log.error('Failed with error:%s ' % str(exp))
            self.result_string = str(exp)
            self.status = constants.FAILED

    def tear_down(self):
        """Tear down function"""

        try:
            self.log.info("Running cleanup code")
            try:
                self.accelerator_machine.remove_directory(self.subclient_content)
            except Exception as err:
                self.log.info(
                    "Failed to delete subclient dir {0}".format(err))
            try:
                self.idautil.cleanup()
                self.entities.cleanup()
            except Exception as exep:
                self.log.info("Cleanup failed%s" % exep)
            CloudLibrary.cleanup_entities(self.commcell, self.log, self.clenup_enties)
        except Exception as err:
            self.log.info("failed to clean test case entities, exception {}".format(err))
