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
from Application.Teams.teams_constants import TeamsConstants
from AutomationUtils import constants
const = TeamsConstants()

msg_type = const.MessageType
file_type = const.FileType


class TestCase(CVTestCase):

    def __init__(self):
        """Initializes test case class object."""

        super(TestCase, self).__init__()
        self.name = "Microsoft O365 verify Teams restore skip and overwrite items Feature"
        self.show_to_user = True
        self.helper = None
        self.plan = None
        self.tcinputs = {
            "ClientName": None,
            "Office365Plan": None,
            "members": None
        }
        self.pub_team = None
        self.pub_team_std_ch = None
        self.previous_modified_time_of_items = {}
        self.current_mod_time = {}

    def setup(self):
        """Setup function of this test case."""
        self.helper = TeamsHelper(self.client, self)
        self.plan = self.tcinputs['Office365Plan']
        self.log.info("\t1.01. Create a PUBLIC team.")
        self.pub_team = self.helper.create_public_team(members=self.tcinputs['members'])
        self.log.info("\t1.02. Create standard channel")
        self.pub_team_std_ch = self.helper.create_standard_channel(self.pub_team)
        self.log.info("\t1.03. Post few conversations to standard channel")
        self.helper.post_text_to_channel(self.pub_team_std_ch, msg_type.TEXT, "Hi")
        self.helper.post_text_to_channel(self.pub_team_std_ch, msg_type.TEXT, "Good morning")
        self.helper.post_text_to_channel(self.pub_team_std_ch, msg_type.TEXT, "Welcome to teams")

        self.log.info("\t1.04. upload different types of files to the standard channel")
        self.helper.upload_file(self.pub_team_std_ch, f_type=file_type.TEXT)
        self.helper.upload_file(self.pub_team_std_ch, f_type=file_type.BIN)
        self.helper.upload_file(self.pub_team_std_ch, f_type=file_type.PDF)
        self.helper.upload_file(self.pub_team_std_ch, f_type=file_type.PNG)
        self.helper.upload_file(self.pub_team_std_ch, f_type=file_type.XLSX)
        self.helper.upload_file(self.pub_team_std_ch, f_type=file_type.PPTX)
        self.helper.upload_file(self.pub_team_std_ch, f_type=file_type.DOCX)
        self.helper.upload_file(self.pub_team_std_ch, f_type=file_type.JPG)
        self.helper.upload_file(self.pub_team_std_ch, f_type=file_type.JSON)
        self.helper.upload_file(self.pub_team_std_ch, f_type=file_type.C)
        self.helper.upload_file(self.pub_team_std_ch, f_type=file_type.CPP)
        self.helper.upload_file(self.pub_team_std_ch, f_type=file_type.MP3)
        self.helper.upload_file(self.pub_team_std_ch, f_type=file_type.PY)


    def run(self):
        """Main function for test case execution."""

        try:
            self.log.info('\t2.01. DISCOVERING & ADDING %s to CONTENT.', self.pub_team.name)
            self.helper.set_content([self.pub_team.mail], self.plan)
            self.log.info(f'\t2.02. Run a backup job for {self.pub_team.mail} team.')
            backup_job = self.helper.backup([self.pub_team.mail])
            self.log.info(f'\tBackup job id {backup_job.job_id}')
            if backup_job.status.upper() != "COMPLETED":
                raise Exception(f"Backup job {backup_job.job_id} did not complete successfully.")

            self.log.info('\t3. Get modified time of items before running a restore.')
            for item in self.helper.get_children_in_folder(self.pub_team_std_ch._sharepoint_drives['driveId'],
                                                           self.pub_team_std_ch._sharepoint_drives['root_id']):
                self.previous_modified_time_of_items[item['name']] = item['fileSystemInfo']['lastModifiedDateTime']

            self.log.info(f'\t4. Run a Restore inplace  for {self.pub_team.name} with skip items')
            restore_job = self.helper.restore_to_original_location(self.pub_team.mail)
            self.log.info(f'\tRestore job id {restore_job.job_id}')
            if restore_job.status.upper() != "COMPLETED":
                raise Exception(f"Restore job {restore_job.job_id} did not complete successfully.")
            self.log.info('\t5. Get modified time of items after running a restore.')
            for item in self.helper.get_children_in_folder(self.pub_team_std_ch._sharepoint_drives['driveId'],
                                                           self.pub_team_std_ch._sharepoint_drives['root_id']):
                self.current_mod_time[item['name']] = item['fileSystemInfo']['lastModifiedDateTime']
            self.log.info(f'\t6. Verify skip option was working fine or not.')

            for item in self.current_mod_time:
                if self.previous_modified_time_of_items[item] != self.current_mod_time[item]:
                    raise Exception("Skip was not working properly")

            self.log.info(f'\t7. Run a Restore inplace  for {self.pub_team.name} with unconditional overwrite items')
            restore_job = self.helper.restore_to_original_location(self.pub_team.mail, skip_items=False)
            self.log.info(f'\tRestore job id {restore_job.job_id}')
            if restore_job.status.upper() != "COMPLETED":
                raise Exception(f"Restore job {restore_job.job_id} did not complete successfully.")
            self.log.info('\t8. Get modified time of items after running a restore.')
            for item in self.helper.get_children_in_folder(self.pub_team_std_ch._sharepoint_drives['driveId'],
                                                           self.pub_team_std_ch._sharepoint_drives['root_id']):
                self.current_mod_time[item['name']] = item['fileSystemInfo']['lastModifiedDateTime']
            self.log.info(f'\t9. Verify Unconditional overwrite option was working fine or not.')

            for item in self.current_mod_time:
                if self.previous_modified_time_of_items[item] >= self.current_mod_time[item]:
                    raise Exception("Unconditional overwrite was not working properly")

        except Exception as ex:
            self.log.exception(ex)
            self.status = constants.FAILED

        finally:
            self.log.info("STEP 10 - Delete all created teams.")
            self.helper.delete_team(self.pub_team)
            self.helper.remove_team_association([self.pub_team.mail])
