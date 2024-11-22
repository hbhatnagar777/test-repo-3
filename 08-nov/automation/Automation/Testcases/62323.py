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
    __init__()      --  initialize TestCase class

    run()           --  run function of this test case
"""

import calendar
import csv
import os
import time
from dateutil.relativedelta import relativedelta
from AutomationUtils.options_selector import CVEntities
from AutomationUtils import constants
from AutomationUtils.machine import Machine
from AutomationUtils.options_selector import OptionsSelector
from AutomationUtils.cvtestcase import CVTestCase
from Server.Scheduler import schedulerhelper, schedulerconstants


# Class of Testcase is named as TestCase which inherits from CVTestCase
class TestCase(CVTestCase):
    """ Class for executing test case for Custom Alert to notify When Scan Phase Exceeds Threshold"""

    # Constructor for the testcase
    def __init__(self):
        """Initializes the testcase object"""
        super(TestCase, self).__init__()
        self.name = 'Script to create Entities, populate content and created schedules' \
                    ' for clients that pass check readiness'
        self.entities = None
        self._utility = None
        self.options_selector = None
        self.schedule_creator = None
        self.cs_machine_obj = None
        self.num_daily_schedules = 3

    def filter_clients_list(self, clients_list):
        clients = []
        for client in clients_list:
            if 'indexserver' not in client:
                clients.append(client)
        return clients

    def create_client_machine_obj(self, client_name):
        client_machine = Machine(machine_name=client_name,
                                 commcell_object=self.commcell)
        drive = self.options_selector.get_drive(client_machine, size=1)
        if drive is None:
            raise Exception("No free space to genereate test data")
        # Generate folder with current timestamp in drive
        test_data_path = client_machine.create_current_timestamp_folder(folder_path=drive)

        self.log.info(f'Generating test data at {test_data_path} in client {client_name}')
        client_machine.generate_test_data(test_data_path, file_size=1)
        return test_data_path

    def save_automation_output(self, created_entities, exception_messages):
        """Saves the automation outpus -> Entities created, exception messages for exceptions encountered during run"""
        self.log.info("Saving automtion output to scale_test_entities_script.csv")
        try:
            current_user_desktop = os.path.join(os.path.join(os.environ['USERPROFILE']), 'Desktop')
            # Save created entities file
            with open(os.path.join(current_user_desktop, "scale_test_entities_script.csv"),
                      mode='w', newline='', encoding='utf-8') as diff_file:
                writer = csv.writer(diff_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
                writer.writerow(['ClientName', 'BackupsetName', 'SubclientName'])
                for data in created_entities:
                    writer.writerow(list(data))
            self.log.info(f"Saved created entities csv file at : {current_user_desktop}")

            # Save exception messages file
            if exception_messages:
                with open(os.path.join(current_user_desktop, "exception_messages.csv"),
                          mode='w', newline='', encoding='utf-8') as diff_file:
                    writer = csv.writer(diff_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
                    writer.writerow(['ClientName', 'ExceptionMessage'])
                    for data in exception_messages:
                        writer.writerow(list(data))
                self.log.info(f"Saved exception messaages csv file at : {current_user_desktop}")
            else:
                self.log.info("No exception messages during scale test entities creation")

        except Exception as excp:
            self.log.error(f"Encountered exception {excp}")

    def run(self):
        """Main function for test case execution"""
        try:
            # Initialization
            self.options_selector = OptionsSelector(self.commcell)
            self.entities = CVEntities(self.commcell)
            backup_types = schedulerconstants.SCHEDULE_BACKUP_TYPES
            self.schedule_creator = schedulerhelper.ScheduleCreationHelper(self)
            self.cs_machine_obj = Machine(self.commcell.commserv_client)
            weekdays = [calendar.day_name[self.cs_machine_obj.current_time().weekday()],
                        calendar.day_name[(self.cs_machine_obj.current_time() + relativedelta(
                            days=1)).weekday()]]

            # Entities Setup
            storage_policy = self.tcinputs["StoragePolicy"]
            self.log.info(f"Storage policy to be used : {storage_policy}")

            # Get list of clients that pass check readiness
            clients_list = self.options_selector.get_ready_clients(list(self.commcell.clients.all_clients),
                                                                   validate=False)[0]
            filtered = self.filter_clients_list(clients_list)
            self.log.info(filtered)

            created_entities = []
            exception_messages = []
            # For each client
            for i, client in enumerate(filtered[:1]):
                self.log.info(f"""
                            ===============================================
                            Creating Entities, Schedules for : {client}
                            ===============================================
                            """)
                try:
                    # Per client create 2 subclients -> For these two subclients create 3 schedules each
                    generated_data_path_1 = self.create_client_machine_obj(client_name=client)
                    generated_data_path_2 = self.create_client_machine_obj(client_name=client)
                    backupset_name = "Backupset_auto" + str(i)
                    subclient1_name = "Subclient_auto_1_" + str(i)
                    subclient2_name = "Subclient_auto_2_" + str(i)
                    # Create Backupset using CVEntities.create()
                    backupset_inputs = {
                        'backupset':
                            {
                                'name': backupset_name,
                                'client': client,
                                'agent': "File system",
                                'instance': "defaultinstancename",
                                'on_demand_backupset': False,
                                'force': True
                            },
                    }
                    created_backupset = self.entities.create(backupset_inputs)
                    time.sleep(4)
                    # Create subclients using CVEntities.create()
                    subclient_1_inputs = {
                        'subclient':
                            {
                                'name': subclient1_name,
                                'client': client,
                                'agent': "File system",
                                'instance': "defaultinstancename",
                                'storagepolicy': storage_policy,
                                'backupset': backupset_name,
                                'content': [generated_data_path_1],
                                'description': "Automated subclient for scale testing",
                                'subclient_type': None,
                                'force': True
                            },
                    }
                    subclient_2_inputs = {
                        'subclient':
                            {
                                'name': subclient2_name,
                                'client': client,
                                'agent': "File system",
                                'instance': "defaultinstancename",
                                'storagepolicy': storage_policy,
                                'backupset': backupset_name,
                                'content': [generated_data_path_2],
                                'description': "Automated subclient for scale testing",
                                'subclient_type': None,
                                'force': True
                            },
                    }
                    created_subclient_1 = self.entities.create(subclient_1_inputs)
                    created_subclient_2 = self.entities.create(subclient_2_inputs)
                    subclient_1_obj = created_subclient_1.get("subclient").get("object")
                    subclient_2_obj = created_subclient_2.get("subclient").get("object")
                    created_entities.append([client, backupset_name, subclient1_name])
                    created_entities.append([client, backupset_name, subclient2_name])

                    # Create automatic schedule associated to this created subclient
                    # For each backup type (4 in total) creates num_daily_schedules schedules
                    for backup_type in backup_types:
                        for i in range(self.num_daily_schedules):
                            self.log.info(f"Creating Daily Automatic Schedule for "
                                          f"{client}->{backupset_name}->{subclient1_name}, Iteration : [{i}]")
                            daily_sch_obj = self.schedule_creator.create_schedule('subclient_backup',
                                                                                  schedule_pattern={
                                                                                   'freq_type': 'Daily',
                                                                                   'active_start_date':
                                                                                   self.schedule_creator.
                                                                                   add_minutes_to_datetime()[0],
                                                                                   'active_start_time':
                                                                                   self.schedule_creator.
                                                                                   add_minutes_to_datetime(minutes=3)[1],
                                                                                   'time_zone': 'UTC'},
                                                                                  subclient=subclient_1_obj,
                                                                                  backup_type=backup_type,
                                                                                  wait=False)
                            self.log.info(f"Creating Daily Automatic Schedule for "
                                          f"{client}->{backupset_name}->{subclient1_name}, Iteration : [{i}]")
                            daily_sch_obj = self.schedule_creator.create_schedule('subclient_backup',
                                                                                  schedule_pattern={
                                                                                   'freq_type': 'Daily',
                                                                                   'active_start_date':
                                                                                   self.schedule_creator.
                                                                                   add_minutes_to_datetime()[0],
                                                                                   'active_start_time':
                                                                                   self.schedule_creator.
                                                                                   add_minutes_to_datetime(minutes=3)[1],
                                                                                   'time_zone': 'UTC'},
                                                                                  subclient=subclient_2_obj,
                                                                                  backup_type=backup_type,
                                                                                  wait=False)

                except Exception as excp:
                    exception_messages.append([client, str(excp)])

            self.save_automation_output(created_entities, exception_messages)

        except Exception as excp:
            self.log.error('Failed with error %s', str(excp))
            # Set the Test-Case params : result_string, status
            self.result_string = str(excp)
            self.status = constants.FAILED