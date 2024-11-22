# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()                  --  initialize TestCase class

    setup()                     --  setup function of this test case

    run()                       --  run function of this test case
    
    create_library()            --  adds a new disk library to the commcell from json inputs
    
    create_storage_policy()     --  adds a new storage policy from the library created
    
    create_schedule_policy()    --  creates an Aux Copy schedule policy associated to previously created storage policy
    
    create_user()               --  creates a new user with view role
    
    create_usergroup()          --  creates a new usergroup comprising of the user created earlier
    
    create_alert()              --  creates an event viewer alert associated to previously created library
    
    ccm_export()                --  performs CCM Export to new folder inside UNC export location (from json inputs)
    
    ccm_import()                --  performs CCM Import on the destination CS from same folder inside local path
    
    verify_import()             --  verifies all entities are migrated successfully without modification
    
    delete_entities()           --  deletes all entities in source CS (including library and policy)

    verify_deletion()           --  verifies all entities are deleted in destination CS

"""

import time
from AutomationUtils.cvtestcase import CVTestCase
from Server.Alerts.alert_helper import AlertHelper
from Server.CommcellMigration.ccmhelper import CCMHelper
from Server.Scheduler.schedulepolicyhelper import SchedulePolicyHelper
from Server.Security.usergrouphelper import UsergroupHelper
from Server.Security.userhelper import UserHelper
from AutomationUtils.options_selector import OptionsSelector


class TestCase(CVTestCase):
    """Class for executing this test case"""

    def __init__(self):
        """Initializes test case class object

            Properties to be initialized:

                name            (str)       --  name of this test case

                tcinputs        (dict)      --  test case inputs with input name as dict key
                                                and value as input type

                every object variable I will setup is initialized/declared here

        """
        super(TestCase, self).__init__()
        self.folder_name = None
        self.schedule_policy_name = None
        self.policy_name = None
        self.library_name = None
        self.optor = None
        self.destination_cs = None
        self.source_cs = None
        self.ccm_helper = None
        self.alert_name = None
        self.alert_helper = None
        self.user_group = None
        self.user_group_name = None
        self.usergroup_helper = None
        self.user_helper = None
        self.user = None
        self.password = None
        self.user_name = None
        self.schedule_policy_helper = None
        self.storage_policy = None
        self.library = None
        self.time = None
        self.sphelper = None
        self.name = "server_commcellmigration _deleted entities not present"
        self.tcinputs = {
            "media_agent": None,
            "lib_mount_path": None,
            "DestinationCSHostName": None,
            "CSUserName": None,
            "CSPassword": None,
            "DoNotVerifyUsers": None,
            "ExportPathType": None,
            "ExportUserName": None,
            "ExportPassword": None,
            "ExportLocation": None,
            "ImportLocation": None
        }

    def setup(self):
        """
            Setup function of this test case
            All entities are created in src commcell here with arbitrary values whose deletion will be exported to dest
            commcell later. ccm helper and destination commcell objects are also created here

        """
        self.verify_users = not bool(self.tcinputs["DoNotVerifyUsers"])
        self.library_name = OptionsSelector.get_custom_str("library")
        self.policy_name = OptionsSelector.get_custom_str("policy")
        self.schedule_policy_name = OptionsSelector.get_custom_str("schedule_policy")
        self.folder_name = OptionsSelector.get_custom_str("dump")
        self.create_library()
        self.create_storage_policy()
        # self.create_subclient_policy()  sdk support required
        self.create_schedule_policy()
        self.create_user()
        self.create_usergroup()
        self.create_alert()
        # self.create_media_location()  sdk support required
        self.ccm_helper = CCMHelper(self)
        self.ccm_helper.create_destination_commcell(self.tcinputs["DestinationCSHostName"],
                                                    self.tcinputs["CSUserName"],
                                                    self.tcinputs["CSPassword"])

    def run(self):
        """Run function of this test case"""
        self.ccm_export()
        self.ccm_import()
        self.verify_import()
        self.delete_entities()
        self.ccm_export("postdelete")
        self.ccm_import("postdelete")
        self.verify_deletion()

    def create_library(self):
        self.library = self.commcell.disk_libraries.add(self.library_name,
                                                        self.tcinputs["media_agent"],
                                                        self.tcinputs["lib_mount_path"])
        self.log.info('Successfully created disk_library {}'.format(self.library_name))

    def create_storage_policy(self):
        self.storage_policy = self.commcell.storage_policies.add(self.policy_name,
                                                                 self.library,
                                                                 self.tcinputs["media_agent"])
        self.log.info('Successfully created {}'.format(self.policy_name))

    def create_schedule_policy(self):
        """Creates an Aux Copy schedule policy associated to previously created storage policy"""
        self.log.info('Setting up to create new schedule policies')
        self.schedule_policy_helper = SchedulePolicyHelper(self.commcell)
        schedule_associations = [{'storagePolicyName': self.policy_name}]
        schedules = [
            {
                "freq_type": 'daily',
                "active_start_time": '12:00',
                "repeat_days": 7
            },

            {
                "maxNumberOfStreams": 0,
                "useMaximumStreams": True,
                "useScallableResourceManagement": True,
                "totalJobsToProcess": 1000,
                "allCopies": True,
                "mediaAgent": {
                    "mediaAgentName": self.tcinputs["media_agent"]
                }
            }
        ]
        self.schedule_policy_helper.create_schedule_policy(self.schedule_policy_name, 'Auxiliary Copy',
                                                           schedule_associations, schedules)
        self.log.info('Successfully created schedule policy')

    def create_user(self):
        """Creates a new user with view role"""
        self.log.info('Creating new user')
        self.user_helper = UserHelper(self.commcell)
        self.user_name = OptionsSelector.get_custom_str("test_user")
        self.password = OptionsSelector.get_custom_password(9, True)
        security_dict = {
            'assoc1':
                {
                    'storagePolicyName': [self.policy_name],
                    'role': ['View']
                }
        }
        self.user = self.user_helper.create_user(self.user_name, '{}@email.com'.format(self.user_name),
                                                 self.user_name, None, self.password, None,
                                                 security_dict)
        self.log.info('Successfully created new user {}'.format(self.user_name))

    def create_usergroup(self):
        """Creates a new usergroup comprising of the user created earlier"""
        self.log.info('Creating new user group')
        self.usergroup_helper = UsergroupHelper(self.commcell)
        usergroup_entity_dict = {
            'assoc1':
                {
                    'storagePolicyName': [self.policy_name],
                    'role': ['View']
                }
        }
        self.user_group_name = OptionsSelector.get_custom_str("test_user_group")
        self.user_group = self.usergroup_helper.create_usergroup(self.user_group_name, None,
                                                                 [self.user_name],
                                                                 usergroup_entity_dict)
        self.log.info('Successfully created user group {}'.format(self.user_group_name))

    def create_alert(self):
        """Creates an event viewer alert associated to previously created library"""
        self.log.info('Creating new alert')
        self.alert_helper = AlertHelper(self._commcell, 'Media Management', 'Library Management')
        self.alert_name = OptionsSelector.get_custom_str("test_alert")
        self.alert_helper.get_alert_details(self.alert_name,
                                            ['Event Viewer'],
                                            {'disk_libraries': self.library_name},
                                            ['admin'], 22)
        self.alert_helper.create_alert()
        self.log.info('Successfully created alert {}'.format(self.alert_name))

    def ccm_export(self, suffix=""):
        """Function to perform CCM Export to new folder inside export location"""
        options = {
            'pathType': self.tcinputs["ExportPathType"],
            'userName': self.tcinputs["ExportUserName"],
            'password': self.tcinputs["ExportPassword"],
            'captureMediaAgents': False
        }

        ccm_job = self.ccm_helper.run_ccm_export(self.tcinputs["ExportLocation"] + self.folder_name + suffix,
                                                 other_entities=["schedule_policies", "users_and_user_groups",
                                                                 "alerts"],
                                                 options=options)

        self.log.info("Started CCM Export Job: %s", ccm_job.job_id)

        if ccm_job.wait_for_completion():
            self.log.info("CCM Export Job id %s completed successfully", ccm_job.job_id)
        else:
            self.log.error("CCM Export Job id %s failed/ killed", ccm_job.job_id)
            raise Exception("CCM Export job failed")

    def ccm_import(self, suffix=""):
        """Function to perform CCM Import from folder inside export location"""
        options = {
            'forceOverwrite': True,
            'deleteEntitiesNotPresent': True,
            'deleteEntitiesIfOnlyfromSource': True
        }
        import_job = self.ccm_helper.run_ccm_import(self.tcinputs["ImportLocation"] + self.folder_name + suffix,
                                                    options=options)
        self.log.info("Started CCM Import Job: %s", import_job.job_id)

        if import_job.wait_for_completion():
            self.log.info("CCM Import Job id %s completed successfully", import_job.job_id)
        else:
            self.log.error("CCM Import Job id %s failed/ killed", import_job.job_id)
            raise Exception("CCM Import job failed")

    def verify_import(self):
        """Function to verify entities migrated during Commcell Migration on destination commserv."""
        self.source_cs = self._commcell
        self.destination_cs = self.ccm_helper._destination_cs

        alert = self.destination_cs.alerts.get(self.alert_name)
        alert_name = alert.alert_name
        alert_type = alert.alert_type
        alert_category = alert.alert_category

        schedule_policy = self.destination_cs.schedule_policies.get(self.schedule_policy_name)
        schedule_policy_name = schedule_policy.schedule_policy_name
        schedule_policy_type = schedule_policy.policy_type

        user = self.destination_cs.users.get(self.user_name)
        user_name = user.user_name
        user_email = user.email

        user_group = self.destination_cs.user_groups.get(self.user_group_name)

        user_group_name = user_group.user_group_name

        if alert_name == self.alert_name and \
                alert_type == "Library Management" and \
                alert_category == "Media Management" and \
                schedule_policy_name == self.schedule_policy_name and \
                schedule_policy_type == "Auxiliary Copy" and \
                user_name == self.user_name and \
                user_email == "{}@email.com".format(self.user_name) and \
                user_group_name == self.user_group_name:
            self.user_helper.gui_login(self.tcinputs["DestinationCSHostName"],
                                       self.user_name,
                                       self.password)
            self.log.info("Entities migration verified")
        else:
            raise Exception("Entity migration could not be verified")

    def delete_entities(self):
        """Function to delete entities from source to export their deletion"""
        self.log.info("deleting entities from source")
        self.commcell.disk_libraries.delete(self.library_name)
        self.commcell.storage_policies.delete(self.policy_name)
        self.commcell.schedule_policies.delete(self.schedule_policy_name)
        self.commcell.alerts.delete(self.alert_name)
        self.commcell.users.delete(self.user_name, 'admin')
        self.commcell.user_groups.delete(self.user_group_name, 'admin')
        self.log.info("all entities successfully deleted from source")

    def verify_deletion(self):
        """Function to verify entities deleted on destination commcell"""
        time.sleep(60)
        self.destination_cs.refresh()
        login_failed = False
        if self.destination_cs.schedule_policies.has_policy(self.schedule_policy_name):
            raise Exception("schedule policy not deleted on Dest CS")
        self.log.info("schedule policy successfully deleted via import")
        if self.destination_cs.users.has_user(self.user_name):
            if not self.verify_users:
                self.destination_cs.users.delete(self.user_name, 'admin')
            else:
                raise Exception("user not deleted on Dest CS")
        self.log.info("user successfully deleted via import")
        if self.destination_cs.user_groups.has_user_group(self.user_group_name):
            raise Exception("user group not deleted on Dest CS")
        self.log.info("user group successfully deleted via import")
        if self.destination_cs.alerts.has_alert(self.alert_name):
            raise Exception("alert not deleted on Dest CS")
        self.log.info("alert successfully deleted via import")
        try:
            self.user_helper.gui_login(self.tcinputs["DestinationCSHostName"],
                                       self.user_name,
                                       self.password)
        except:
            login_failed = True

        if login_failed:
            self.log.info("Entities deletion verified on Dest CS")
        else:
            raise Exception("user deletion failed on Dest CS")
