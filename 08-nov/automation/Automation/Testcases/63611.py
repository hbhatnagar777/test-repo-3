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
        self.name = "Microsoft O365 Teams Onenote Backup and Restore Verification"
        self.show_to_user = True
        self.helper = None
        self.plan = None
        self.tcinputs = {
            "ClientName": None,
            "Office365Plan": None,
            "members": None
        }
        self.pub_team = None
        self.pub_team2 = None

    def setup(self):
        """Setup function of this test case."""
        self.helper = TeamsHelper(self.client, self)
        self.plan = self.tcinputs['Office365Plan']
        self.log.info("1.create a public team.")
        self.pub_team = self.helper.create_public_team(members=self.tcinputs['members'])
        sharepoint_obj = self.pub_team.sharepoint_site_obj
        self.log.info("2. create notebook")
        notebook_id = sharepoint_obj.create_note_book()
        self.log.info("3. Create section")
        section_id = sharepoint_obj.create_section(note_book_id=notebook_id)
        self.log.info("4. create section pages")
        for _ in range(5):
            sharepoint_obj.create_section_page(section_id)
        self.log.info("5. Create section group")
        section_group_id = sharepoint_obj.create_section_group(note_book_id=notebook_id)
        self.log.info("6. Create section in a section group")
        section_id = sharepoint_obj.create_section_to_the_section_group(section_group_id)
        self.log.info("7. Create section pages in a section group section")
        for _ in range(5):
            sharepoint_obj.create_section_page(section_id)
        self.log.info("8. create destination team")
        self.pub_team2 = self.helper.create_public_team(members=self.tcinputs['members'])

    def run(self):
        """Main function for test case execution."""

        self.log.info(f"9. Add {self.pub_team.mail} to the content")
        self.helper.set_content([self.pub_team.mail],self.plan)
        self.log.info(f"10 Running a backup job for {self.pub_team.mail}")
        backup_job = self.helper.backup([self.pub_team.mail])
        self.log.info(f"Backup JOb Id {backup_job.job_id}")
        self.log.info(f"11. Run a restore out pf place to {self.pub_team2.mail}")
        restore_job = self.helper.out_of_place_restore(self.pub_team.mail,self.pub_team2.mail)
        self.log.info(f"Backup JOb Id {restore_job.job_id}")
        self.log.info("12 Compare source Notebook and Restored Notebook")
        if(self.helper.compare_one_note_of_sharepoint_sites(self.pub_team.sharepoint_site_obj,
                                                               self.pub_team2.sharepoint_site_obj)):
            self.log.info("Notebook backup and restore working fine")
        else:
            self.status = constants.FAILED
            raise Exception("Notebook Backup and restore not working")

    def tear_down(self):
        self.log.info("13 Deleting Teams")
        self.helper.delete_team(self.pub_team)
        self.helper.delete_team(self.pub_team2)












