# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

TestCase is the only class definied in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()              --  Initialize TestCase class

    setup()                 --  initial settings for the test case

    run()                   --  run function of this test case

    get_time()              --  Function to get current time.

    create_disk_library()   --  Function to create disk library.
    
    create_storage_policy() --  Function to create storage policiy.

    alert_setup()           --  Function to setup options required to create alerts.

    schedule_policy_setup() --  Function to setup options required for creating 
                                schedule policies. 

    user_setup()            --  Function to setup options required for creating users.

    user_group_setup()      --  Function to setup options required for creating 
                                user groups.

    create_entities()       --  Function to create entities that are to be migrated 
                                to the destination commserv.

    ccm_export()            --  Function to perform CCM Export.

    import_setup()          --  Function to setup entities requried for CCM import.

    ccm_import()            --  Function to perform CCM Import.

    verify_import()         --  Function to verify entities migrated during 
                                Commcell Migration.
    
    tear_down()             --  Tear down function for this testcase.

"""

from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from Server.Alerts.alert_helper import AlertHelper
from Server.Scheduler.schedulepolicyhelper import SchedulePolicyHelper
from Server.Security.userhelper import UserHelper
from Server.Security.usergrouphelper import UsergroupHelper
from AutomationUtils.options_selector import OptionsSelector
from datetime import datetime
from datetime import timezone
from Server.CommcellMigration.ccmhelper import CCMHelper


class TestCase(CVTestCase):
    """Class for executing this test case."""

    def __init__(self):
        """Initializes test case class object.

            Properties to be initialized:

                name            (str)       --  name of this test case

                tcinputs        (dict)      --  test case inputs with input name as dict key
                                                and value as input type

        """
        super().__init__()
        self.name = "Migration verification for Schedule Policies, User & User Groups, Alerts & " \
                    "Location "
        self.time = None
        self.tcinputs = {
            "ExportLocation": None,
            "ExportPathType": None,
            "ExportUserName": None,
            "ExportPassword": None,
            "MountPathLocation": None,
            "ImportLocation": None,
            "DestinationCommcellHostname": None,
            "DestinationCommcellUsername": None,
            "DestinationCommcellPassword": None
        }

    @property
    def get_time(self):
        """Function to get current time."""
        if not self.time:
            self.time = datetime.now()
            self.time = self.time.replace(tzinfo=timezone.utc).timestamp()
        return self.time

    def create_disk_library(self):
        """Function to create disk libraries."""
        self.log.info('Started creating new disk_library')

        self.library_name = "test_lib_{}".format(self.get_time)
        self.commcell.disk_libraries.add(self.library_name, self.media_agent,
                                         self.tcinputs['MountPathLocation'])

        self.log.info('Successfully created disk_library {}'.format(self.library_name))

    def create_storage_policy(self):
        """Function to create storage policies."""
        self.log.info('Started creating new storage_policy')

        self.storage_policy_name = "test_storage_policy{}".format(self.get_time)
        self.commcell.storage_policies.add(self.storage_policy_name, self.library_name, self.media_agent)

        self.log.info('Successfully created storage_policy {}'.format(self.storage_policy_name))

    def alert_setup(self):
        """Function to setup options required to create alerts."""
        self.log.info('Setting up to create new alerts')

        self.alert_helper = AlertHelper(self.commcell, 'Media Management', 'Library Management')
        self.alert_name = "test_alert_{}".format(self.get_time)
        self.alert_details = self.alert_helper.get_alert_details(self.alert_name,
                                                                 ['Event Viewer'],
                                                                 {'disk_libraries': self.library_name}, ['admin'], 22)
        self.log.info('Successfully completed alert setup')

    def schedule_policy_setup(self):
        """Function to setup options required for creating schedule policies."""
        self.log.info('Setting up to create new schedule policies')

        self.schedule_policy_helper = SchedulePolicyHelper(self.commcell)
        self.schedule_associations = [{'storagePolicyName': self.storage_policy_name}]
        self.schedules = [
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
                    "mediaAgentName": self.media_agent
                }
            }
        ]

        self.log.info('Successfully completed schedule policy setup')

    def user_setup(self):
        """Function to setup options required for creating users."""
        self.log.info('Setting up to create new users')

        self.user_helper = UserHelper(self.commcell)

        self.security_dict = {
            'assoc1':
                {
                    'storagePolicyName': [self.storage_policy_name],
                    'role': ['View']
                }
        }

        self.log.info('Successfully completed user setup')

    def user_group_setup(self):
        """Function to setup options required for creating user groups."""
        self.log.info('Setting up to create new user_groups')

        self.usergroup_helper = UsergroupHelper(self.commcell)
        self.usergroup_entity_dict = {
            'assoc1':
                {
                    'storagePolicyName': [self.storage_policy_name],
                    'role': ['View']
                }
        }

        self.log.info('Successfully completed user group setup')

    def create_entities(self):
        """Function to create entities that are to be migrated to the destination commserv."""
        self.log.info('Creating new alert')
        self.alert_helper.create_alert()
        self.log.info('Successfully created alert {}'.format(self.alert_name))

        self.log.info('Creating new schedule policiy')
        self.schdeule_policy_name = 'test_schedule_policy{}'.format(self.get_time)
        self.schedule_policy = self.schedule_policy_helper.create_schedule_policy(self.schdeule_policy_name,
                                                                                  'Auxiliary Copy',
                                                                                  self.schedule_associations,
                                                                                  self.schedules)
        self.log.info('Successfully created schedule policy {}'.format(self.schdeule_policy_name))

        self.log.info('Creating new user')
        self.user_name = 'test_user_{}'.format(self.get_time)
        self.password = OptionsSelector.get_custom_password(8)
        self.user = self.user_helper.create_user(self.user_name, 'test_user_{}@email.com'.format(self.get_time),
                                                 'test_user_{}'.format(self.get_time), None, self.password, None,
                                                 self.security_dict)
        self.log.info('Successfully created new user {}'.format(self.user_name))

        self.log.info('Creating new user group')
        self.user_group_name = 'test_user_group_{}'.format(self.get_time)
        self.user_group = self.usergroup_helper.create_usergroup(self.user_group_name, None,
                                                                 ['test_user_group_{}'.format(self.get_time)],
                                                                 self.usergroup_entity_dict)
        self.log.info('Successfully created user group {}'.format(self.user_group_name))

        self.custom_role = 'role_{}'.format(self.get_time)
        self.commcell.roles.add(self.custom_role, ['View', 'Agent Management'])

    def ccm_export(self):
        """Function to perform CCM Export."""
        options = {
            'pathType': self.tcinputs["ExportPathType"],
            'userName': self.tcinputs["ExportUserName"],
            'password': self.tcinputs["ExportPassword"],
            'captureMediaAgents': False
        }

        ccm_job = self.ccm_helper.run_ccm_export(self.tcinputs["ExportLocation"],
                                                 other_entities=["schedule_policies", "users_and_user_groups",
                                                                 "alerts"],
                                                 options=options
                                                 )

        self.log.info("Started CCM Export Job: %s", ccm_job.job_id)

        if ccm_job.wait_for_completion():
            self.log.info("CCM Export Job id %s "
                          "completed successfully", ccm_job.job_id)
        else:
            self.log.error("CCM Export Job id %s "
                           "failed/ killed", ccm_job.job_id)
            raise Exception("CCM Export job failed")

    def import_setup(self):
        """Function to setup entities requried for CCM import."""
        self.destination_cs = self.ccm_helper.create_destination_commcell(
            self.tcinputs["DestinationCommcellHostname"],
            self.tcinputs["DestinationCommcellUsername"],
            self.tcinputs["DestinationCommcellPassword"]
        )
        self.log.info("Successfully created and logged in to destination commcell {}".format(
            self.tcinputs["DestinationCommcellHostname"]))

    def ccm_import(self):
        """Function to perform CCM import."""
        options = {
            'forceOverwrite': True
        }
        import_job = self.ccm_helper.run_ccm_import(self.tcinputs["ImportLocation"], options=options)
        self.log.info("Started CCM Import Job: %s", import_job.job_id)

        if import_job.wait_for_completion():
            self.log.info("CCM Import Job id %s "
                          "completed successfully", import_job.job_id)
        else:
            self.log.error("CCM Import Job id %s "
                           "failed/ killed", import_job.job_id)
            raise Exception("CCM Import job failed")

    def verify_import(self):
        """Function to verify entities migrated during Commcell Migration on destination commserv."""
        self.source_cs = self.commcell
        self.destination_cs = self.ccm_helper._destination_cs

        try:
            alert = self.destination_cs.alerts.get(self.alert_name)

        except:
            raise Exception("Alert doesn't exist on {}.".format(self.destination_cs.commserv_name))

        alert_name = alert.alert_name
        alert_type = alert.alert_type
        alert_category = alert.alert_category

        try:
            schedule_policy = self.destination_cs.schedule_policies.get(self.schdeule_policy_name)

        except:
            raise Exception("Schedule Policy doesn't exist on {}.".format(self.destination_cs.commserv_name))

        schedule_policy_name = schedule_policy.schedule_policy_name
        schedule_policy_type = schedule_policy.policy_type

        try:
            user = self.destination_cs.users.get(self.user_name)

        except:
            raise Exception("User doesn't exist on {}.".format(self.destination_cs.commserv_name))

        user_name = user.user_name
        user_email = user.email

        try:
            user_group = self.destination_cs.user_groups.get(self.user_group_name)

        except:
            raise Exception("User group doesn't exist on {}.".format(self.destination_cs.commserv_name))

        user_group_name = user_group.user_group_name

        try:
            custom_role = self.destination_cs.roles.get(self.custom_role)

        except:
            raise Exception("Role doesn't exist on {}.".format(self.destination_cs.commserv_name))

        if alert_name == self.alert_name and \
                alert_type == "Library Management" and \
                alert_category == "Media Management" and \
                schedule_policy_name == self.schdeule_policy_name and \
                schedule_policy_type == "Auxiliary Copy" and \
                user_name == self.user_name and \
                user_email == "{}@email.com".format(self.user_name) and \
                user_group_name == self.user_group_name and \
                custom_role is not None:
            custom_role.associate_user(self.custom_role, self.user_name)
            self.user_helper.gui_login(self.tcinputs["DestinationCommcellHostname"],
                                       self.user_name,
                                       self.password)
            self.log.info("Entities migration verified")

        else:
            raise Exception("Entitiy migration could not be verified")

    def setup(self):
        """Setup function of this test case."""
        self.ccm_helper = CCMHelper(self)
        self.media_agent = self.ccm_helper.get_active_mediaagent()
        self.create_disk_library()
        self.create_storage_policy()
        self.alert_setup()
        self.schedule_policy_setup()
        self.user_setup()
        self.user_group_setup()
        self.import_setup()

    def run(self):
        """Run function of this test case."""
        try:
            self.create_entities()
            self.ccm_export()
            self.ccm_import()
            self.verify_import()

        except Exception as exp:
            self.log.error('Failed to execute test case with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED

    def tear_down(self):
        """Tear down function of this test case."""
        self.source_cs.disk_libraries.delete(self.library_name)
        self.source_cs.storage_policies.delete(self.storage_policy_name)

        self.source_cs.schedule_policies.delete(self.schdeule_policy_name)
        self.destination_cs.schedule_policies.delete(self.schdeule_policy_name)

        self.source_cs.alerts.delete(self.alert_name)
        self.destination_cs.alerts.delete(self.alert_name)

        self.source_cs.users.delete(self.user_name, 'admin')
        self.destination_cs.users.delete(self.user_name, 'admin')

        self.source_cs.user_groups.delete(self.user_group_name, 'admin')
        self.destination_cs.user_groups.delete(self.user_group_name, 'admin')
