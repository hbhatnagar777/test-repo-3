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
        self.name = "Microsoft O365 Teams Shared Channels backup and backup , restore different types of Files"
        self.show_to_user = True
        self.helper = None
        self.plan = None
        self.tcinputs = {
            "ClientName": None,
            "Office365Plan": None,
            "members": None
        }
        self.pub_team = None
        self.pub_team_srd_ch = None
        self.dest_team = None
        self.pub_team_2 = None
        self.pub_team_2_std_ch = None

    def setup(self):
        """Setup function of this test case."""
        self.helper = TeamsHelper(self.client, self)
        self.plan = self.tcinputs['Office365Plan']
        self.log.info("\t1.01. Create a PUBLIC team.")
        self.pub_team = self.helper.create_public_team(members=self.tcinputs['members'])
        self.log.info("\t1.02. Create shared channel")
        self.pub_team_srd_ch = self.helper.create_shared_channel(self.pub_team, owners=self.tcinputs['members'],
                                                                 members=self.tcinputs['members'])
        self.log.info("\t1.03. Post few conversations to shared channel")
        self.helper.post_text_to_channel(self.pub_team_srd_ch, msg_type.TEXT, "Hi")
        self.helper.post_text_to_channel(self.pub_team_srd_ch, msg_type.TEXT, "Good morning")
        self.helper.post_text_to_channel(self.pub_team_srd_ch, msg_type.TEXT, "Welcome to teams")

        self.log.info("\t2.01. Create a PUBLIC team.")
        self.pub_team_2 = self.helper.create_public_team(members=self.tcinputs['members'])
        self.log.info("\t2.02. Create a standard channel.")
        self.pub_team_2_std_ch = self.helper.create_standard_channel(self.pub_team_2)
        self.log.info("\t2.03. upload different types of files to the standard channel")
        self.helper.upload_file(self.pub_team_2_std_ch, f_type=file_type.TEXT)
        self.helper.upload_file(self.pub_team_2_std_ch, f_type=file_type.BIN)
        self.helper.upload_file(self.pub_team_2_std_ch, f_type=file_type.PDF)
        self.helper.upload_file(self.pub_team_2_std_ch, f_type=file_type.PNG)
        self.helper.upload_file(self.pub_team_2_std_ch, f_type=file_type.XLSX)
        self.helper.upload_file(self.pub_team_2_std_ch, f_type=file_type.PPTX)
        self.helper.upload_file(self.pub_team_2_std_ch, f_type=file_type.DOCX)
        self.helper.upload_file(self.pub_team_2_std_ch, f_type=file_type.JPG)
        self.helper.upload_file(self.pub_team_2_std_ch, f_type=file_type.JSON)
        self.helper.upload_file(self.pub_team_2_std_ch, f_type=file_type.C)
        self.helper.upload_file(self.pub_team_2_std_ch, f_type=file_type.CPP)
        self.helper.upload_file(self.pub_team_2_std_ch, f_type=file_type.MP3)
        self.helper.upload_file(self.pub_team_2_std_ch, f_type=file_type.PY)
        self.log.info("\t3.01. Create a public team as a destination.")
        self.dest_team = self.helper.create_public_team(members=self.tcinputs['members'])

    def run(self):
        """Main function for test case execution."""

        try:
            self.log.info('\t4.01. DISCOVERING & ADDING %s to CONTENT.', self.pub_team.name)
            self.helper.set_content([self.pub_team.mail], self.plan)
            self.log.info('\t4.02. Run a backup job for shared channel team.')
            backup_job = self.helper.backup([self.pub_team.mail])
            self.log.info(f'\tBackup job id {backup_job.job_id}')
            if backup_job.status.upper() != "COMPLETED":
                raise Exception(f"Backup job {backup_job.job_id} did not complete successfully.")
            self.log.info('\t5.01. DISCOVERING & ADDING %s to CONTENT.', self.pub_team_2.name)
            self.helper.set_content([self.pub_team_2.mail], self.plan)
            self.log.info('\t5.02. Run a backup job')
            backup_job = self.helper.backup([self.pub_team_2.mail])
            self.log.info(f'\tBackup job id {backup_job.job_id}')
            if backup_job.status.upper() != "COMPLETED":
                raise Exception(f"Backup job {backup_job.job_id} did not complete successfully.")

            self.log.info(f'\t6.01. Run a Restore out of place to another location for {self.pub_team_2.name}')
            restore_job = self.helper.out_of_place_restore(self.pub_team_2.mail, self.dest_team.mail)
            self.log.info(f'\tRestore job id {restore_job.job_id}')
            if restore_job.status.upper() != "COMPLETED":
                raise Exception(f"Restore job {restore_job.job_id} did not complete successfully.")
            self.dest_team.refresh_team_channels()
            self.log.info(f'\t6.02. Compare source team Files and destination team Files.')
            if not self.helper.compare_channels_files_folder(self.pub_team_2_std_ch,
                                                      self.dest_team.channels[self.pub_team_2_std_ch.name]):
                raise Exception("Failed to restore different types of files.")
            else:
                self.log.info("Files restored sucessfully.")

        except Exception as ex:
            self.log.exception(ex)
            self.status = constants.FAILED

        finally:
            self.log.info("STEP 7 - Delete all created teams.")
            self.helper.delete_team(self.pub_team)
            self.helper.delete_team(self.pub_team_2)
            self.helper.delete_team(self.dest_team)
            self.helper.remove_team_association([self.pub_team_2.mail, self.pub_team.mail])
