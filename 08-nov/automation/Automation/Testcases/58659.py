# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Test Case for validating Download Software"

TestCase:   Class for executing this test case

TestCase:

    __init__()      --  initialize TestCase class

    setup()         --  setup the requirements for the test case

    run()           --  run function of this test case

"""
import inspect
import time

from cvpysdk.deployment.deploymentconstants import DownloadOptions
from cvpysdk.deployment.deploymentconstants import DownloadPackages
from cvpysdk.commcell import Commcell

from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.vmoperations import VmOperations
from AutomationUtils.machine import Machine
from AutomationUtils.options_selector import OptionsSelector
from Server.serverhelper import ServerTestCases
from Server.JobManager.jobmanager_helper import JobManager

class TestCase(CVTestCase):
    """Test case class for Download software validation for released Maintenance Releases"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = """Download Software validation for released Maintenance Releases"""
        self.show_to_user = False
        self.tcinputs = {
            'feature_releases': None,
            'vm_name': None,
            'hyperv_hostname': None,
            'hyperv_username': None,
            'hyperv_password': None,
            'report_db_server': None,
            'report_user': None,
            'report_password': None,
            'network_log_path': None,
            'network_user': None,
            'network_password': None
        }

    def run(self):
        for feature_release in list(self.tcinputs['feature_releases'].split(",")):
            self.download(feature_release)

    def commcell_object(self):
        _commcell = self.inputJSONnode['commcell']['webconsoleHostname']
        _user = self.inputJSONnode['commcell']['commcellUsername']
        _password = self.inputJSONnode['commcell']['commcellPassword']
        self.log.info("Creating commcell [{0}] object for username [{1}]".format(_commcell, _user))
        commcell = Commcell(_commcell, _user, _password)
        commcell.refresh()
        return commcell

    def sleep_time(self):
        # Sleep is important as the commcell object creation sometimes looses connection to CS
        # Making sure the CS is in sane state before going ahead.
        self.log.info("Sleeping for 3 minutes to gain sanity for the CS")
        time.sleep(180)

    def download(self, feature_release):
        """ Main function for test case execution."""
        try:
            self.log.info("************  Feature Release -- {0}".format(feature_release))
            inputs = {}
            inputs['server_host_name'] = self.tcinputs['hyperv_hostname']
            inputs['vm_name'] = self.tcinputs['vm_name']
            inputs['username'] = self.tcinputs['hyperv_username']
            inputs['password'] = self.tcinputs['hyperv_password']
            inputs['server_type'] = "HyperV"

            _cu = ""
            _cuoncloud = ""
            _custatus = ""
            _downloadstatus = ""
            _date = ""
            _timetaken = ""
            _downloaded_mediasize = ""
            _logs = ""

            # Revert VM snapshot to specific Feature Release
            inputs['snapshot_name'] = feature_release
            self.log.info("Reverting the vm {0} to snapshot {1}".format(inputs['vm_name'], inputs['snapshot_name']))
            vm_obj = VmOperations.create_vmoperations_object(inputs)
            # Sometimes VM fails to be reverted
            i = 1
            while i in range(0, 10):
                try:
                    vm_obj.revert_snapshot(inputs['vm_name'], inputs['snapshot_name'])
                    break
                except Exception as excp:
                    self.log.error(str(excp))
                    if i == 9:
                        raise Exception("Failed to revert snapshot")
                    i += 1

            self.sleep_time()

            # After reverting the snapshot have to refresh the commcell object
            commcell = self.commcell_object()
            try:
                self.log.info("Restarting commcell [{0}] services for refreshing CU details".format(commcell.commserv_name))
                commcell.commserv_client.restart_services()
            except Exception as excp:
                self.log.error("Commcell services restart failed")
                pass
            self.sleep_time()
            commcell = self.commcell_object()
            utility = OptionsSelector(commcell)
            self.commcell = commcell

            # Download Software
            options = DownloadOptions.LATEST_HOTFIXES.value
            os_list = [platform.value for platform in DownloadPackages]
            os_list.remove('Linux-S390')
            os_list.remove('Linux-S390-31')
            self.log.info("""Starting download software job for platforms
             {0}""".format(os_list))
            download_job = commcell.download_software(options=options, os_list=os_list)
            self.log.info("Download Software Job - %s", download_job.job_id)
            jm_object = JobManager(download_job, commcell)

            try:
                _ = jm_object.wait_for_state(retry_interval=240, time_limit=90)

                # Get download job details
                _downloadstatus = download_job.status
                job_summary = download_job._get_job_details()
                _downloaded_mediasize = job_summary['jobDetail']['detailInfo']['numOfObjects']
                self.log.info("Total files downloaded : [{0}]".format(_downloaded_mediasize))

                endtime = job_summary['jobDetail']['detailInfo']['endTime']
                starttime = job_summary['jobDetail']['detailInfo']['startTime']
                _timetaken = str((endtime - starttime)/(60)).split(".")[0]
                _timetaken = str(_timetaken) + 'min'
                self.log.info("Time taken by Download job: [{0}]".format(_timetaken))

                cu_query = r"""select u.upnumber from patchmulticache m join patchspversion v on m.spversionid=v.id
                                join patchcacheupdatepackmap pcpm on pcpm.cacheId=m.id
                                join patchupversion u on pcpm.updatepackid = u.upversionid
                                where m.clientid=2 and m.OSId = 1"""
                _cu = 'CU' + str(utility.update_commserve_db(cu_query).rows[0][0])
                self.log.info("CU Downloaded: [{0}]".format(_cu))

            except Exception as excp:
                # In case download fails. Add soft error as the logs should still be copied
                # and db also should be updated with status.
                self.log.error("Download Software failed. {0}".format(str(excp)))
                _downloadstatus = "Failed"

            # Copy DownloadSoftware logs to a network location
            _logs = self.copy_client_logs(Machine(commcell.commserv_name, commcell), commcell, feature_release)

            # Validation
            # Get the latest CU available on cloud and Get the CU downloaded on the Server and compare.

            # Gather CU Pack Downloaded Details and write Download Status to DB Tables
            self.update_db(feature_release, _cu, _cuoncloud, _custatus, _downloadstatus,
                           download_job.start_time, _timetaken, _downloaded_mediasize, _logs)

        except Exception as excp:
            ServerTestCases(self).fail(excp)
            self.log.error("Testcase failed with exception [{0}]".format(str(excp)))
            self.update_db(feature_release, _cu, _cuoncloud, _custatus, _downloadstatus,
                           download_job.start_time, _timetaken, _downloaded_mediasize, _logs)

    def update_db(self, feature_release, cupack, cuoncloud, custatus, downloadstatus,
                  start_time, timetaken, downloaded_mediasize, logs):
        """ Updates AkamaiDownloadStatus Table on the reporting db server

         Args:
                feature_release         (str): Feature Release
                cupack                  (str): cu pack
                cuoncloud               (str): cu pack on cloud
                custatus                (str): cu validation status
                downloadstatus          (str): download job status
                start_time              (str): download job start time
                timetaken               (str): download job time taken
                downloaded_mediasize    (str): download job files downloaded
                logs                    (str): Logs

        """
        self.log.info("Updating AkamaiDownloadStatus Table on [{0}]".format(self.tcinputs['report_db_server']))
        _downloadstatus = "Failed" if not downloadstatus else downloadstatus
        db_query = r"""INSERT INTO AkamaiDownloadStatus values
                        ('{0}', '{1}', '{2}', '{3}', '{4}', '{5}', '{6}', '{7}', '{8}')
                        """.format(feature_release, cupack, cuoncloud, custatus, downloadstatus,
                                   start_time, timetaken, downloaded_mediasize, logs)
        self.log.info("""Executing query
        {0}""".format(db_query))
        db_commcell = Commcell(
            self.tcinputs['report_db_server'], self.tcinputs['report_user'], self.tcinputs['report_password']
        )
        db_utility = OptionsSelector(db_commcell)
        db_utility.update_commserve_db(db_query)


    def copy_client_logs(self, machine_object, commcell, feature_release):
        """ Copy client logs to a network path

         Args:
                machine_object  (object):                       Client object for Machine class

                commcell (object):                              Commcell object

                feature_release:                                Feature Release

        Returns: log location
            False: If failed to copy logs.

        Raises: Exception:
            - If exceptions out while performing any operation.

        """
        try:
            os_sep = machine_object.os_sep
            os_info = machine_object.os_info
            client = machine_object.machine_name

            network_path = self.tcinputs['network_log_path']
            username = self.tcinputs['network_user']
            password = self.tcinputs['network_password']

            # Create destination location first.
            drive = machine_object.mount_network_path(network_path, username, password)
            custom_string = OptionsSelector.get_custom_str()
            dest_path = os_sep.join([drive + ":", feature_release, custom_string])

            utility = OptionsSelector(commcell)
            utility.create_directory(machine_object, dest_path)

            if machine_object.os_info == 'WINDOWS':
                install_dir = utility.check_reg_key(machine_object, 'Base', 'dGALAXYHOME')
                if not install_dir:
                    self.log.error("Failed to get installation directory for client [{0}]".format(client))
                    self.log.error("Failed to copy logs for client [{0}]".format(client))
                    return False
                source_dir = os_sep.join([install_dir, "Log Files"])

            self.log.info("Copying logs from client [{0}]. From [{1}] to [{2}]".format(client, source_dir, dest_path))
            machine_object.copy_folder(source_dir, dest_path)

            return os_sep.join([network_path, self.id, os_info, custom_string])

        except Exception as excp:
            raise Exception("\n [{0}] [{1}]".format(inspect.stack()[0][3], str(excp)))
        finally:
            machine_object.unmount_drive(drive)
