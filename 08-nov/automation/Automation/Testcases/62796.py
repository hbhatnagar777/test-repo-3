
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
from AutomationUtils import constants


class TestCase(CVTestCase):
    def __init__(self):
        """Initializes test case class object."""

        super(TestCase, self).__init__()
        self.name = "Microsoft O365 Teams Public Channels - Backup & Restring of leaf file."
        self.show_to_user = True
        self.helper = None
        self.tcinputs = {
            "ClientName": None,
            "Office365Plan": None,
            "IndexServer": None,
            "members": None,
            "filename": None
        }

        self.pub_team = None
        self.pub_team_std_ch = None
        self.dest_team = None
        self.dest_team_std_ch = None

    def setup(self):
        """Setup function of this test case."""
        self.helper= TeamsHelper(self.client, self)
        self.log.info("STEP 1 - Create test data.")

        self.log.info("\t1.01. Create a PUBLIC team.")
        self.pub_team = self.helper.create_public_team(members=self.tcinputs.get("members"))
        self.log.info("\t1.02. Create a STANDARD CHANNEL for the PUBLIC team.")
        self.pub_team_std_ch = self.helper.create_standard_channel(self.pub_team)
        self.log.info(f"\t1.03. Upload a Folder with 10 nested folders to {self.pub_team_std_ch.name} of PUBLIC team.")
        parent_id = self.pub_team_std_ch.sharepoint_drives['root_id']
        for i in range(10):
            flag, resp = self.pub_team_std_ch.upload_folder(parent_id=parent_id)
            parent_id = resp['id']
        self.log.info(f"\t1.04. Upload a FILE to leaf folder of {self.pub_team_std_ch.name} of PUBLIC team.")
        self.helper.upload_file(self.pub_team_std_ch, file=self.tcinputs.get('filename'), parent_id=parent_id)
        self.log.info("\t1.05. Create a DESTINATION team.")
        self.dest_team = self.helper.create_public_team(members=self.tcinputs.get("members"))
        self.log.info("\t1.06. Create a STANDARD CHANNEL for the DESTINATION team.")
        self.dest_team_std_ch = self.helper.create_standard_channel(self.dest_team, name=self.pub_team_std_ch.name)

    def run(self):
        """Main function for test case execution."""
        try:
            self.log.info("STEP 2 - Run a BACKUP, ensure it completes.")

            self.log.info('\t2.01. DISCOVERING & ADDING %s to CONTENT.', self.pub_team.name)
            self.helper.set_content([self.pub_team.mail], self.tcinputs.get('Office365Plan'))
            self.log.info("\t2.02. Running a BACKUP.")
            backup_job = self.helper.backup([self.pub_team.mail])
            if backup_job.status.upper() != "COMPLETED":
                raise Exception(f"Backup job {backup_job.job_id} did not complete successfully.")
            self.log.info("\t      Backup job ID is %s\n", backup_job.job_id)

            self.log.info("STEP 3 - Restore Leaf file OUT OF PLACE TO other team, ensure it completes.")

            self.log.info("\t3.01. Running a RESTORE.")
            restore_job = self.helper.out_of_place_files_restore(self.pub_team.mail,
                                                                 self.dest_team.mail,
                                                                 self.dest_team_std_ch,
                                                                 [self.tcinputs.get('filename')],
                                                                 self.helper)
            if restore_job.status.upper() != "COMPLETED":
                raise Exception(f"Restore job {restore_job.job_id} did not complete successfully.")
            self.log.info("\t      Restore job ID is %s\n", restore_job.job_id)
            self.log.info("STEP 4 - COMPARE SOURCE TEAM FILES FOLDER WITH DESTINATION TEAM FILES FOLDER")
            destination_item = self.dest_team_std_ch.sharepoint_drives['root_id']
            dest_drive_id = self.dest_team_std_ch.sharepoint_drives['driveId']
            items = self.helper.get_children_in_folder(dest_drive_id, destination_item)
            if len(items) == 1 and items[0]['name'] == self.tcinputs['filename']:
                self.log.info("\t      Files folder reconstructed sucessfully.")
            else:
                raise Exception("\t      Files folder was not reconstructed sucessfully.")
        except Exception as ex:
            self.log.exception(ex)
            self.status = constants.FAILED

        finally:
            self.helper.delete_team(self.pub_team)
            self.helper.delete_team(self.dest_team)
            self.helper.remove_team_association([self.pub_team.mail])
