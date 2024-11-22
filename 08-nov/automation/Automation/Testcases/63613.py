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
        self.name = "Microsoft O365 Teams failed items retry and deleted items validation"
        self.show_to_user = True
        self.helper = None
        self.plan = None
        self.backup_job = None
        self.tcinputs = {

        }
        self.pub_team = None
        self.pub_team_gnl_ch = None
        self.file_id = None

    def setup(self):
        """Setup function of this test case."""
        self.helper = TeamsHelper(self.client)
        self.plan = self.tcinputs.get("Office365Plan")
        self.log.info("\t1.01. Create a PUBLIC team.")
        self.pub_team = self.helper.create_public_team(members=self.tcinputs.get("members"))

        try:
            self.pub_team_gnl_ch = self.pub_team.channels["General"]
            self.log.info("\t1.02. uploading file to General CHANNEL of the PUBLIC team.")
            flag, resp = self.helper.upload_file(self.pub_team_gnl_ch, file=self.tcinputs['file_name'])
            self.file_id = resp['id']
        except Exception as ex:
            self.helper.delete_team(self.pub_team)
            raise Exception(ex)

    def run(self):
        """Main function for test  case execution."""
        self.log.info("STEP 2 - Run a BACKUP, ensure it completes.")

        self.log.info('\t2.01. DISCOVERING & ADDING %s to CONTENT.', self.pub_team.name)
        self.helper.set_content([self.pub_team], self.plan)

        acess_node = WindowsMachine(self.tcinputs.get("accessnode"), self._commcell)
        self.log.info(f"\t2.02. set sTeamsFileNamesToFail reg key value to {self.tcinputs['file_name']} under IDataAgent")
        if acess_node.check_registry_exists("iDataAgent", "sTeamsFileNamesToFail"):
            acess_node.update_registry("iDataAgent", "sTeamsFileNamesToFail", self.tcinputs['file_name'], "String")
        else:
            acess_node.create_registry("iDataAgent", "sTeamsFileNamesToFail", self.tcinputs['file_name'], "String")
        try:
            self.log.info("\t2.03. Running a BACKUP.")
            first_job = self.helper.backup([self.pub_team])
            self.log.info("\tBACKUP JOB ID is %s", first_job.job_id)
            team_gui_id = self.pub_team.id.upper().replace("-", "X")

            self.log.info("\t2.05. Get failed files in first job.")
            path = "%s\\iDataAgent\\JobResults\\CV_JobResults\\2\\2\\%s\\%s\\FailedItems.csv" % \
                   (self.tcinputs.get("path"), first_job.job_id, team_gui_id)
            retry = 3
            created = False
            while retry and not created:
                if acess_node.check_file_exists(path):
                    created = True
                    break
                time.sleep(10)
                retry -= 1
            if not created:
                raise Exception("\t       failed items file was not created under job result folder.")

            first_job_failed_file = acess_node.read_file(file_path=path)
            is_file_present = False
            first_job_retry_count = 0
            for entry in first_job_failed_file.split("\n")[1:]:
                item = entry[:-1].split(",")[1]
                if self.tcinputs['file_name'] in item:
                    is_file_present = True
                    count = entry[:-1].split(",")[-1]
                    count.strip("'")
                    first_job_retry_count = int(count[1:-1])
                    break
            if not is_file_present:
                raise Exception("File not failed")

            second_job = self.helper.backup([self.pub_team])
            self.log.info("\tBACKUP JOB ID is %s",second_job.job_id)
            team_gui_id = self.pub_team.id.upper().replace("-", "X")

            self.log.info("\t2.05. Get failed files in second job.")
            path = "%s\\iDataAgent\\JobResults\\CV_JobResults\\2\\2\\%s\\%s\\FailedItems.csv" % \
                   (self.tcinputs.get("path"), second_job.job_id, team_gui_id)
            retry = 3
            created = False
            while retry and not created:
                if acess_node.check_file_exists(path):
                    created = True
                    break
                time.sleep(10)
                retry -= 1
            if not created:
                raise Exception("\t       failed items file was not created under job result folder.")

            second_job_failed_file = acess_node.read_file(file_path=path)
            is_file_present = False
            second_job_retry_count = 0
            for entry in second_job_failed_file.split("\n")[1:]:
                item = entry[:-1].split(",")[1]
                if self.tcinputs['file_name'] in item:
                    is_file_present = True
                    count = entry[:-1].split(",")[-1]
                    count.strip("'")
                    second_job_retry_count = int(count[1:-1])
                    break
            if not is_file_present:
                raise Exception("File not failed")

            if second_job_retry_count > first_job_retry_count:
                self.log.info("Retry for failed items working fine")
            else:
                raise Exception("Retry failed items not working")

            self.log.info(f"Delete {self.tcinputs['file_name']} from {self.pub_team_gnl_ch.name}")
            self.pub_team_gnl_ch.delete_item(self.file_id)
            second_job = self.helper.backup([self.pub_team])
            self.log.info("\tBACKUP JOB ID is %s", second_job.job_id)
            team_gui_id = self.pub_team.id.upper().replace("-", "X")

            self.log.info("\t2.05. Get failed files in second job.")
            path = "%s\\iDataAgent\\JobResults\\CV_JobResults\\2\\2\\%s\\%s\\FailedItems.csv" % \
                   (self.tcinputs.get("path"), second_job.job_id, team_gui_id)
            retry = 3
            created = False
            while retry and not created:
                if acess_node.check_file_exists(path):
                    created = True
                    break
                time.sleep(10)
                retry -= 1
            if not created:
                raise Exception("\t       failed items file was not created under job result folder.")

            second_job_failed_file = acess_node.read_file(file_path=path)
            print(second_job_failed_file.split("\n"))
            is_file_present = False
            if len(second_job_failed_file.split("\n")) > 2:
                is_file_present = True
            if is_file_present:
                raise Exception("File not deleted from failed items after deletion from source")

        except Exception as ex:
            self.log.exception(ex)
            self.status = constants.FAILED

        finally:
            self.helper.delete_team(self.pub_team)
            self.log.info("Removing Team from Content\n")
            self.helper.remove_team_association([self.pub_team.mail])
            if acess_node.check_registry_exists("iDataAgent", "sTeamsFileNamesToFail"):
                acess_node.update_registry("iDataAgent", "sTeamsFileNamesToFail", "", "String")






