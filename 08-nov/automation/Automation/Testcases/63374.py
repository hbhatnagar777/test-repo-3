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
from Application.Teams.teams_constants import TeamsConstants
from AutomationUtils import constants
const = TeamsConstants()

file_type = const.FileType


class TestCase(CVTestCase):

    def __init__(self):
        """Initializes test case class object."""

        super(TestCase, self).__init__()
        self.name = "Microsoft O365 Teams Sharepoint Site Document Library Backup and Restore."
        self.show_to_user = True
        self.helper = None
        self.plan = None
        self.backup_job = None
        self.tcinputs = {
            "ClientName": None,
            "Office365Plan": None,
            "members": None
        }
        self.pub_team = None
        self.dest_team = None

    def setup(self):
        """Setup function of this test case."""
        self.helper = TeamsHelper(self.client, self)
        self.plan = self.tcinputs.get("Office365Plan")
        self.log.info("\t1.01. Create a PUBLIC team.")
        self.pub_team = self.helper.create_public_team(members=self.tcinputs.get("members"))

        try:
            self.log.info("\t1.02. Create document libraries.")
            self.pub_team.create_document_library("LIBRARY_1")
            self.pub_team.create_document_library("LIBRARY_2")
            self.pub_team.create_document_library("LIBRARY_3")
            self.log.info("\t1.03. upload some files and folders to the  document libraries.")
            self.pub_team.upload_file_to_document_library(name="LIBRARY_1", f_type=file_type.TEXT)
            self.pub_team.upload_file_to_document_library(name="LIBRARY_1", f_type=file_type.JPG)
            self.pub_team.upload_file_to_document_library(name="LIBRARY_1", f_type=file_type.PNG)
            self.pub_team.upload_file_to_document_library(name="LIBRARY_2", f_type=file_type.DOCX)
            self.pub_team.upload_file_to_document_library(name="LIBRARY_2", f_type=file_type.PPTX)
            self.pub_team.upload_file_to_document_library(name="LIBRARY_2", f_type=file_type.PDF)
            self.pub_team.upload_file_to_document_library(name="LIBRARY_3", f_type=file_type.XLSX)
            self.pub_team.upload_file_to_document_library(name="LIBRARY_3", f_type=file_type.MP3)
            self.pub_team.upload_file_to_document_library(name="LIBRARY_3", f_type=file_type.DOCX)
            self.pub_team.upload_file_to_document_library(name="LIBRARY_3", f_type=file_type.BIN)
            flag, resp = self.pub_team.upload_folder_to_document_library(name='LIBRARY_1')
            self.pub_team.upload_file_to_document_library(name='LIBRARY_1', parent_id=resp['id'])
            self.log.info("\t1.04. Create a PUBLIC team.")
            self.dest_team = self.helper.create_public_team(members=self.tcinputs.get("members"))
        except Exception as ex:
            self.helper.delete_team(self.pub_team)
            self.helper.delete_team(self.dest_team)
            raise Exception(ex)

    def run(self):
        """Main function for test case execution."""
        self.log.info("STEP 2 - Run a BACKUP, ensure it completes.")

        try:
            self.log.info('\t2.01. DISCOVERING & ADDING %s to CONTENT.', self.pub_team.name)
            self.helper.set_content([self.pub_team.mail], self.plan)
            self.log.info("\t2.02. Running a BACKUP.")
            self.backup_job = self.helper.backup([self.pub_team.mail])
            if self.backup_job.status.upper() != "COMPLETED":
                raise Exception(f"Backup job {self.backup_job.job_id} did not complete successfully.")
            self.log.info("\tBACKUP JOB ID is %s", self.backup_job.job_id)
            self.log.info("\t2.03. Restore Team to out of place to another team.")
            restore_job = self.helper.out_of_place_restore(self.pub_team.mail, self.dest_team.mail)
            if restore_job.status.upper() != "COMPLETED":
                raise Exception(f"Restore job {restore_job.job_id} did not complete successfully.")
            self.log.info("\tRestore JOB ID is %s", restore_job.job_id)
            self.dest_team._compute_document_libraries_to_team()
            self.log.info("\t2.04. Now compare source team and destination team Document Libraries.")
            if not (self.helper.compare_document_libraries_of_teams(self.pub_team, self.dest_team)):
                raise Exception(f"\tlibraries of {self.pub_team.name} and {self.dest_team.name} team did not match")

        except Exception as ex:
            self.log.exception(ex)
            self.status = constants.FAILED

        finally:
            self.helper.delete_team(self.pub_team)
            self.helper.delete_team(self.dest_team)
            self.log.info("Removing Team from Content\n")
            self.helper.remove_team_association([self.pub_team.mail])







