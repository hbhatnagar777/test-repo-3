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
    __init__()              --  initialize TestCase class

    create_entities_setup() --  Function to setup everything to create entities

    create_entities()       --  Function to create entities required by the testcase

    ccm_export()            --  Function to perform CCM Export

    ccm_import()            --  Function to perform CCM Import

    create_destination_cs() --  Post CCM restore from a tape library

    restore_a_job()         --  Function to restore a backup job

    setup()                 --  setup function of this test case

    run()                   --  run function of this test case

    tear_down()             --  tear down function of this test case

"""

"""
STEPS:
1. Perform steps 2-3 on commcells running three previous service packs.
2. Create new alerts, schedule policies, subclient policies, users, user groups and roles.
3. Perform CCM Export on the CS	Export job completes successfully and the dump files are created. 
4. Perform CCM Import using the exported dump files in Step 2 on a CS running current SP.
5. Verify the imported entities and perform a restore from the imported client.
"""

from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from Server.CommcellMigration.ccmhelper import CCMHelper
from ast import literal_eval
from Server.Alerts.alert_helper import AlertHelper
from Server.Scheduler.schedulepolicyhelper import SchedulePolicyHelper
from Server.Security.userhelper import UserHelper
from Server.Security.usergrouphelper import UsergroupHelper
from AutomationUtils.options_selector import OptionsSelector
from datetime import datetime
from datetime import timezone


class TestCase(CVTestCase):
    """Class for executing this test case"""

    def __init__(self):
        """Initializes test case class object

            Properties to be initialized:

                name            (str)       --  name of this test case

                tcinputs        (dict)      --  test case inputs with input name as dict key
                                                and value as input type
                    SourceCommcellsList = [
                        ["commcellHostname1", "username1", "password1", "clientName1"],
                        ["commcellHostname2", "username2", "password2", "clientName2"],
                        ...
                    ]

        """
        super(TestCase, self).__init__()
        self.custom_role = None
        self.user_group = None
        self.user_group_name = None
        self.user = None
        self.password = None
        self.user_name = None
        self.schedule_policy = None
        self.schedule_policy_name = None
        self.usergroup_entity_dict = None
        self.usergroup_helper = None
        self.alert_details = None
        self.alert_name = None
        self.alert_helper = None
        self.security_dict = None
        self.user_helper = None
        self.schedules = None
        self.schedule_associations = None
        self.schedule_policy_helper = None
        self.storage_policy_name = None
        self.library_name = None
        self.source_commcells_list = None
        self.name = "Cross Version CCM Validation"
        self.ccm_helper = None
        self.destination_cs = None
        self.time = None
        self.tcinputs = {
            "SourceCommcellsList": None,
            "MountPathLocation": None,
            "ExportLocation": None,
            "ExportPathType": None,
            "ExportUserName": None,
            "ExportPassword": None,
            "ImportLocation": None,
            "DestinationCommcellHostname": None,
            "DestinationCommcellUsername": None,
            "DestinationCommcellPassword": None,
            "RestoreFolder": None
        }

    @property
    def get_time(self):
        """Function to get time."""
        if not self.time:
            self.time = datetime.now()
            self.time = self.time.replace(tzinfo=timezone.utc).timestamp()
        return self.time

    def create_entities_setup(self, media_agent):
        def create_disk_library():
            """Function to create disk libraries."""
            self.log.info('Started creating new disk_library')

            self.library_name = "test_lib_{}".format(self.get_time)
            self.commcell.disk_libraries.add(self.library_name, media_agent,
                                             self.tcinputs['MountPathLocation'])

            self.log.info('Successfully created disk_library {}'.format(self.library_name))

        def create_storage_policy():
            """Function to create storage policies."""
            self.log.info('Started creating new storage_policy')

            self.storage_policy_name = "test_storage_policy{}".format(self.get_time)
            self.commcell.storage_policies.add(self.storage_policy_name, self.library_name, media_agent)

            self.log.info('Successfully created storage_policy {}'.format(self.storage_policy_name))

        def alert_setup():
            """Function to setup options required to create alerts."""
            self.log.info('Setting up to create new alerts')

            self.alert_helper = AlertHelper(self.commcell, 'Media Management', 'Library Management')
            self.alert_name = "test_alert_{}".format(self.get_time)
            self.alert_details = self.alert_helper.get_alert_details(self.alert_name,
                                                                     ['Event Viewer'],
                                                                     {'disk_libraries': self.library_name}, ['admin'],
                                                                     22)
            self.log.info('Successfully completed alert setup')

        def schedule_policy_setup():
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
                        "mediaAgentName": media_agent
                    }
                }
            ]

            self.log.info('Successfully completed schedule policy setup')

        def user_setup():
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

        def user_group_setup():
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

        create_disk_library()
        create_storage_policy()
        alert_setup()
        schedule_policy_setup()
        user_setup()
        user_group_setup()

    def create_entities(self):
        """Function to create entities that are to be migrated to the destination commserv."""
        self.log.info('Creating new alert')
        self.alert_helper.create_alert()
        self.log.info('Successfully created alert {}'.format(self.alert_name))

        self.log.info('Creating new schedule policy')
        self.schedule_policy_name = 'test_schedule_policy{}'.format(self.get_time)
        self.schedule_policy = self.schedule_policy_helper.create_schedule_policy(self.schedule_policy_name,
                                                                                  'Auxiliary Copy',
                                                                                  self.schedule_associations,
                                                                                  self.schedules)
        self.log.info('Successfully created schedule policy {}'.format(self.schedule_policy_name))

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

    def ccm_export(self, commcell, client):
        """Function to run CCM Export."""
        options = {
            "pathType": self.tcinputs["ExportPathType"],
            "userName": self.tcinputs["ExportUserName"],
            "password": self.tcinputs["ExportPassword"],
            "captureMediaAgents": False
        }

        export_job = self.ccm_helper.run_ccm_export(export_location=self.tcinputs["ExportLocation"],
                                                    commcell=commcell,
                                                    client_names=[client],
                                                    other_entities=[
                                                        "schedule_policies",
                                                        "users_and_user_groups",
                                                        "alerts"
                                                    ],
                                                    options=options)

        self.log.info("Started CCM Export Job: {}".format(export_job.job_id))

        if export_job.wait_for_completion():
            self.log.info("CCM Export Job id {} completed successfully".format(export_job.job_id))
        else:
            self.log.error("CCM Export Job id {} failed/ killed".format(export_job.job_id))
            raise Exception("CCM Export job failed")

    def create_commcell_objects(self, commcell_hostname, commcell_username, commcell_password):
        """Function to create Destination Commcell Object."""
        commcell_object = self.ccm_helper.create_destination_commcell(commcell_hostname,
                                                                      commcell_username,
                                                                      commcell_password
                                                                      )
        self.log.info("Successfully created commcell object for {}".format(commcell_object.commserv_name))

        return commcell_object

    def ccm_import(self):
        """Function to run CCM Import."""
        import_job = self.ccm_helper.run_ccm_import(
            self.tcinputs["ImportLocation"]
        )
        self.log.info("Started CCM Import Job: {}".format(import_job.job_id))

        if import_job.wait_for_completion():
            self.log.info("CCM Import Job id {} completed successfully".format(import_job.job_id))
        else:
            self.log.error("CCM Import Job id {} failed/ killed".format(import_job.job_id))
            raise Exception("CCM Import job failed")

    def get_active_media_agent(self, commcell):
        """To Fetch only active Media agent, Returns Media Agent Name if it is available"""
        self.log.info('Selecting Media Agent with Checking readiness..')
        media_agents = list(commcell.media_agents.all_media_agents.keys())
        for media_agent in media_agents:
            if commcell.media_agents.get(media_agent_name=media_agent).is_online:
                self.log.info(f'MA [{media_agent}] is ready..')
                ma = media_agent
                return ma
        else:
            raise Exception('None of the Media Agent is Ready!')

    def restore_a_job(self, client_name):
        """Function to restore a backup job on destination commcell."""
        subclient = self.ccm_helper.get_latest_subclient(client_name, destination_commcell=True)
        job = subclient.restore_out_of_place(self.destination_cs.commserv_name,
                                             self.tcinputs["RestoreFolder"],
                                             subclient.content)

        self.log.info("Restore job started with Jobid : {}".format(job.job_id))

        if job.wait_for_completion():
            self.log.info("Restore Job with jobid {} completed successfully".format(job.job_id))

        else:
            self.log.error("Restore job with Jobid {} failed/ killed".format(job.job_id))
            raise Exception("Restore job failed post CCM")

    def setup(self):
        """Setup function of this test case"""
        self.ccm_helper = CCMHelper(self)
        self.source_commcells_list = literal_eval(self.tcinputs["SourceCommcellsList"])

    def run(self):
        """Run function of this test case"""
        try:
            # Run all the CCM Exports
            for commcell in self.source_commcells_list:
                media_agent = self.get_active_media_agent(commcell)
                self.create_entities_setup(media_agent)
                commcell_object = self.create_commcell_objects(commcell_hostname=commcell[0],
                                                               commcell_username=commcell[1],
                                                               commcell_password=commcell[2])
                self.ccm_export(commcell=commcell_object, client=commcell[3])

            # CCM Import for all the exports
            self.destination_cs = self.create_commcell_objects(
                commcell_hostname=self.tcinputs["DestinationCommcellHostname"],
                commcell_username=self.tcinputs["DestinationCommcellUsername"],
                commcell_password=self.tcinputs["DestinationCommcellPassword"])

            self.ccm_import()
            self.commcell.refresh()

            for commcell in self.source_commcells_list:
                self.log.info("Starting restore job for {}".format(commcell[3]))
                self.restore_a_job(commcell[3])

        except Exception as exp:
            self.log.error('Failed to execute test case with error {}'.format(exp))
            self.result_string = str(exp)
            self.status = constants.FAILED

    def tear_down(self):
        """Tear down function for this test case"""
        try:
            for commcell in self.source_commcells_list:
                self.destination_cs.clients.delete(commcell[3])

        except Exception as exp:
            self.log.error('Failed to execute test case with error {}'.format(exp))
            self.result_string = str(exp)
            self.status = constants.FAILED
