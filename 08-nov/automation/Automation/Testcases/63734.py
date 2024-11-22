import time

from AutomationUtils.cvtestcase import CVTestCase
from Application.Teams.teams_helper import TeamsHelper
from Application.Teams.teams_constants import TeamsConstants
from AutomationUtils import constants

const = TeamsConstants()


class TestCase(CVTestCase):

    def __init__(self):
        """Initializes test case class object."""

        super(TestCase, self).__init__()
        self.name = "Microsoft O365 verify Archive Teams Backup and Restore Verification"
        self.show_to_user = True
        self.helper = None
        self.plan = None
        self.tcinputs = {
            "ClientName": None,
            "Office365Plan": None,
            "members": None
        }
        self.archive_team = None
        self.destination_team = None

    def setup(self):
        """Setup function of this test case."""
        self.helper = TeamsHelper(self.client)
        self.plan = self.tcinputs['Office365Plan']
        self.log.info("1 Create a public team")
        self.archive_team = self.helper.create_public_team(members=self.tcinputs['members'])
        channel = self.archive_team.channels['General']
        self.log.info("2 Post some text messages to the general channel.")
        for _ in range(10):
            self.helper.post_text_to_channel(channel, const.MessageType.TEXT)
        self.log.info("3 Upload some files to the channel")
        for _ in range(5):
            self.helper.upload_file(channel)
        self.log.info(f"4 Archive a {self.archive_team.mail}")
        self.archive_team.archive_team()
        self.log.info("5 Create a destination team")
        self.destination_team = self.helper.create_public_team(members=self.tcinputs['members'])

    def run(self):
        """Main function for test case execution."""
        self.log.info("6 Discover and add team to the content")
        self.helper.set_content([self.archive_team.mail], self.plan)
        self.log.info(f"7 Run a backup job for {self.archive_team.mail}")
        backup_job = self.helper.backup([self.archive_team.mail])
        if backup_job.status.upper() != "COMPLETED":
            raise Exception(f"Backup job {backup_job.job_id} was not completed successfully")
        self.log.info(f"Backup Job id {backup_job.job_id}")
        self.log.info(f"8 Run a restore out of place for {self.archive_team.mail} to {self.destination_team.mail}")
        restore_job = self.helper.out_of_place_restore(self.archive_team.mail, self.destination_team.mail)
        if restore_job.status.upper() != "COMPLETED":
            raise Exception(f"Restore job {restore_job.job_id} was not completed successfully")
        self.log.info(f"Restore Job id {backup_job.job_id}")
        self.log.info(f"9 Compare {self.archive_team.mail} to {self.destination_team.mail}")
        if self.helper.compare_team_items(self.archive_team.name, self.destination_team.name):
            self.log.info("Backup and Restore of Archive team was working properly")
        else:
            self.status = constants.FAILED
            raise Exception(f"Items did not matched for {self.archive_team.mail} to {self.destination_team.mail}")

    def tear_down(self):
        """Tear down function for test case"""
        self.log.info("10 Delete all created teams")
        self.helper.delete_team(self.archive_team)
        self.helper.delete_team(self.destination_team)



