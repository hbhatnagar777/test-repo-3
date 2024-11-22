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

from AutomationUtils.cvtestcase import CVTestCase
from Application.Teams.teams_helper import TeamsHelper
from AutomationUtils.windows_machine import WindowsMachine
import json
from AutomationUtils import constants
import time


class TestCase(CVTestCase):

    def __init__(self):
        """Initializes test case class object."""

        super(TestCase, self).__init__()
        self.name = "Microsoft O365 Teams Public Channels Partial files commit feature"
        self.show_to_user = True
        self.helper = None
        self.plan = None
        self.backup_job = None
        self.tcinputs = {
            "ClientName": None,
            "Office365Plan": None,
            "members": None,
            "path": None,
            "accessnode": None
        }
        self.pub_team = None
        self.pub_team_gnl_ch = None

    def setup(self):
        """Setup function of this test case."""
        self.helper = TeamsHelper(self.client)
        self.plan = self.tcinputs.get("Office365Plan")
        self.log.info("\t1.01. Create a PUBLIC team.")
        self.pub_team = self.helper.create_public_team(members=self.tcinputs.get("members"))

        try:
            self.pub_team_gnl_ch = self.pub_team.channels["General"]
            self.log.info("\t1.02. uploading 10 files to General CHANNEL of the PUBLIC team.")
            for _ in range(10):
                self.helper.upload_file(self.pub_team_gnl_ch)
        except Exception as ex:
            self.helper.delete_team(self.pub_team)
            raise Exception(ex)

    def run(self):
        """Main function for test  case execution."""
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
            self.log.info("\t2.03. Running a BACKUP.")
            self.backup_job = self.helper.backup([self.pub_team.mail], False)
            time.sleep(180)
            self.backup_job.kill()
            self.log.info("\tBACKUP JOB ID is %s", self.backup_job.job_id)
            time.sleep(60)
            teams = self.helper.discover()
            team_gui_id = teams[self.pub_team.mail]['user']['userGUID']

            self.log.info("\t2.05. Get left over files in first job.")
            path = "%s\\iDataAgent\\JobResults\\CV_JobResults\\iDataAgent\\Cloud Apps Agent\\2\\%s\\%s" \
                   "\\LeftoverDriveScanItems.xml" % (self.tcinputs.get(
                "path"), self.helper._subclient._subClientEntity['subclientId'], team_gui_id)

            retry = 3
            created = False
            while retry and not created:
                if acess_node.check_file_exists(path):
                    created = True
                    break
                time.sleep(10)
                retry -= 1
            if not created:
                raise Exception("\t       leftoverdrivescanitems file was not created under subclient folder.")

            left_over_items_file = json.loads(json.dumps(self.helper.read_xml(path, self.tcinputs.get("accessnode"))))
            left_files_in_first_job = sorted([i['@itemId'] for i in left_over_items_file[
                'ExchangeVirtualAgent_TeamDriveItemsScan'][
                'channelDriveInfo']['driveItemInfo']])

            self.log.info("\t2.06. Running second backup job on same team.")
            self.backup_job = self.helper.backup([self.pub_team.mail])

            self.log.info("\t2.07. Get processed drive items in second job.")
            path = "%s\\iDataAgent\\JobResults\\CV_JobResults\\2\\2\\%s\\%s\\ProcessedDriveScanItems.xml" % \
                   (self.tcinputs.get("path"), self.backup_job.job_id, team_gui_id)

            processed_items_file = json.loads(json.dumps(self.helper.read_xml(path, self.tcinputs.get("accessnode"))))
            processed_files_in_second_job = sorted([i['@itemId'] for i in
                              processed_items_file['ExchangeVirtualAgent_TeamDriveItemsScan'][
                                  'channelDriveInfo']['driveItemInfo']])

            self.log.info("\t2.08. compare left_over_files in first job to processed_files in second job.")
            if left_files_in_first_job == processed_files_in_second_job:
                self.log.info("partial files commit feature was working properly.")
            else:
                raise Exception("\t       partial files commit feature was not working properly.")

        except Exception as ex:
            self.log.exception(ex)
            self.status = constants.FAILED

        finally:
            self.helper.delete_team(self.pub_team)
            self.log.info("Removing Team from Content\n")
            self.helper.remove_team_association([self.pub_team.mail])
            if acess_node.check_registry_exists("iDataAgent", "iTeamsPartialCommitFileCount"):
                acess_node.update_registry("iDataAgent", "iTeamsPartialCommitFileCount", 0, "DWord")






