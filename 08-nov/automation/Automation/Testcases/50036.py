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

    run()           --  run function of this test case
"""

from AutomationUtils.cvtestcase import CVTestCase
from Server.serverhelper import ServerTestCases
from Server.DisasterRecovery import drhelper
from AutomationUtils.options_selector import CVEntities, OptionsSelector
from AutomationUtils.machine import Machine
from AutomationUtils import cvhelper
from cvpysdk.commcell import Commcell


class TestCase(CVTestCase):
    """Class for executing Staging of CS from remote location using CSRecovery Assistant"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Staging Production Database using CSRecoveryAssistant"

    def setup(self):
        """Setup function of this test case"""
        self._server_tc = ServerTestCases(self)
        self._entities = CVEntities(self)
        self._utility = OptionsSelector(self.commcell)

    def run(self):
        """Main function for test case execution"""

        try:

            self._server_tc.log_step(
                            """ 
                            Test Case
                            1) Recover Original Database before restore
                            2) Mount Network Path
                            3) Find the latest DR folder
                            4) Get the commserv Dump from the DR Folder
                            5) Copy the folder locally
                            6) Restore the Dump in staging mode
                            7) Perform some post staging operations
                            """, 200
                            )

            local_machine_obj = Machine()
            drhelper_object = drhelper.DRHelper()

            source_dr_path = self.tcinputs.get('source_dr_path', r"C:\DRStaging")
            external_group = self.tcinputs.get('external_group', r"commvault-nj\\commvault worldwide")
            local_group = self.tcinputs.get('local_group', r"master")

            self.log.info("Starting the Staging Process of Production Database")

            self.log.info("setting registry key nDoNotDetectDRRestore to skip updating sql password from prod DB")
            local_machine_obj.create_registry("Cvd", "nDoNotDetectDRRestore", 1, "DWord")

            self.log.info("Recovery of the original Database before starting the process")
            latest_set_folder = local_machine_obj.get_latest_timestamp_file_or_folder(self.tcinputs['local_dr_path'])

            drhelper_object.set_er_directory()

            drhelper_object.db_dumplocation = latest_set_folder
            drhelper_object.operation = 'Recovery'
            self.log.info("Precautionary stop of services because CS Migration Tool doesnt stop all services sometimes")
            drhelper_object.stopservices()
            self._utility.sleep_time(180)
            drhelper_object.restore_db_with_cvmigrationtool()
            drhelper_object.startservices()

            # Copy all the required dumps from the shared network path
            self.log.info("mounting the shared network path {0}".format(self.tcinputs['production_dr_path']))
            mounted_path = local_machine_obj.mount_network_path(self.tcinputs['production_dr_path'],
                                                                self.tcinputs.get('dr_path_username'),
                                                                self.tcinputs.get('dr_path_password'))

            self.log.info("Getting the latest DR folder in shared network path")

            latest_set_folder = drhelper_object.get_latest_folder_network_dr_path(mounted_path)
            if not latest_set_folder:
                raise Exception("There is no DR Folder with CS Dump present in the shared location")
            self.log.info("Latest DR folder drive path {0}".format(latest_set_folder))
            local_machine_obj.remove_directory(source_dr_path)
            local_machine_obj.create_directory(source_dr_path)
            commserv_dump = drhelper_object.get_cs_dump_in_path(latest_set_folder)
            self.log.info("copy DR dump '{0}' from network share to local path {1}".format(commserv_dump[0],
                                                                                           source_dr_path))
            local_machine_obj.copy_folder(commserv_dump[0], source_dr_path)
            self.log.info("dr dump copied successfully")

            # run full db restore in staging mode and start services
            self.log.info("Run Full DB restore with CS recovery tool in staging mode")
            commcellobj = Commcell(local_machine_obj.machine_name, self.tcinputs['test_cs_cvuname'],
                                   self.tcinputs['test_cs_cvpass'])

            # getting encrypted password from registry
            encrypted_pass = local_machine_obj.get_registry_value(r"Database", "pAccess")
            sql_password = cvhelper.format_string(commcellobj, encrypted_pass).split("_cv")[1]

            drhelper_object.set_er_directory()

            drhelper_object.db_dumplocation = source_dr_path
            drhelper_object.operation = 'Staging'
            drhelper_object.restore_db_with_cvmigrationtool()
            self.log.info(
                "Full DB restore is successful with CS recovery tool")

            # starting service
            self.log.info("Start services with DRrestore.exe")
            drhelper_object.startservices()
            self._utility.sleep_time(120)

            # update webconsole URL

            self.log.info("Updating the webconsoleURL to the current machine name")
            webconsole_query = (r"update GXGlobalParam set value = 'https://{0}/webconsole/' where name = " 
                                "'WebConsoleURL'". format(local_machine_obj.machine_name))
            drhelper_object.executecvquery(webconsole_query, "sqladmin_cv", sql_password)
            self.log.info("successfully updated webconsole URL")

            self.log.info("Restarting the services again to make sure Public Sharing user is updated")
            drhelper_object.stopservices()
            self._utility.sleep_time(180)
            drhelper_object.startservices()
            self._utility.sleep_time(200)

            drhelper_object.set_er_directory()

            commcellobj = Commcell(local_machine_obj.machine_name, 'admin', 'admin')
            commcellobj.user_groups.get(local_group).update_usergroup_members(request_type='UPDATE',
                                                                              external_usergroups=[external_group])
            self.log.info("Successfully updated usergroup {0} with the external group {1}".format(local_group,
                                                                                                  external_group))

            self.log.info("All Staging operations are completed, machine ready to use")

        except Exception as excp:
            self._server_tc.fail(excp)

        finally:
            self.log.info("cleaning up the entities")
            local_machine_obj.unmount_drive(mounted_path)
