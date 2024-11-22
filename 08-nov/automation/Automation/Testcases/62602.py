# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
""" Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()      --  Initialize TestCase class

    setup()         --  Setup function of this test case

    run()           --  Run function of this test case

"""
import time

from AutomationUtils.cvtestcase import CVTestCase
from Application.Teams.teams_helper import TeamsHelper
from AutomationUtils.windows_machine import WindowsMachine
import json
from AutomationUtils import constants


class TestCase(CVTestCase):

    def __init__(self):
        """Initializes test case class object."""

        super(TestCase, self).__init__()
        self.name = "Microsoft O365 Teams Public Channels Suspend and Resume While Backup Feature ."
        self.show_to_user = True
        self.helper = None
        self.plan = None
        self.backup_job = None
        self.tcinputs = {
            "ClientName": None,
            "Office365Plan": None,
            "members": None,
            "accessnode": None,
            "path": None
        }
        self.pub_team = None
        self.pub_team_std_ch = None
        self.dest_team = None

    def setup(self):
        """Setup function of this test case."""
        self.helper = TeamsHelper(self.client, self)
        self.plan = self.tcinputs.get("Office365Plan")
        self.log.info("\t1.01. Create a PUBLIC team.")
        self.pub_team = self.helper.create_public_team(members=self.tcinputs.get("members"))

        try:
            self.log.info("\t1.02. Create standard channel")
            self.pub_team_std_ch = self.helper.create_standard_channel(self.pub_team)
            self.log.info("\t1.03. uploading 10 files to standard CHANNEL of the PUBLIC team.")
            for _ in range(10):
                self.helper.upload_file(self.pub_team_std_ch)
            self.log.info("\t1.04. Create a destination team.")
            self.dest_team = self.helper.create_public_team(members=self.tcinputs.get("members"))
        except Exception as ex:
            self.helper.delete_team(self.pub_team)
            raise Exception(ex)

    def run(self):
        """Main function for test case execution."""
        self.log.info("STEP 2 - Run a BACKUP, ensure it completes.")

        self.log.info('\t2.01. DISCOVERING & ADDING %s to CONTENT.', self.pub_team.name)
        self.helper.set_content([self.pub_team.mail], self.plan)

        acess_node = WindowsMachine(self.tcinputs.get("accessnode"), self.helper.commcell_object)
        self.log.info('\t2.02. set iTeamsPartialCommitFileCount reg key value to 5 under IDataAgent')
        if acess_node.check_registry_exists("iDataAgent", "iTeamsPartialCommitFileCount"):
            acess_node.update_registry("iDataAgent", "iTeamsPartialCommitFileCount", 5, "DWord")
        else:
            acess_node.create_registry("iDataAgent", "iTeamsPartialCommitFileCount", 5, "DWord")
        try:

            self.backup_job = self.helper.backup([self.pub_team.mail], False)
            time.sleep(180)
            self.log.info("\t2.04. Suspending a backup job after processing after processing 5 files.")
            self.backup_job.pause(True)
            if self.backup_job.status.upper() != "SUSPENDED":
                raise Exception(f"Backup job {self.backup_job.job_id} did not SUSPENDED")
            self.log.info("\tBACKUP JOB ID is %s", self.backup_job.job_id)
            teams = self.helper.discover()
            team_gui_id = teams[self.pub_team.mail]['user']['userGUID']

            self.log.info("\t2.05. Get left over files after suspend.")
            path = "%s\\iDataAgent\\JobResults\\CV_JobResults\\2\\2\\%s\\%s\\ProcessedDriveScanItems.xml" % \
                   (self.tcinputs['path'], self.backup_job.job_id, team_gui_id)

            if not acess_node.check_file_exists(path):
                raise Exception(f"\t       Processeddrivescanitems file was not created under {path} path.")

            left_over_items_file = json.loads(json.dumps(self.helper.read_xml(path, self.tcinputs.get("accessnode"))))
            left_files_in_first_job = []
            for i in left_over_items_file['ExchangeVirtualAgent_TeamDriveItemsScan']['channelDriveInfo'][1]['driveItemInfo']:
                if '@itemOffset' not in i:
                    left_files_in_first_job.append(i['@itemId'])

            self.log.info("\t2.06. Resume a backup job on same team.")
            self.log.info('\t   set iTeamsPartialCommitFileCount reg key value to 0 under IDataAgent')
            acess_node.update_registry("iDataAgent", "iTeamsPartialCommitFileCount", 0, "DWord")
            self.backup_job.resume(True)
            self.backup_job._wait_for_status("COMPLETED")
            if self.backup_job.status.upper() != "COMPLETED":
                raise Exception(f"Backup job {self.backup_job.job_id} did not complete successfully.")
            self.log.info("\tBACKUP JOB ID is %s", self.backup_job.job_id)

            self.log.info("\t2.07. Get processed drive items after resume.")
            path = "%s\\iDataAgent\\JobResults\\CV_JobResults\\2\\2\\%s\\%s\\ProcessedDriveScanItems.xml" % \
                   (self.tcinputs['path'], self.backup_job.job_id, team_gui_id)

            processed_items_file = json.loads(json.dumps(self.helper.read_xml(path, self.tcinputs.get("accessnode"))))
            processed_files_in_second_job = [i['@itemId'] for i in
                              processed_items_file['ExchangeVirtualAgent_TeamDriveItemsScan'][
                                  'channelDriveInfo']['driveItemInfo']]
            processed_files_in_second_job.pop(0)
            self.log.info("\t2.08. compare left_over_files before resume to processed_files after resume.")
            if left_files_in_first_job == processed_files_in_second_job and len(left_files_in_first_job) > 0:
                self.log.info("SUSPEND AND RESUME FEATURE WAS WORKING FINE.")
            else:
                raise Exception("\t    SUSPEND AND RESUME FEATURE WAS NOT WORKING FINE.")
            self.log.info("\t2.09. Restore Team to out of place to another team.")
            restore_job = self.helper.out_of_place_restore(self.pub_team.mail, self.dest_team.mail)
            if restore_job.status.upper() != "COMPLETED":
                raise Exception(f"Restore job {restore_job.job_id} did not complete successfully.")
            self.log.info("\tRestore JOB ID is %s", restore_job.job_id)
            self.dest_team.refresh_team_channels()
            self.log.info("\t2.10. Now compare source team and destination team")
            if not (self.helper.compare_channels_files_folder(self.pub_team_std_ch,
                                                              self.dest_team.channels[self.pub_team_std_ch.name])):
                raise Exception(f"\tFiles Folder of {self.pub_team.name} and {self.dest_team.name} team did not match.")

        except Exception as ex:
            self.log.exception(ex)
            self.status = constants.FAILED
            if self.backup_job.status.upper() == "SUSPENDED":
                self.backup_job.kill()

        finally:
            self.helper.delete_team(self.pub_team)
            self.helper.delete_team(self.dest_team)
            self.log.info("Removing Team from Content\n")
            self.helper.remove_team_association([self.pub_team.mail])
            acess_node.remove_registry("iDataAgent", "iTeamsPartialCommitFileCount")






