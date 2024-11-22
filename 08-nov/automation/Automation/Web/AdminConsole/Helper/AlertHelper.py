from selenium.webdriver.common.by import By
#FixMe https://engweb.commvault.com/engtools/defect/222090
# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
This module provides the function or operations that can be used to run
basic operations on Alerts page.

To begin, create an instance of ALertMain for Alerts test case.

To initialize the class variables, pass the instance object to the appropriate
definition of AdminConsoleInfo

Call the required definition using the instance object.

add_alert_definition                --   Add new ALert definition in admin console

validate_alert_definition           --   Validate New alert definition in adminconsole

__validate_db_values                --   Validate if the alert creation is reflected in db
                                        successfully or not

__validate_alert_details            --   validate alert details displayed on UI match the
                                        ones provided as input

__get_input_values                  --   Fetch & arrange input values to match the format
                                        values are displayed in UI

validate_triggered_alert            --   Validate if the alert is triggered successfully

create_fs_subclient                 --   Create new subclient in adminconsole for provided
                                        client

perform_fs_subclient_backup         --   Perform backup for specified subclient

disable_and_validate                --   Disabled Alert definition and validate if its
                                        triggered or not with valid conditions

enable_and_validate                 --   Disabled Alert definition and validate if its
                                        triggered or not with valid conditions

edit_alert_definition               --   Edit values for alert definition

delete_alert_definition             --   Delete alert definition from admin console

delete_test_subclient               --   Delete subclient from specified client

perform_fs_subclient_restore        --   Perform a restore for specified subclient

logout_and_navigate_to_login_page   --   logout of admin console and navigate to login
                                        page

delete_curr_triggered_alert         --   Delete the triggered alert

clear_triggered_alerts              --   Delete all triggered alerts



Class:

    RAlertMain()

Methods:

    get_alert_notification_text             --      Method to get the alert notification text

    __select_unopened_triggered_alert       --      Method to select the triggered alert



Class:

    RAlertMain()

Methods:

    get_alert_notification_text             --      Method to get the alert notification text

    __select_unopened_triggered_alert       --      Method to select the triggered alert

"""

import ast
import os
import re
from bs4 import BeautifulSoup
import time
import http.server
import socketserver

from Web.AdminConsole.Components.table import Table, Rtable
from Web.AdminConsole.Components.panel import Backup
from Web.AdminConsole.Components.dialog import RModalDialog
from Web.AdminConsole.AdminConsolePages.AlertsDefinitionsInfo import AlertsDefinitionsInfo
from Web.AdminConsole.AdminConsolePages.AlertDefinitions import AlertDefinitions, RAlertDefinitions
from Web.AdminConsole.AdminConsolePages.Alerts import Alerts, Ralerts
from Web.AdminConsole.FileServerPages.file_servers import FileServers
from Web.AdminConsole.FileServerPages.fsagent import FsSubclient
from Web.AdminConsole.AdminConsolePages.Jobs import Jobs
from Web.Common.exceptions import CVWebAutomationException


class AlertMain(object):
    '''
    Helper file to provide arguments and handle function call to base files
    '''

    def __init__(self, admin_console, commcell=None, csdb=None):
        '''
        Initialize method for AlertMain

        Args:
            admin_console      (object)   --  the admin console file object

            commcell    (object)   --  an instance of the commcell class

            csdb        (object)   --  the cs DB object
        '''

        self.__admin_console = admin_console
        self.__driver = admin_console.driver
        self.csdb = csdb
        self.__commcell = commcell
        self.log = admin_console.log

        self.alert_details = AlertsDefinitionsInfo(self.__admin_console)
        self.alerts = Alerts(self.__admin_console)
        self.alerts_definitions = AlertDefinitions(self.__admin_console)
        self.__table = Table(self.__admin_console)
        self.file_servers = FileServers(self.__admin_console)
        self.file_server_subclient = FsSubclient(self.__admin_console)
        self.jobs = Jobs(self.__admin_console)

        self._alert_name = None
        self._validatekeyedit = False
        self._backupdata = None
        self._client_name = None
        self._alert_criteria = None
        self._alert_target = None
        self._recipients = []
        self.update_recipients = []
        self._value_of_x = None
        self._subclient_name = None
        self._plan_name = None
        self._alert_entities = {'server_group_list': ['Server groups'],
                                'server_list': ['Servers']}
        self._alert_disabled = False
        self._restore_path = None
        self._backup_set = "defaultBackupSet"
        self._agent_name = "Windows File System"
        self._ind_notification = 'OFF'
        self._alert_locale = None
        self._mail_subject = None
        self._job_id = None

    @property
    def alert_name(self):
        """ Get alert name"""
        return self._alert_name

    @alert_name.setter
    def alert_name(self, value):
        """ Set alert name"""
        self._alert_name = value

    @property
    def alert_entities(self):
        """ Get alert entities"""
        return self._alert_entities

    @alert_entities.setter
    def alert_entities(self, value):
        """ Set alert entities"""
        self._alert_entities = value

    @property
    def client_name(self):
        """ Get client name"""
        return self._client_name

    @client_name.setter
    def client_name(self, value):
        """ Set client name"""
        self._client_name = value

    @property
    def alert_criteria(self):
        """ Get alert_criteria"""
        return self._alert_criteria

    @alert_criteria.setter
    def alert_criteria(self, value):
        """ Set alert_criteria"""
        self._alert_criteria = value

    @property
    def alert_target(self):
        """ Get alert_target"""
        return self._alert_target

    @alert_target.setter
    def alert_target(self, value):
        """ Set alert_target"""
        self._alert_target = value

    @property
    def recipients(self):
        """ Get recipients"""
        return self._recipients

    @recipients.setter
    def recipients(self, value):
        """ Set recipients"""
        self._recipients = value

    @property
    def value_of_x(self):
        """ Get value_of_x"""
        return self._value_of_x

    @value_of_x.setter
    def value_of_x(self, value):
        """ Set value_of_x"""
        self._value_of_x = value

    @property
    def subclient_name(self):
        """ Get subclient name"""
        return self._subclient_name

    @subclient_name.setter
    def subclient_name(self, value):
        """ Set subclient name"""
        self._subclient_name = value

    @property
    def plan_name(self):
        """ Get plan_name"""
        return self._plan_name

    @plan_name.setter
    def plan_name(self, value):
        """ Set plan_name"""
        self._plan_name = value

    @property
    def backupdata(self):
        """ Get backupdata"""
        return self._backupdata

    @backupdata.setter
    def backupdata(self, value):
        """ Set backupdata"""
        self._backupdata = value

    @property
    def validatekeyedit(self):
        """Get validatekeyedit"""
        return self._validatekeyedit

    @validatekeyedit.setter
    def validatekeyedit(self, value):
        """Set validatekeyedit"""
        self._validatekeyedit = value

    @property
    def alert_disabled(self):
        """Get alert_disabled value"""
        return self._alert_disabled

    @alert_disabled.setter
    def alert_disabled(self, value):
        """Set alert_disabled value"""
        self._alert_disabled = value

    @property
    def restore_path(self):
        """Get restore_path value"""
        return self._restore_path

    @restore_path.setter
    def restore_path(self, value):
        """Set restore_path value"""
        self._restore_path = value

    @property
    def ind_notification(self):
        """Get ind_notification value"""
        return self._ind_notification

    @ind_notification.setter
    def ind_notification(self, value):
        """Set ind_notification value"""
        self._ind_notification = value

    @property
    def alert_locale(self):
        """Get alert_locale value"""
        return self._alert_locale

    @alert_locale.setter
    def alert_locale(self, value):
        """Set alert_locale value"""
        self._alert_locale = value

    @property
    def mail_subject(self):
        """Get mail_subject value"""
        return self._mail_subject

    @mail_subject.setter
    def mail_subject(self, value):
        """Set mail_subject value"""
        self._mail_subject = value

    @property
    def agent_name(self):
        """Get agent_name value"""
        return self._agent_name

    @agent_name.setter
    def agent_name(self, value):
        """Set agent_name value"""
        self._agent_name = value

    @property
    def backup_set(self):
        """Get backup_set value"""
        return self._backup_set

    @backup_set.setter
    def backup_set(self, value):
        """Set backup_set value"""
        self._backup_set = value

    def add_alert_definition(self):
        """calls create_alert_definition function from Alerts Class
            and generates alert in Admin Console"""

        self.__admin_console.navigator.navigate_to_alerts()
        self.alerts.select_alert_definitions()
        self.alerts_definitions.create_alert_definition(self.alert_name,
                                                   self.alert_criteria,
                                                   self.recipients['To'],
                                                   self.recipients['Cc'],
                                                   self.recipients['Bcc'],
                                                   self.value_of_x,
                                                   self.alert_entities,
                                                   self.alert_target,
                                                   self.ind_notification)

    def validate_alert_definition(self):
        """validates the designated plan in admin console plans page"""

        if self.__validate_db_values():
            self.log.info("Alert entry is successfully created in database")
        else:
            raise CVWebAutomationException("Alert entry is not created in database, alert creation failed")
        self.__validate_alert_details()

    def __validate_db_values(self):
        """Validates existence of created alert in database and returns Boolean result"""

        query = "select id from NTnotificationRule where \
notificationName = '{0}'".format(self.alert_name)
        self.csdb.execute(query)
        db_output = self.csdb.fetch_one_row()
        if db_output:
            self.log.info("Database Validation Succeeded")
            return True
        self.log.info("Database Validation Failed")
        return False

    def __validate_alert_details(self):
        """validates if the plan details are displayed correctly"""

        self.__admin_console.navigator.navigate_to_alerts()
        self.alerts.select_alert_definitions()
        self.alerts_definitions.select_alert(self.alert_name)
        displayed_val = self.alert_details.alert_info(self.alert_target)


        displayed_val, validatekeydict = self.__get_input_values(
            displayed_val, get_validatekeydict=True)

        displayed_val['Entities'] = displayed_val.pop('Objects')

        validatekeydict = ast.literal_eval(validatekeydict)
        for key_dict, val_dict in validatekeydict.items():
            if isinstance(val_dict, list):
                self.log.info('Entity given_val "%s"', val_dict)
                if set(displayed_val[key_dict]) == set(validatekeydict[key_dict]):
                    self.log.info("{0} displayed for {1} matches with {2} given".format\
                            (displayed_val[key_dict], key_dict, validatekeydict[key_dict]))
                else:
                    exp = "{0} displayed for {1} does not match with {2} given ".format\
                            (displayed_val[key_dict], key_dict, validatekeydict[key_dict])
                    raise CVWebAutomationException(exp)
            elif isinstance(val_dict, str):
                self.log.info('Entity given_val "%s"', val_dict)
                if displayed_val[key_dict] == validatekeydict[key_dict]:
                    self.log.info("{0} displayed for {1} matches with {2} given".format\
                        (displayed_val[key_dict], key_dict, validatekeydict[key_dict]))
                else:
                    exp = "{0} displayed for {1} does not match with {2} given ".format\
                    (displayed_val[key_dict], key_dict, validatekeydict[key_dict])
                    raise CVWebAutomationException(exp)
            else:
                self.log.info('Entity given_val :%s', val_dict)
                for item, valuedict in val_dict.items():
                    d_val = displayed_val[key_dict][item]
                    key_val = validatekeydict[key_dict][item]
                    if d_val == key_val:
                        self.log.info("%s values match", item)
                    else:
                        exp = "{0} displayed for {1} does not match with {2} given ".format\
                             (d_val, item, key_val)
                        raise CVWebAutomationException(exp)

    def __get_input_values(self,
                           displayed_val,
                           get_validatekeydict=False):
        """ This function sets default values to the parameters provided for plan creation """
        if self.alert_criteria in ['Backup Delayed by X Hrs', 'Backup Job Activity',
                                   'Backup Job completed with Errors', 'Backup Job Failed',
                                   'Backup Job Skipped', 'Backup Job Started',
                                   'Backup Job Succeeded']:
            alert_criteria = self.alert_criteria.lstrip('Backup ')
            default_comp_values = {
                "Alert_type": "Data Protection",
                "Alert_category": "Job Management",
                "Alert_criteria": alert_criteria}
        elif self.alert_criteria in ['Restore Job Activity',
                                     'Restore Job completed with Errors',
                                     'Restore Job Failed',
                                     'Restore Job Skipped',
                                     'Restore Job Started',
                                     'Restore Job Succeeded']:
            alert_criteria = self.alert_criteria.lstrip('Restor')
            alert_criteria = self.alert_criteria.lstrip('e ')
            default_comp_values = {
                "Alert_type": "Data Recovery",
                "Alert_category": "Job Management",
                "Alert_criteria":alert_criteria}
        elif self.alert_criteria == 'Increase in Data size by X percent for backup job':
            alert_criteria = 'Increase in Data size by %s percent', self.value_of_x
            default_comp_values = {
                "Alert_type": "Data Recovery",
                "Alert_category": "Job Management",
                "Alert_criteria": alert_criteria}
        elif self.alert_criteria == 'Decrease in Data size by X percent for backup job':
            alert_criteria = 'Decrease in Data size by %s percent', self.value_of_x
            default_comp_values = {
                "Alert_type": "Data Recovery",
                "Alert_category": "Job Management",
                "Alert_criteria": alert_criteria}
        elif self.alert_criteria == 'No Back up for last X days':
            alert_criteria = 'No Back up for last %s days', self.value_of_x
            default_comp_values = {
                "Alert_type": "Data Protection",
                "Alert_category": "Job Management",
                "Alert_criteria": alert_criteria}
        elif self.alert_criteria == 'VM Backup Failed':
            alert_criteria = 'Job Failed'
            default_comp_values = {
                "Alert_type": "Data Protection",
                "Alert_category": "Job Management",
                "Alert_criteria": alert_criteria}
        elif self.alert_criteria == 'VM Backup Succeeded':
            alert_criteria = 'Job Succeeded'
            default_comp_values = {
                "Alert_type": "Data Protection",
                "Alert_category": "Job Management",
                "Alert_criteria": alert_criteria}
        else:
            default_comp_values = {
                "Alert_type": "Clients",
                "Alert_category": "Configuration",
                "Alert_criteria": "Disk Space Low"}

        entities = []
        if self.alert_entities['server_group_list']:
            if "Server groups" in self.alert_entities['server_group_list']:
                entities.append("All server groups")
            else:
                for value in self.alert_entities['server_group_list']:
                    entities.append(value)
        else:
            entities.append("No server group selected")

        if self.alert_entities['server_list']:
            if "Servers" in self.alert_entities['server_list']:
                entities.append("All servers")
            else:
                for value in self.alert_entities['server_list']:
                    entities.append(value)
        else:
            entities.append("No server selected")

        for key, value in displayed_val.items():
            if isinstance(value, list):
                if displayed_val[key] == [None]:
                    displayed_val[key] = default_comp_values[key]
            elif isinstance(value, str):
                if displayed_val[key] == [None]:
                    displayed_val[key] = default_comp_values[key]
            else:
                for item, valuedict in value.items():
                    if displayed_val[key][item] is None:
                        displayed_val[key][item] = default_comp_values[key][item]

        if self.alert_target['Email']:
            send_alert_to = 'Email'
            recips = 3
        if self.alert_target['Event viewer']:
            if not self.alert_target['Email']:
                send_alert_to = 'Event viewer'
                recips = 0
            else:
                send_alert_to = send_alert_to +', Event viewer'
                recips = 3
        if self.alert_target['Console']:
            if not self.alert_target['Email'] and not self.alert_target['Event viewer']:
                send_alert_to = 'Console'
                recips = 1
            elif not self.alert_target['Email'] and self.alert_target['Event viewer']:
                send_alert_to = send_alert_to +', Console'
                recips = 1
            else:
                send_alert_to = send_alert_to +', Console'
                recips = 3
        if self.alert_target['SNMP']:
            if not self.alert_target['Email'] and not self.alert_target\
                ['Event viewer'] and not self.alert_target['Console']:
                send_alert_to = 'SNMP'
                recips = 0
            elif not self.alert_target['Email'] and self.alert_target\
                ['Event viewer'] and not self.alert_target['Console']:
                send_alert_to = send_alert_to +', SNMP'
                recips = 0
            elif not self.alert_target['Email'] and self.alert_target\
                ['Event viewer'] and self.alert_target['Console']:
                send_alert_to = send_alert_to +', SNMP'
                recips = 1
            elif not self.alert_target['Email'] and not self.alert_target\
                ['Event viewer'] and self.alert_target['Console']:
                send_alert_to = send_alert_to +', SNMP'
                recips = 1
            else:
                send_alert_to = send_alert_to +', SNMP'
                recips = 3

        recipients_in_to = {}
        recipients_in_cc = {}
        recipients_in_bcc = {}

        if self.validatekeyedit:
            update_to_recipients = self.update_recipients['To']
            update_cc_recipients = self.update_recipients['Cc']
            update_bcc_recipients = self.update_recipients['Bcc']

            update_to_recipients['Add']['Group'].extend(self.recipients['To']['Group'])
            update_to_recipients['Add']['Email'].extend(self.recipients['To']['Email'])
            update_to_recipients['Add']['User'].extend(self.recipients['To']['User'])
            update_cc_recipients['Add']['Group'].extend(self.recipients['Cc']['Group'])
            update_cc_recipients['Add']['Email'].extend(self.recipients['Cc']['Email'])
            update_cc_recipients['Add']['User'].extend(self.recipients['Cc']['User'])
            update_bcc_recipients['Add']['Group'].extend(self.recipients['Bcc']['Group'])
            update_bcc_recipients['Add']['Email'].extend(self.recipients['Bcc']['Email'])
            update_bcc_recipients['Add']['User'].extend(self.recipients['Bcc']['User'])

            to_recipients = update_to_recipients['Add']
            cc_recipients = update_cc_recipients['Add']
            bcc_recipients = update_bcc_recipients['Add']

        else:
            to_recipients = self.recipients['To']
            cc_recipients = self.recipients['Cc']
            bcc_recipients = self.recipients['Bcc']

        if to_recipients['Group']:
            for value in to_recipients['Group']:
                recipients_in_to.update({value : 'Group'})
        if to_recipients['User']:
            for value in to_recipients['User']:
                recipients_in_to.update({value: 'User'})
        if to_recipients['Email']:
            for value in to_recipients['Email']:
                recipients_in_to.update({value: 'Email'})

        if cc_recipients['Group']:
            for value in cc_recipients['Group']:
                recipients_in_cc.update({value : 'Group'})
        if cc_recipients['User']:
            for value in cc_recipients['User']:
                recipients_in_cc.update({value: 'User'})
        if cc_recipients['Email']:
            for value in cc_recipients['Email']:
                recipients_in_cc.update({value: 'Email'})

        if bcc_recipients['Group']:
            for value in bcc_recipients['Group']:
                recipients_in_bcc.update({value : 'Group'})
        if bcc_recipients['User']:
            for value in bcc_recipients['User']:
                recipients_in_bcc.update({value: 'User'})
        if bcc_recipients['Email']:
            for value in bcc_recipients['Email']:
                recipients_in_bcc.update({value: 'Email'})

        if get_validatekeydict:
            if recips == 0:
                validatekeydict = """{'AlertName':'""" + str(self.alert_name) + """',
                'Alert target': {'Send alert to': '"""+str(send_alert_to)+"""'},
                'Entities': """ + str(entities)+""",
                'Alert summary': {'Alert type': '"""+str(default_comp_values["Alert_type"])\
                                  +"""',
                'Alert category':'"""+str(default_comp_values["Alert_category"])+"""',
                'Alert criteria' : '"""+str(default_comp_values["Alert_criteria"])+"""',
                'Send individual notification':'"""+str(self.ind_notification)+"""'}}"""
            if recips == 1:
                validatekeydict = """{'AlertName':'""" + str(self.alert_name) + """',
                'Alert target': {'Send alert to': '"""+str(send_alert_to)+"""',
                'To':"""+str(recipients_in_to)+"""}, 'Entities': """ + str(entities)+""",
                'Alert summary': {'Alert type': '"""+str(default_comp_values["Alert_type"])\
                                  +"""',
                'Alert category':'"""+str(default_comp_values["Alert_category"])+"""',
                'Alert criteria' : '"""+str(default_comp_values["Alert_criteria"])+"""',
                'Send individual notification':'"""+str(self.ind_notification)+"""'}}"""
            else:
                validatekeydict = """{'AlertName':'""" + str(self.alert_name) + """',
                'Alert target': {'Send alert to': '"""+str(send_alert_to)+"""',
                'To':"""+str(recipients_in_to)+""", 'Cc':"""+str(recipients_in_cc)+""",
                'Bcc':"""+str(recipients_in_bcc)+"""}, 'Entities': """ + str(entities)+""",
                'Alert summary': {'Alert type': '"""+str(default_comp_values["Alert_type"])\
                                  +"""',
                'Alert category':'"""+str(default_comp_values["Alert_category"])+"""',
                'Alert criteria' : '"""+str(default_comp_values["Alert_criteria"])+"""',
                'Send individual notification':'"""+str(self.ind_notification)+"""'}}"""
        return displayed_val, validatekeydict

    def validate_triggered_alert(self):
        """ Method to Validate if an alert is triggered or not """
        count = 0
        self.__admin_console.navigator.navigate_to_alerts()
        self.alerts.select_triggered_alerts()
        self.__table.search_for(self.alert_name)
        if self.alert_disabled:
            if not self.__admin_console.check_if_entity_exists("link", self.alert_name):
                self.log.info("Alert is not displayed in Triggered Alerts Screen as it\
                        is disabled, verification successful")
            else:
                exp = "Alert was disabled but still displayed, validation failed"
                raise CVWebAutomationException(exp)
        else:
            if self.__admin_console.check_if_entity_exists("link", self.alert_name):
                self.__table.apply_filter_over_column('Alert info', self.alert_name)
                self.__table.apply_filter_over_column('Client name', self.client_name)
                if self.__admin_console.check_if_entity_exists("link", self.alert_name):
                    self.log.info("Alert is displayed in Triggered Alerts Screen")
                else:
                    exp = "Alert was enabled but still not displayed, validation failed"
                    raise CVWebAutomationException(exp)
            else:
                exp = "Alert was enabled but still not displayed, validation failed"
                raise CVWebAutomationException(exp)

    def create_fs_subclient(self):
        """ Method to add new subclient to a client """
        self.__admin_console.navigator.navigate_to_file_servers()
        self.file_servers.access_server(self.client_name)
        self.file_server_subclient.add_fs_subclient(self.backup_set,
                                                    self.subclient_name,
                                                    self.plan_name)
        self.__driver.find_element(By.XPATH, "//*[@id='createFsContentGroup_button_#2561']").click()
        self.__admin_console.wait_for_completion()

    def perform_fs_subclient_backup(self):
        """Calls method initiate_server_backup to initiate a backup for a subclient
            or client mentioned"""
        self.__admin_console.navigator.navigate_to_file_servers()
        self.file_servers.access_server(self.client_name)
        job_id = self.file_server_subclient.backup_subclient(self.backup_set, self.subclient_name,
                                                             Backup.BackupType.INCR)
        self.jobs.job_completion(job_id)
        self._job_id = job_id

    def disable_and_validate(self):
        """Disables the alert and then validates if the alert is triggered or not"""
        self.__admin_console.navigator.navigate_to_alerts()
        self.alerts.select_alert_definitions()
        self.alerts_definitions.disable_alert_definition(self.alert_name)
        self.alert_disabled = True
        self.perform_fs_subclient_backup()
        self.validate_triggered_alert()

    def enable_and_validate(self):
        """Enables the alert and then validates if the alert is triggered or not"""
        self.__admin_console.navigator.navigate_to_alerts()
        self.alerts.select_alert_definitions()
        self.alerts_definitions.enable_alert_definition(self.alert_name)
        self.alert_disabled = False
        self.perform_fs_subclient_backup()
        self.validate_triggered_alert()

    def edit_alert_definition(self):
        """Calls different methods to edit tiles for an Existing Alert"""
        self.__admin_console.navigator.navigate_to_alerts()
        self.alerts.select_alert_definitions()
        self.alerts_definitions.select_alert(self.alert_name)
        self.alert_details.edit_alert_target(self.alert_target,
                                             self.update_recipients['To'],
                                             self.update_recipients['Cc'],
                                             self.update_recipients['Bcc'])
        self.alert_details.edit_alert_entities(self.alert_entities)
        self.alert_details.edit_alert_summary(self.ind_notification)
        self.validatekeyedit = True

    def delete_alert_definition(self):
        """deletes the designated alert definition"""
        self.__admin_console.navigator.navigate_to_alerts()
        self.alerts.select_alert_definitions()
        self.alerts_definitions.delete_alert_definition(self.alert_name)

    def delete_test_subclient(self):
        """Calls method to delete test subclient created"""
        self.__admin_console.navigator.navigate_to_file_servers()
        self.file_servers.access_server(self.client_name)
        self.file_server_subclient.delete_subclient(self.backup_set, self.subclient_name)
        self.__admin_console.wait_for_completion()

    def perform_fs_subclient_restore(self):
        """Calls method to initiate Restore"""
        self.__admin_console.navigator.navigate_to_file_servers()
        self.file_servers.access_server(self.client_name)
        job_id = self.file_server_subclient.restore_subclient(self.backup_set, self.subclient_name)
        self.jobs.job_completion(job_id)

    def delete_curr_triggered_alert(self):
        """Method to call base function to delete selected alert"""
        self.__admin_console.navigator.navigate_to_alerts()
        self.alerts.select_triggered_alerts()
        self.alerts.delete_current_triggered_alert(self.alert_name, self.client_name)

    def clear_triggered_alerts(self):
        """Method to call base function to delete all alerts on Triggered alerts page"""
        self.__admin_console.navigator.navigate_to_alerts()
        self.alerts.select_triggered_alerts()
        self.__admin_console.refresh_page()
        self.__admin_console.close_popup()
        self.alerts.delete_all_triggered_alerts()


class RAlertMain(object):

    """
    This class provides the function or operations that can be used to run
    basic operations on Alerts page.

    To begin, create an instance of RALertMain for Alerts test case.
    """

    def __init__(self, admin_console):
        """
        This method initializes the RAlertMain class

        Args:
            admin_console   (object)    --  instance of the AdminConsole class
        """
        self.__admin_console = admin_console
        self.__navigator = self.__admin_console.navigator
        self.__alerts = Ralerts(admin_console)
        self.__table = Rtable(admin_console)
        self.__alert_definitions = RAlertDefinitions(admin_console)
        self.log = admin_console.log
    
    def __select_unopened_triggered_alert(self, alert_name, wait=300):
        """Select the triggered alert
        
        Args:
            alert_name (str): The name of the alert

        Raises:
            Exception: If the alert is not found or already opened
        """
        try:
            self.__table.wait_for_rows([alert_name], wait=wait)
            self.__admin_console.click_by_xpath(f"//a[@role='button']/strong[contains(text(), '{alert_name}')]")
        except:
            raise Exception("Alert not found or already opened")
    
    def get_alert_notification_text(self, alert_name, wait=300):
        """Check the alert notification
        
        Args:
            alert_name (str): The name of the alert

        Returns:
            str: The alert text
        """
        
        self.__admin_console.navigator.navigate_to_alerts()
        self.__select_unopened_triggered_alert(alert_name, wait=wait)
        self.__admin_console.driver.switch_to.frame(self.__admin_console.driver.find_element(By.XPATH, "//iframe[@title='Alert template previewer']"))
        # read the text in html/body
        alert_text = self.__admin_console.driver.find_element(By.XPATH, "//body").text
        self.__admin_console.driver.switch_to.default_content()
        RModalDialog(self.__admin_console, "Alert details").click_close()
        return alert_text


    def validate_alert_email(self, alert_name, temp_dir, expected_alert_content):
        """ Validate alert email
        
            Args:
                alert_name (str): Name of the alert
                temp_dir (str): Path to the directory containing the alert email
                expected_alert_content (list): List of expected strings in the alert email
                
        """
        
        self.log.info("verifying [%s] alert email", alert_name)

        # Use a pattern to match the alert email file with alert_name
        escaped_alert_name = re.escape(alert_name)  # Escape any special characters in alert_name
        pattern = re.compile(rf'^\d+-{escaped_alert_name}\.html$')
        files = os.listdir(temp_dir)
        matching_files = [f for f in files if pattern.match(f)]

        if not matching_files:
            raise FileNotFoundError(f"No file matching the pattern '*-{alert_name}.html' found.")

        # Selecting last file since there can me many files matching the pattern
        # and last file is the latest (most recent)
        email_path = os.path.join(temp_dir, matching_files[-1])
        with open(email_path, 'r') as file:
            mail_content = file.read()

        # Parse the email content using BeautifulSoup
        soup = BeautifulSoup(mail_content, 'html.parser')
        text_content = soup.get_text()

        # Check if all expected strings are in the email content
        for expected_string in expected_alert_content:
            if expected_string not in text_content:
                self.log.error("Expected string [%s] not found in the email content", expected_string)
                raise AssertionError(f"Expected string [{expected_string}] not found in the email content")

        self.log.info("Alert [%s] mail validated", alert_name)
    
    def navigate_and_delete_custom_alert(self, alert_name):
        """Navigate to Alerts page and delete the custom alert
        
        Args:
            alert_name (str): Name of the alert
        """
        self.__navigator.navigate_to_alerts()
        self.__alerts.select_alert_definitions()
        self.__alert_definitions.delete_alert_definition(alert_name)

    def validate_console_notification(self, alert_name, text_to_verify):
        """Validate the console notification
        
        Args:
            alert_name (str): Name of the alert
            text_to_verify (str): Text to verify in the console notification
        """
        alert_notif_text = self.get_alert_notification_text(alert_name).split('|')
        for i in range(len(text_to_verify)):
            if text_to_verify[i] not in alert_notif_text[i]:
                raise CVWebAutomationException("Console Notification does not match the expected text")
        
        self.log.info("Console Notification validated")


    def trigger_backup_fail_three_times_alert(self, subclient_obj):
        """Trigger the Backup Fail Three Times alert

        Args:
            subclient_obj (object): Subclient object
        """
        for _ in range(3):
            self.log.info("Backing up")
            subclient_obj.backup('Full')
            latest_job = subclient_obj.find_latest_job()
            latest_job.wait_for_completion()
            time.sleep(120)

    class CustomHandlerForPostRequests(http.server.SimpleHTTPRequestHandler):
        """ Custom handler to handle POST requests """
        def do_POST(self):
            """
            Handle POST requests
            """

            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length).decode('utf-8')

            # Store the data in the server object
            self.server.post_data = post_data

            # Create a response
            response = f"Received data: {post_data}"

            # Send HTTP response
            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(response.encode('utf-8'))

    def run_server_return_post_data(self, mutable_object_return, port, timeout=120):
        """
        Run a server to receive POST requests and return the data received
        
        Args:
            mutable_object_return (list): A mutable object to store the received data
            port (int): Port number to run the server on
            timeout (int): Timeout in seconds for the server to wait for a POST request
            
        Returns:
            str: The data received from the POST request
                
        """
        with socketserver.TCPServer(("", port), self.CustomHandlerForPostRequests) as httpd:
            httpd.timeout = timeout
            httpd.post_data = None
            httpd.handle_request()  # Handles only one request and stops

            if httpd.post_data is None:
                raise TimeoutError("Server timeout: no POST request received.")
            
            mutable_object_return += [httpd.post_data] # for use in multithreading
            return httpd.post_data
