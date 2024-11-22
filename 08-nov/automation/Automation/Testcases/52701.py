
# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

TestCase is the only class defined in this file

TestCase: Class for executing this test case

TestCase:
    __init__()      --  initialize TestCase class

    run()           --  run function of this test case
"""

import traceback

from cvpysdk import eventviewer
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.options_selector import OptionsSelector
from AutomationUtils.idautils import CommonUtils
from Server.ActivityControl import activitycontrolhelper
from Server.serverhelper import ServerTestCases
from Server.JobManager.jobmanager_helper import JobManager


class TestCase(CVTestCase):
    """Class for executing Basic activity control acceptance test with File System backup and
        restore test case"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "[Acceptance]: Basic Activity Control backup/restore test validation"
        self.applicable_os = self.os_list.WINDOWS
        self.product = self.products_list.COMMSERVER
        self.feature = self.features_list.ACTIVITYCONTROL
        self.show_to_user = True
        self.sleep_time = 10  # seconds

    def run(self):
        """Main function for test case execution"""
        log = self.log
        tc = ServerTestCases(self)
        tc_base = CommonUtils(self)
        utility = OptionsSelector(self.commcell)

        try:
            log.info("Started executing {0} testcase".format(self.id))

            tc.log_step("""
                        Test Case
                            For Backup:
                                Disable the Data Management Activity on Commcell
                                Trigger Backup on CS client default subclient
                                Verify Job fails and returns appropriate event message
                                Enable Data Management Activity back on the Commcell
                                Trigger Backup on CS client default subclient
                                Verify Backup Job completes
                            For Restore:
                                Disable the Data Recovery Activity on Commcell
                                Trigger In Place Restore on CS client default subclient
                                Verify Restore Job fails and returns appropriate event message
                                Enable Data Management Activity back on the Commcell
                                Trigger In place restore again on CS client default subclient
                                Verify restore Job completes""", 200)

            log.info("Create Activity Control Helper class object")
            activity = activitycontrolhelper.ActivityControlHelper(self)

            log.info("Read subclient content")
            log.info("Subclient Content: {0}".format(self.subclient.content))

            if self.subclient.content == [] or self.subclient.content == ['/']:
                raise Exception(
                    "Subclient Content is empty please add\
                     subclient content from Commcell Console"
                )

            log.info("Create Activity Control class object")
            activity_control = self.commcell.activity_control

            log.info("Create Job Controller class object")
            job_controller_obj = self.commcell.job_controller

            log.info("Create Event Viewer class object")
            events_obj = self.commcell.event_viewer

            log.info("Disabling Data Management Activity")
            activity_control.set(activity_type='DATA MANAGEMENT', action='Disable')

            if not activity.backup_with_activity_disabled('Incremental'):
                raise Exception("Backup validation failed with activity disabled")

            utility.sleep_time(self.sleep_time)

            jobs_dict = job_controller_obj.finished_jobs(options={'limit': 1})
            job_id = next(iter(jobs_dict))

            log.info("Job Id Obtained is: %s", str(job_id))

            job_obj = job_controller_obj.get(job_id)

            events_dict = events_obj.events({'jobId': job_obj.job_id})
            log.info("Event Id and Event Code obtained for the \
                    associated Job id is: {0}".format(events_dict))

            event_obj = eventviewer.Event(self.commcell, next(iter(events_dict)))

            if event_obj.is_backup_disabled:
                log.info('Backup Disabled Event Found')
            else:
                raise Exception("Backup Disabled Event not found")

            log.info("Enabling Data Management Activity back")
            activity_control.set(activity_type='DATA MANAGEMENT', action='Enable')

            job = tc_base.subclient_backup(self.subclient, "Incremental", False)
            job_manager = JobManager(job, self.commcell)
            job_manager.wait_for_state('completed', 30, 60)

            log.info("Disabling Data Recovery Activity")
            activity_control.set(activity_type='DATA RECOVERY', action='Disable')

            log.info("*" * 10 + " Run Restore in place " + "*" * 10)
            # run restore in place job
            job_obj = self.subclient.restore_in_place([self.subclient.content[0]])

            log.info("Started restore in place job with job id: %s", str(job_obj.job_id))

            utility.sleep_time(self.sleep_time)

            events_dict = events_obj.events({'jobId': job_obj.job_id})

            log.info("Event Id and Event Code obtained for \
                    the associated Job id is: {0}".format(events_dict))

            event_obj = eventviewer.Event(self.commcell, next(iter(events_dict)))

            if event_obj.is_restore_disabled:
                log.info('Restore Disabled Event Found')
            else:
                raise Exception("Restore Disabled Event not found")

            log.info("Enabling Data Recovery Activity back")
            activity_control.set(activity_type='DATA RECOVERY', action='Enable')

            log.info("*" * 10 + " Run Restore in place " + "*" * 10)
            # run restore in place job
            job_obj = self.subclient.restore_in_place([self.subclient.content[0]])

            log.info("Started restore in place job with job id: %s", str(job_obj.job_id))

            if not job_obj.wait_for_completion():
                raise Exception("Failed to run restore in place job with error: " +
                                job_obj.delay_reason)

            log.info("Successfully finished restore in place job")

        except Exception as excp:
            tc.fail(excp, traceback.format_exc())
        finally:
            activity.cleanup()
