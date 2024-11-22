# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()                  --  initialize TestCase class

    setup()                     --  setup function of this test case

    run()                       --  run function of this test case

    run_backup()                --  runs a full backup for subclient

    trigger_export_schedule()   --  triggers the cloud grc export schedule

    trigger_import_schedule()   --  triggers the cloud grc import schedule

    transfer_export_files()     --  transfers the grc export dump to local directory

    transfer_import_files()     --  copies local directory to grc export directory

    verify_job_restore()        --  verifies the new job restore in global cell

Prerequisites before executing:

    - cloud GRC schedule must be created on Global and Pod cell manually
    - The exported entities must include a subclient on a non-default backupset under some client
    - The subclient must already have some job (so library mapping can be set)
    - The commcell library mapping properties must be set already
    - Do not keep the schedules to run frequently, this testcase forces the schedules to trigger and verifies migration

"""
from time import sleep

from AutomationUtils.cvtestcase import CVTestCase
from cvpysdk.commcell import Commcell
from AutomationUtils.machine import Machine


class TestCase(CVTestCase):
    """Class for executing this test case"""

    def __init__(self):
        """Initializes test case class object

            Properties to be initialized:

                name            (str)       --  name of this test case

                tcinputs        (dict)      --  test case inputs with input name as dict key
                                                and value as input type

                every object variable I will setup is initialized/declared here

        """
        super(TestCase, self).__init__()
        self.commcell_machine = None
        self.global_subclient = None
        self.user_helper = None
        self.import_schedule = None
        self.export_schedule = None
        self.pod_subclient = None
        self.podcell = None
        self.name = "Cloud GRC Export and Import"
        self.tcinputs = {
            "import_schedule_name": None,
            "export_schedule_name": None,
            "ImportCloudPath": None,
            "PodCS": {
                "HostName": None,
                "UserName": None,
                "Password": None,
                "ExportCloudPathUNC": None,
                "UNCUserName": None,
                "UNCPassword": None
            },
            "Monitored": {
                "ClientName": None,
                "AgentName": None,
                "BackupSetName": None,
                "SubclientName": None
            }
        }

    def setup(self):
        """Setup function of this test case"""
        self.tcinputs["PodCS"] = eval(self.tcinputs["PodCS"])
        self.tcinputs["Monitored"] = eval(self.tcinputs["Monitored"])
        self.podcell = Commcell(self.tcinputs["PodCS"]["HostName"],
                                self.tcinputs["PodCS"]["UserName"],
                                self.tcinputs["PodCS"]["Password"])
        self.pod_subclient = self.podcell.clients.get(self.tcinputs["Monitored"]["ClientName"]).agents \
            .get(self.tcinputs["Monitored"]["AgentName"]).backupsets \
            .get(self.tcinputs["Monitored"]["BackupSetName"]).subclients \
            .get(self.tcinputs["Monitored"]["SubclientName"])
        self.import_schedule = self.commcell.schedules.get(self.tcinputs["import_schedule_name"])
        self.export_schedule = self.podcell.schedules.get(self.tcinputs["export_schedule_name"])
        self.commcell_machine = Machine()

    def run(self):
        """Run function of this test case"""
        job_id = self.run_backup()
        sleep(30)
        self.trigger_export_schedule()
        self.transfer_export_files()
        self.trigger_import_schedule()
        self.transfer_import_files()
        self.commcell.refresh()
        self.podcell.refresh()
        self.verify_job_restore(job_id)

    def run_backup(self):
        """Triggers full backup job, waits for completion and returns job id"""
        self.log.info("Running backup on pod cell")
        job = self.pod_subclient.backup("Incremental")
        if not job.wait_for_completion():
            raise Exception("pod cell subclient backup job failed")
        self.log.info("Backup completed succesfully")
        return job.job_id

    def trigger_export_schedule(self):
        """Triggers the cloud grc export schedule on pod cell and waits for completion"""
        self.log.info("Triggering grc schedule")
        id = self.export_schedule.run_now()
        if not self.podcell.job_controller.get(id).wait_for_completion():
            raise Exception("cloud grc export job failed")
        self.log.info("cloud GRC export schedule successfully completed")

    def trigger_import_schedule(self):
        """Triggers the cloud grc import schedule on global cell and waits for completion"""
        self.log.info("Triggering grc schedule")
        id = self.import_schedule.run_now()
        if not self.commcell.job_controller.get(id).wait_for_completion():
            raise Exception("cloud grc import job failed")
        self.log.info("cloud GRC import schedule successfully completed")

    def transfer_export_files(self):
        """Transfers the cloud export directory files to import directory to simulate cloud"""
        src = self.tcinputs["PodCS"]["ExportCloudPathUNC"]
        dest = "\\".join(self.tcinputs["ImportCloudPath"].split("\\")[:-1])
        self.log.info(f"transfer from {src} to {dest}")
        self.commcell_machine.copy_from_network_share(
            src,
            dest,
            self.tcinputs["PodCS"]["UNCUserName"],
            self.tcinputs["PodCS"]["UNCPassword"],
            log_output=True
        )
        self.log.info(f"export files transfer successfully completed")

    def transfer_import_files(self):
        """Transfers the cloud import directory files to export directory to simulate cloud"""
        src = self.tcinputs["ImportCloudPath"]
        dest = "\\".join(self.tcinputs["PodCS"]["ExportCloudPathUNC"].split("\\")[:-1])
        self.log.info(f"transfer from {src} to {dest}")
        self.commcell_machine.copy_folder_to_network_share(
            src,
            dest,
            self.tcinputs["PodCS"]["UNCUserName"],
            self.tcinputs["PodCS"]["UNCPassword"],
            log_output=True
        )
        self.log.info(f"import files transfer successfully completed")

    def verify_job_restore(self, job_id):
        """Verifies the latest job is available """
        self.global_subclient = self.commcell.clients.get(self.tcinputs["Monitored"]["ClientName"]).agents \
            .get(self.tcinputs["Monitored"]["AgentName"]).backupsets \
            .get(self.tcinputs["Monitored"]["BackupSetName"]).subclients \
            .get(self.tcinputs["Monitored"]["SubclientName"])

        all_clients = self.commcell.clients.all_clients
        internal_client_name = [
            client for client in all_clients
            if all_clients[client]['displayName'] == self.tcinputs["Monitored"]["ClientName"]
        ][0]
        migrated_job = self.commcell.job_controller.all_jobs(internal_client_name)[int(job_id)]
        original_job = self.podcell.job_controller.all_jobs()[int(job_id)]
        del migrated_job['subclient_id']
        del original_job['subclient_id']

        if migrated_job != original_job:
            self.log.error("Job Stats Mismatched After Import")
            raise Exception("Destination Job does not Match Source Job")

        self.log.info("trying browse ...")
        self.global_subclient.browse(path=self.pod_subclient.content)
        self.log.info("browse is succesfull, now trying restore ...")

        temp_restore_path = f"{self.commcell_machine.tmp_dir}\\restore"

        self.commcell_machine.create_directory(temp_restore_path, True)
        job = self.global_subclient.restore_out_of_place(
            self.tcinputs["Monitored"]["ClientName"],
            temp_restore_path,
            self.pod_subclient.content,
            fs_options={'media_agent': self.commcell.commserv_name, "proxy_client": self.commcell.commserv_name}
        )
        if not job.wait_for_completion():
            raise Exception("restore job failed to complete")
        self.log.info("Restore completed successfully!")

        try:
            self.commcell_machine.remove_directory(temp_restore_path)
        except:
            self.log.error("failed to delete restore directory")
