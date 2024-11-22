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
    __init__()             --  Initialize TestCase class

    run()                  --  run function of this test case
"""
import datetime, time
from cvpysdk.schedules import Schedules
from cvpysdk.client import Client
from AutomationUtils import logger, constants
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.options_selector import OptionsSelector
from AutomationUtils.machine import Machine
from Server.Scheduler import schedulerhelper
from Server.JobManager.jobmanager_helper import JobManager

class TestCase(CVTestCase):
    '''
    Scenario 1: verify that OSC prescan schedule for install updates is triggering at correct interval time and updates
    are installed successfully on client or not.
        1: Check whether download updates job ran in 24 hrs
        2: Check whether install updates job triggered by schedule in 24 hrs.
        4: If job triggered, check the baseline status, if it is up-to-date or not.
        5. If baseline is up-to-date, check whether all the updates which are installed on CS for fs core package are
            installed on client oo or not.
        6. Turn on the second client and wait for the workqueue request to trigger install updates on the client and
            validate the updates installed.
        7  Finally turn off the second cleint again for the next run.
        '''

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "OSC Install Updates validation"
        self.applicable_os = self.os_list.MAC
        self.product = self.products_list.FILESYSTEM
        self.feature = self.features_list.DATAPROTECTION
        self._entities = None
        self.runid = None
        self._schedule_creator = None
        self._utility = OptionsSelector(self._commcell)
        self.slash_format = None
        self.show_to_user = False

    def validate_updates(self, client_id):
        '''Validates whether core package updates installed on CS are same as in client or not'''

        self.log.info("Get the update list installed on CS")

        query = 'select additionalpatches from simInstalledPackages where clientid=2 and simpackageId=1'

        data1, cur1 = self._utility.exec_commserv_query(query)
        self.log.info("Get the update list installed on Client")

        query = 'select additionalpatches from simInstalledPackages where clientid='+client_id+ ' and simpackageId=1'
        data2, cur2 = self._utility.exec_commserv_query(query)

        if not cur1 == cur2:
            raise Exception("There are some client updates needs to be installed {0}".format(cur1-cur2))
        else:
            self.log.info("all updates on cs are installed on client")

    def getbaselinestatus(self, client_id):
        ''' Gets the baseline status of the client'''

        self.log.info("Get the baseline status on client")

        query = 'select Baseline from simInstalledPackages where clientid='+client_id
        data, cur = self._utility.exec_commserv_query(query)
        if cur[0][0] == '1':
            self.log.info("Client is up-to-date")

        elif cur[0][0] == '2':
            raise Exception("Clients needs some updates")

        elif cur[0][0] == '3':
            raise Exception("Client is ahead of cache")
        else:
            raise Exception("Improper baseline status {0}".format(cur[0][0]))


    def run(self):
        """Main function for test case execution"""
        log = logger.get_log()
        client_name = self.tcinputs['ClientName']
        client_name2_host_name = self.tcinputs['ClientName2']
        client_name2_username = self.tcinputs['ClientName2_username']
        client_name2_password = self.tcinputs['ClientName2_password']
        client_id = self.client.client_id
        job_manager = JobManager(commcell=self.commcell)
        client2_obj = Machine(client_name2_host_name,
                              username=client_name2_username,
                              password=client_name2_password)
        client_object = Client(self.commcell, client_name2_host_name)
        install_directory = client_object.install_directory
        try:
            # Initialize test case inputs

            self.log.info("Started executing %s testcase", str(self.id))
            self.log.info("Check if latest download updates job ran in 24 hrs or not")

            schedule_obj = Schedules(self.commcell)

            sch_obj = schedule_obj.get(schedule_name="Downlaod Updates")
            _sch_helper_obj = schedulerhelper.SchedulerHelper(sch_obj, self.commcell)

            self.log.info("Get the latest download updates job id triggered by the task id")
            jobs_obj = _sch_helper_obj.check_job_for_taskid()
            download_job = jobs_obj[-1]
            #download_jobs = job_manager.get_filtered_jobs(client=None, lookup_time=48, job_filter="Download Updates")
            download_job_start_time = download_job.start_time
            download_job_start_time = datetime.datetime.strptime(download_job_start_time, "%Y-%m-%d %H:%M:%S")
            now = datetime.datetime.now()
            now_minus_26hrs = now - datetime.timedelta(hours=26)
            if download_job_start_time < now_minus_26hrs:
                raise Exception("download updates job didn't start from 26 hrs")

            self.getbaselinestatus(client_id)

            self.log.info("get the task id for the system created osc install updates schedule")

            schedule_obj = Schedules(self.commcell)
            sch_obj = schedule_obj.get(schedule_name="System Created Install Software for Laptops")
            _sch_helper_obj = schedulerhelper.SchedulerHelper(sch_obj, self.commcell)

            self.log.info("Get the latest install updates job id triggered by the task id")
            jobs_obj = _sch_helper_obj.check_job_for_taskid()
            job_obj = jobs_obj[-1]

            job_start_time = job_obj.start_time
            job_start_time = datetime.datetime.strptime(job_start_time, "%Y-%m-%d %H:%M:%S")
            now = datetime.datetime.now()
            now_minus_24hrs = now - datetime.timedelta(hours=24)

            if job_start_time < now_minus_24hrs:
                self.log.info("osc install updates job didn't start from 24 hrs")

                self.getbaselinestatus(client_id)

            log.info("Getting baseline status for the client")
            self.getbaselinestatus(client_id)

            self.validate_updates(client_id)

            self.log.info("Turn on the client to check if osc updates are getting installed after turning it on")

            command = "Gxadmin.exe -consoleMode -startsvcgrp ALL"
            stop_command = "Gxadmin.exe -consoleMode -stopsvcgrp ALL"
            client2_obj.execute_command(command)

            self._utility.sleep_time(300, "Wait for the workqueue o start install udpates on the client")
            jobs_obj = _sch_helper_obj.check_job_for_taskid()

            job_obj = jobs_obj[-1]

            job_start_time = job_obj.start_time
            job_start_time = datetime.datetime.strptime(job_start_time, "%Y-%m-%d %H:%M:%S")
            now = datetime.datetime.now()
            now_minus_5mins = now - datetime.timedelta(minutes=5)
            job_obj.wait_for_completion()

            if job_start_time < now_minus_5mins:
                self.log.info("osc install updates job didn't start after power on")

            self.getbaselinestatus(client_id)

            self.validate_updates(client_id)


            log.info("***TEST CASE COMPLETED SUCCESSFULLY AND PASSED***")
        except Exception as excp:
            log.error('Failed with error: %s', str(excp))
            self.result_string = str(excp)
            self.status = constants.FAILED

        finally:
            client2_obj.execute_command(stop_command)
