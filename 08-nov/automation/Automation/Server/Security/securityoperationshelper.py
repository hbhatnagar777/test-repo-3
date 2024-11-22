# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Main file for performing security operations on Commcell

SecurityOperationsHelper:
    __init__()                              --  Initializes SecurityOperationsHelper object

    fetch_operations_for_user()             --  Fetches commserve related operations based on user
                                                capability

    perform_operations()                    --  Fetches commserve related operations based on user
                                                capability

    _return_formatted_dict()                --  Fetches security associations from entity.

    return_subclient()                      --  Returns default subclient object of client

    operation_drbackup()                    --  Triggers DR Backup Job on commcell

    operation_dataaging()                   --  Triggers DataAging Job on commcell

    operation_activitycontroloncg()         --  Activity Control operations on clientGroup

    operation_activitycontrolonclient()     --  Activity Control operations on client

    operation_setclientprop()               --  Modifies client properties

    operation_backup()                      --  Triggers Backup job on given client

    operation_restore()                     --  Triggers Restore job on given client

    operation_updatecgprop()                --  Modifies client group properties

    operation_createuser()                  --  Creates user on this commcell

    operation_createusergroup()             --  Create usergroup on this commcell

    operation_createclientgroup()           --  Creates client group on this commcell

    operation_operationwindowforcommserve() --  Creates operation rule on the initialized commcell
                                                entity

    operation_createglobalfilters()         --  Adds the filters list to the specified agent global
                                                filters list

    operation_createlibrary()               --  Adds a new Disk Library to the Commcell

    operation_runreport()                   --  Runs Job Summary Reports on the commcell

    operation_backupschedule()              --  Executes backup on any subclient object and create
                                                a schedule

    operation_inplacerestoreschedule()      --  Restores the files / folders specified in the input
                                                paths list to the same location

    operation_adminschedule()               -- Executes data aging job on any commcell subclient
                                                object and create a schedule

    operation_createbackupschedulepolicy()  --  Adds a schedule policy to the commcell

    operation_createstoragepolicyandcopy()  --  Adds a storage policy and copy to the commcell

    operation_joboperations()               --  Performs suspend, resulme and job kill operations
                                                on currently running jobs

    operation_result_generator()            --  Performs suspend, HTML content to render results
                                                in table and send mail with all operations results

    operation_validator()                   --  validates actual results of operations against
                                                intended results

"""
import os
from Server.Security import securityconstants
from Server.Security.securityhelper import SecurityHelper
from Server.Security.userhelper import UserHelper
from Server.JobManager.jobmanager_helper import JobManager
from AutomationUtils import logger, database_helper, config
from cvpysdk.commcell import Commcell
from AutomationUtils.idautils import CommonUtils
from cvpysdk.agent import Agent
from cvpysdk.job import Job
from cvpysdk.operation_window import OperationWindow
from Server.DisasterRecovery.drhelper import DRHelper
from cvpysdk.clientgroup import ClientGroup
from Server.Scheduler.schedulerhelper import ScheduleCreationHelper
import time
from datetime import timedelta


class SecurityOperationsHelper:
    """Helper class to perform various Security operations"""

    def __init__(self, commcell, user, password):
        """Initializes SecurityOperationsHelper object

            Args:
                commcell    (obj)   -- Commcell object

                user        (str)   -- user name

                password    (str)   --  User password
        """
        self._admin_commcell_obj = commcell
        self.config_json = config.get_config()
        self.commcell_obj = Commcell(commcell.webconsole_hostname, user, password, verify_ssl=self.config_json.API.VERIFY_SSL_CERTIFICATE)
        self.user_obj = self.commcell_obj.users.get(user)
        self._sqlite = database_helper.SQLite(database_file_path=os.path.join(os.path.dirname(
            os.path.realpath(__file__)), securityconstants.SQLiteDB))
        self.subclient_obj = None
        self.subclient_flag = 0
        self.utils_obj = CommonUtils(self.commcell_obj)
        self.client = None
        self.lib_obj = None
        self.media_agent = None
        self.log = logger.get_log()
        self._user_helper = UserHelper(self._admin_commcell_obj)
        self._securityhelper_obj = SecurityHelper(self._admin_commcell_obj)
        self.sched_helper_obj = ScheduleCreationHelper(init_object=self._admin_commcell_obj)
        self.failed_operation_count = 0

    def fetch_operations_for_user(self, username):
        """Fetches commserve related operations based on user capability
            Args:
                username    (str)   --  name of the user

            Returns:
                returns dictionary of valid and invalid operations from db
                example:
                {
                   "DRBackup":[
                      "DRBackup",
                      "commCellName",
                      "pmirje-server",
                      0,
                      "testuser_48755"
                   ],
                   "DataAging":[
                      "DataAging",
                      "commCellName",
                      "pmirje-server",
                      0,
                      "testuser_48755"
                   ],
                   .
                   .
                   }
        """
        self._securityhelper_obj.valid_operations_for_user(user_name=username)
        sql_cmd1 = 'select * from intendedResulttable'
        results = self._sqlite.execute(sql_cmd1)
        operation_dict = self._return_formatted_dict(db_results=results.rows)
        return operation_dict

    def perform_operations(self, operation_dictionary):
        """Fetches commserver related operations based on user capability
            Args:
                operation_dictionary    (dict)  --  Dictionary consisting of valid and invalid
                                                    operations for user

            Returns:
                result_list             (list)  --  List consisting of operations name and result
        """
        result_list = []
        for each_operation, values in operation_dictionary.items():
            result_list.append(getattr(self, 'operation_{0}'.format(each_operation.lower()))(
                values))

        self.log.info('Total Positive and Negative operations for user:%s', result_list)
        return result_list

    def _return_formatted_dict(self, db_results):
        """returns formatted valid and invalid operaions
        Args:
            db_results    (list)   --  list of valid, invalid operations with other details
        Returns:
            returns formatted dictionary of valid and invalid operations from db
        """
        operation_dictionary = {}
        for key in db_results:
            operation_dictionary.setdefault(key[0], list(key))
        self.log.info('formatted dictionary of operation:%s', operation_dictionary)
        return operation_dictionary

    def return_subclient(self, client_obj):
        """Returns default subclient object of client
            Args:
                client_obj    (obj)   --  object of client class
            Returns:
                returns default subclient object
        """
        try:
            job_manager = JobManager(commcell=self._admin_commcell_obj)
            job_manager.kill_active_jobs(client=client_obj.client_name)
        except Exception as ex:
            self.log.info("SOFT FAILURE:Entity may not be present", ex)
        if self.subclient_flag != 1:
            # self.sched_helper_obj.entities_setup(client_name=self.commcell_obj.commserv_name)
            client_obj = self.commcell_obj.clients.get(client_obj.client_name)
            _agent = client_obj.agents.all_agents
            _agent_obj = Agent(client_object=client_obj, agent_name='file system',
                               agent_id=_agent['file system'])
            _backupset_obj = _agent_obj.backupsets.get('defaultBackupSet')
            self.subclient_obj = _backupset_obj.subclients.get('testSC')
            self.subclient_flag = 1
        return self.subclient_obj

    def operation_drbackup(self, input_list):
        """Triggers DR Backup Job on commcell
            Args:
                input_list    (list)    --  list consists of (operation, entityType, EntityName,
                                            BitMask and USerName)
            Returns:
                returns status of operation
        """
        try:
            self.log.info("Inputs received DRBackup operation:%s", input_list)
            _dr_obj = DRHelper(commcell_object=self.commcell_obj)
            job = _dr_obj.trigger_dr_backup(backup_type='differential', wait_for_completion=False)
            self.log.info('Successfully triggered backup job:%s', job)
            return [input_list[0], 1, 'Success']
        except Exception as ex:
            self.log.info('Failed:%s', str(ex))
            return [input_list[0], 0, str(ex)]

    def operation_dataaging(self, input_list):
        """Triggers Data Aging Backup Job on commcell
            Args:
                input_list    (list)    --  list consists of (operation, entityType, EntityName,
                                            BitMask and USerName)
            Returns:
                returns status of operation
        """
        try:
            self.log.info("Inputs received DataAging operation:%s", input_list)
            job = self.commcell_obj.run_data_aging()
            self.log.info('Successfully triggered Data Aging job:%s', job)
            return [input_list[0], 1, 'Success']
        except Exception as ex:
            self.log.info('Failed:%s', str(ex))
            return [input_list[0], 0, str(ex)]

    def operation_activitycontroloncg(self, input_list):
        """Activity Control operations on clientGroup
            Args:
                input_list    (list)    --  list consists of (operation, entityType, EntityName,
                                            BitMask and USerName)
            Returns:
                returns status of operation
        """
        try:
            self.log.info("Inputs received Activity Control on CG :%s", input_list)
            cg_object = ClientGroup(self.commcell_obj, input_list[2])
            cg_object.disable_backup()
            cg_object.enable_backup()
            self.log.info('Activity control on client group was successful:%s', input_list[2])
            return [input_list[0], 1, 'Success']
        except Exception as ex:
            self.log.info('Failed:%s', str(ex))
            return [input_list[0], 0, str(ex)]

    def operation_activitycontrolonclient(self, input_list):
        """Activity Control operations on client
            Args:
                input_list    (list)    --  list consists of (operation, entityType, EntityName,
                                            BitMask and USerName)
            Returns:
                returns status of operation
        """
        try:
            self.log.info("Inputs received Activity Control on Client:%s", input_list)
            self.client = self.commcell_obj.clients.get(input_list[2])
            self.client.disable_backup()
            self.client.enable_backup()
            self.log.info('Activity control on client was successful:%s', input_list[2])
            return [input_list[0], 1, 'Success']
        except Exception as ex:
            self.log.info('Failed:%s', str(ex))
            return [input_list[0], 0, str(ex)]

    def operation_setclientprop(self, input_list):
        """Modifies client properties
            Args:
                input_list    (list)    --  list consists of (operation, entityType, EntityName,
                                            BitMask and USerName)
            Returns:
                returns status of operation
        """
        try:
            self.log.info("Inputs received set client properties operation:%s", input_list)
            self.client = self.commcell_obj.clients.get(input_list[2])
            display_name = self.client.display_name
            self.client.display_name = self.client.display_name+'_appended by automation'
            self.client.display_name = display_name
            self.client.description = 'Description is updated by Automation Testcase'
            self.log.info('Set client properties operation was successful:%s', input_list[2])
            return [input_list[0], 1, 'Success']
        except Exception as ex:
            self.log.info('Failed:%s', str(ex))
            return [input_list[0], 0, str(ex)]

    def operation_backup(self, input_list):
        """Triggers Backup job on given client
            Args:
                input_list    (list)    --  list consists of (operation, entityType, EntityName,
                                            BitMask and USerName)
            Returns:
                returns status of operation
        """
        try:
            self.log.info("Inputs received Backup operation:%s", input_list)
            self.client = self.commcell_obj.clients.get(input_list[2])

            _subclient_obj = self.return_subclient(client_obj=self.client)
            response = _subclient_obj.backup()
            response.wait_for_completion()
            self.log.info('Successfully triggered backup job:%s', response)
            return [input_list[0], 1, 'Success']
        except Exception as ex:
            self.log.info('Failed:%s', str(ex))
            return [input_list[0], 0, str(ex)]

    def operation_restore(self, input_list):
        """Triggers Restore job on given client
            Args:
                input_list    (list)    --  list consists of (operation, entityType, EntityName,
                                            BitMask and USerName)
            Returns:
                returns status of operation
        """
        try:
            self.log.info("Inputs received Restore operation:%s", input_list)
            self.client = self.commcell_obj.clients.get(input_list[2])

            _subclient_obj = self.return_subclient(client_obj=self.client)
            content = _subclient_obj.browse(self.subclient_obj.content[0])
            response = _subclient_obj.restore_out_of_place(
                client=self.client, destination_path=_subclient_obj.content[0] + "\\RESTOREDATA",
                paths=_subclient_obj.content)
            self.log.info('Successfully triggered restore jobs: %s', response)
            return [input_list[0], 1, 'Success']
        except Exception as ex:
            self.log.info('Failed:%s', str(ex))
            return [input_list[0], 0, str(ex)]

    def operation_updatecgprop(self, input_list):
        """Modifies client group properties
            Args:
                input_list    (list)    --  list consists of (operation, entityType, EntityName,
                                            BitMask and USerName)
            Returns:
                returns status of operation
        """
        try:
            self.log.info("Inputs received for updating client group properties %s", input_list)
            _cg_obj = self.commcell_obj.client_groups.get(input_list[2])
            old_name = _cg_obj.clientgroup_name
            _cg_obj.clientgroup_name = old_name+'Sec_Modified by automation'
            self.log.info('reverting back client group name')
            _cg_obj.clientgroup_name = old_name
            _cg_obj.description = 'Sec_description is changed by automation code'
            self.log.info('Update client group operation was successful:%s', input_list[2])
            return [input_list[0], 1, 'Success']
        except Exception as ex:
            self.log.info('Failed:%s', str(ex))
            return [input_list[0], 0, str(ex)]

    def operation_createuser(self, input_list):
        """Creating User on this commcell
            Args:
                input_list    (list)    --  list consists of (operation, entityType, EntityName,
                                            BitMask and USerName)
            Returns:
                returns status of operation
        """
        try:
            self.log.info("Inputs received for user creation operation:%s", input_list)
            if self._admin_commcell_obj.users.has_user('Sec_Auto_user1'):
                self.log.info('Deleting existing user with same name')
                self._admin_commcell_obj.users.delete(user_name='Sec_Auto_user1', new_user='Admin')

            self.commcell_obj.refresh()
            password = self._user_helper.password_generator()
            user_name = self.commcell_obj.users.add(user_name='Sec_Auto_user1',
                                                    email='Sec_abc@commmvault.com',
                                                    full_name='Sec_Automation_User1',
                                                    password=password)
            self.log.info('Successfully created User:%s', user_name)
            return [input_list[0], 1, 'Success']
        except Exception as ex:
            self.log.info('Failed:%s', str(ex))
            return [input_list[0], 0, str(ex)]

    def operation_createusergroup(self, input_list):
        """Creating UserGroup on this commcell
            Args:
                input_list    (list)    --  list consists of (operation, entityType, EntityName,
                                            BitMask and USerName)
            Returns:
                returns status of operation
        """
        try:
            self.log.info("Inputs received for user group creation operation:%s", input_list)
            if self._admin_commcell_obj.user_groups.has_user_group('Sec_Auto_group1'):
                self.log.info('Deleting existing user group with same name')
                self._admin_commcell_obj.user_groups.delete(user_group='Sec_Auto_group1',
                                                            new_user='admin')

            ug_obj = self.commcell_obj.user_groups.add('Sec_Auto_group1')
            self.log.info('Successfully created User group:%s', ug_obj)
            return [input_list[0], 1, 'Success']
        except Exception as ex:
            self.log.info('Failed:%s', str(ex))
            return [input_list[0], 0, str(ex)]

    def operation_createclientgroup(self, input_list):
        """Creating client group on this commcell
            Args:
                input_list    (list)    --  list consists of (operation, entityType, EntityName,
                                            BitMask and USerName)
            Returns:
                returns status of operation
        """
        try:
            self.log.info("Inputs received for client group creation operation:%s", input_list)
            if self._admin_commcell_obj.client_groups.has_clientgroup('Sec_Auto_CG1'):
                self.log.info('Deleting existing client group with same name')
                self._admin_commcell_obj.client_groups.delete('Sec_Auto_CG1')

            cg_obj = self.commcell_obj.client_groups.add(clientgroup_name='Sec_Auto_CG1')
            self.log.info('Successfully created Client group:%s', cg_obj)
            return [input_list[0], 1, 'Success']
        except Exception as ex:
            self.log.info('Failed:%s', str(ex))
            return [input_list[0], 0, str(ex)]

    def operation_operationwindowforcommserve(self, input_list):
        """Creates operation rule on the initialized commcell entity
            Args:
                input_list    (list)    --  list consists of (operation, entityType, EntityName,
                                            BitMask and USerName)
            Returns:
                returns status of operation
        """
        window_ids = []
        try:
            self.log.info("Inputs received blackout window operation:%s", input_list)
            try:
                # Few changes needed to operation window file
                rules_dict = self._admin_commcell_obj.operation_window.list_operation_window()
                window_ids = []
                for each_window in rules_dict:
                    if each_window['name'] == 'Sec_Automated1':
                        window_ids.append(each_window)
            except Exception as ex:
                # if 'More than one operation window are named as Sec_Automated1 exists' in str(ex):
                #     self.log.info('More than one window is present! proceed ahead and delete')
                self.log.info('SOFT FAILURE:Entity May not be present:%s', ex)
            self.log.info('Deleting previously created operation window')
            for each_window in window_ids:
                self._admin_commcell_obj.operation_window.delete_operation_window(
                    rule_id=each_window['ruleId'])
            ow_obj = OperationWindow(self.commcell_obj)
            ctime = int(time.time())
            start_date = ctime - ctime % (24 * 60 * 60)
            etime = int(time.time()) + int(timedelta(days=365).total_seconds())
            end_date = etime - etime % (24 * 60 * 60)
            window_obj = ow_obj.create_operation_window(name='Sec_Automated1', start_date=start_date, end_date=end_date)
            self.log.info('Successfully created operation window:%s', window_obj)
            self._admin_commcell_obj.operation_window.delete_operation_window(name='Sec_Automated1')
            return [input_list[0], 1, 'Success']
        except Exception as ex:
            self.log.info('Failed:%s', str(ex))
            return [input_list[0], 0, str(ex)]

    def operation_createglobalfilters(self, input_list):
        """Adds the filters list to the specified agent global filters list
            Args:
                input_list    (list)    --  list consists of (operation, entityType, EntityName,
                                            BitMask and USerName)
            Returns:
                returns status of operation
        """
        try:
            self.log.info("Inputs received global filters creation operation:%s", input_list)
            filters_obj = self.commcell_obj.global_filters.get('WINDOWS')
            filters_obj.add(filters_list=["*.xml", "*.bat", "*.txt"])
            self.log.info("Successfully added Global filters")
            filters_obj.delete_all()
            self.log.info('Deleted all Global filters present for agent')
            return [input_list[0], 1, 'Success']
        except Exception as ex:
            self.log.info('Failed:%s', str(ex))
            return [input_list[0], 0, str(ex)]

    def operation_createlibrary(self, input_list):
        """Adds a new Disk Library to the Commcell
            Args:
                input_list    (list)    --  list consists of (operation, entityType, EntityName,
                                            BitMask and USerName)
            Returns:
                returns status of operation
        """
        self.media_agent = self.commcell_obj.media_agents.get(input_list[2])
        try:
            self.log.info("Inputs received Library creation operation:%s", input_list)
            if self._admin_commcell_obj.disk_libraries.has_library('Sec_AutomatedLibrary'):
                self.log.info('Deleting existing library with same name')
                self._admin_commcell_obj.disk_libraries.delete('Sec_AutomatedLibrary')
            self.lib_obj = self.commcell_obj.disk_libraries.add(library_name=
                                                                'Sec_AutomatedLibrary',
                                                                media_agent=self.media_agent,
                                                                mount_path='C\\lib1')
            self.log.info('Successfully created Library:%s', self.lib_obj)
            return [input_list[0], 1, 'Success']
        except Exception as ex:
            self.log.info('Failed:%s', str(ex))
            return [input_list[0], 0, str(ex)]

    def operation_runreport(self, input_list):
        """Runs Job Summary Reports on the commcell
            Args:
                input_list    (list)    --  list consists of (operation, entityType, EntityName,
                                            BitMask and USerName)
            Returns:
                returns status of operation
        """
        # Report functions returning wrong error string, need to check and ask for fix
        try:
            self.log.info("Inputs received Run Job summary report operation:%s", input_list)
            reports = self.commcell_obj.reports
            reports.backup_job_summary.select_local_drive('C\\Report1')
            reports.backup_job_summary.select_protected_objects()
            job_id = reports.backup_job_summary.run_report()
            self.log.info('Successfully triggered Report job:%s', job_id)
            return [input_list[0], 1, 'Success']
        except Exception as ex:
            self.log.info('Failed:%s', str(ex))
            return [input_list[0], 0, str(ex)]

    def operation_backupschedule(self, input_list):
        """Executes backup on any subclient object and create a schedule
            Args:
                input_list    (list)    --  list consists of (operation, entityType, EntityName,
                                            BitMask and USerName)
            Returns:
                returns status of operation
        """
        try:
            self.log.info("Inputs received Backup Schedule operation:%s", input_list)
            if self._admin_commcell_obj.schedules.has_schedule('BackupSchedule1'):
                self.log.info('Deleting previously created admin schedule')
                self._admin_commcell_obj.schedules.delete('BackupSchedule1')
            self.client = self.commcell_obj.clients.get(input_list[2])

            _subclient_obj = self.return_subclient(client_obj=self.client)
            self.utils_obj.subclient_backup(subclient=_subclient_obj, backup_type='Incremental',
                                            wait=False,
                                            schedule_pattern={
                                                'schedule_name': 'BackupSchedule1',
                                                'freq_type': 'daily'})
            self.log.info("Successfully created backup schedule:%s", input_list)
            return [input_list[0], 1, 'Success']
        except Exception as ex:
            self.log.info('Failed:%s', str(ex))
            return [input_list[0], 0, str(ex)]

    def operation_inplacerestoreschedule(self, input_list):
        """Restores the files / folders specified in the input paths list to the same location
            Args:
                input_list    (list)    --  list consists of (operation, entityType, EntityName,
                                            BitMask and USerName)
            Returns:
                returns status of operation
        """
        try:
            self.log.info('Inputs received for In-PlacerestoreSchedule operation:%s', input_list[2])
            self.client = self.commcell_obj.clients.get(input_list[2])

            _subclient_obj = self.return_subclient(client_obj=self.client)
            if self._admin_commcell_obj.schedules.has_schedule('RestoreSchedule'):
                self.log.info('Deleting previously created restore schedule')
                self._admin_commcell_obj.schedules.delete('RestoreSchedule')
            self.utils_obj.subclient_restore_out_of_place(destination_path='',
                                                          paths=_subclient_obj.content,
                                                          client=self.client,
                                                          subclient=_subclient_obj,
                                                          wait=False,
                                                          schedule_pattern={
                                                              'schedule_name':
                                                                  'RestoreSchedule',
                                                              'freq_type': 'daily'})
            return [input_list[0], 1, 'Success']
        except Exception as ex:
            self.log.info('Failed:%s', str(ex))
            return [input_list[0], 0, str(ex)]

    def operation_adminschedule(self, input_list):
        """Executes data aging job on any commcell subclient object and create a schedule
            Args:
                input_list    (list)    --  list consists of (operation, entityType, EntityName,
                                            BitMask and USerName)
            Returns:
                returns status of operation
        """
        try:
            self.log.info('Inputs received for AdminSchedule operation:%s', input_list)
            if self._admin_commcell_obj.schedules.has_schedule('Sec_schedule_ptrn3'):
                self.log.info('Deleting previously created admin schedule')
                self._admin_commcell_obj.schedules.delete('Sec_schedule_ptrn3')
            schedeule_id = self.commcell_obj.run_data_aging(schedule_pattern={
                'schedule_name': 'Sec_schedule_ptrn3', 'freq_type': 'daily'})
            self.log.info('Successfully created admin schedule:%s', schedeule_id.subtask_id)
            return [input_list[0], 1, 'Success']
        except Exception as ex:
            self.log.info('Failed:%s', str(ex))
            return [input_list[0], 0, str(ex)]

    def operation_createbackupschedulepolicy(self, input_list):
        """Adds a schedule policy to the commcell
            Args:
                input_list    (list)    --  list consists of (operation, entityType, EntityName,
                                            BitMask and USerName)
            Returns:
                returns status of operation
        """
        try:
            self.log.info('Inputs received for Backup Schedule policy operation:%s', input_list)
            if self._admin_commcell_obj.schedule_policies.has_policy('Sec_auto_backupschedule1'):
                self.log.info('Deleting existing schedule with same name')
                self._admin_commcell_obj.schedule_policies.delete('Sec_auto_backupschedule1')

            asso = [{'clientName': input_list[2]}]
            backup_schedule_obj = self.commcell_obj.schedule_policies.add(
                name='Sec_auto_backupschedule1',
                policy_type='Data Protection',
                associations=asso,
                schedules=[{'schedule_name': 'BackupSchedulePolicy1', 'freq_type': 'daily'}])
            self.log.info('Successfully Created Backup Schedule copy:%s', backup_schedule_obj)
            return [input_list[0], 1, 'Success']
        except Exception as ex:
            self.log.info('Failed:%s', str(ex))
            return [input_list[0], 0, str(ex)]

    def operation_createstoragepolicyandcopy(self, input_list):
        """Adds a storage policy and copy to the commcell
            Args:
                input_list    (list)    --  list consists of (operation, entityType, EntityName,
                                            BitMask and USerName)
            Returns:
                returns status of operation
        """
        self.log.info('creating storage policy and copy:%s', input_list[2])

        try:
            self.log.info('Inputs received for storage policy copy operation:%s', input_list)
            if self.commcell_obj.storage_policies.has_policy('Sec_auto_policyandcopy1'):
                self.log.info('Deleting existing storage policy with same name')
                self._admin_commcell_obj.storage_policies.delete('Sec_auto_policyandcopy1')
            self.commcell_obj.storage_policies.add(storage_policy_name='Sec_auto_policyandcopy1',
                                                   library=self.lib_obj,
                                                   media_agent=self.media_agent)
            second_copy = self.commcell_obj.storage_policies.get('Sec_auto_policyandcopy1')

            if second_copy.has_copy('Sec_auto_secondary_copy1'):
                self.log.info('Deleting existing secondary storage policy copy')
                second_copy.delete_secondary_copy(copy_name='Sec_auto_policyandcopy1')

            second_copy.create_secondary_copy(copy_name='Sec_auto_secondary_copy1',
                                              library_name=self.lib_obj.library_name,
                                              media_agent_name=self.media_agent.media_agent_name)
            self.log.info('Successfully created Primary and Secondary Storage copy:')
            return [input_list[0], 1, 'Success']
        except Exception as ex:
            self.log.info('Failed:%s', str(ex))
            return [input_list[0], 0, str(ex)]

    def operation_joboperations(self, input_list):
        """Performs suspend, resulme and job kill operations on currently running jobs
            Args:
                input_list      (list)  --  list consists of (operation, entityType, EntityName,
                                            BitMask and USerName)
            Returns:
                returns status of operation
        """
        self.log.info('Job operations is performed on:%s', input_list[2])
        try:
            self.log.info('Inputs received for Job operation:%s', input_list)
            client_obj = self._admin_commcell_obj.clients.get(name=input_list[2])
            _agent = client_obj.agents.all_agents
            _agent_obj = Agent(client_object=client_obj, agent_name='file system',
                               agent_id=_agent['file system'])
            _backupset_obj = _agent_obj.backupsets.get('defaultBackupSet')
            _subclient_obj = _backupset_obj.subclients.get('testSC')
            response = _subclient_obj.backup(backup_level="Full", incremental_backup=True,
                                             incremental_level='BEFORE_SYNTH',
                                             collect_metadata=False)
            job_obj = response
            self.log.info('Job operations started on:%s', job_obj)
            job_manager = Job(commcell_object=self.commcell_obj, job_id=job_obj.job_id)
            job_manager.pause(wait_for_job_to_pause=True)
            job_manager.resume(wait_for_job_to_resume=True)
            job_manager.kill(wait_for_job_to_kill=True)
            self.log.info('Successfully completed suspend resume and kill operations:%s',
                          input_list[2])
            return [input_list[0], 1, 'Success']
        except Exception as ex:
            self.log.info('Failed:%s', str(ex))
            return [input_list[0], 0, str(ex)]

    def operations_result_generator(self, operations_list, reciever=None):
        """Performs suspend, HTML content to render results oin table and send mail with all
        operations results
            Args:
                operations_list     (list)  --  list consists of (operation, Result and comment)
        """
        data = ''
        count = 0
        for row in operations_list:
            count = count + 1
            data = data + """\
            <tr>
                <td>{str0}</td>
                <td>{str1}</td>
                {str2}
                <td>{str3}</td>
            </tr>
            """.format(str0=count, str1=row[0], str2=row[1], str3=row[2])
        table_dec = """ \
            <style type="text/css">
              table {
                background: white;
                border-radius:3px;
                border-collapse: collapse;
                height: auto;
                max-width: 900px;
                padding:5px;
                width: 100%;
                animation: float 5s infinite;
              }
              th {
                color:#D5DDE5;
                background:#1b1e24;
                border-bottom: 4px solid #9ea7af;
                font-size:14px;
                font-weight: 300;
                padding:10px;
                text-align:center;
                vertical-align:middle;
              }
              tr {
                border-top: 1px solid #C1C3D1;
                border-bottom: 1px solid #C1C3D1;
                border-left: 1px solid #C1C3D1;
                color:#666B85;
                font-size:16px;
                font-weight:normal;
              }
              tr:hover td {
                background:#4E5066;
                color:#FFFFFF;
                border-top: 1px solid #22262e;
              }
              td {
                background:#FFFFFF;
                padding:10px;
                text-align:center;
                vertical-align:middle;
                font-weight:300;
                font-size:13px;
                border-right: 1px solid #C1C3D1;
              }
              H1{
                background:#FFFFFF;
                padding:10px;
                text-align:center;
                vertical-align:middle;
                font-weight:1000;
                font-size:30px;
                border-right: 1px solid #C1C3D1;
                color:#692E06;
              }
              H2 H3{
                background:#FFFFFF;
                padding:10px;
                text-align:center;
                vertical-align:middle;
                font-weight:300;
                font-size:13px;
                border-right: 1px solid #C1C3D1;
                color:#A908F9
              }
            </style>
        """

        html = '<html>'\
               '<head>' + table_dec +\
               '</head>' \
               '<p><H1><CENTER>Valid Operations Report</CENTER></H1>'\
               '<H3> User: ' + self.user_obj.user_name+'</H3>'\
               '<H3> Associations: ' + str(list(self.user_obj.user_security_associations.values())
                                           )+'</H3></p>'\
               '<body><H2>Security Operations Result:</H2>'\
               '<table style="width:100%">' \
               '<tr>'\
               '<th>Sl. No.</th>'\
               '<th>Operation</th>'\
               '<th>Result</th>'\
               '<th>Reason for failure</th>'\
               '</tr>'+data +\
               '</table>'\
               '</body>'\
               '</html>'
        self._admin_commcell_obj.send_mail(receivers=reciever,
                                           subject='Security Automation Operations Results',
                                           body=html, is_html_content='True')
        self.log.info('Successfully sent report ')

    def operation_validator(self, intended_result, actual_result):
        """Validates actual results of operations against intended results
            Args:
                intended_result     (list)  --  list consists of (operation, entityType,
                                                EntityName, BitMask and USerName)
                actual_result       (List)  --  list consists of results derived from
                                                performing operations
            Returns:
                returns final result consisting of each operations result
        """
        final_result = []
        for each_item in intended_result.keys():
            for each_row in actual_result:
                if each_item == each_row[0]:
                    if intended_result[each_item][3] == 1:
                        if intended_result[each_item][3] == each_row[1]:
                            final_result.append([each_row[0],
                                                 '<td style = "color:#228B22">ALLOWED</td>',
                                                 each_row[2]])
                        else:
                            final_result.append([each_row[0],
                                                 '<td style = "color:#F90808">ALLOWED</td>',
                                                 each_row[2]])
                            self.failed_operation_count = self.failed_operation_count+1
                    elif each_row[1] == 0:
                        final_result.append(
                            [each_row[0], '<td style = "color:#228B22">NOT ALLOWED</td>',
                             each_row[2]])
                    else:
                        final_result.append([each_row[0], '<td style = "color:#F90808">'
                                                          'NOT ALLOWED</td>', each_row[2]])
                        self.failed_operation_count = self.failed_operation_count + 1

                    break
        return final_result, self.failed_operation_count

    def clear_cache_tables(self):
        """Method clears cache tables used for security operations

        """
        query1 = 'delete from intendedResulttable'
        self._sqlite.execute(query=query1)
        query2 = 'delete from EntityCapabilityBitMask'
        self._sqlite.execute(query=query2)
