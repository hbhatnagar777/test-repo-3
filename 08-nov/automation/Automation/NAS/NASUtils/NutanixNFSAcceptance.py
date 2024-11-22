# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Helper file that executes the  Intellisnap basic acceptance test cases for nas client

Intellisnap BasicAcceptance is the only class defined in this file

This class include below cases:
•	Full snap backup with skip catalog
•	Add data and run Inc snap backup with skip catalog
•	Add data and run Diff snap backup with skip catalog
•	Add data and run Full snap backup with skip catalog
•	Add data and run Inc snap backup with skip catalog
•	Add data and run Diff snap backup with skip catalog
•	Mount snap & validate
•	Unmount snap & validate
•	Restore to unix proxy and validate
•	Inplace restore and validate
•	Backup copy
•	Restore to unix proxy from backupcopy and validate
•	Inplace restore from backupcopy and validate



BasicAcceptance:
     run()                   --  runs the basic acceptance test case
"""

from time import sleep
from AutomationUtils.machine import Machine
from AutomationUtils.options_selector import OptionsSelector
from NAS.NASUtils.snapbasicacceptance import SnapBasicAcceptance
from datetime import datetime


class NutanixNFSAcceptance(SnapBasicAcceptance):
    """Helper class to run Intellisnap basic acceptance test case for nas client"""

    def add_content(self):
        if not self.automount:
            for content in self.sccontent:
                self._nas_helper.copy_test_data_to_proxy(self.proxy, content)
        else:
            for content in self.sccontent:
                mountpoint = self._inputs["mount_path"]
                temp = content.split(":")
                self._log.info(temp)
                server = temp[0]
                share = temp[1]
                self.proxy.mount_nfs_share(
                    mountpoint, server, share, cleanup=True, version=None
                )
                self._log.info("Mounting done")
                self._nas_helper.copy_test_data_to_proxy(self.proxy, mountpoint)

    def generate_dest_path(self, linux_restore_location):
        if self.automount:
            mountpoint = self._inputs["mount_path"]
            temp = self._subclient.content[0].split(":")
            self._log.info(temp)
            server = temp[0]
            share = temp[1]
            self.proxy.mount_nfs_share(
                mountpoint, server, share, cleanup=True, version=None
            )
            self.sccontent[0] = mountpoint
            temp1 = self.restorecontent[0].split("/")
            destination_path = linux_restore_location + "/" + temp1[-1]
            self._log.info(f"Configured Destination path {destination_path}")
        else:
            destination_path = linux_restore_location + self.sccontent[0]
        return destination_path

    def get_restore_client(self, client_machine, size=5120):
        """Returns the instance of the Machine class for the given client,
                and the directory path to restore the contents at.


        Args:
            client_machine      (object)     --- name of the client on which is used for restore
            size    (int)   --  minimum available free space required on restore machine



        Returns:
            (object, str)   -   (instance of the Machine class, the restore directory path)

                object  -   instance of the Machine class for the Windows client

                str     -   directory path to restore the contents at
        """

        restore_client = Machine(self._commcell.clients.get(client_machine))
        self._log.info(f"Restore client selected is {restore_client.machine_name}")

        drive = self.options_selector.get_drive(restore_client, size)

        current_time = datetime.strftime(datetime.now(), "%Y-%m-%d_%H-%M-%S")

        restore_path = f"{drive}CVAutomationRestore-{current_time}"

        restore_client.create_directory(restore_path)
        self._log.info(f"Restore location is {restore_path}")

        return restore_client, restore_path

    def run(self):
        """Executes Intellisnap basic acceptance test case"""
        self._log.info(
            "Will run below test case on: %s subclient",
            format(str(self._inputs["SubclientName"])),
        )
        self._log.info("Number of data readers: " + str(self._subclient.data_readers))
        if self._subclient.data_readers != 3:
            self._log.info("Setting the data readers count to 3")
            self._subclient.data_readers = 3
        self._log.info("Get NAS Client object")
        self.nas_client = self._nas_helper.get_nas_client(
            self._client, self._agent, is_cluster=self._is_cluster
        )
        self.proxy = Machine(self._inputs["ProxyClient"], self._commcell)
        self.sccontent = self._inputs["SubclientContent"].split(",")
        ignore_files = self._nas_helper.ignore_files_list
        ignore_folder = self._nas_helper.ignore_files_list

        if self.sccontent[0][0] != "/":
            self._log.info("This subclient supports Auto-mount")
            self.automount = True
        self.add_content()
        job = self._run_backup("FULL")
        self.add_content()
        job = self._run_backup("INCREMENTAL")
        self.add_content()
        job = self._run_backup("FULL")
        self.add_content()
        job = self._run_backup("INCREMENTAL")
        self.snapjob = job
        if self._inputs.get("mount_path"):
            self.mount_path = self._inputs["mount_path"]

        self._log.info(
            "*" * 10 + " Run out of place restore to Linux Client" + "*" * 10
        )
        if self._inputs.get("RestoreClient"):
            linux_restore_client, linux_restore_location = self.get_restore_client(
                self._inputs.get("RestoreClient")
            )
        else:
            (
                linux_restore_client,
                linux_restore_location,
            ) = self.options_selector.get_linux_restore_client()
        if self.automount:
            path2 = []
            for i in range(len(self.sccontent)):
                path1 = self.sccontent[i].split(":")
                temp2 = "/" + path1[0] + path1[1]
                path2.append(temp2)
            self.restorecontent = path2
        else:
            self.restorecontent = self.sccontent
        job = self._subclient.restore_out_of_place(
            linux_restore_client.machine_name,
            linux_restore_location,
            self.restorecontent,
            restore_data_and_acl=False,
        )
        self._log.info(
            "Started restore out of place to linux client job with Job ID: "
            + str(job.job_id)
        )

        if not job.wait_for_completion():
            raise Exception(
                "Failed to run restore out of place job with error: "
                + str(job.delay_reason)
            )

        self._log.info("Successfully finished Restore out of place to linux client")
        destination_path = self.generate_dest_path(linux_restore_location)
        out = linux_restore_client.compare_folders(
            linux_restore_client,
            self.sccontent[0],
            destination_path,
            ignore_files,
            ignore_folder,
        )
        if out:
            self._log.error(
                "Restore validation failed. List of different files \n%s",
                format(str(out)),
            )
            raise Exception(
                "Restore validation failed. Please check logs for more details."
            )

        self._log.info("Successfully validated restored content")
        sleep(200)
        self._log.info("*" * 10 + " Run Restore in place " + "*" * 10)
        job = self._subclient.restore_in_place(
            self.restorecontent, proxy_client=self.proxy.machine_name
        )

        self._log.info(
            "Started restore in place job with Job ID: %s", format(str(job.job_id))
        )
        if not job.wait_for_completion():
            raise Exception(
                "Failed to run restore in place job with error: {0}".format(
                    job.delay_reason
                )
            )
        self._log.info("Successfully finished restore in place job")
        out = linux_restore_client.compare_folders(
            linux_restore_client,
            destination_path,
            self.sccontent[0],
            ignore_files,
            ignore_folder,
        )
        if out:
            self._log.error(
                "Restore validation failed. List of different files \n%s",
                format(str(out)),
            )
            raise Exception(
                "Restore validation failed. Please check logs for more details."
            )

        self._log.info("Successfully validated restored content")

        backup_copy_name = self.execute_query(self.get_backup_copy, self._storage_policy.storage_policy_id)
        sleep(200)

        self._log.info("*" * 10 + "Running backup copy now" + "*" * 10)

        job = self._storage_policy.run_backup_copy()
        self._log.info("Backup copy workflow job id is : %s", format(job.job_id))
        if not job.wait_for_completion():
            raise Exception(
                "Failed to run backup copy job with error: " + str(job.delay_reason)
            )
        self._log.info(
            "Successfully finished backup copy workflow Job :%s", format(job.job_id)
        )

        if job.status != "Completed":
            raise Exception(
                "job: {0} for Backup copy operation is completed with errors, \
                    Reason: {1}".format(
                    job.job_id, job.delay_reason
                )
            )

        self._log.info("*" * 10 + "Run out of place restore from backupcopy" + "*" * 10)
        copy_precedence = self._get_copy_precedence(
            self._subclient.storage_policy, backup_copy_name
        )
        if self._inputs.get("RestoreClient"):
            linux_restore_client, linux_restore_location = self.get_restore_client(
                self._inputs.get("RestoreClient")
            )
        else:
            (
                linux_restore_client,
                linux_restore_location,
            ) = self.options_selector.get_linux_restore_client()
        job = self._subclient.restore_out_of_place(
            linux_restore_client.machine_name,
            linux_restore_location,
            self.restorecontent,
            restore_data_and_acl=False,
            copy_precedence=int(copy_precedence),
        )

        self._log.info("Started Restore out of place job with Job ID: %d", job.job_id)
        if not job.wait_for_completion():
            raise Exception(
                "Failed to run restore out of place job with error: {0}".format(
                    job.delay_reason
                )
            )
        self._log.info("Successfully finished Restore out of place from backup copy")
        destination_path = self.generate_dest_path(linux_restore_location)
        out = linux_restore_client.compare_folders(
            linux_restore_client,
            self.sccontent[0],
            destination_path,
            ignore_files,
            ignore_folder,
        )
        if out:
            self._log.error(
                "Restore validation failed. List of different files \n%s",
                format(str(out)),
            )
            raise Exception(
                "Restore validation failed. Please check logs for more details."
            )

        self._log.info("Successfully validated restored content")

        sleep(200)

        self._log.info(
            "*" * 10 + " Run Restore in place restore from backup copy " + "*" * 10
        )
        job = self._subclient.restore_in_place(
            self.restorecontent,
            copy_precedence=int(copy_precedence),
            proxy_client=self.proxy.machine_name,
        )

        self._log.info(
            "Started restore in place job with Job ID: %s", format(str(job.job_id))
        )
        if not job.wait_for_completion():
            raise Exception(
                "Failed to run restore in place job with error: {0}".format(
                    job.delay_reason
                )
            )
        self._log.info("Successfully finished restore in place job from backup copy")
        out = linux_restore_client.compare_folders(
            linux_restore_client,
            destination_path,
            self.sccontent[0],
            ignore_files,
            ignore_folder,
        )
        if out:
            self._log.error(
                "Restore validation failed. List of different files \n%s",
                format(str(out)),
            )
            raise Exception(
                "Restore validation failed. Please check logs for more details."
            )

        self._log.info("Successfully validated restored content")

        snap_copy_name = self.execute_query(self.get_snap_copy, self._storage_policy.storage_policy_id)
        copy_precedence = self._get_copy_precedence(
            self._subclient.storage_policy, snap_copy_name
        )
        if self._inputs.get("RestoreClient"):
            linux_restore_client, linux_restore_location = self.get_restore_client(
                self._inputs.get("RestoreClient")
            )
        else:
            (
                linux_restore_client,
                linux_restore_location,
            ) = self.options_selector.get_linux_restore_client()

        sleep(200)

        job = self._subclient.restore_out_of_place(
            linux_restore_client.machine_name,
            linux_restore_location,
            self.restorecontent,
            restore_data_and_acl=False,
            copy_precedence=int(copy_precedence),
        )
        self._log.info("Started Restore out of place job with Job ID: %d", job.job_id)
        if not job.wait_for_completion():
            raise Exception(
                "Failed to run restore out of place job with error:{0}".format(
                    job.delay_reason
                )
            )
        self._log.info(
            "Successfully finished Restore out of place from deferred catalog"
        )
        destination_path = self.generate_dest_path(linux_restore_location)
        out = linux_restore_client.compare_folders(
            linux_restore_client,
            self.sccontent[0],
            destination_path,
            ignore_files,
            ignore_folder,
        )
        if out:
            self._log.error(
                "Restore validation failed. List of different files \n%s",
                format(str(out)),
            )
            raise Exception(
                "Restore validation failed. Please check logs for more details."
            )
        self._log.info("Successfully validated restored content")


        # Validating Snapshot content by comparing with subclient content
        self._log.info("Running snap operations")
        self.mount_snap(job.job_id, snap_copy_name, self.proxy.machine_name)
        query = f"SELECT MountPath FROM SMVolume WHERE JobId = {job.job_id}"
        self._csdb.execute(query)
        rest_loc = self._csdb.fetch_all_rows()[0]
        if self._inputs.get("RestoreClient"):
            linux_restore_client, linux_restore_location = self.get_restore_client(
                self._inputs.get("RestoreClient")
            )
        else:
            (
                linux_restore_client,
                linux_restore_location,
            ) = self.options_selector.get_linux_restore_client()

        out = linux_restore_client.compare_folders(
            linux_restore_client,
            self.sccontent[0],
            rest_loc,
            ignore_files,
            ignore_folder,
        )
        if out:
            self._log.error(
                "Restore validation failed. List of different files \n%s",
                format(str(out)),
            )
            raise Exception(
                "Restore validation failed. Please check logs for more details."
            )
        self._log.info("Successfully validated restored content")
