# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# ---------------------------------------------------------------------------

"""Helper file for performing update operations

UpdateHelper: Helper class to perform Update operations

UpdateHelper:

    check_job_status()              --  Checks for job status

    download_software()             --  Downloads the packages on the commcell

    push_sp_upgrade()               --  Performs push Service Pack upgrade of clients

    push_maintenance_release()      --  Performs push maintenance release upgrade of clients

    commserv_dbupgrade()            --  Performs DBUpgrade with repair on a Windows / Unix Commserver

UnixUpdateHelper:

    check_job_status()              --  Checks for job status

    download_software()             --  Downloads the packages on the commcell

    push_sp_upgrade()               --  Performs push Service Pack upgrade of clients

    push_maintenance_release()      --  Performs push maintenance release upgrade of clients

    commserv_dbupgrade()            --  Performs DBUpgrade with repair on a Unix Commserver

WindowsUpdateHelper:

    check_job_status()              --  Checks for job status

    download_software()             --  Downloads the packages on the commcell

    push_sp_upgrade()               --  Performs push Service Pack upgrade of clients

    push_maintenance_release()      --  Performs push maintenance release upgrade of clients

    commserv_dbupgrade()            --  Performs DBUpgrade with repair on a Windows Commserver

"""
import time
import requests.exceptions
from cvpysdk.deployment.deploymentconstants import DownloadPackages, DownloadOptions
from AutomationUtils import logger


class UpdateHelper:
    """Helper class to perform  install operations"""

    def __new__(cls, commcell, machine_obj=None):
        """
        Returns the respective class object based on the platform OS

        Args:
           commcell   -- commcell object

           machine_obj -- machine object

        Returns (obj) -- Return the class object based on the OS

        """
        if cls is not __class__ or machine_obj is None:
            return super().__new__(cls)

        if 'windows' in machine_obj.os_info.lower():
            return object.__new__(WindowsUpdateHelper)

        elif 'unix' in machine_obj.os_info.lower():
            return object.__new__(UnixUpdateHelper)

    def __init__(self, commcell=None, machine_obj=None):
        """
        constructor for update related files
        """
        self.log = logger.get_log()
        self.commcell = commcell
        self.client_machine_obj = machine_obj

    def check_job_status(self, job_object=None, wait_time=30):
        """
        checks for job status

        Args:
            job_object  (object)    -- Object of Job class

            wait_time  (int)        -- Minutes after which the job should be killed and exited,
                                       if the job has been in Pending / Waiting state

        Returns:
            None

        Raises:
            Exception

            if communication services are down after a threshold time

        """
        self.log.info("Job {0} started will wait {1} minutes "
                      "before job is killed.".format(job_object.job_id, wait_time))
        summary = job_object.summary
        try:
            result = job_object.wait_for_completion(wait_time)
        except requests.exceptions.ConnectionError:
            # Handling case were CS is patching
            if summary["destinationClient"]['clientId'] == 2 and summary["opType"] == 35:
                if 'windows' in self.client_machine_obj.os_info.lower():
                    if not self.client_machine_obj.wait_for_process_to_exit('Setup', 10800, 300):
                        raise Exception("Upgrade didn't complete within the specified time limit")
                else:
                    if not self.client_machine_obj.wait_for_process_to_exit('newinstall', 7200, 180):
                        raise Exception("Upgrade didn't complete within the specified time limit")
                time.sleep(120)
            result = job_object.wait_for_completion(wait_time)

        if result:
            if job_object.status.lower() in ["completed w/ one or more errors", "completed w/ one or more warnings"]:
                self.log.error("Job {0} Completed with one or more errors/warnings".format(job_object.job_id))
                return False
            elif job_object.status.lower() == "completed":
                self.log.info("Job {0} Completed successfully".format(job_object.job_id))
                return True
            else:
                self.log.info("Job {0} Failed".format(job_object.job_id))
                return False
        else:
            self.log.info("Job {0} Failed".format(job_object.job_id))
            return False

    def download_software(
                self,
                options=None,
                os_list=None,
                service_pack=None,
                cu_number=0,
                sync_cache=True,
                **kwargs):
        """Downloads the packages on the commcell

            Args:

                options      (enum)            --  Download option to download software

                os_list      (list of enum)    --  list of windows/unix packages to be downloaded

                service_pack (int)             --  service pack to be downloaded

                cu_number (int)                --  maintenance release number

                sync_cache (bool)              --  True if download and sync
                                                   False only download

            Returns:
                object - instance of the Job class for this download job

            Raises:
                SDKException:
                    if Download job failed

                    if response is empty

                    if response is not success

                    if another download job is running

            Usage:

            -   if download_software is not given any parameters it takes default value of latest
                service pack for options and downloads WINDOWS_64 package for WindowsCS and Linux X86_64 for linuxCS

                # >>> commcell_obj.download_software()

            -   DownloadOptions and DownloadPackages enum is used for providing input to the
                download software method, it can be imported by

                # >>> from cvpysdk.deployment.deploymentconstants import DownloadOptions
                    from cvpysdk.deployment.deploymentconstants import DownloadPackages

            -   Sample method calls for different options, for latest service pack

                # >>> commcell_obj.download_software(
                        options=DownloadOptions.LATEST_SERVICEPACK.value,
                        os_list=[DownloadPackages.WINDOWS_64.value]
                        )

            -   For Latest hotfixes for the installed service pack

                # >>> commcell_obj.download_software(
                        options='DownloadOptions.LATEST_HOTFIXES.value',
                        os_list=[DownloadPackages.WINDOWS_64.value,
                                DownloadPackages.UNIX_LINUX64.value]
                        )

            -   For service pack and hotfixes

                # >>> commcell_obj.download_software(
                        options='DownloadOptions.SERVICEPACK_AND_HOTFIXES.value',
                        os_list=[DownloadPackages.UNIX_MAC.value],
                        service_pack=13
                        )

                    **NOTE:** service_pack parameter must be specified for third option

        """

        if os_list is None:
            if self.commcell.is_linux_commserv():
                os_list = [DownloadPackages.UNIX_LINUX64.value]
            else:
                os_list = [DownloadPackages.WINDOWS_64.value]

        return self.commcell.download_software(
            options=options,
            os_list=os_list,
            service_pack=service_pack,
            cu_number=cu_number,
            sync_cache=sync_cache,
            schedule_pattern=None,
            **kwargs
        )

    def push_sp_upgrade(
            self,
            client_computers=None,
            client_computer_groups=None,
            all_client_computers=False,
            all_client_computer_groups=False,
            reboot_client=False,
            run_db_maintenance=False,
            download_software=False):
        """
        Performs push Service Pack upgrade of clients

            Args:
                client_computers (list)               -- Client machines to install service pack on

                client_computer_groups (list)         -- Client groups to install service pack on

                all_client_computers (bool)           -- boolean to specify whether to install on all client
                                                         computers or not

                all_client_computer_groups (bool)     -- boolean to specify whether to install on all client
                                                         computer groups or not

                reboot_client (bool)                  -- boolean to specify whether to reboot the client or not

                run_db_maintenance (bool)             -- boolean to specify whether to run db maintenance not

                download_software (bool)              -- whether to initiate a download software job before upgrade

            Returns:
                object - instance of the Job class for this download job

            Raises:
                SDKException:
                    if Download job failed

                    if response is empty

                    if response is not success

        """
        raise NotImplementedError("Module not implemented for the class")

    def push_maintenance_release(
            self,
            client_computers=None,
            client_computer_groups=None,
            all_client_computers=False,
            all_client_computer_groups=False,
            download_software=False):
        """
        Performs push maintenance release upgrade of clients

            Args:
                client_computers (list)               -- Client machines to install service pack on

                client_computer_groups (list)         -- Client groups to install service pack on

                all_client_computers (bool)           -- boolean to specify whether to install on all client
                                                         computers or not

                all_client_computer_groups (bool)     -- boolean to specify whether to install on all client
                                                         computers or not

                download_software (bool)              -- whether to initiate a download software job before upgrade

            Returns:
                object - instance of the Job class for this upgrade job

            Raises:
                SDKException:
                    if Upgrade job failed

                    if response is empty

                    if response is not success

        """
        raise NotImplementedError("Module not implemented for the class")
    
    def commserv_dbupgrade(self, machine_object, installation_path, logs_path):
        """
        Performs DBUpgrade with repair on a Windows / Unix Commserver.

        Args:
            machine_object (object): Machine object representing the Commserver
            installation_path (str): Installation path of the Commvault software
            logs_path (str): Path to store the logs of DBUpgrade

        Raises:
            Exception: If DBUpgrade validation fails

        """
        raise NotImplementedError("Module not implemented for the class")


class UnixUpdateHelper(UpdateHelper):
    """Helper class to perform Unix update operations"""

    def __init__(self, commcell, machine_obj):
        """
        Initialises the UnixUpdateHelper class

        Args:

            commcell   -- commcell object

            machine_obj -- machine object
        """
        super(UnixUpdateHelper, self).__init__(commcell, machine_obj)

    def push_sp_upgrade(
            self,
            client_computers=None,
            client_computer_groups=None,
            all_client_computers=False,
            all_client_computer_groups=False,
            reboot_client=False,
            run_db_maintenance=False,
            download_software=False,
            all_updates=False):
        """
        Performs push Service Pack upgrade of clients

            Args:
                client_computers (list)               -- Client machines to install service pack on

                client_computer_groups (list)         -- Client groups to install service pack on

                all_client_computers (bool)           -- boolean to specify whether to install on all client
                                                         computers or not

                all_client_computer_groups (bool)     -- boolean to specify whether to install on all client computer
                                                         groups or not

                reboot_client (bool)                  -- boolean to specify whether to reboot the client or not

                run_db_maintenance (bool)             -- boolean to specify whether to run db maintenance not

                download_software (bool)              -- whether to initiate a download software job before upgrade

                all_updates (bool)                    -- whether to initiate a download software job for all OS flavours

            Returns:
                object - instance of the Job class for this download job

            Raises:
                SDKException:
                    if Download job failed

                    if response is empty

                    if response is not success

        """
        if download_software:
            self.log.info("Starting Download Software Job")
            if all_updates:
                os_list = [package.value for package in DownloadPackages]
            else:
                os_list = getattr(DownloadPackages, 'UNIX_LINUX64').value
            job_id = self.download_software(
                    options=getattr(DownloadOptions, 'LATEST_SERVICEPACK').value,
                    os_list=os_list,
                    sync_cache=True)

            self.check_job_status(job_object=job_id, wait_time=10)

        self.log.info("Starting Upgrade Software Job")
        job_id = self.commcell.push_servicepack_and_hotfix(
                    client_computers=client_computers,
                    client_computer_groups=client_computer_groups,
                    all_client_computers=all_client_computers,
                    all_client_computer_groups=all_client_computer_groups,
                    reboot_client=reboot_client,
                    run_db_maintenance=run_db_maintenance)

        if not self.check_job_status(job_id, wait_time=60):
            raise Exception(f'SP Upgrade of clients {client_computers} failed!!')

    def push_maintenance_release(
            self,
            client_computers=None,
            client_computer_groups=None,
            all_client_computers=False,
            all_client_computer_groups=False,
            download_software=False):
        """
        Performs push maintenance release upgrade of clients

            Args:
                client_computers (list)               -- Client machines to install service pack on

                client_computer_groups (list)         -- Client groups to install service pack on

                all_client_computers (bool)           -- boolean to specify whether to install on all client
                                                         computers or not

                all_client_computer_groups (bool)     -- boolean to specify whether to install on all client
                                                         computers or not

                download_software (bool)              -- whether to initiate a download software job before upgrade

            Returns:
                object - instance of the Job class for this upgrade job

            Raises:
                SDKException:
                    if Upgrade job failed

                    if response is empty

                    if response is not success

        """
        if download_software:
            self.log.info("Starting Download Software Job")
            job_id = self.download_software(
                    options=getattr(DownloadOptions, 'LATEST_HOTFIXES').value,
                    os_list=getattr(DownloadPackages, 'UNIX_LINUX64').value, sync_cache=True)

            self.check_job_status(job_object=job_id, wait_time=30)

        self.log.info("Starting Update Software Job")
        job_id = self.commcell.push_servicepack_and_hotfix(
                    client_computers=client_computers,
                    client_computer_groups=client_computer_groups,
                    all_client_computers=all_client_computers,
                    all_client_computer_groups=all_client_computer_groups,
                    reboot_client=False,
                    run_db_maintenance=False,
                    maintenance_release_only=True)

        if not self.check_job_status(job_id, wait_time=150):
            raise Exception(f'CU Upgrade of clients {client_computers} failed!!')
    
    def commserv_dbupgrade(self, machine_object, installation_path, logs_path):
        """
        Performs DBUpgrade with repair on a Unix Commserver.

        Args:
            machine_object (object): Machine object representing the Commserver
            installation_path (str): Installation path of the Commvault software
            logs_path (str): Path to store the logs of DBUpgrade

        Raises:
            Exception: If DBUpgrade validation fails

        """
        self.log.info(f"Stopping all services before performing upgrade with repair on Commserver {machine_object.machine_name}")
        machine_object.stop_all_cv_services()
        time.sleep(60)
        self.log.info(f"Starting DBUpgrade with repair on Commserver {machine_object.machine_name}") 
        base_path = machine_object.join_path(installation_path, 'Base')       
        upgrade_cmd = (
            f'./cvDBUpgradeWrapper -PhaseName All -ProductName All -instance Instance001 '
            f'-log "{logs_path}"  -repair -DoNotBackupDB -DBBackupDir "{base_path}/temp"'
        )
        
        repair_cmd = f"cd {base_path} && {upgrade_cmd}; echo $?"
        self.log.info(f"Command used for running DBUpgrade: {repair_cmd}")
        output = machine_object.execute_command(repair_cmd)
        try:
            cmd_output = int(output.output.strip())
        except ValueError:
            cmd_output = output.output

        if output.exit_code == 0 and (cmd_output in (0, 101)  or not cmd_output )and not output.exception:
            self.log.info(
                f"DBUpgrade of Client {machine_object.machine_name} successful with output: {output.output}. "
                f"Starting services and waiting for 1 minute."
            )
            try:
                counter = 0
                while counter <= 1:
                    self.log.info(f"Waiting for 2 minutes and starting services on Commserver {machine_object.machine_name}")
                    time.sleep(120)
                    machine_object.start_all_cv_services()
                    counter += 1
            except Exception as e:
                self.log.error(f"Failed to start services on Commserver {machine_object.machine_name} with error: {e}")
            time.sleep(120)
        else:
            self.log.error(
                f"DBUpgrade validation of Client {machine_object.machine_name} failed with error: {output.output}. "
                f"Exit code: {output.exit_code} : {cmd_output}"
                
            )
            
            raise Exception(
                f"DBUpgrade validation of Client {machine_object.machine_name} failed with error: {output.output}. "
                f"Exit code: {output.exit_code} : {cmd_output}"
            )


class WindowsUpdateHelper(UpdateHelper):
    """Helper class to perform Windows Update operations"""

    def __init__(self, commcell, machine_obj):
        """
        Initialises the WindowsUpdateHelper class

        Args:

            commcell   -- commcell object

            machine_obj -- machine object
        """
        super(WindowsUpdateHelper, self).__init__(commcell, machine_obj)

    def push_sp_upgrade(
            self,
            client_computers=None,
            client_computer_groups=None,
            all_client_computers=False,
            all_client_computer_groups=False,
            reboot_client=False,
            run_db_maintenance=False,
            download_software=False,
            all_updates=False):
        """
        Performs push Service Pack upgrade of clients

            Args:
                client_computers (list)               -- Client machines to install service pack on

                client_computer_groups (list)         -- Client groups to install service pack on

                all_client_computers (bool)           -- boolean to specify whether to install on all client
                                                         computers or not

                all_client_computer_groups (bool)     -- boolean to specify whether to install on all client
                                                         computers or not

                reboot_client (bool)                  -- boolean to specify whether to reboot the client or not

                run_db_maintenance (bool)             -- boolean to specify whether to run db maintenance not

                download_software (bool)              -- whether to initiate a download software job before upgrade

                all_updates (bool)                    -- whether to initiate a download software job for all OS flavours

            Returns:
                object - instance of the Job class for this download job

            Raises:
                SDKException:
                    if Download job failed

                    if response is empty

                    if response is not success

                    if another download job is already running

                """
        if download_software:
            self.log.info("Starting Download Software Job")
            self.log.info("Starting Download Software Job")
            if all_updates:
                os_list = [package.value for package in DownloadPackages]
            else:
                os_list = getattr(DownloadPackages, 'WINDOWS_64').value
            job_id = self.download_software(
                    options=getattr(DownloadOptions, 'LATEST_SERVICEPACK').value,
                    os_list=os_list, sync_cache=True)

            self.check_job_status(job_object=job_id, wait_time=30)

        self.log.info("Starting Upgrade Software Job")
        job_id = self.commcell.push_servicepack_and_hotfix(
                    client_computers=client_computers,
                    client_computer_groups=client_computer_groups,
                    all_client_computers=all_client_computers,
                    all_client_computer_groups=all_client_computer_groups,
                    reboot_client=reboot_client,
                    run_db_maintenance=run_db_maintenance)

        if not self.check_job_status(job_id, wait_time=60):
            raise Exception(f'SP Upgrade of clients {client_computers} failed!!')

    def push_maintenance_release(
            self,
            client_computers=None,
            client_computer_groups=None,
            all_client_computers=False,
            all_client_computer_groups=False,
            download_software=False):
        """
        Performs push maintenance release upgrade of clients

            Args:
                client_computers (list)               -- Client machines to install service pack on

                client_computer_groups (list)         -- Client groups to install service pack on

                all_client_computers (bool)           -- boolean to specify whether to install on all client
                                                         computers or not

                all_client_computer_groups (bool)     -- boolean to specify whether to install on all client
                                                         computers or not

                download_software (bool)              -- whether to initiate a download software job before upgrade

            Returns:
                object - instance of the Job class for this upgrade job

            Raises:
                SDKException:
                    if Upgrade job failed

                    if response is empty

                    if response is not success

                """
        if download_software:
            self.log.info("Starting Download Software Job")
            job_id = self.download_software(
                options=getattr(DownloadOptions, 'LATEST_HOTFIXES').value,
                os_list=getattr(DownloadPackages, 'WINDOWS_64').value, sync_cache=True)

            self.check_job_status(job_object=job_id, wait_time=30)

        self.log.info("Starting Update Software Job")
        job_id = self.commcell.push_servicepack_and_hotfix(
            client_computers=client_computers,
            client_computer_groups=client_computer_groups,
            all_client_computers=all_client_computers,
            all_client_computer_groups=all_client_computer_groups,
            reboot_client=False,
            run_db_maintenance=False,
            maintenance_release_only=True)

        if not self.check_job_status(job_id, wait_time=150):
            raise Exception(f'CU Upgrade of clients {client_computers} failed!!')

    def commserv_dbupgrade(self, machine_object, installation_path, logs_path):
        """
        Performs DBUpgrade with repair on a Windows Commserver.
        Args:
            machine_object (object): Machine object representing the Commserver
            installation_path (str): Installation path of the Commvault software
            logs_path (str): Path to store the logs of DBUpgrade
        Raises:
            Exception: If DBUpgrade validation fails
        """
        self.log.info(f"Stopping all services before performing upgrade with repair on Commserver {machine_object.machine_name}")
        machine_object.stop_all_cv_services()
        time.sleep(60)
        self.log.info(f"Starting DBUpgrade with repair on Commserver {machine_object.machine_name}")
        base_path = machine_object.join_path(installation_path, 'Base')
        repair_cmd = (
            f'cd "{base_path}"\n .\cvDBUpgradeWrapper.exe -PhaseName All -ProductName All -instance Instance001 '
            f'-log "{logs_path}" -repair -DoNotBackupDB -DBBackupDir "{base_path}\\temp"'
        )
        
        self.log.info(f"Command used for running DBUpgrade: {repair_cmd}")
        output = machine_object.execute_command(repair_cmd)
        try:
            cmd_output = int(output.output.strip())
        except ValueError:
            cmd_output = output.output
        if output.exit_code == 0 and (cmd_output in (0, 101)  or not cmd_output )and not output.exception:
            self.log.info(
                f"DBUpgrade of Client {machine_object.machine_name} successful with output: {output.output}. "
                f"Starting services and waiting for 1 minute."
            )
            try:
                counter = 0
                while counter <= 1:
                    self.log.info(f"Waiting for 2 minutes and starting services on Commserver {machine_object.machine_name}")
                    time.sleep(120)
                    machine_object.start_all_cv_services()
                    counter += 1
            except Exception as e:
                self.log.error(f"Failed to start services on Commserver {machine_object.machine_name} with error: {e}")
            time.sleep(120)
        else:
            self.log.error(
                f"DBUpgrade validation of Client {machine_object.machine_name} failed with error: {output.output} and exception {output.exception}"
                f"Exit code: {output.exit_code}"
            )
            raise Exception(
                f"DBUpgrade validation of Client {machine_object.machine_name} failed with error: {output.output}. "
                f"Exit code: {output.exit_code} : cmdoutput : {cmd_output}"
            )
