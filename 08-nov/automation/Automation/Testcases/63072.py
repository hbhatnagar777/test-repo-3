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
from Application.Teams.teams_constants import TeamsConstants
import time

const = TeamsConstants()

msg_type = const.MessageType


class TestCase(CVTestCase):

    def __init__(self):
        """Initializes test case class object."""

        super(TestCase, self).__init__()
        self.name = "Microsoft O365 Teams Public Channels Partial posts commit feature"
        self.show_to_user = True
        self.helper = None
        self.plan = None
        self.backup_job = None
        self.tcinputs = {
            "ClientName": None,
            "Office365Plan": None,
            "members": None,
            "accessnode": None
        }
        self.pub_team = None
        self.pub_team_gnl_ch = None

    def setup(self):
        """Setup function of this test case."""
        self.helper = TeamsHelper(self.client, self)
        self.plan = self.tcinputs.get("Office365Plan")
        self.log.info("\t1.01. Create a PUBLIC team.")
        self.pub_team = self.helper.create_public_team(members=self.tcinputs.get("members"))

        try:
            self.pub_team_gnl_ch = self.pub_team.channels["General"]
            self.log.info("\t1.02. post 130 text messages to GENERAL CHANNEL of the PUBLIC team.")
            for _ in range(130):
                self.helper.post_text_to_channel(self.pub_team_gnl_ch, msg_type.TEXT, "HI")
        except Exception as ex:
            self.helper.delete_team(self.pub_team)
            raise Exception(ex)

    def run(self):
        """Main function for test case execution."""
        self.log.info("STEP 2 - Run a BACKUP, ensure it completes.")

        self.log.info('\t2.01. DISCOVERING & ADDING %s to CONTENT.', self.pub_team.name)
        self.helper.set_content([self.pub_team.mail], self.plan)
        access_node_details = self.helper.get_hostname_and_dir()
        access_node = WindowsMachine(self.tcinputs.get("accessnode"), self.helper.commcell_object)
        self.log.info('\t2.02. set iTeamsPartialCommitPostCount reg key value to 102 under IDataAgent')
        if access_node.check_registry_exists("iDataAgent", "iTeamsPartialCommitPostCount"):
            access_node.update_registry("iDataAgent", "iTeamsPartialCommitPostCount", 102, "DWord")
        else:
            access_node.create_registry("iDataAgent", "iTeamsPartialCommitPostCount", 102, "DWord")
        try:
            self.log.info("\t2.03. Running a BACKUP.")
            self.backup_job = self.helper.backup([self.pub_team.mail], False)
            time.sleep(180)
            self.log.info("\t2.04. killing a backup job after processing 102 posts.")
            self.backup_job.kill()
            self.log.info("\tBACKUP JOB ID is %s", self.backup_job.job_id)
            time.sleep(60)
            teams = self.helper.discover()
            team_gui_id = teams[self.pub_team.mail]['user']['userGUID']

            self.log.info("\t2.05. Get left over post pages in first job.")
            path = "%s\\CV_JobResults\\iDataAgent\\Cloud Apps Agent\\2\\%s\\%s" \
                   "\\LeftoverPostPages.xml" % (access_node_details[1],
                                                self.helper._subclient._subClientEntity['subclientId'], team_gui_id)
            if not access_node.check_file_exists(path):
                raise Exception("\t       leftoverPostPages file was not created under subclient folder.")

            self.log.info('\t      set iTeamsPartialCommitPostCount reg key value to 0 under IDataAgent')
            access_node.update_registry("iDataAgent", "iTeamsPartialCommitPostCount", 0, "DWord")
            self.log.info("\t2.06. Running second backup job on same team.")
            self.backup_job = self.helper.backup([self.pub_team.mail])
            self.log.info("\tBACKUP JOB ID is %s", self.backup_job.job_id)

            self.log.info("\t2.07. Get processed post pages in second job.")
            path = "%s\\CV_JobResults\\2\\2\\%s\\%s\\ProcessedPostPages.xml" % \
                   (access_node_details[1], self.backup_job.job_id, team_gui_id)
            processed_post_pages = json.loads(json.dumps(self.helper.read_xml(path, self.tcinputs.get("accessnode"))))
            processed_pages = 0
            for page_info in processed_post_pages['ExchangeVirtualAgent_TeamPostItemsScan'] \
                    ['listChannelPostInfo']['listPostPageInfo']:
                if int(page_info['@successfulItemsCount']) <= 50:
                    processed_pages += 1
            if processed_pages == 2:
                self.log.info("partial posts commit feature was working properly.")
            else:
                raise Exception("\t       partial posts commit feature was not working properly.")

        except Exception as ex:
            self.log.exception(ex)
            self.status = constants.FAILED

        finally:
            self.helper.delete_team(self.pub_team)
            self.helper.remove_team_association([self.pub_team.mail])
            if access_node.check_registry_exists("iDataAgent", "iTeamsPartialCommitPostCount"):
                access_node.update_registry("iDataAgent", "iTeamsPartialCommitPostCount", 0, "DWord")






