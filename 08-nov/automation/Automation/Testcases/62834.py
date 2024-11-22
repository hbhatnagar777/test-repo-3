# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()      --  initialize TestCase class

    setup()         --  setup function of this test case

    previous_run_cleanup() -- for deleting the left over
    backupset and storage policy from the previous run

    create_resources()      -- creates the required resources/ defines
                                paths for this testcase

    run()           --  run function of this test case

    tear_down()     --  tear down function of this test case

This is the testcase for checking that administrative shares are being blocked in Commvault.
Blocking Library Creation and Mountpath Addition with Admin Shares.

input json file arguments required:

                       : {
                                    "ClientName": "",
                                    "AgentName": "File System",
                                    "MediaAgentName": "",
                                    "admin_share_path": "",
                                    "network_username":"",
                                    "network_password":""
                                }

                        "library_name": name of the Library to be reused
                        "admin_share_path": input example
                            \\\\dummymachine\\C$\\path\\directory\\folder\\mount_path",

                        note --
                                ***********************************
                                if library_name_given then reuse_library
                                else it will auto_generate_library_path

                                ***********************************
"""
# Design Steps:
# clean up previous run config, Create resources.
# try to create a new library with mount path using admin shares.
#     check in Media Manager log that it gets blocked with correct error.
# try to add a mount path to an existing disk library using admin shares.
#     check in Media Manager log that it gets blocked with correct error.
# try to share a mount path using admin shares.
#     check in Media Manager log that it gets blocked with correct error.

import re
import time
from AutomationUtils import constants, machine
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.options_selector import OptionsSelector
from MediaAgents.MAUtils import mahelper


class TestCase(CVTestCase):
    """Class for executing this test case"""

    def __init__(self):
        """Initializes test case class object

            Properties to be initialized:

                name            (str)       --  name of this test case

                tcinputs        (dict)      --  test case inputs with input name as dict key
                                                and value as input type

        """
        super(TestCase, self).__init__()
        self.name = "Blocking Library Creation and Mountpath Addition with Admin Shares."

        self.tcinputs = {
            "MediaAgentName": None,
            "admin_share_path": None,
            "network_username": None,
            "network_password": None
        }

        self.mount_path = None
        self.testcase_path = None
        self.testcase_path_media_agent = None

        self.mm_helper = None
        self.dedup_helper = None
        self.opt_selector = None

        self.client_machine = None
        self.media_agent_machine = None

        self.library_name = None
        self.library = None
        self.is_user_defined_lib = False
        self.suffix = None

    def setup(self):
        """sets up the variables to be used in testcase"""
        if self.tcinputs.get("library_name"):
            self.is_user_defined_lib = True

        self.suffix = str(self.tcinputs["MediaAgentName"]) + str(self.tcinputs["ClientName"])
        if self.is_user_defined_lib:
            self.log.info("Existing library name supplied")
            self.library_name = self.tcinputs.get("library_name")
        else:
            self.library_name = f"{str(self.id)}_lib{self.suffix}"

        self.dedup_helper = mahelper.DedupeHelper(self)
        self.mm_helper = mahelper.MMHelper(self)
        self.opt_selector = OptionsSelector(self.commcell)
        self.client_machine = machine.Machine(
            self.client.client_name, self.commcell)
        self.media_agent_machine = machine.Machine(
            self.tcinputs["MediaAgentName"], self.commcell)

    def previous_run_clean_up(self):
        """
        delete previous run items

        Args:
            None

        Returns:
            None
        """

        self.log.info("********* previous run clean up **********")
        try:
            if not self.is_user_defined_lib:
                if self.commcell.disk_libraries.has_library(self.library_name):
                    self.commcell.disk_libraries.delete(self.library_name)
                    self.log.info("Library deleted")
                else:
                    self.log.info("Library does not exist.")
            self.log.info("clean up COMPLETED")

        except Exception as exp:
            self.log.info("clean up ERROR")
            self.log.info("ERROR:%s", exp)


    def create_resources(self):
        """
        creates the required resources/ defines paths for this testcase

        Args:
            None

        Returns:
            None

        """
        if not re.fullmatch(r"^\\\\[a-zA-Z0-9\-\_]+\\[a-zA-Z0-9\-\_]+\$\\[a-zA-Z0-9\-\_\\]+$",
                            self.tcinputs.get("admin_share_path")):
            raise Exception("Admin share UNC path supplied is not in correct format. Please check test case documentation for more details.")

        # create the required resources for the testcase
        # get the drive path with required free space
        drive_path_media_agent = self.opt_selector.get_drive(self.media_agent_machine)
        self.testcase_path_media_agent = f"{drive_path_media_agent}{self.id}"
        self.mount_path = self.media_agent_machine.join_path(
            self.testcase_path_media_agent, "mount_path")

        # if user defined library exists don't create new else create new library
        if self.commcell.disk_libraries.has_library(self.tcinputs.get("library_name", "library does not exist")):
            self.log.info("user defined library already exists - %s", self.tcinputs.get("library_name"))
            self.library = self.commcell.disk_libraries.get(self.tcinputs.get("library_name"))
        else:
            # create library
            self.library = self.mm_helper.configure_disk_library(
                library_name=self.library_name,
                ma_name=self.tcinputs["MediaAgentName"],
                mount_path=self.mount_path)

    def run(self):
        """Run function of this test case"""
        try:
            # clean up previous run config, Create resources.
            self.previous_run_clean_up()
            self.create_resources()
            # we created a regular disk library in create resources.

            error_flag = []

            new_lib = self.media_agent_machine.join_path(self.tcinputs.get("admin_share_path"), "new_lib")
            if not self.media_agent_machine.check_directory_exists(new_lib):
                self.media_agent_machine.create_directory(new_lib)

            # try to create a new library using admin shares
            try:
                self.commcell.disk_libraries.add("admin_share"+self.suffix,
                                                 self.tcinputs.get("MediaAgentName"),
                                                 new_lib,
                                                 self.tcinputs.get("network_username"),
                                                 self.tcinputs.get("network_password"))
            except Exception as e:
                self.log.info("New library creation using admin shares did not happen")
                self.log.info(str(e))

            self.log.info("***********************************************")
            self.log.info("check 1 - try to add admin share mount path through a new library")
            # sample log lines we are trying to find
            # Admin shares are not allowed to configure as Device Controller Path [\\admin_share\C$\mount_path]
            # Admin shares is not allowed to configure as Device Controller Path [\\admin_share\C$\mount_path]
            blocked = False
            log_lines = []
            find_string = "Admin shares .* not allowed to configure as Device Controller Path"

            (matched_lines, matched_string) = self.dedup_helper.parse_log(
                self.commcell.commserv_name,
                "MediaManager.log",
                regex=find_string,
                escape_regex=False, single_file=False)

            if matched_lines:
                for matched_line in matched_lines:
                    if new_lib in matched_line:
                        blocked = True
                        log_lines.append(matched_line)

            if blocked:
                self.log.info("Result check 1:Pass")
                self.log.info(log_lines)
            else:
                self.log.error("Result check 1: Failed")
                error_flag += ["We did not find the log line depicting creation of"
                               " mount path using admin share for a new library"
                               " is blocked in MediaManager logs."]
            self.log.info("******************************************")

            existing_mount_path = self.media_agent_machine.join_path(self.tcinputs.get("admin_share_path"),
                                                                     "existing_mount_path")
            if not self.media_agent_machine.check_directory_exists(existing_mount_path):
                self.media_agent_machine.create_directory(existing_mount_path)

            # try to add admin share mount path to an existing disk library
            try:
                self.library.add_mount_path(mount_path=existing_mount_path,
                                            media_agent=self.tcinputs.get("MediaAgentName"),
                                            username=self.tcinputs.get("network_username"),
                                            password=self.tcinputs.get("network_password"))
            except Exception as e:
                self.log.info("Adding admin share mount path to existing Library did not happen")
                self.log.info(str(e))

            self.log.info("***********************************************")
            self.log.info("check 2 - try to add admin share mount path to an existing library")
            # sample log line
            # Admin shares is not allowed to configure as Device Controller Path [\\admin_share\C$\mount_path]
            blocked = False
            log_lines = []
            find_string = "Admin shares .* not allowed to configure as Device Controller Path"

            (matched_lines, matched_string) = self.dedup_helper.parse_log(
                self.commcell.commserv_name,
                "MediaManager.log",
                regex=find_string,
                escape_regex=False, single_file=False)

            if matched_lines:
                for matched_line in matched_lines:
                    if existing_mount_path in matched_line:
                        blocked = True
                        log_lines.append(matched_line)

            if blocked:
                self.log.info("Result check 2:Pass")
                self.log.info(log_lines)
            else:
                self.log.error("Result check 2: Failed")
                error_flag += [f"We did not find the log line depicting creation of"
                               f" mount path using admin share to an existing library"
                               f" is blocked in MediaManager logs."]
            self.log.info("******************************************")

            share_mount_path = self.media_agent_machine.join_path(self.tcinputs.get("admin_share_path"),
                                                                  "share_mount_path")
            if not self.media_agent_machine.check_directory_exists(share_mount_path):
                self.media_agent_machine.create_directory(share_mount_path)

            # try to share a mount path using admin share
            try:
                all_MAs = self.commcell.media_agents.all_media_agents
                for MA in all_MAs.items():
                    # dont choose the same MA as given in input
                    if MA[0] != self.tcinputs.get("MediaAgentName") and MA[1]['is_online']:
                        new_ma = MA[0]
                        break

                # due to media agent not being associated with library object explicit declaration needed
                self.library.media_agent = self.tcinputs.get("MediaAgentName")

                # due to mount path not being associated with library object explicit declaration needed
                self.library.mount_path = self.mount_path

                self.library.share_mount_path(new_mount_path=share_mount_path,
                                              new_media_agent=new_ma,
                                              access_type=6,
                                              username=self.tcinputs.get("network_username"),
                                              password=self.tcinputs.get("network_password"))
            except Exception as e:
                self.log.info("Sharing admin share mount path did not happen")
                self.log.info(str(e))

            self.log.info("***********************************************")
            self.log.info("check 3 - try to share mount path using admin share")
            # sample log line
            # Error occurred while adding device controller for device[some_number] clientId[some_number]
            #  folder[\\admin_share\C$\mount_path]

            blocked = False
            log_lines = []
            find_string = "Error occurred while adding device controller"

            (matched_lines, matched_string) = self.dedup_helper.parse_log(
                self.commcell.commserv_name,
                "MediaManager.log",
                regex=find_string,
                escape_regex=True, single_file=False)

            if matched_lines:
                for matched_line in matched_lines:
                    if share_mount_path in matched_line:
                        blocked = True
                        log_lines.append(matched_line)

            if blocked:
                self.log.info("Result check 3:Pass")
                self.log.info(log_lines)
            else:
                self.log.error("Result check 3: Failed")
                error_flag += [f"We did not find the log line depicting sharing of"
                               f" mount path using admin share"
                               f" is blocked in MediaManager logs."]
            self.log.info("******************************************")

            if error_flag:
                # if the list is not empty then error was there, fail the testcase
                self.log.info(error_flag)
                raise Exception(f"testcase failed: {error_flag}")

        except Exception as exp:
            self.log.error('Failed to execute test case with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED

    def tear_down(self):
        """delete all items created for the testcase"""
        try:
            self.log.info("*********************************************")
            self.log.info("Restoring defaults")

            self.previous_run_clean_up()

        except Exception as exp:
            self.log.info("clean up not successful")
            self.log.info("ERROR:%s", exp)
