
# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""Main file for executing this test case

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
from AutomationUtils import constants

from Application.Teams.teams_constants import TeamsConstants

const = TeamsConstants()

msg_type = const.MessageType


class TestCase(CVTestCase):
    def __init__(self):
        """Initializes test case class object."""

        super(TestCase, self).__init__()
        self.name = "Microsoft O365 Teams Public Channels - Backup & Restore to File location"
        self.show_to_user = True
        self.helper = None
        self.plan = None
        self.backup_job = None
        self.tcinputs = {
            "ClientName": None,
            "Office365Plan": None,
            "IndexServer": None,
            "destination_client": None,
            "destination_path": None,
            "members": None
        }
        self.pub_team = None
        self.pub_team_std_ch = None
        self.items = []
        self.files_count = 0
        self.destination_path = None

    def setup(self):
        """Setup function of this test case."""
        self.helper = TeamsHelper(self.client, self)
        self.plan = self.tcinputs.get("Office365Plan")
        self.destination_path = self.tcinputs.get("destination_path")

        self.log.info("STEP 1 - Create test data.")

        self.log.info("\t1.01. Create a PUBLIC team.")
        self.pub_team = self.helper.create_public_team(members=self.tcinputs.get("members"))

        try:
            self.log.info("\t1.02. Create a STANDARD CHANNEL for the PUBLIC team.")
            self.pub_team_std_ch = self.helper.create_standard_channel(self.pub_team)

            self.items.append(
                self.destination_path + "\\" + self.pub_team.name + "\\" + self.pub_team_std_ch.name)

            self.items.append(
                self.destination_path + "\\" + self.pub_team.name + "\\" + self.pub_team_std_ch.name + "\\" + "Files")
            self.items.append(
                self.destination_path + "\\" + self.pub_team.name + "\\" + self.pub_team_std_ch.name + "\\" + "Posts")

            self.files_count+=1
            self.log.info(f"\t Upload a Folder to {self.pub_team_std_ch.name} of PUBLIC team.")
            flag, resp = self.pub_team_std_ch.upload_folder(folder_name='A')
            parent_id = resp['id']
            self.items.append(self.items[1] + "\\" + "A")
            self.log.info(f"\t1.03. Upload a FILE to A FOLDER.")
            self.helper.upload_file(self.pub_team_std_ch,"file_"+str(self.files_count)+".txt", parent_id=parent_id)
            self.items.append(self.destination_path + "\\" + self.pub_team.name + "\\" + self.pub_team_std_ch.name +
                              "\\" + "Files" + "\\" + "A" + "\\" + "file_" + str(self.files_count) + ".txt")

            self.files_count += 1
            self.log.info(f"\t1.04. Upload a FILE to {self.pub_team_std_ch.name} of PUBLIC team.")
            self.helper.upload_file(self.pub_team_std_ch,"file_"+str(self.files_count)+".txt")
            self.items.append(
                self.destination_path + "\\" + self.pub_team.name + "\\" + self.pub_team_std_ch.name + "\\" + "Files" +
                "\\" + "file_" + str(self.files_count) + ".txt")

            self.log.info(f"\t1.05. POST a few conversation items to {self.pub_team_std_ch.name} of PUBLIC team.")
            self.helper.post_text_to_channel(self.pub_team_std_ch, msg_type.TEXT, "HI")
            self.helper.post_text_to_channel(self.pub_team_std_ch, msg_type.TEXT, "GOOD MORNING")
            self.helper.post_text_to_channel(self.pub_team_std_ch, msg_type.TEXT, "THANK U")

            self.items.append(self.destination_path + "\\" + self.pub_team.name + "\\" + self.pub_team_std_ch.name +
                              "\\" + "Posts" + "\\" + "conv_restore.html")
        except Exception as ex:
            self.helper.delete_team(self.pub_team)
            raise Exception(ex)

    def run(self):
        """Main function for test case execution."""
        try:
            self.log.info("STEP 2 - Run a BACKUP, ensure it completes.")

            self.log.info('\t2.01. DISCOVERING & ADDING %s to CONTENT.', self.pub_team.name)
            self.helper.set_content([self.pub_team.mail], self.plan)

            self.log.info("\t2.02. Running a BACKUP.")
            self.backup_job = self.helper.backup([self.pub_team.mail])
            if self.backup_job.status.upper() != "COMPLETED":
                raise Exception(f"Backup job {self.backup_job.job_id} did not complete successfully.")
            self.log.info("\t      Backup job ID is %s\n", self.backup_job.job_id)

            self.log.info("STEP 3 - Restore TEAMS OUT OF PLACE TO FILE LOCATION, ensure it completes.")

            self.log.info("\t3.01. Running a RESTORE.")
            restore_job = self.helper.out_of_place_restore_to_file_location(self.pub_team.mail,
                                                                            self.tcinputs.get("destination_client"),
                                                                            self.destination_path,
                                                                            self.helper
                                                                            )

            if restore_job.status.upper() != "COMPLETED":
                raise Exception(f"Restore job {restore_job.job_id} did not complete successfully.")
            self.log.info("\t      Restore job ID is %s\n", restore_job.job_id)

            self.log.info("STEP 4 - COMPARE SOURCE TEAM ITEMS AND ITEMS in a RESTORED FILE LOCATION")

            destination_client = WindowsMachine(self.tcinputs.get("destination_client"), self.commcell)
            if(sorted(destination_client.get_items_list(self.destination_path + "\\" + self.pub_team.name)) ==
                    sorted(self.items)):
                self.log.info("\t      Team sucessfully Restored to file location.")
            else:
                raise Exception("\t       Team was not restored sucessfully.")
        except Exception as ex:
            self.log.exception(ex)
            self.status = constants.FAILED

        finally:
            self.helper.delete_team(self.pub_team)
            self.helper.remove_team_association([self.pub_team.mail])
