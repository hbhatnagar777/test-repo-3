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
"""
import os
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.mailer import Mailer
from AutomationUtils.machine import Machine
from AutomationUtils.idautils import CommonUtils
from AutomationUtils.options_selector import CVEntities, OptionsSelector
from Server import serverconstants
from Server import serverhelper
from Server.Scheduler import schedulerhelper



class TestCase(CVTestCase):
    """Class for executing Laptop server call statistics"""

    def __init__(self):
        """Initializes TestCase object"""
        super(TestCase, self).__init__()
        self.name = "Laptop server call statistics"
        self.product = self.products_list.LAPTOP
        self.show_to_user = True
        self.tcinputs = {
            "ClientName": None,
            "receiver": None,
        }
        self._schedule_creator = None
        self._utility = OptionsSelector(self._commcell)

    def setup(self):
        """Initializes pre-requisites for test case"""
        self.log.info("This Test case will verify backup call statistics")
        self._schedule_creator = schedulerhelper.ScheduleCreationHelper(self)

    def run(self):
        """Execution method for this test case"""
        try:
            self.log.info("Started executing %s testcase", str(self.id))
            logfile_to_check = ["ApplicationMgr.log"]
            templog_dictory = "C:\\Application_MGR_logs"
            receiver = self.tcinputs['receiver']
            loglines_with_required_calls = []
            #
            server = serverhelper.ServerTestCases(self)
            client_machine = Machine(self.tcinputs['ClientName'], self._commcell)
            headers = {}
            string_to_check = {}
            subclient_content = self._utility.create_test_data(client_machine)

            client = self.tcinputs['ClientName']
            subclient  = CommonUtils(self.commcell).get_subclient(client)
            self._backupset = CommonUtils(self.commcell).get_backupset(client)

            subclient.content = [subclient_content]
            validatelog = os.path.join(self.client.log_directory, logfile_to_check[0])
            validatelog = client_machine.get_unc_path(validatelog)
            all_jobs_statistics = {}
            client_machine.set_logging_debug_level('ApplicationMgr', level=10)
            client_machine.set_logging_debug_level('CCSDB', level=10)
            try:
                if client_machine.check_file_exists(templog_dictory):
                    client_machine.remove_directory(templog_dictory)
            except:
                self.log.info("failed to remove directory")
            self._utility.create_directory(client_machine)
            #client_machine.create_directory(templog_dictory)
            server.rename_remove_logfile(client_machine, validatelog, templog_dictory="", substring='')
            self.log.info(" Creating an automatic schedule")
            sch_obj = self._schedule_creator.create_schedule(
                'subclient_backup',
                schedule_pattern={
                    'freq_type': 'automatic',
                    'min_interval_hours': 0,
                    'min_interval_minutes': 2

                },
                subclient=subclient,
                backup_type="Incremental",
                wait=False)
            _sch_helper_obj = schedulerhelper.SchedulerHelper(sch_obj, self.commcell)
            self.log.info("validating if backup triggered for subclient")
            previous_job = _sch_helper_obj.automatic_schedule_wait(newcontent=True)
            if previous_job.job_id:
                self.log.info('Job triggered for new subclient content case')
            server.rename_remove_logfile(client_machine, validatelog, templog_dictory, str(previous_job.job_id))
            for iteration in range(2):
                self.log.info("started iteration: %s", (str(iteration)))
                self.log.info("Generating test data at %s", str(subclient_content))
                subclient_changing_content = [subclient_content + "\\data" + str(iteration)]
                client_machine.generate_test_data(subclient_changing_content[0] + "\\dir1")
                self.log.info("Changing the subclient content to %s", str(subclient_changing_content))
                subclient.content = subclient_changing_content
                self.log.info("validating if backup triggered for subclient")
                previous_job = _sch_helper_obj.automatic_schedule_wait(newcontent=True)
                if previous_job.job_id:
                    self.log.info('Job triggered for new subclient content case')
                all_jobs_statistics[previous_job.job_id] = server.validatelogs(
                    client_machine, loglines_with_required_calls,
                    validatelog, serverconstants.statics_constant())
                self.log.info("Job %s Statastics %s", previous_job.job_id, all_jobs_statistics[previous_job.job_id])
                server.rename_remove_logfile(client_machine, validatelog, templog_dictory, str(previous_job.job_id))
            for iteration in range(2):
                self.log.info("started iteration: %s", (str(iteration)))
                self.log.info("Generating test data at %s", str(subclient_changing_content[0]))
                client_machine.generate_test_data(subclient_changing_content[0] + "\\dir1")
                self.log.info("validating if backup triggered for subclient")
                previous_job = _sch_helper_obj.automatic_schedule_wait()
                if previous_job.job_id:
                    self.log.info('Job triggered for new subclient content case')
                all_jobs_statistics[previous_job.job_id] = server.validatelogs(
                    client_machine, loglines_with_required_calls,
                    validatelog, serverconstants.statics_constant())
                self.log.info("Job %s Statastics %s", previous_job.job_id, all_jobs_statistics[previous_job.job_id])
                server.rename_remove_logfile(client_machine, validatelog, templog_dictory, str(previous_job.job_id))
            self.log.info("All jobs statistics are %s", str(all_jobs_statistics))
            headers = ["Request Type:"]
            headerchange = 0
            jobheader = {}
            for key in all_jobs_statistics.keys():
                if headerchange >=2:
                    jobheader[key] = "Data Change"
                else:
                    jobheader[key] = "Content Change"
                headerchange = headerchange + 1

            for key in all_jobs_statistics.keys():
                headers.append("JOB ID: " + key + " " + "(" + jobheader[key] + ")")
            string_to_check = {}
            for key, value in all_jobs_statistics.items():
                for item in value.keys():
                    string_to_check[item] = []
                break
            for key, value in all_jobs_statistics.items():
                for key in string_to_check:
                    string_to_check[key].append(value[key])
            self.log.info("All jobs statistics formatted data %s", str(string_to_check))
            self.log.info("header data  %s", str(headers))
            self.log.info("Email content data  %s", str(string_to_check))

            data = server.generate_email_body(headers, string_to_check)
            mail = Mailer({'receiver':receiver}, commcell_object=self.commcell)
            mail.mail("Laptop backup call statistics information", data)
            if client_machine.check_file_exists(validatelog.replace(".log", "_1.log")):
                client_machine.remove_directory(validatelog.replace(".log", "_1.log"))
            install_path = self.client.install_directory.split(os.path.sep)[0]
            if not install_path.endswith(os.path.sep):
                install_path += os.path.sep
            fileobj = open(os.path.join(install_path, logfile_to_check[0]), "w")
            for line in loglines_with_required_calls:
                fileobj.write(line)
                fileobj.write("\n")
            fileobj.close()
            self.log.info("Testcase execution completed")
        except Exception as exp:
            self.log.error('Failed with error: %s', str(exp))
            self.result_string = str(exp)
            self.status = constants.FAILED
        finally:
            self._schedule_creator.cleanup_schedules()
            client_machine.remove_directory(subclient_content + "\\data1\\dir1")
            client_machine.remove_directory(subclient_content + "\\data2\\dir1")

