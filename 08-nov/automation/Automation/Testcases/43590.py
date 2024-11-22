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
    __init__()          --  initialize TestCase class

    setup()             --  setup function of this test case

    run()               --  run function of this test case

    tear_down()         --  tear down function of this test case

    setup_op_window()   --  adds a new blackout/operation window with arbitrary configs

    setup_entities()    --  adds new library (from json inputs), storage policy and creates an FS subclient associated
                            to them (other args taken from json inputs)

    setup_schedule()    --  adds a backup schedule for the created subclient

    run_job()           --  runs the created schedule once and waits till completion

    ccm_export(suffix)  --  performs ccm export to new folder inside UNC location. the folder name is appended with
                            suffix if provided (because we perform 2 exports and imports in this test case)

    ccm_import(suffix)  --  performs ccm_import from new folder inside local path. suffix determines the ending of the
                            folder name from which to import

    verify_op_window()  --  verifies source CS and destination CS have same operation/blackout window properties

    verify_entities()   --  verifies library, policy, and subclient's presence in destination CS

    verify_schedule()   --  verifies source CS and destination CS have the same schedule for subclient

    modify_op_window()  --  modifies the properties of created operation/blackout window arbitrarily

    modify_schedule()   --  modifies created subclient's schedule pattern arbitrarily

    delete_op_window()  --  deletes the created operation/blackout window from both source and destination CS

    delete_entities()   --  deletes library,policy and subclient from both CS
"""

from datetime import datetime

from dateutil.relativedelta import relativedelta

from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.idautils import CommonUtils
from AutomationUtils.options_selector import OptionsSelector
from Server.CommcellMigration.ccmhelper import CCMHelper
from Server.OperationWindow.ophelper import OpHelper


class TestCase(CVTestCase):
    """Class for executing this test case"""

    def __init__(self):
        """Initializes test case class object

            Properties to be initialized:

                name            (str)       --  name of this test case

                tcinputs        (dict)      --  test case inputs with input name as dict key
                                                and value as input type

        """
        super(TestCase, self).__init__()
        self.folder_name = None
        self.subclient_name = None
        self.policy_name = None
        self.library_name = None
        self.dest_schedule = None
        self.dest_subclient = None
        self.dest_opw = None
        self.schedule_name = None
        self.src_opw = None
        self.destination_cs = None
        self.schedule = None
        self.policy = None
        self.library = None
        self.entity_dict = None
        self.schedule_time = None
        self.opw_name = None
        self.op_helper = None
        self.time = None
        self.ccm_helper = None
        self.name = "server_commcellmigration_Force overwrite options for nonclient entities"
        self.tcinputs = {
            "ClientName": None,
            "AgentName": None,
            "BackupsetName": None,
            "MediaAgent": None,
            "LibraryPath": None,
            "DestinationCSHostName": None,
            "CSUserName": None,
            "CSPassword": None,
            "ExportPathType": None,
            "ExportUserName": None,
            "ExportPassword": None,
            "ExportLocation": None,
            "ImportLocation": None,
        }

    def setup(self):
        """Setup function of this test case"""
        self.ccm_helper = CCMHelper(self)
        self.folder_name = OptionsSelector.get_custom_str("dump")
        # self.setup_holiday()  needs sdk support
        self.setup_op_window()
        self.setup_entities()
        self.setup_schedule()
        self.ccm_helper.create_destination_commcell(self.tcinputs["DestinationCSHostName"],
                                                    self.tcinputs["CSUserName"],
                                                    self.tcinputs["CSPassword"])
        self.destination_cs = self.ccm_helper.destination_cs

    def run(self):
        """Run function of this test case"""
        self.run_job()
        self.ccm_export()
        self.ccm_import()
        self.verify_entities()
        self.verify_schedule()
        self.verify_op_window()
        self.modify_schedule()
        self.modify_op_window()
        self.ccm_export("postmod")
        self.ccm_import("postmod")
        self.verify_op_window()
        self.verify_schedule(True)

    def tear_down(self):
        """Tear down function of this test case"""
        self.delete_op_window()
        self.delete_entities()

    def setup_op_window(self):
        """creates an operation/blackout window in source CS"""
        self.log.info("creating blackout window")
        self.opw_name = OptionsSelector.get_custom_str("Blackout_Window")
        self.op_helper = OpHelper(self, self.commcell,initialize_sch_helper=False)
        date_arg = (datetime.now() + relativedelta(years=1)).strftime("%d/%m/%Y")
        from_time = datetime.now().strftime("%H:%M")
        to_time = (datetime.now() + relativedelta(hours=1)).strftime("%H:%M")
        self.src_opw = self.op_helper.add(self.opw_name, date_arg, date_arg, ["FULL_DATA_MANAGEMENT", "DR_BACKUP"],
                                          ["SUNDAY", "SATURDAY"], from_time, to_time)
        self.log.info("blackout window created successfully")

    def setup_entities(self):
        """adds new library (from json inputs), storage policy and creates an FS subclient associated
                            to them (other args taken from json inputs)"""
        self.log.info("creating library,policy,subclient")
        self.library_name = OptionsSelector.get_custom_str("library")
        self.policy_name = OptionsSelector.get_custom_str("policy")
        self.subclient_name = OptionsSelector.get_custom_str("subclient")
        self.library = self.commcell.disk_libraries.add(self.library_name, self.tcinputs["MediaAgent"],
                                                        self.tcinputs["LibraryPath"])
        self.policy = self.commcell.storage_policies.add(self.policy_name, self.library,
                                                         self.tcinputs["MediaAgent"])
        self.subclient = self.backupset.subclients.add(self.subclient_name, self.policy.name,
                                                       "FILE_FILEGROUP")
        self.subclient.content = [self.tcinputs["ContentPath"]]
        self.log.info("subclient configured successfully")

    def setup_schedule(self):
        """creates a backup schedule for the created subclient"""
        self.log.info("creating backup schedule")
        schedule_time = (datetime.now() + relativedelta(hours=4)).strftime("%H:%M")
        self.schedule_name = OptionsSelector.get_custom_str("schedule")
        self.schedule = CommonUtils(self).subclient_backup(self.subclient, "full", False, schedule_pattern={
            "freq_type": 'weekly',
            "active_start_date": (datetime.today() + relativedelta(years=1)).strftime("%m/%d/%Y"),
            "active_start_time": schedule_time,
            "repeat_weeks": 1,
            "weekdays": ['Monday', 'Tuesday']
        })
        self.schedule.name = self.schedule_name
        self.log.info("created backup schedule successfully")

    def run_job(self):
        """runs the created schedule once and waits till completion"""
        self.log.info("running schedule once")
        job_id = self.schedule.run_now()
        if self.commcell.job_controller.get(job_id).wait_for_completion():
            self.log.info("schedule completed successfully")
        else:
            self.log.error("Scheduled job id %s failed/killed", job_id)
            raise Exception("Schedule Failed to Run")

    def ccm_export(self, suffix=""):
        """Function to perform CCM Export to new folder inside export location"""
        options = {
            'pathType': self.tcinputs["ExportPathType"],
            'userName': self.tcinputs["ExportUserName"],
            'password': self.tcinputs["ExportPassword"],
            'captureSchedules': True,
            'captureActivityControl': True,
            'captureOperationWindow': True,
            'captureHolidays': True
        }
        export_location = f'{self.tcinputs["ExportLocation"]}{self.folder_name}{suffix}'
        ccm_job = self.ccm_helper.run_ccm_export(export_location,
                                                 [self.client.name],
                                                 options=options)

        self.log.info("Started CCM Export Job: %s", ccm_job.job_id)

        if ccm_job.wait_for_completion():
            self.log.info("CCM Export Job id %s completed successfully", ccm_job.job_id)
        else:
            self.log.error("CCM Export Job id %s failed/ killed", ccm_job.job_id)
            raise Exception("CCM Export job failed")

    def ccm_import(self, suffix=""):
        """Function to perform CCM Import from folder inside export location"""
        options = {
            'forceOverwrite': True,
            'mergeHolidays': True,
            'mergeOperationWindow': True,
            'mergeSchedules': True,
            'forceOverwriteHolidays': True,
            'forceOverwriteOperationWindow': True,
            'forceOverwriteSchedule': True,
        }
        import_location = f'{self.tcinputs["ImportLocation"]}{self.folder_name}{suffix}'
        import_job = self.ccm_helper.run_ccm_import(import_location,
                                                    options=options)
        self.log.info("Started CCM Import Job: %s", import_job.job_id)

        if import_job.wait_for_completion():
            self.log.info("CCM Import Job id %s completed successfully", import_job.job_id)
        else:
            self.log.error("CCM Import Job id %s failed/ killed", import_job.job_id)
            raise Exception("CCM Import job failed")

    def verify_op_window(self):
        """verifies source CS and destination CS have same operation/blackout window properties"""
        self.log.info("verifying operation window")
        self.destination_cs.refresh()
        ophelpdest = OpHelper(self, self.destination_cs,initialize_sch_helper=False)
        self.dest_opw = ophelpdest.get(self.opw_name)
        if self.dest_opw.name == self.src_opw.name and self.dest_opw.start_date == self.src_opw.start_date and \
                self.dest_opw.start_time == self.src_opw.start_time and \
                self.dest_opw.end_time == self.src_opw.end_time and \
                self.dest_opw.operations == self.src_opw.operations and \
                self.dest_opw.day_of_week == self.src_opw.day_of_week:
            self.log.info("Operation Window Verified on DestinationCS")
        else:
            raise Exception("Operation Window Migration Couldn't be verified")

    def verify_entities(self):
        """verifies library, policy, and subclient's presence in destination CS"""
        self.log.info("verifying subclient, library and policy migration")
        self.destination_cs.refresh()
        backupset = self.destination_cs.clients.get(self.client.name).agents.get(self.agent.name).backupsets.get(
            self.backupset.name)
        self.dest_subclient = backupset.subclients.get(self.subclient_name)
        self.destination_cs.disk_libraries.get(f'CCM_{self.library_name}')
        self.destination_cs.storage_policies.get(f'CCM_{self.policy_name}')
        self.log.info("subclient, library and policy migrated successfully")

    def verify_schedule(self, postmod=False):
        """verifies source CS and destination CS have the same schedule for subclient"""
        self.log.info("verifying schedule")
        self.destination_cs.refresh()
        self.dest_schedule = self.dest_subclient.schedules.get(self.schedule_name)
        if not postmod:
            if self.dest_schedule.weekly != self.schedule.weekly:
                raise Exception("Schedule patterns mismatch")
        else:
            if self.dest_schedule.daily != self.schedule.daily:
                raise Exception("Schedule patterns mismatch")
        self.log.info("Schedule migrated successfully")

    def modify_op_window(self):
        """modifies the properties of created operation/blackout window arbitrarily"""
        self.log.info("modifying operation window")
        date_from = (datetime.now() + relativedelta(years=2)).strftime("%d/%m/%Y")
        date_to = (datetime.now() + relativedelta(years=2, months=1)).strftime("%d/%m/%Y")
        from_time = (datetime.now() + relativedelta(hours=1)).strftime("%H:%M")
        to_time = (datetime.now() + relativedelta(hours=3)).strftime("%H:%M")
        self.src_opw = self.op_helper.edit(
            name=self.opw_name,
            start_date=date_from,
            end_date=date_to,
            operations=["SYNTHETIC_FULL", "DATA_RECOVERY"],
            day_of_week=["WEDNESDAY", "THURSDAY"],
            start_time=from_time,
            end_time=to_time,
        )
        self.log.info("Operation Window Successfully Modified")

    def modify_schedule(self):
        """modifies created subclient's schedule pattern arbitrarily"""
        self.log.info("modifying schedule")
        schedule_time = (datetime.now() + relativedelta(hours=2)).strftime("%H:%M")
        self.schedule.daily = {
            "active_start_time": schedule_time,
            "repeat_days": 2
        }
        self.log.info("schedule modified successfully")

    def delete_op_window(self):
        """deletes the created operation/blackout window from both source and destination CS"""
        self.op_helper.delete(self.opw_name)
        OpHelper(self, self.destination_cs,initialize_sch_helper=False).delete(self.opw_name)

    def delete_entities(self):
        """deletes library,policy and subclient from both CS"""
        try:
            self.log.info("deleting library,policy,subclient in source CS")
            self.backupset.subclients.delete(self.subclient_name)
            self.commcell.storage_policies.delete(self.policy_name)
            self.commcell.disk_libraries.delete(self.library_name)
            self.log.info("source entities deleted\ndeleting library,policy,subclient in destination CS")
            self.destination_cs.refresh()
            self.destination_cs.clients.delete(self.tcinputs["ClientName"])
            self.destination_cs.storage_policies.delete("CCM_" + self.policy_name)
            self.destination_cs.disk_libraries.delete("CCM_" + self.library_name)
            self.log.info("all entities deleted successfully")
        except Exception as exp:
            self.log.error("Could not delete all migrated entities")
            self.log.error(str(exp))
