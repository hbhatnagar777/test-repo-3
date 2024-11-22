from selenium.webdriver.common.by import By

# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
This module provides the function or operations that can be used to run
basic operations on plans or subscriptions page.

To begin, create an instance of PlanMain for plans test case.

To initialize the class variables, pass the instance object to the appropriate
definition of AdminConsoleInfo

Call the required definition using the instance object.

list_plans                      --  Lists all the plans

delete_plan__attempt_deletion   --  Attempt plan deletion and check for dual authorization message
delete_plan__approve_deletion   --  Perform approval action for dual authorization
delete_plans                    --  delete plans from admin console

validate_plans                   --               validate plans in admin console

add_plan                        --                add plans in the admin console

get_copy_info                   --  Retrieves all information from Copy details page in the form of a dictionary
is_compliance_lock_enabled      --  Checks if compliance lock is enabled on copy of given plan

plans_lookup                    --  looks up for plans listed in various places in the CC.

"""
import time

from _collections import OrderedDict
from Web.AdminConsole.Components.table import Table, Rtable
from Web.AdminConsole.AdminConsolePages.Plans import Plans, RPO
from Web.AdminConsole.AdminConsolePages.PlanDetails import PlanDetails
from Web.Common.exceptions import CVWebAutomationException, CVTestStepFailure
from random import sample, randint, choice
from Server.Plans.planshelper import PlansHelper
from Web.Common.page_object import (WebAction, PageService)
from Web.AdminConsole.Helper.file_servers_helper import FileServersMain
from Web.AdminConsole.Components.dialog import RModalDialog
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Components.alert import Alert
from Web.AdminConsole.FileServerPages import file_servers
from Web.AdminConsole.Components.panel import RDropDown, RPanelInfo
from Web.AdminConsole.VSAPages import vm_groups

# Dual Authorization for Plan Deletion
from Web.Common.cvbrowser import BrowserFactory
from Web.WebConsole.Forms.forms import Forms, Actions


class PlanMain:
    """ Helper file to provide arguments and handle function call to main file """

    def __init__(self, admin_console: AdminConsole, commcell=None, csdb=None):
        """
        Initialize method for PlanMain
        """
        self.__admin_console = admin_console
        self.__navigator = self.__admin_console.navigator
        self.__props = self.__admin_console.props
        self.__driver = self.__admin_console.driver
        self.__plans = Plans(self.__admin_console)
        self.__plan_details = PlanDetails(self.__admin_console)
        self.__table = Table(self.__admin_console)
        self.__rtable = Rtable(self.__admin_console)
        self.__rmodal_diag = RModalDialog(self.__admin_console)
        self.__alert = Alert(self.__admin_console)
        self.log = self.__admin_console.log
        self.csdb = csdb
        self.commcell = commcell

        self._plan_name = None
        self._sec_copy_name = None
        self._laptop_edited = False
        self._server_edited = False
        self._derived_plan = False
        self._backup_data = {'file_system': ["Mac", "Unix", "Windows"],
                             'content_backup': ["Content Library", "Documents", "Desktop",
                                                "Office", "Music", "Pictures", "Videos"],
                             'content_library': ['Content Library', 'Image',
                                                 'Office', 'System',
                                                 'Temporary Files (Windows)', 'Text',
                                                 'Thumbnail Supported', 'Video',
                                                 'Virtual Machine'],
                             'custom_content': '',
                             'exclude_folder': ['Documents'],
                             'exclude_folder_library': ['Audio', 'Disk Images', 'Executable',
                                                        'Email Files', 'Image', 'Office',
                                                        'System', 'Thumbnail Supported',
                                                        'Video', 'Temporary Files (Mac)'],
                             'exclude_folder_custom_content': ''}
        self._allow_override = {"Storage_pool": "Override required",
                                "RPO": "Override optional",
                                "Folders_to_backup": "Override not allowed",
                                "Retention": None}
        self._system_state = True
        self._full_backup = False
        self._vss = False
        self._allowed_features = {'Edge Drive': 'OFF',
                                  'audit_drive_operations': True,
                                  'notification_for_shares': True,
                                  'edge_drive_quota': '200',
                                  'DLP': 'ON',
                                  'Archiving': 'ON'}
        self._archiving_rules = {"start_clean": "40", "stop_clean": "90",
                                 "file_access_time": "85", "file_modify_time": None,
                                 "file_create_time": "2", "archive_file_size": None,
                                 "max_file_size": None, "archive_read_only": True,
                                 "replace_file": None, "delete_file": None}
        self._file_system_quota = '250'
        self._storage = {'pri_storage': None,
                         'pri_ret_period': '20',
                         'sec_storage': None,
                         'sec_ret_period': '45',
                         'ret_unit': 'Day(s)'}
        self._throttle_send = 'No limit'
        self._throttle_receive = 'No limit'
        self._alerts = {"Backup": "No backup for last 4 days",
                        "Jobfail": "Restore Job failed",
                        "edge_drive_quota": "Edge drive quota alert",
                        "file_system_quota": "File system quota alert"}
        self._backup_day = dict.fromkeys(['1', '2', '3'], 1)
        self._backup_duration = dict.fromkeys(['2', '3', '4', '5'], 1)
        self._backup_window = "Monday through Wednesday : 12am-4am"
        self._snap_recovery_points = '12'
        self._rpo_hours = '5'
        self._edit_plan_dict = {'throttle_send': '1000', 'throttle_receive': '1000',
                                'file_system_quota': '250', 'rpo_hours': '30',
                                'additional_storage': {'storage_name': 'Store',
                                                       'storage_pool': 'Secondary',
                                                       'ret_period': '10'},
                                'allowed_features': {"Edge Drive": "ON",
                                                     'audit_drive_operations': False,
                                                     'notification_for_shares': False,
                                                     'edge_drive_quota': '250',
                                                     "DLP": "OFF",
                                                     "Archiving": "OFF"},
                                "region": None,
                                'edit_storage': None,
                                'override_restrictions': {"Storage_pool": "Override optional",
                                                          "RPO": "Override not allowed",
                                                          "Folders_to_backup": "Override optional"}}
        self._edit_server_plan_dict = {'override_restrictions': {"Storage_pool": "Override optional",
                                                                 "RPO": "Override not allowed",
                                                                 "Folders_to_backup": "Override optional"},
                                       'rpo_hours': '5',
                                       'additional_storage': {'storage_name': 'Store',
                                                              'storage_pool': 'StorageA',
                                                              'ret_period': '10'},
                                       'edit_storage': None
                                       }
        self._user_usergroup_association = None
        self._user_usergroup_de_association = None
        self._content_selected = None
        self._retention = {'min_retention': {'value': 'Indefinitely', 'unit': None},
                           'deleted_item_retention': {'value': '5', 'unit': 'day(s)'},
                           'file_version_retention': {'duration': None,
                                                      'versions': None,
                                                      'rules': {'days': '4',
                                                                'weeks': '5',
                                                                'months': '6'}}}
        self._snapshot_options = {'snap_recovery_points': '8',
                                  'Enable_backup_copy': 'ON',
                                  'sla_hours': '11',
                                  'sla_minutes': '22'}

        self._database_options = {'sla_hours': '11',
                                  'sla_minutes': '22'}
        self._media_agent = None
        self.__rpo = RPO(self.__admin_console)
        self._selective = None
        self._regions = None
        self._modify_retention = False
        self._specify_date = False
        self._service_commcells = None
        if self.commcell:
            self.file_server_helper = FileServersMain(
                self.__admin_console, self.commcell)
            self._sdk_plan_helper = PlansHelper(commcell_obj=self.commcell)
        self.__fs = file_servers.FileServers(self.__admin_console)
        self.__rdropdown = RDropDown(self.__admin_console)
        self.__rpanel_info = RPanelInfo(self.__admin_console)
        self.__vm_group = vm_groups.VMGroups(self.__admin_console)

    @property
    def plan_name(self):
        """ Get plan name"""
        return self._plan_name

    @plan_name.setter
    def plan_name(self, value):
        """ Set plan name"""
        self._plan_name = value

    @property
    def sec_copy_name(self):
        """" Get secondary copy name"""
        return self._sec_copy_name

    @sec_copy_name.setter
    def sec_copy_name(self, value):
        """ Set secondary copy name"""
        self._sec_copy_name = value

    @property
    def selective(self):
        """" Get selective value"""
        return self._selective

    @selective.setter
    def selective(self, value):
        """ Set sselective value"""
        self._selective = value

    @property
    def regions(self):
        """" Get regions value"""
        return self._regions

    @regions.setter
    def regions(self, value):
        """ Set regions value"""
        self._regions = value

    @property
    def modify_retention(self):
        """" Get modify retention value"""
        return self._modify_retention

    @modify_retention.setter
    def modify_retention(self, value):
        """ Set modify retention value"""
        self._modify_retention = value

    @property
    def specify_date(self):
        """" Get specify date value"""
        return self._specify_date

    @specify_date.setter
    def specify_date(self, value):
        """ Set specify date value"""
        self._specify_date = value

    @property
    def server_edited(self):
        """ Get server edited value """
        return self._server_edited

    @server_edited.setter
    def server_edited(self, value):
        """ Set server edited value """
        self._server_edited = value

    @property
    def laptop_edited(self):
        """ Get laptop edited value """
        return self._laptop_edited

    @laptop_edited.setter
    def laptop_edited(self, value):
        """ Set lapotp edited value """
        self._laptop_edited = value

    @property
    def derived_plan(self):
        """ Get derived  plan value """
        return self._derived_plan

    @derived_plan.setter
    def derived_plan(self, value):
        """ Set derived plan value """
        self._derived_plan = value

    @property
    def media_agent(self):
        """ Get media_agent"""
        return self._media_agent

    @media_agent.setter
    def media_agent(self, value):
        """ Set media_agent"""
        self._media_agent = value

    @property
    def backup_data(self):
        """Get backup data values"""
        return self._backup_data

    @backup_data.setter
    def backup_data(self, value):
        """Set backup data values"""
        self._backup_data = value

    @property
    def allow_override(self):
        """Get allow override values"""
        return self._allow_override

    @allow_override.setter
    def allow_override(self, value):
        """Set allow override values"""
        self._allow_override = value

    @property
    def system_state(self):
        """Get system_state value"""
        return self._system_state

    @system_state.setter
    def system_state(self, value):
        """Set system_state value"""
        self._system_state = value

    @property
    def full_backup(self):
        """Get full_backup value"""
        return self._full_backup

    @full_backup.setter
    def full_backup(self, value):
        """Set full_backup value"""
        self._full_backup = value

    @property
    def vss(self):
        """Get vss value"""
        return self._vss

    @vss.setter
    def vss(self, value):
        """Set vss value"""
        self._vss = value

    @property
    def allowed_features(self):
        """Get allowed_features value"""
        return self._allowed_features

    @allowed_features.setter
    def allowed_features(self, value):
        """Set allowed_features value"""
        self._allowed_features = value

    @property
    def archiving_rules(self):
        """Get archiving_rules value"""
        return self._archiving_rules

    @archiving_rules.setter
    def archiving_rules(self, value):
        """Set archiving_rules value"""
        self._archiving_rules = value

    @property
    def file_system_quota(self):
        """Get file_system_quota value"""
        return self._file_system_quota

    @file_system_quota.setter
    def file_system_quota(self, value):
        """Set file_system_quota value"""
        self._file_system_quota = value

    @property
    def storage(self):
        """Get primary and secondary storage attributes"""
        return self._storage

    @storage.setter
    def storage(self, value):
        """Set primary and secondary storage attributes"""
        self._storage = value

    @property
    def throttle_send(self):
        """Get throttle_send value"""
        return self._throttle_send

    @throttle_send.setter
    def throttle_send(self, value):
        """Set throttle_send value"""
        self._throttle_send = value

    @property
    def throttle_receive(self):
        """Get throttle_receive value"""
        return self._throttle_receive

    @throttle_receive.setter
    def throttle_receive(self, value):
        """Set throttle_receive value"""
        self._throttle_receive = value

    @property
    def alerts(self):
        """Get alerts values"""
        return self._alerts

    @alerts.setter
    def alerts(self, value):
        """Set alerts values"""
        self._alerts = value

    @property
    def backup_day(self):
        """Get backup_day values"""
        return self._backup_day

    @backup_day.setter
    def backup_day(self, value):
        """Set backup_day values"""
        self._backup_day = value

    @property
    def backup_duration(self):
        """Get backup_duration values"""
        return self._backup_duration

    @backup_duration.setter
    def backup_duration(self, value):
        """Set backup_duration values"""
        self._backup_duration = value

    @property
    def snap_recovery_points(self):
        """Get snap_recovery_points value"""
        return self._snap_recovery_points

    @snap_recovery_points.setter
    def snap_recovery_points(self, value):
        """Set snap_recovery_points value"""
        self._snap_recovery_points = value

    @property
    def rpo_hours(self):
        """Get rpo_hours value"""
        return self._rpo_hours

    @rpo_hours.setter
    def rpo_hours(self, value):
        """Set rpo_hours value"""
        self._rpo_hours = value

    @property
    def edit_plan_dict(self):
        """Get edit_plan_dict value"""
        return self._edit_plan_dict

    @edit_plan_dict.setter
    def edit_plan_dict(self, value):
        """Set edit_plan_dict value"""
        self._edit_plan_dict = value

    @property
    def edit_server_plan_dict(self):
        """Get edit_plan_dict value"""
        return self._edit_server_plan_dict

    @edit_server_plan_dict.setter
    def edit_server_plan_dict(self, value):
        """Set edit_plan_dict value"""
        self._edit_server_plan_dict = value

    @property
    def user_usergroup_association(self):
        """Get user_usergroup_association values"""
        return self._user_usergroup_association

    @user_usergroup_association.setter
    def user_usergroup_association(self, value):
        """Set user_usergroup_association values"""
        self._user_usergroup_association = value

    @property
    def user_usergroup_de_association(self):
        """Get user_usergroup_de_association values"""
        return self._user_usergroup_de_association

    @user_usergroup_de_association.setter
    def user_usergroup_de_association(self, value):
        """Set user_usergroup_de_association values"""
        self._user_usergroup_de_association = value

    @property
    def retention(self):
        """Get retention values"""
        return self._retention

    @retention.setter
    def retention(self, value):
        """Set retention values"""
        self._retention = value

    @property
    def snapshot_options(self):
        """Get snapshot_options values"""
        return self._snapshot_options

    @snapshot_options.setter
    def snapshot_options(self, value):
        """Set snapshot_options values"""
        self._snapshot_options = value

    @property
    def database_options(self):
        """Get database_options values"""
        return self._database_options

    @database_options.setter
    def database_options(self, value):
        """Set database_options values"""
        self._database_options = value

    def list_plans(self, plan_type='All', company_name='All'):
        """Lists all the plans
            Args:
                plan_type       (str) - To filter/ fetch plans of a particular type
                company_name    (str) - To filter/ fetch plans of a particular company
        """
        self.log.info('Listing plans of type [%s] associated to company [%s]' % (plan_type, company_name))
        self.__navigator.navigate_to_plan()
        return self.__plans.list_plans(plan_type, company_name)

    def add_plan(self):
        """calls create plan functions from Plans file based on input
            and generates plans in Admin Console"""

        self.__navigator.navigate_to_plan()
        for key, value in self.plan_name.items():
            if key == "server_plan":
                if value != None:
                    self.__plans.create_server_plan(
                        value,
                        self.storage,
                        self.rpo_hours,
                        self.allow_override,
                        self.backup_day,
                        self.backup_duration,
                        self.backup_data,
                        self.snapshot_options,
                        self.database_options,
                        sec_copy_name=self._sec_copy_name,
                        selective=self._selective,
                        regions=self._regions,
                        modify_ret=self._modify_retention,
                        specify_date=self._specify_date,
                        service_commcells=self._service_commcells
                    )
                    time.sleep(3)
                    self.__navigator.navigate_to_plan()
            elif key == "laptop_plan":
                if value != None:
                    self.__plans.create_laptop_plan(
                        value,
                        self.allowed_features,
                        self.media_agent,
                        self.archiving_rules,
                        self.backup_data,
                        self.file_system_quota,
                        self.storage,
                        self.rpo_hours,
                        self.retention,
                        self.throttle_send,
                        self.throttle_receive,
                        self.alerts
                    )
                    time.sleep(3)
                    self.__navigator.navigate_to_plan()

    def validate_plans(self):
        """validates the designated plan in admin console plans page"""

        self.validate_plan_details()
        for key, value in self.plan_name.items():
            if key == "laptop_plan":
                self.__navigator.navigate_to_server_groups()
                self.__table.search_for(value + " clients")
                if self.__admin_console.check_if_entity_exists("link", "{0} clients".format(value)):
                    self.log.info("Server group created for plan named {0} is "
                                  "validated successfully.".format(value))
                self.__navigator.navigate_to_plan()
                break

    def delete_plan__attempt_deletion(self, plan_name, dual_auth_enabled=True):
        """ Attempt plan deletion and check for dual authorization message

            Args:
                plan_name           (str)   --  Plan name
                dual_auth_enabled   (bool)  --  If need to check for dual authorization message
        """
        self.__navigator.navigate_to_plan()
        try:
            self.log.info(f"Attempting delete for plan {plan_name}")
            self.__plans.delete_plan(plan_name)
            self.log.info(f"Plan {plan_name} deleted successfully!")
            if dual_auth_enabled:
                self.log.error(f"Deleted plan {plan_name} without dual authorization!")
                raise Exception(f"Deleted plan {plan_name} without dual authorization!")
        except Exception as exp:
            if dual_auth_enabled:
                err_msg = ("An email has been sent to the administrator to authorize the delete plan request. The plan "
                           "will be automatically deleted once the request is accepted.")
                if err_msg in str(exp):
                    self.log.info("Captured dual authorization message.")
                else:
                    raise Exception(f"Plan {plan_name} deletion failed with error {str(exp)}") from exp
            else:
                raise Exception(f"Plan {plan_name} deletion failed with error {str(exp)}") from exp

    def delete_plan__approve_deletion(self,
                                      plan_name,
                                      automation_username,
                                      reuse_admin_console=None,
                                      admin_username=None,
                                      admin_password=None,
                                      deny=False):
        """ Perform approval action for dual authorization

            Args:
                plan_name           (str)   --  Plan name
                automation_username (str)   --  login name of user who requested plan deletion
                reuse_admin_console (AdminConsole) -- Reuse AdminConsole for user who will approve plan deletion
                admin_username      (str)   --  login name of user who will approve plan deletion
                admin_password      (str)   --  credential of user who will approve plan deletion
                deny                (bool)  --  Used for negative case testing
        """
        browser = None
        admin_console = None
        try:
            if reuse_admin_console is None:
                browser = BrowserFactory().create_browser_object()
                browser.open()
                if self.commcell is None:
                    admin_console = AdminConsole(browser, self.__admin_console.machine_name)
                else:
                    admin_console = AdminConsole(browser, self.commcell.webconsole_hostname)
                self.log.info(f"Login using admin id: {admin_username}")
                admin_console.login(admin_username, admin_password)
            else:
                admin_console = reuse_admin_console

            forms = Forms(admin_console)
            actions = Actions(admin_console)
            actions.goto_Actions()
            actions.goto_Open_Actions()

            # Force data reload
            table_title = self.__props.get('Approvals_Title', 'Approvals')
            open_actions_table = Rtable(admin_console, title=table_title)
            open_actions_table.reload_data()

            approval_title = f"Delete plan [ {plan_name} ] requested by [ {automation_username} ]"
            self.log.info(f"Approval title [{approval_title}]")

            try:
                actions.open_Action(approval_title)
                self.__admin_console.wait_for_completion()
            except Exception as exp:
                if "no such element" in str(exp):
                    self.log.error(f"Dual authorization approval not visible to current user")
                raise exp

            if deny:
                action = self.__admin_console.props.get('label.configuration.deny', 'Deny')
            else:
                action = self.__admin_console.props.get('label.configuration.accept', 'Accept')
            self.log.info(f"Performing action {action}")
            forms.click_action_button(action)
            self.__admin_console.wait_for_completion()
            time.sleep(60)  # Delay to let the workflow complete request processing
        except Exception as exp:
            self.log.error(f'Failed to accept delete plan authorization with error: {str(exp)}')
            raise Exception(f'Failed to accept delete plan authorization with error: {str(exp)}') from exp
        finally:
            if reuse_admin_console is None:
                AdminConsole.logout_silently(admin_console)
                browser.close()

    def delete_plans(self,
                     dual_auth_enabled=False,
                     automation_username=None,
                     reuse_admin_console=None,
                     admin_username=None,
                     admin_password=None):
        """deletes the designated plan

            Args:
                dual_auth_enabled   (bool)  --  If need to check for dual authorization message
                automation_username (str)   --  login name of user who requested plan deletion
                reuse_admin_console (AdminConsole) -- Reuse AdminConsole for user who will approve plan deletion
                admin_username      (str)   --  login name of user who will approve plan deletion
                admin_password      (str)   --  credential of user who will approve plan deletion
        """
        for plan_name in self.plan_name.values():
            self.delete_plan__attempt_deletion(plan_name, dual_auth_enabled=dual_auth_enabled)
            if dual_auth_enabled:
                if (
                        (reuse_admin_console is None or automation_username is None) and
                        (admin_username is None or admin_password is None or automation_username is None)
                ):
                    self.log.error("Please provided admin credentials for dual authorization approval")
                    raise Exception("Please provided admin credentials for dual authorization approval")
                self.delete_plan__approve_deletion(plan_name, automation_username,
                                                   reuse_admin_console,
                                                   admin_username, admin_password,
                                                   deny=False)

    def validate_plan_details(self, validation_dict=None):
        """validates if the plan details are displayed correctly"""

        for key, value in self.plan_name.items():
            self.__navigator.navigate_to_plan()
            self.__plans.select_plan(value)
            displayed_val = self.__plan_details.plan_info(key)
            if validation_dict is None:
                validation_dict = self.__set_default_values_if_none(key, value)
            self.log.info("Displayed values: ", displayed_val)
            self.log.info("Validation values: ", validation_dict)

            for key_dict, val_dict in validation_dict.items():
                if isinstance(val_dict, list):
                    self.log.info('Entity given_val "{0}"'.format(val_dict))
                    if set(displayed_val[key_dict]) == set(validation_dict[key_dict]):
                        self.log.info(
                            "{0} displayed for {1} matches with {2} given".format(
                                displayed_val[key_dict], key, validation_dict[key_dict]))
                    else:
                        exp = "{0} displayed for {1} does not match with {2} given ".format(
                            displayed_val[key_dict], key, validation_dict[key_dict])
                        raise Exception(exp)
                elif isinstance(val_dict, str):
                    self.log.info('Entity given_val "{0}"'.format(val_dict))
                    if displayed_val[key_dict] == validation_dict[key_dict]:
                        self.log.info(
                            "{0} displayed for {1} matches with {2} given".format(
                                displayed_val[key_dict], key_dict, validation_dict[key_dict]))
                    else:
                        exp = "{0} displayed for {1} does not match with {2} given " \
                            .format(displayed_val[key_dict], key_dict, validation_dict[key_dict])
                        raise Exception(exp)
                else:
                    self.log.info('Entity given_val :{0}'.format(val_dict))
                    for item, value_dict in val_dict.items():
                        d_val = displayed_val[key_dict][item]
                        key_val = validation_dict[key_dict][item]
                        if d_val == key_val:
                            self.log.info("{0} values match".format(item))
                        else:
                            exp = "{0} displayed for {1} does not match with {2} given " \
                                .format(d_val, item, key_val)
                            raise Exception(exp)

    def get_val_dict(self, plan_type, plan_name):
        """ gets val dict """
        return self.__set_default_values_if_none(plan_type, plan_name)

    def __set_default_values_if_none(self, plan_type, plan_name):
        """ this function sets default values to the parameters provided for plan creation """

        default_comp_values = {
            "No. of users": "0",
            'User/Group': "Role",
            "master": "Plan Creator Role",
            "No. of devices": "0",
            "secondary_schedule": plan_name + " aux copy",
            "associated_entities": []}

        self._content_selected = self.__get_selected_backup_content()

        override = {}
        if not self.server_edited:
            if self.allow_override['Storage_pool']:
                override.update(
                    {'Storage pool': self.allow_override['Storage_pool']})
            if self.allow_override['RPO']:
                override.update({'RPO': self.allow_override['RPO']})
            if self.allow_override['Folders_to_backup']:
                override.update(
                    {'Folders to backup': self.allow_override['Folders_to_backup']})
            if self.allow_override['Retention']:
                override.update(
                    {'Retention': self.allow_override['Retention']})
        else:
            override.update(
                {'Storage pool': self.edit_server_plan_dict['override_restrictions']['Storage_pool']})
            override.update(
                {'RPO': self.edit_server_plan_dict['override_restrictions']['RPO']})
            override.update({'Folders to backup':
                                 self.edit_server_plan_dict['override_restrictions']['Folders_to_backup']})

        retention_tile = {}

        if self.retention['deleted_item_retention']['value'] == 'Indefinitely':
            retention_tile.update(
                {'Deleted item retention': self.retention['deleted_item_retention']['value']})
        else:
            retention_tile.update({'Deleted item retention': self.retention['deleted_item_retention']['value']
                                                             + " " + self.retention['deleted_item_retention']['unit']})

        if self.retention['file_version_retention']['versions']:
            retention_tile.update(
                {'File versions': self.retention['file_version_retention']['versions']})
        elif self.retention['file_version_retention']['duration']:
            retention_tile.update({'File versions': self.retention['file_version_retention']['duration']['value'] + " "
                                                    + self.retention['file_version_retention']['duration']['unit']})
        else:
            if self.retention['file_version_retention']['rules']['days'] and \
                    not self.retention['file_version_retention']['rules']['weeks'] and \
                    not self.retention['file_version_retention']['rules']['months']:
                retention_tile.update({'File versions': 'Daily versions for ' +
                                                        self.retention['file_version_retention']['rules'][
                                                            'days'] + ' day(s)'})
            elif self.retention['file_version_retention']['rules']['weeks'] and \
                    not self.retention['file_version_retention']['rules']['days'] and \
                    not self.retention['file_version_retention']['rules']['months']:
                retention_tile.update({'File versions': 'Weekly versions for ' +
                                                        self.retention['file_version_retention']['rules'][
                                                            'weeks'] + ' week(s)'})
            elif self.retention['file_version_retention']['rules']['months'] and \
                    not self.retention['file_version_retention']['rules']['days'] and \
                    not self.retention['file_version_retention']['rules']['weeks']:
                retention_tile.update({'File versions': 'Weekly versions for ' +
                                                        self.retention['file_version_retention']['rules'][
                                                            'weeks'] + ' month(s)'})
            elif self.retention['file_version_retention']['rules']['days'] and \
                    self.retention['file_version_retention']['rules']['weeks'] and \
                    not self.retention['file_version_retention']['rules']['months']:
                retention_tile.update({'File versions': 'Daily versions for ' +
                                                        self.retention['file_version_retention']['rules'][
                                                            'days'] + ' day(s)\nWeekly versions for ' +
                                                        self.retention['file_version_retention']['rules']['weeks'] +
                                                        ' week(s)'})
            elif self.retention['file_version_retention']['rules']['days'] and \
                    not self.retention['file_version_retention']['rules']['weeks'] and \
                    self.retention['file_version_retention']['rules']['months']:
                retention_tile.update({'File versions': 'Weekly versions for ' +
                                                        self.retention['file_version_retention']['rules'][
                                                            'days'] + ' day(s)\nMonthly versions for ' +
                                                        self.retention['file_version_retention']['rules']['months'] +
                                                        ' month(s)'})
            elif not self.retention['file_version_retention']['rules']['days'] and \
                    self.retention['file_version_retention']['rules']['weeks'] and \
                    self.retention['file_version_retention']['rules']['months']:
                retention_tile.update({'File versions': 'Weekly versions for ' +
                                                        self.retention['file_version_retention']['rules'][
                                                            'weeks'] + ' week(s)\nMonthly versions for ' +
                                                        self.retention['file_version_retention']['rules'][
                                                            'months'] + ' month(s)'})
            elif self.retention['file_version_retention']['rules']['days'] and \
                    self.retention['file_version_retention']['rules']['weeks'] and \
                    self.retention['file_version_retention']['rules']['months']:
                retention_tile.update({'File versions': 'Daily versions for ' +
                                                        self.retention['file_version_retention']['rules'][
                                                            'days'] + ' day(s)\nWeekly versions for ' +
                                                        self.retention['file_version_retention']['rules'][
                                                            'weeks'] + ' week(s)\nMonthly versions for ' +
                                                        self.retention['file_version_retention']['rules'][
                                                            'months'] + ' month(s)'})

        def ret_value(ret_period):
            if int(ret_period) % 30 == 0:
                if int(ret_period) // 30 == 1:
                    retention_val = str(int(ret_period) // 30) + ' Month'
                else:
                    retention_val = str(int(ret_period) // 30) + ' Months'
            elif int(ret_period) % 7 == 0:
                if int(ret_period) // 7 == 1:
                    retention_val = str(int(ret_period) // 7) + ' Week'
                else:
                    retention_val = str(int(ret_period) // 7) + ' Weeks'
            else:
                retention_val = ret_period + ' Days'
            return retention_val

        pri_ret_val = ret_value(self.storage['pri_ret_period'])
        if self.storage['sec_ret_period']:
            sec_ret_val = ret_value(self.storage['sec_ret_period'])

        if self.edit_plan_dict['edit_storage'] or self.edit_server_plan_dict['edit_storage']:
            if self.storage.get('sec_storage'):
                storage_text = {self.edit_server_plan_dict['edit_storage']['new_storage_name']:
                                    [self.storage['pri_storage'], pri_ret_val],
                                'Secondary': [self.storage['sec_storage'], sec_ret_val]}
            else:
                storage_text = {self.edit_server_plan_dict['edit_storage']['new_storage_name']:
                                    [self.storage['pri_storage'], pri_ret_val],
                                f"{plan_name} snap copy": [self.storage['pri_storage'], '10 Recovery points']
                                }
        else:
            if self.storage.get('sec_storage'):
                storage_text = {'Primary': [self.storage['pri_storage'], pri_ret_val],
                                'Secondary': [self.storage['sec_storage'], sec_ret_val]}
            else:
                storage_text = {'Primary': [self.storage['pri_storage'], pri_ret_val],
                                f"{plan_name} snap copy": [self.storage['pri_storage'], '1 Month']}

        backup_copy_rpo = self.snapshot_options['sla_hours'] + " hour(s) and " + \
                          self.snapshot_options['sla_minutes'] + " minute(s)"

        log_backup_rpo = self.database_options['sla_hours'] + " hour(s) and " + \
                         self.database_options['sla_minutes'] + " minute(s)"

        alert_list = []
        if self.alerts['Backup']:
            alert_list.append(self.alerts['Backup'])
        if self.alerts['Jobfail']:
            alert_list.append(self.alerts['Jobfail'])
        if self.alerts['edge_drive_quota']:
            alert_list.append(self.alerts['edge_drive_quota'])
        if self.alerts['file_system_quota']:
            alert_list.append(self.alerts['file_system_quota'])

        if plan_type == "server_plan":

            validation_dict = {'PlanName': plan_name,
                               'Security': {'master': [[default_comp_values['master']]]},
                               'RPO': {'Backup frequency': "Runs every 5 Day(s) at 9:00 PM",
                                       'Add full backup': 'OFF',
                                       'Backup window': self._backup_window,
                                       'Full backup window': self._backup_window},
                               'Override restrictions': override,
                               'Backup destinations': storage_text,
                               'Snapshot options': {'Backup Copy': self.snapshot_options['Enable_backup_copy'],
                                                    'Backup copy frequency (in HH:MM)': backup_copy_rpo},
                               'Database options': {'Log backup RPO': log_backup_rpo},
                               'Backup content': self._content_selected}

            return validation_dict

        elif plan_type == "laptop_plan":

            if not self.laptop_edited:
                allowed_features = self.allowed_features
                allowed_features.pop("audit_drive_operations")
                allowed_features.pop("notification_for_shares")
                allowed_features.pop("edge_drive_quota")

                validation_dict = {
                    'PlanName': plan_name,
                    'General': {'No. of users': default_comp_values['No. of users'],
                                'No. of laptops': default_comp_values['No. of devices']},
                    'Allowed features': allowed_features,
                    'Security': {'master': [[default_comp_values["master"]]]},
                    'RPO': {'Backup frequency': 'Runs every ' + self.rpo_hours + ' Hour(s)'},
                    'Override restrictions': override,
                    'Backup destinations': [self.storage['pri_storage'], self.storage['sec_storage']],
                    'Retention': retention_tile,
                    'Alerts': alert_list,
                    'Associated users and user groups': [],
                    'Options': {'File system quota': self.file_system_quota + ' GB'},
                    'Backup content': self._content_selected}

                return validation_dict

            else:
                no_of_users = self.__get_no_of_users()
                allowed_features = dict(
                    self.edit_plan_dict['allowed_features'])
                allowed_features.pop("audit_drive_operations")
                allowed_features.pop("notification_for_shares")
                allowed_features.pop("edge_drive_quota")

                backup_dest = [self.storage['pri_storage']]
                if self.storage['sec_storage']:
                    backup_dest.append(self.storage['sec_storage'])
                if not self.edit_plan_dict['region']:
                    if self.edit_plan_dict['edit_storage']:
                        if self.edit_plan_dict['edit_storage']['pri_storage']:
                            backup_dest[0] = self.edit_plan_dict['edit_storage']['pri_storage']
                        if self.edit_plan_dict['edit_storage']['sec_storage']:
                            backup_dest[1] = self.edit_plan_dict['edit_storage']['sec_storage']
                    if self.edit_plan_dict['additional_storage']:
                        backup_dest.append(
                            self.edit_plan_dict['additional_storage']['storage_pool'])
                else:
                    storage_list = backup_dest
                    if self.edit_plan_dict['edit_storage']:
                        if self.edit_plan_dict['edit_storage']['pri_storage']:
                            storage_list[0] = self.edit_plan_dict['edit_storage']['pri_storage']
                        if self.edit_plan_dict['edit_storage']['sec_storage']:
                            storage_list[1] = self.edit_plan_dict['edit_storage']['sec_storage']
                    if self.edit_plan_dict['additional_storage']:
                        storage_list.append(
                            self.edit_plan_dict['additional_storage']['storage_pool'])
                    backup_dest = {self.edit_plan_dict['region']: storage_list}

                validation_dict = {
                    'PlanName': plan_name,
                    'General': {'No. of users': str(no_of_users),
                                'No. of laptops': default_comp_values['No. of devices']},
                    'Allowed features': allowed_features,
                    'Network resources': {'Throttle send': self.edit_plan_dict['throttle_send'] + ' Kbps',
                                          'Throttle receive': self.edit_plan_dict['throttle_receive'] + ' Kbps'},
                    'Security': {'master': [[default_comp_values["master"]]]},
                    'RPO': {'Backup frequency': 'Runs every ' + self.edit_plan_dict['rpo_hours'] + ' Hour(s)'},
                    'Override restrictions':
                        {'Storage pool': self.edit_plan_dict['override_restrictions']['Storage_pool'],
                         'RPO': self.edit_plan_dict['override_restrictions']['RPO'],
                         'Folders to backup': self.edit_plan_dict['override_restrictions']['Folders_to_backup'],
                         'Retention': self.edit_plan_dict['override_restrictions']['Retention']},
                    'Backup destinations': backup_dest,
                    'Retention': retention_tile,
                    'Alerts': alert_list,
                    'Associated users and user groups': self.user_usergroup_association,
                    'Options': {'File system quota': self.edit_plan_dict['file_system_quota'] + ' GB'},
                    'Backup content': self._content_selected}
                return validation_dict

    def edit_laptop_plan(self):
        """ This function gives call to functions for editing plan tiles """

        for value in self.plan_name.values():
            self.__navigator.navigate_to_plan()
            self.__plans.select_plan(value)
            if self.__plan_details.is_advance_view_toggle_visible():
                self.__plan_details.enable_advanced_view()
            if self.edit_plan_dict['additional_storage']:
                self.__plan_details.edit_plan_storage_pool(self.edit_plan_dict['additional_storage'],
                                                           self.edit_plan_dict['edit_storage'],
                                                           self.edit_plan_dict['region'])
            if self.edit_plan_dict['alerts']:
                self.__plan_details.edit_plan_alerts(self.edit_plan_dict['alerts'])

            if self.edit_plan_dict['throttle_send'] or self.edit_plan_dict['throttle_receive']:
                self.__plan_details.edit_plan_network_resources(self.edit_plan_dict['throttle_send'],
                                                                self.edit_plan_dict['throttle_receive'])
            if self.edit_plan_dict['rpo_hours']:
                self.__plan_details.edit_plan_rpo_hours(
                    self.edit_plan_dict['rpo_hours'])
            if self.edit_plan_dict['file_system_quota']:
                self.__plan_details.edit_plan_options(
                    self.edit_plan_dict['file_system_quota'])
            if self.edit_plan_dict['backup_data']:
                new_data = self.edit_plan_dict['backup_data']
                self.__plan_details.edit_plan_backup_content(new_data['file_system'],
                                                             new_data['content_backup'],
                                                             new_data['content_library'],
                                                             str(new_data['custom_content']),
                                                             new_data['exclude_folder'],
                                                             new_data['exclude_folder_library'],
                                                             str(new_data['exclude_folder_custom_content']))
            if self.user_usergroup_association:
                self.__plan_details.edit_plan_associate_users_and_groups(
                    self.user_usergroup_association)
            if self.edit_plan_dict['allowed_features']:
                self.__plan_details.edit_plan_features(self.edit_plan_dict['allowed_features'],
                                                       self.archiving_rules)
            if self.retention:
                self.__plan_details.edit_plan_retention(self.retention)
            if self.edit_plan_dict['override_restrictions']:
                self.__plan_details.edit_plan_override_restrictions(self.edit_plan_dict['override_restrictions'],
                                                                    override_laptop_plan=True)
        self._laptop_edited = True

    def edit_server_plan(self):
        """ This function gives call to functions for editing plan tiles """

        for key, value in self.plan_name.items():
            self.__navigator.navigate_to_plan()
            self.__plans.select_plan(value)
            self.__plan_details.edit_plan_rpo_hours(
                self.edit_server_plan_dict['rpo_hours'])
            self.__plan_details.edit_server_plan_storage_pool(additional_storage={},
                                                              edit_storage=self.edit_server_plan_dict['edit_storage'])
            self.__plan_details.edit_plan_override_restrictions(
                self.edit_server_plan_dict['override_restrictions'])
            self.__plan_details.edit_snapshot_options(
                {'hours': '11', 'minutes': '22'}, '10')
            self.__plan_details.edit_database_options(
                {'hours': '11', 'minutes': '22'})
            self.__plan_details.edit_plan_backup_content(self.backup_data['file_system'],
                                                         self.backup_data['content_backup'],
                                                         self.backup_data['content_library'],
                                                         str(
                                                             self.backup_data['custom_content']),
                                                         self.backup_data['exclude_folder'],
                                                         self.backup_data['exclude_folder_library'],
                                                         str(self.backup_data['exclude_folder_custom_content']))
        self._server_edited = True

    def remove_associations(self):
        """ This function gives call to another function for removing Users/UserGroups associated to a plan """
        for key, value in self.plan_name.items():
            self.__navigator.navigate_to_plan()
            self.__plans.select_plan(value)
            self.__plan_details.remove_associated_users_and_groups(
                self.user_usergroup_de_association)

    def __get_selected_backup_content(self):
        """ This function gives value of backup content selected for laptop and filesystem plan
        based on user input from test case """
        # divyanshu
        if not self.backup_data:
            self._content_selected = {
                'Windows': 'Desktop, Documents, Office, Pictures, Image, MigrationAssistant',
                'Mac': 'Desktop, Documents, Office, Pictures, Image, MigrationAssistant',
                'Unix': 'Desktop, Documents, Office, Pictures, Image'
            }
            return self._content_selected
        if 'Library' in self.backup_data['content_backup']:
            if self.backup_data['custom_content']:
                self._content_selected = {'Windows': 'Archives, Audio, Disk images, Email files, Executable, Image, '
                                                     'Office, Scripts, System, Temporary files (linux), '
                                                     'Temporary files (mac), Temporary files (windows), Text, '
                                                     'Thumbnail supported, Video, Virtual machine, Desktop,'
                                                     'Documents, Music, Pictures, Videos, ' +
                                                     str(
                                                         self.backup_data['custom_content']) + '',
                                          'Mac': 'Archives, Audio, Disk images, Email files, Executable, Image, '
                                                 'Office, Scripts, System, Temporary files (linux), '
                                                 'Temporary files (mac), Temporary files (windows), Text, '
                                                 'Thumbnail supported, Video, Virtual machine, Desktop, '
                                                 'Documents, Music, Pictures, Videos, ' +
                                                 str(
                                                     self.backup_data['custom_content']) + '',
                                          'Unix': 'Archives, Audio, Disk images, Email files, Executable, Image, '
                                                  'Office, Scripts, System, Temporary files (linux), '
                                                  'Temporary files (mac), Temporary files (windows), Text, '
                                                  'Thumbnail supported, Video, Virtual machine, ' +
                                                  str(self.backup_data['custom_content'])}
            else:
                self._content_selected = {
                    'Windows': 'Archives, Audio, Disk images, Email files, Executable, Image,'
                               'Office, Scripts, System, Temporary files (linux), '
                               'Temporary files (mac), Temporary files (windows), Text, '
                               'Thumbnail supported, Video, Virtual machine, Desktop, '
                               'Documents, Music, Pictures, Videos',
                    'Mac': 'Archives, Audio, Disk images, Email files, Executable, Image, Office,'
                           ' Scripts, System, Temporary files (linux), Temporary files (mac), '
                           'Temporary files (windows), Text, Thumbnail supported, Video, '
                           'Virtual machine, Desktop,Documents, Music, Pictures, Videos',
                    'Unix': 'Archives, Audio, Disk images, Email files, Executable, Image, '
                            'Office, Scripts, System, Temporary files (linux), '
                            'Temporary files (mac), Temporary files (windows), Text, '
                            'Thumbnail supported, Video, Virtual machine, Desktop, '
                            'Documents, Music, Pictures, Videos'}

        elif 'Content Library' in self.backup_data['content_backup']:
            if 'Content Library' in self.backup_data['content_library']:
                self.backup_data['content_backup'] = sorted(
                    self.backup_data['content_backup'])
                if self.backup_data['custom_content']:
                    content = ['Archives', 'Audio', 'Disk images', 'Email files', 'Executable',
                               'Image', 'Office', 'Scripts', 'System', 'Temporary files (linux)',
                               'Temporary files (mac)', 'Temporary files (windows)',
                               'Text', 'Thumbnail supported', 'Video', 'Virtual machine'] \
                              + self.backup_data['content_backup']
                    content.append(self.backup_data['custom_content'])
                else:
                    content = ['Archives', 'Audio', 'Disk images', 'Email files', 'Executable',
                               'Image', 'Office', 'Scripts', 'System', 'Temporary files (linux)',
                               'Temporary files (mac)', 'Temporary files (windows)',
                               'Text', 'Thumbnail supported', 'Video', 'Virtual machine'] + \
                              self.backup_data['content_backup']
                content.remove('Content Library')
                content = list(OrderedDict.fromkeys(content))
                final_content = ', '.join(content)
                self._content_selected = {
                    'Windows': final_content, 'Mac': final_content, 'Unix': final_content}
            else:
                self.backup_data['content_backup'] = sorted(
                    self.backup_data['content_backup'])
                self.backup_data['content_library'] = sorted(
                    self.backup_data['content_library'])
                if self.backup_data['custom_content']:
                    content = self.backup_data['content_library'] + \
                              self.backup_data['content_backup']
                    content.append(str(self.backup_data['custom_content']))
                else:
                    content = self.backup_data['content_library'] + \
                              self.backup_data['content_backup']
                content.remove('Content Library')
                content = list(OrderedDict.fromkeys(content))
                final_content = ', '.join(content)
                self._content_selected = {
                    'Windows': final_content, 'Mac': final_content, 'Unix': final_content}
        else:
            self.backup_data['content_backup'] = sorted(
                self.backup_data['content_backup'])
            if self.backup_data['custom_content']:
                content = self.backup_data['content_backup']
                content.append(str(self.backup_data['custom_content']))
            else:
                content = self.backup_data['content_backup']
            content = list(OrderedDict.fromkeys(content))
            final_content = ', '.join(content)
            self._content_selected = {
                'Windows': final_content, 'Mac': final_content, 'Unix': final_content}
        return self._content_selected

    def __get_no_of_users(self):

        list_user_groups = []
        no_of_users = 0

        self.__navigator.navigate_to_users()
        for value in self.user_usergroup_association:
            self.__table.search_for(value)
            if not self.__admin_console.check_if_entity_exists("link", value):
                list_user_groups.append(value)
            elif self.__admin_console.check_if_entity_exists("link", value):
                no_of_users += 1

        if not list_user_groups:
            for value in list_user_groups:
                self.__navigator.navigate_to_user_groups()
                self.__table.access_link(value)
                user_grid = self.__driver.find_element(By.XPATH,
                                                       "//div[@class='ui-grid-canvas']")
                users_user_group = user_grid.find_elements(By.XPATH,
                                                           ".//div[@class='ui-grid-row ng-scope']")
                no_of_users += len(users_user_group)
        return no_of_users

    def add_laptop_derivedplan(self):
        """method to create laptop derived plan """

        self.__navigator.navigate_to_plan()
        self.__admin_console.wait_for_completion()
        self.__plans.select_plan(self.plan_name['laptop_plan'])
        self.__plans.click_create_derived_plan_button()
        self.__plans.create_laptop_derived_plan(self.derived_plan,
                                                self.allow_override,
                                                self.backup_data,
                                                self.storage,
                                                self.rpo_hours,
                                                self.retention)
        time.sleep(3)
        self.__navigator.navigate_to_plan()

    def validate_derivedplan_overriding(self, validation_dict):
        """
        Method to validate derive plan

        Args:
            validation_dict (str): Name of the plan to be validated

        Raises:
            Exception:
                -- if fails to validate the plan
        """

        self.log.info(
            "validation of derived plan overriding started{0}".format(self._derived_plan))
        self.__navigator.navigate_to_plan()
        self.__admin_console.wait_for_completion()
        self.__plans.select_plan(self._derived_plan)
        displayed_val = self.__plan_details.plan_info('laptop_plan')
        for key_dict, val_dict in validation_dict.items():
            if isinstance(val_dict, list):
                self.log.info('Entity given_val "{0}"'.format(val_dict))
                if set(displayed_val[key_dict]) == set(validation_dict[key_dict]):
                    self.log.info(
                        "Override displayed value {0} matches with {1} given".format(
                            displayed_val[key_dict], validation_dict[key_dict]))
                else:
                    exp = "Override displayed value [{0}] does not match with given value [{1}]".format(
                        displayed_val[key_dict], validation_dict[key_dict])
                    raise Exception(exp)
            elif isinstance(val_dict, str):
                self.log.info('Entity given_val "{0}"'.format(val_dict))
                if displayed_val[key_dict] == validation_dict[key_dict]:
                    self.log.info(
                        "Override displayed value {0} matches with {1} given".format(
                            displayed_val[key_dict], validation_dict[key_dict]))
                else:
                    exp = "Override displayed value [{0}] does not match with given value [{1}]" \
                        .format(displayed_val[key_dict], validation_dict[key_dict])
                    raise Exception(exp)
            else:
                self.log.info('Entity given_val :{0}'.format(val_dict))
                for item, value_dict in val_dict.items():
                    d_val = displayed_val[key_dict][item]
                    key_val = validation_dict[key_dict][item]
                    if (isinstance(d_val, list) and set(d_val) == set(key_val)) or d_val == key_val:
                        self.log.info("{0} values match".format(item))
                    else:
                        exp = "Override displayed value [{0}] does not match with given value [{1}]" \
                            .format(d_val, key_val)
                        raise Exception(exp)

    @PageService()
    def __get_data_for_validation(self, query, company_name=None, tab_name=None):
        """Method to get plan data from UI and DB for validation"""
        self.__plans.reset_filters()  # reset filters before fetching data
        ui_data = []
        for x in self.__plans.list_plans(plan_type=tab_name, company_name=company_name):
            if ' - Base plan' in x:
                ui_data.append(x[:x.index(" - Base plan")])
            else:
                ui_data.append(x)

        self.csdb.execute(query)
        ui_data = set(ui_data)
        db_data = {plans[0]
                   for plans in self.csdb.fetch_all_rows() if plans[0] != ''}
        # remove extra space from db data
        db_data = set(map(lambda x: ' '.join(x.split()), db_data))
        self.__plans.list_plans(plan_type='All', company_name='All')  # reset filter
        if db_data != ui_data:
            self.log.info(f'DB Plans : {sorted(db_data)}')
            self.log.info(f'UI Plans : {sorted(ui_data)}')
            data_missing_from_ui = db_data - ui_data
            extra_entities_on_ui = ui_data - db_data
            raise CVWebAutomationException(
                f'Mismatch found between UI and DB\nData missing from UI : {data_missing_from_ui}\
                                           Extra entities on UI : {extra_entities_on_ui}')
        self.log.info('Validation completed')

    @PageService()
    def validate_listing_simple_plan_creation(self, plan_name=None, storage_name=None):
        """Method to validate a simple plan creation"""
        if not plan_name:
            plan_name = "DEL Automated plan- " + str(randint(0, 100000))
        if not storage_name:    
            self.csdb.execute(
                f"SELECT NAME FROM ARCHGROUP WHERE id = {sample(list(self.commcell.storage_pools.all_storage_pools.values()), 1)[0]}")
            storage_name = self.csdb.fetch_all_rows()[0][0]

        self.log.info("Validating plan creation...")
        self.__navigator.navigate_to_plan()

        self.__plans.create_server_plan(plan_name=plan_name, storage={
            'pri_storage': storage_name})
        self.__admin_console.wait_for_completion()
        from time import sleep
        sleep(60)
        self.__navigator.navigate_to_plan()

        self.csdb.execute(
            f"SELECT NAME FROM APP_PLAN WHERE NAME = '{plan_name}'")
        if not [plans[0] for plans in self.csdb.fetch_all_rows() if plans[0] != '']:
            raise CVWebAutomationException('[DB] Plan not found in database')

        if not self.__plans.is_plan_exists(plan_name):
            raise CVWebAutomationException('[UI] Plan not found on UI')
        self.commcell.plans.refresh()
        self.commcell.plans.delete(plan_name)
        self.log.info('Plan creation validation completed')

    @PageService()
    def validate_listing_company_filter(self):
        """Method to validate company filter"""
        self.log.info("Validating company filter on plans listing page...")
        self.__navigator.navigate_to_plan()

        flags = (0x00004 | 0x40000000 | 0x00020)  # marked for deletion plans or hidden plans

        query_all = (
            "SELECT P.NAME "
            "FROM APP_PLAN P WITH (NOLOCK) "
            "WHERE P.SUBTYPE <> 83918853 "
            f"AND (P.FLAG & {flags}) = 0"
        )
        self.__get_data_for_validation(query_all, company_name='All')

        query_commcell = (
            "SELECT P.NAME "
            "FROM APP_PLAN P WITH (NOLOCK) "
            "LEFT JOIN APP_COMPANYENTITIES CE WITH (NOLOCK) "
            "ON P.ID = CE.ENTITYID AND CE.ENTITYTYPE = 158 "
            "WHERE P.SUBTYPE <> 83918853 "
            f"AND P.flag & {flags} = 0 "
            "AND CE.ENTITYID IS NULL;"
        )
        self.__get_data_for_validation(query_commcell, company_name='CommCell')

        self.csdb.execute(
            "SELECT ID, HOSTNAME "
            "FROM UMDSPROVIDERS WITH (NOLOCK) "
            "WHERE SERVICETYPE = 5 "
            "AND ENABLED = 1 "
            "AND FLAGS = 0"
        )
        company_details = self.csdb.fetch_all_rows()

        if len(company_details) > 5:
            company_details = sample(company_details, 5)

        for id, company_name in company_details:
            query = (
                "SELECT P.NAME "
                "FROM APP_PLAN P WITH (NOLOCK) "
                "INNER JOIN APP_COMPANYENTITIES CE WITH (NOLOCK) ON P.ID = CE.ENTITYID AND CE.ENTITYTYPE = 158 "
                "WHERE P.SUBTYPE <> 83918853 "
                f"AND (P.FLAG & {flags}) = 0 "
                f"AND CE.COMPANYID = {id}"
            )
            self.__get_data_for_validation(query, company_name=company_name)

        self.log.info('Company filter validation completed')

    @PageService()
    def validate_listing_plan_tabs_filter(self):
        """Method to validate the plan tabs filter"""
        self.log.info("Validating plan TABs filter on plans listing page...")
        self.__navigator.navigate_to_plan()

        plan_subtype = {
            "Server": "'33554437','83886085'",
            "Laptop": "'33554439'",
            "Database": "'33579013'",
            "Exchange mailbox": "'100859907', '100794372'",
            "Office 365": "'100859937'",
            "Dynamics 365": "'100794391'",
            "Data classification": "'117506053'",
            "Archive": "'150994951'"
        }
        flags = (0x00004 | 0x40000000 | 0x00020)  # marked for deletion plans or hidden plans

        for tab in self.__plans.available_plan_types():
            self.log.info(f'Validating: {tab}')
            if tab in plan_subtype:
                self.__get_data_for_validation(
                    query=f"SELECT NAME FROM APP_PLAN WITH (NOLOCK) WHERE SUBTYPE IN ({plan_subtype[tab]}) AND (FLAG & {flags}) = 0",
                    company_name='All', tab_name=tab)
        self.log.info('Plan TAB filter validation completed')

    @PageService()
    def validate_listing_plan_deletion(self, plan_name=None, storage_name=None):
        """Method to validate deletion of a plan"""
        if not plan_name:
            plan_name = "DEL Automated plan- " + str(randint(0, 100000))
            if not storage_name:
                storage_name = sample(list(self.commcell.storage_pools.all_storage_pools.keys()), 1)[0]
            self.commcell.plans.add(plan_name=plan_name, plan_sub_type='Server', storage_pool_name=storage_name)
        self.log.info("Validating plan deletion..")
        self.__navigator.navigate_to_plan()
        self.__plans.action_delete_plan(plan_name)
        self.__driver.implicitly_wait(10)

        if self.__plans.is_plan_exists(plan_name):
            raise CVWebAutomationException(
                '[UI] plan found on ui after deletion')

        self.csdb.execute(
            f"SELECT NAME FROM APP_PLAN WHERE NAME = '{plan_name}'")
        if [plans[0] for plans in self.csdb.fetch_all_rows() if plans[0] != '']:
            raise CVWebAutomationException(
                '[DB] plan found in database after deletion')

        self.__driver.implicitly_wait(0)
        self.log.info('Delete plan validation completed')

    @PageService()
    def validate_listing_edit_plan_name(self, old_name=None, new_name=None, Delete_flag=True, storage_name=None):
        """Method to validate edit plan name"""
        if not old_name:
            old_name, new_name = "DEL Automated plan- " + \
                                 str(randint(0, 100000)), "DEL Automated plan- " + \
                                 str(randint(0, 100000))
            if not storage_name:
                storage_name = sample(list(self.commcell.storage_pools.all_storage_pools.keys()), 1)[0]
            self.commcell.plans.add(plan_name=old_name, plan_sub_type='Server', storage_pool_name=storage_name)
        self.log.info("Validating Edit Plan name...")
        self.__navigator.navigate_to_plan()
        self.__plans.select_plan(old_name)
        self.__plans.edit_plan_name(new_name=new_name)
        self.__admin_console.wait_for_completion()
        self.__navigator.navigate_to_plan()
        if self.__plans.is_plan_exists(old_name):
            raise CVWebAutomationException(
                '[UI] Old plan name is showing up on UI')

        if not self.__plans.is_plan_exists(new_name):
            raise CVWebAutomationException(
                '[UI] New plan name is not showing up on UI')
        self.commcell.plans.refresh()
        if Delete_flag:
            self.commcell.plans.delete(new_name)
        self.log.info('Edit plan name validation completed')

    def get_edit_details(self, plan_name):
        """Method to get details on edits that user can perform wrt plans"""
        edit_status = {
            'PLAN_APPEARS_ON_LISTING': False,
            'PANEL': {},
            'PLAN_CAN_BE_DERIVED': False,
            'PLAN_CAN_BE_DELETED': False
        }
        edit_status['PLAN_APPEARS_ON_LISTING'] = self.__plans.is_plan_exists(
            plan_name)

        if edit_status['PLAN_APPEARS_ON_LISTING']:
            self.__plans.select_plan(plan_name)
            tile_names = self.__plan_details.plan_tiles()
            self.log.info(
                f'Available panels in plan details page: {tile_names}')

            for tile_name in tile_names:
                if self.__plan_details.is_tile_editable(tile_name):
                    edit_status['PANEL'][tile_name] = True
                else:
                    edit_status['PANEL'][tile_name] = False

            edit_status['PLAN_CAN_BE_DERIVED'] = self.__plan_details.is_plan_derivable()
            edit_status['PLAN_CAN_BE_DELETED'] = self.__plan_details.is_plan_deletable()
        return edit_status

    def validate_permission(self, **kwargs):
        """Method to validate users plan permission from UI"""
        edit_status = self.get_edit_details(self.plan_name)
        self.log.info(f'Edit Status : [{edit_status}]')
        for key, value in kwargs.items():
            temp_str = f"Validation failed for '{key}'"
            if key == 'can_see_plan_in_listing':
                assert edit_status.get(
                    'PLAN_APPEARS_ON_LISTING') == value, temp_str
            if key == 'can_edit_all_tiles':
                assert any(
                    list(edit_status['PANEL'].values())) == value, temp_str
            if key == 'can_derive':
                assert edit_status.get(
                    'PLAN_CAN_BE_DERIVED') == value, temp_str
            if key == 'can_delete':
                assert edit_status.get(
                    'PLAN_CAN_BE_DELETED') == value, temp_str
            if key == 'can_create_plans':
                assert edit_status.get(
                    'PLAN_CAN_BE_CREATED') == value, temp_str

    def get_rpo_string(self, weeks=0, days=0, hours=0, minutes=0):
        """ Method to get rpo string

        Args:
            weeks   (int) : number of weeks
            days    (int) : number of days
            hours   (int) : number of hours
            minutes (int) : number of minutes
        """
        template = {
            "week": "Runs every {0} week",
            "weeks": "Runs every {0} weeks",
            "day": "Runs every {0} day",
            "days": "Runs every {0} days",
            "hours": "Runs every {0} hour(s)",
            "minutes": "Runs every {0} minute(s)",
            "hours_minutes": "Runs every {0} hour(s) {1} minute(s)"
        }

        if weeks:
            return template['weeks'].format(weeks) if weeks > 1 else template['week'].format(weeks)
        elif days:
            return template['days'].format(days) if days > 1 else template['day'].format(days)
        elif not any([hours, minutes]):
            raise Exception(
                '[Invalid Argument]: Both hours and minutes cant be zero')
        elif hours and minutes:
            return template['hours_minutes'].format(hours, minutes)
        elif hours:
            return template['hours'].format(hours)
        elif minutes:
            return template['minutes'].format(minutes)
        else:
            raise Exception('Invalid Arguments passed')

    @PageService()
    def validate_snapshot_options(self):
        """Method to validate snapshot options"""
        self.__plans.select_plan(self.plan_name)

        # Default Value Validation
        expected_values = {
            'Enable backup copy': True,
            'Backup copy RPO': self.get_rpo_string(hours=4)
        }

        def compare_dicts(expected_values: dict, ui_data: dict) -> bool:
            for expected_key, expected_value in expected_values.items():
                if expected_key in ui_data and expected_value != ui_data[expected_key]:
                    return False
            return True

        ui_values = self.__plan_details.get_snapshot_options()

        assert compare_dicts(expected_values,
                             ui_values), f'Snapshot Options Default Value is not matching {expected_values} != {ui_values}'

        # Edit Backup copy RPO
        hours = randint(1, 24)
        minutes = randint(1, 60)
        self.log.info(f'Changing Backup Copy RPO to {hours} hours and {minutes} minutes')
        self.__plan_details.edit_snapshot_options(enable_backup_copy=True,
                                                  backup_rpo={"hours": hours, "minutes": minutes})

        # expected backup copy rpo value after edit
        expected_values['Backup copy RPO'] = self.get_rpo_string(hours=hours, minutes=minutes)

        self.__admin_console.refresh_page()
        ui_values = self.__plan_details.get_snapshot_options()

        assert compare_dicts(expected_values,
                             ui_values), f'Updated Backup Copy RPO value is not matching {expected_values} != {ui_values}'

        # Disable Backup Copy
        self.log.info('Disabling Backup Copy...')
        self.__plan_details.edit_snapshot_options(enable_backup_copy=False)

        # expected values after disabling backup copy
        expected_values['Enable backup copy'] = False
        expected_values.pop('Backup copy RPO')

        self.__admin_console.refresh_page()
        ui_values = self.__plan_details.get_snapshot_options()

        assert compare_dicts(expected_values,
                             ui_values), f'Backup copy option is not disabled {expected_values} != {ui_values}'

        # Enable Backup Copy
        self.log.info('Enabling Backup Copy...')
        self.__plan_details.edit_snapshot_options(enable_backup_copy=True)

        # expected values after enabling backup copy
        expected_values['Enable backup copy'] = True
        expected_values['Backup copy RPO'] = self.get_rpo_string(hours=hours,
                                                                 minutes=minutes)  # old backup copy rpo values would be retained

        self.__admin_console.refresh_page()
        ui_values = self.__plan_details.get_snapshot_options()

        assert compare_dicts(expected_values,
                             ui_values), f'Enabling Backup Copy Failed {expected_values} != {ui_values}'

        self.log.info('Snapshot options validations are completed!')

    def validate_tags(self):
        """Method to validate tags"""
        self.__plans.select_plan(self.plan_name)

        random_tags = {'key ' + str(i): 'value ' + str(randint(0, 10))
                       for i in range(randint(2, 5))}
        self.log.info(f'Initial Tags: {random_tags}')

        # Add the new Tags
        self.__plan_details.edit_tags(random_tags)
        self.__admin_console.refresh_page()
        ui_tags = self.__plan_details.get_associated_tags()
        assert random_tags == ui_tags, f'Newly added Tags are not matching {random_tags} != {ui_tags}'

        # modify any Tag
        x, y = choice(list(random_tags.items()))  # pick random old tag
        modified_key, modified_value = 'modified_key_' + \
                                       str(randint(0, 10)), 'modified_value_' + \
                                       str(randint(0, 10))  # new tag
        random_tags.pop(x)
        # remove and update new value in dict
        random_tags[modified_key] = modified_value

        self.__plan_details.modify_tag(
            old_tag=(x, y), new_tag=(modified_key, modified_value))
        self.__admin_console.refresh_page()
        ui_tags = self.__plan_details.get_associated_tags()
        assert random_tags == ui_tags, f'After Modification Tags are not matching {random_tags} != {ui_tags}'

        # delete the Tag
        x, y = choice(list(random_tags.items()))  # pick random old tag
        random_tags.pop(x)

        self.__plan_details.edit_tags({x: y}, 'DELETE')
        self.__admin_console.refresh_page()
        ui_tags = self.__plan_details.get_associated_tags()
        assert random_tags == ui_tags, f'After Deletion Tags are not matching {random_tags} != {ui_tags}'

        # search for tag from plan listing page
        self.__navigator.navigate_to_plan()
        self.__admin_console.wait_for_completion()
        plan_list = self.__plans.get_plans_with_tag(choice(list(ui_tags)))

        if self.plan_name not in plan_list:
            raise CVWebAutomationException('Searching plan with tag filter failed!')

        self.log.info('Tags Validations are completed!')

    def submit_copy_promotion_request(self, plan_name, copy_name, region=None, backup_type=None,
                                      synchronize_and_convert_time=-1,
                                      synchronize_and_convert_unit=None,
                                      force_conversion=True):
        """Submit specified copy for copy promotion.

            Args:
                plan_name                   (str)   -   Name of plan
                copy_name                   (str)   -   Name of copy
                region                      (str)   -   Region name, if it is a multi-region plan
                backup_type                 (str)   -   Defined for compatibility with UI, example: 'All jobs'
                                                        Defaults to 'All jobs' if None
                synchronize_and_convert_time(int)   -   Time, -1 for immediate copy promotion (Convert immediately)
                synchronize_and_convert_unit(str)   -   Defined for compatibility with UI
                                                        Uses UI default if None. UI default would be 'Hour(s)'
                force_conversion        (boolean)   -   [True] Force copy conversion after x hours
                                                        [False] Fail copy conversion after x hours
        """
        self.log.info(f"Navigating to plan {plan_name}")
        self.__plans.select_plan(plan_name)

        self.log.info("Navigating to backup destinations")
        self.__admin_console.access_tab(self.__props['label.nav.storagePolicy'])
        table = Rtable(self.__admin_console, id='planBackupDestinationTable')
        if region:
            table.expand_row(region)

        convert_to_primary_label = self.__props.get("label.convertToPrimary", "Convert to primary")
        self.log.info(f"Selecting action: {convert_to_primary_label}")

        try:
            name_field = self.__props.get("Name", "Name")
            available_copies = table.get_column_data(name_field)

            if backup_type is None:
                backup_type = self.__props.get("label.allJobs", "All jobs")
            self.log.info("Searching for copy: %s" % (copy_name + '\n' + backup_type))
            index = available_copies.index(copy_name + f"\n{backup_type}")
            self.log.info(f"Found copy at index: {index}")

            table.access_action_item_by_row_index(action_item=convert_to_primary_label, row_index=index)
        except (ValueError, IndexError) as e:
            raise Exception(f"Copy with given name {copy_name} not found!") from e
        except Exception as exp:
            raise Exception(f"Failed to perform action {convert_to_primary_label} on given copy {copy_name}") from exp

        copy_promotion_dialog = RModalDialog(self.__admin_console, title=convert_to_primary_label)
        if synchronize_and_convert_time == -1:
            self.log.info("Submitting request for immediate copy conversion")
            copy_promotion_dialog.select_radio_by_value('immediate')
        else:
            copy_promotion_dialog.select_radio_by_value(radio_value="syncAndCovert")
            log_line_template = ("Submitting request for %s copy conversion after "
                                 f"{synchronize_and_convert_time} {synchronize_and_convert_unit}")
            if not force_conversion:
                self.log.info(log_line_template % 'fail')
                copy_promotion_dialog.select_radio_by_value(radio_value="failConversion")
                if synchronize_and_convert_unit is not None:
                    copy_promotion_dialog.select_dropdown_values(drop_down_id='failConversionTimeUnit',
                                                                 values=[synchronize_and_convert_unit])
                copy_promotion_dialog.fill_text_in_field("failConversionTime",
                                                         text=synchronize_and_convert_time)
            else:
                self.log.info(log_line_template % 'force')
                copy_promotion_dialog.select_radio_by_value(radio_value="forceKillAndPromote")
                if synchronize_and_convert_unit is not None:
                    copy_promotion_dialog.select_dropdown_values(drop_down_id='forceKillAndPromoteTimeUnit',
                                                                 values=[synchronize_and_convert_unit])
                copy_promotion_dialog.fill_text_in_field("forceKillAndPromoteTime",
                                                         text=synchronize_and_convert_time)

        copy_promotion_dialog.click_submit(wait=False)
        self.log.info("Submitted request for copy promotion")

    def get_copy_info(self, plan_name, copy_name, region=None):
        """Retrieves all information from Copy details page in the form of a dictionary

            Args:
                plan_name   (str)   - Name of plan
                copy_name   (str)   - Name of copy
                region      (str)   - Region name if it is a multi-region plan

            Returns:
                dict                - All the information displayed on copy page
        """
        self.log.info('Retrieving information displayed on copy page...')
        self.__plans.select_plan(plan_name)
        return self.__plan_details.copy_info(copy_name, region)

    def is_compliance_lock_enabled(self, plan_name, copy_name, region=None):
        """Checks if compliance lock is enabled on copy of given plan

            Args:
                plan_name   (str)   - Name of plan
                copy_name   (str)   - Name of copy
                region      (str)   - Region name if it is a multi-region plan

            Returns:
                bool    - True if compliance lock is enabled
                          False if compliance lock is not enabled
        """
        self.log.info('Checking if compliance lock is enabled on copy [%s] of plan [%s] in region [%s]' % (copy_name,
                                                                                                           plan_name,
                                                                                                           region))
        copy_details = self.get_copy_info(plan_name, copy_name, region)
        general = self.__props['label.general']
        compliance_lock = self.__props['label.softwareWORM']
        is_enabled = copy_details.get(general, {}).get(compliance_lock, False)
        if is_enabled:
            self.log.info('Compliance Lock is enabled on copy [%s] of plan [%s] in region [%s]' % (copy_name,
                                                                                                   plan_name,
                                                                                                   region))
        else:
            self.log.info('Compliance Lock is disabled on copy [%s] of plan [%s] in region [%s]' % (copy_name,
                                                                                                    plan_name,
                                                                                                    region))
        return is_enabled

    def modify_retention_on_copy(self,
                                 plan_name,
                                 copy_name,
                                 ret_days,
                                 ret_unit=False,
                                 jobs=False,
                                 snap_copy=False,
                                 region=None, waitForCompletion=False):
        """Method to modify retention on existing copy
            Args:
                plan_name (str)   :   Name of plan
                copy_name (str)   :   Name of copy
                ret_days (int)    :   number of days to retain
                ret_unit (str)    :   Unit to use (Day(s), Month(s), etc
                jobs (bool)       :   Want to retain by jobs or not
                snap_copy (bool)  :   editing snapshot copy or not
                region (str)      :   Region name if it is a multi-region plan;
                                      default value is None -> implying region is not configured in plan
                waitForCompletion (bool): Want to wait for completion or not, after click on Yes
        """

        self.log.info("Modifying retention on copy...")
        self.__plans.select_plan(plan_name)
        return self.__plan_details.edit_copy_retention_rules(copy_name, ret_days, ret_unit, jobs, snap_copy, region, waitForCompletion)

    def modify_extended_retention_on_copy(self,
                                          plan_name,
                                          copy_name,
                                          num_rules,
                                          ret_period,
                                          ret_unit,
                                          ret_freq,
                                          region=None):
        """Method to modify extended retention rules on existing copy
            Args:
                    plan_name (str)   :   Name of plan
                    copy_name (str)   :   Name of copy
                    num_rules (int)   :   number of extended rules to apply
                    ret_period (list of int): list of retention periods for each rule
                    ret_unit (list of str)  : Unit to use (Day(s), Month(s), etc.)
                    ret_freq (list of str)  : retention frequencies ('Monthly Fulls', 'Quarterly Fulls', etc.)
                    region (str)    : Region name if it is a multi-region plan;
                                      default value is None -> implying region is not configured in plan
        """

        self.log.info("Modifying extended retention on copy...")
        self.__plans.select_plan(plan_name)
        self.__plan_details.edit_copy_extended_retention_rules(num_rules,
                                                               copy_name,
                                                               ret_period,
                                                               ret_unit,
                                                               ret_freq,
                                                               region)

    def delete_copy_and_validate(self, plan_name, copy_name, region=None):
        """ Method to delete a copy of a plan
            Args:
                    plan_name (str)   :   Name of plan
                    copy_name (str)   :   Name of copy
                    region (str)    : Region name if it is a multi-region plan

        """
        self.log.info(f"Deleting copy of plan {plan_name}")
        self.__navigator.navigate_to_plan()
        self.__plans.select_plan(plan_name)
        self.__admin_console.access_tab(self.__props['label.nav.storagePolicy'])
        #  self.__rtable.expand_row('default')
        if region:
            self.__rtable.expand_row(region)
        self.__rtable.access_action_item(copy_name, 'Delete', search=False)
        self.__rmodal_diag.type_text_and_delete('Delete', checkbox_id='onReviewConfirmCheck', button_name="Submit")

        # Checks if copy deletion is reflected on UI
        entity_name = f'{copy_name}\nAll jobs'
        self.__rtable.search_for('Secondary')
        name_field = self.__props['Name']
        available_fields = self.__table.get_visible_column_names()
        if name_field in available_fields:
            column_data = self.__table.get_column_data(name_field)
            if entity_name in column_data:
                raise CVWebAutomationException('[UI] copy found on ui after deletion')

        query = f"""SELECT AGC.Name
                              FROM   archGroupCopy AGC WITH (NOLOCK)
                              JOIN   archGroup AG WITH (NOLOCK)
                                     ON     AGC.archGroupId = AG.id
                              WHERE	AG.name = '{plan_name}'
                              AND     AGC.name = '{copy_name}'"""

        self.csdb.execute(query)

        if [copy[0] for copy in self.csdb.fetch_all_rows() if copy[0] != '']:
            raise CVWebAutomationException('[DB] copy found in database after deletion')

        self.__driver.implicitly_wait(0)
        self.log.info('Delete copy validation completed')

    def validate_backup_content(self):
        """Method to Validate backup content"""
        library = ['Desktop', 'Documents', 'Downloads', 'Music', 'Pictures', 'Videos',
                   'Google Drive', 'OneDrive', 'Dropbox', 'Audio', 'Office', 'Image']

        custom_paths = {
            'Windows': ['C:\\hellowrld\\' + str(i) + str(randint(0, 1000)) for i in range(1, 15)],
            'Unix': ['//hello/world/' + str(i) + str(randint(0, 1000)) for i in range(1, 15)]
        }

        for file_system, content_paths in custom_paths.items():
            self.log.info(
                f'Validating Backup Content for file system : {file_system}')
            self.__plans.select_plan(self.plan_name)
            content_folders = exclude_folders = exception_folders = sample(
                library, 3)
            custom_content = exclude_custom_content = exception_custom_content = sample(
                custom_paths[file_system], 3)

            expected_content = {
                file_system: {
                    'BACKUP_CONTENT': content_folders + custom_content,
                    'EXCLUDED_CONTENT': exclude_folders + exclude_custom_content,
                    'EXCEPTION_CONTENT': exception_folders + exception_custom_content
                }
            }

            for content in expected_content[file_system]:
                # sort all the list inside dict before comparision
                expected_content[file_system][content].sort()
            self.log.info(f'Expected : {expected_content}')

            self.__plan_details.edit_plan_backup_content(file_system, content_folders, custom_content,
                                                         exclude_folders, exclude_custom_content,
                                                         exception_folders, exception_custom_content)
            self.__admin_console.refresh_page()

            ui_content = self.__plan_details.get_backup_content(file_system)
            for content in ui_content[file_system]:
                # sort all the list inside dict before comparision
                ui_content[file_system][content].sort()
            self.log.info(f'UI : {ui_content}')

            assert expected_content == ui_content, f'Backup content values are not matching for {file_system}: {expected_content} != {ui_content}'

        self.log.info('Backup Content Validation completed!')

    def validate_backup_system_state(self):
        """Method to validate the backup system state"""
        self.log.info('Validating backup system state...')
        self.__plans.select_plan(self.plan_name)

        # first enable backup content, if not enabled
        ui_data = self.__plan_details.get_backup_system_state_details()
        if not ui_data:
            self.__plan_details.enable_backup_content()

        expected = {
            'backupSystemState': True,
            'useVss': True,
            'onlyWithFullBackup': False
        }

        # Default Value Validation
        ui_data = self.__plan_details.get_backup_system_state_details()
        assert expected == ui_data, f'Default Backup System State Validation Failed : {expected} != {ui_data}'

        # Edit Backup System State Checkbox
        expected['useVss'] = choice([True, False])
        expected['onlyWithFullBackup'] = choice([True, False])
        self.__plan_details.edit_backup_system_state(
            True, expected['useVss'], expected['onlyWithFullBackup'])
        self.__admin_console.refresh_page()
        ui_data = self.__plan_details.get_backup_system_state_details()
        assert expected == ui_data, f'Backup System State details are not matching : {expected} != {ui_data}'

        # Disable Backup System State
        self.__plan_details.edit_backup_system_state(False)
        self.__admin_console.refresh_page()
        expected = {'backupSystemState': False}
        ui_data = self.__plan_details.get_backup_system_state_details()
        assert expected == ui_data, f'Backup System State is not disabled : {expected} != {ui_data}'

        self.log.info('Backup System State Validation completed!')

    @PageService()
    def listing_page_search(self, plan_name):
        """Method to validate a plan in listing page"""
        if self.__plans.is_plan_exists(plan_name=plan_name):
            self.log.info(
                'listing page search validation completed for the plan')
        else:
            raise CVWebAutomationException('plan not listed in listing page')

    def validate_override_restrictions(self):
        """Method to validate override restrictions"""
        self.log.info('Validating Override Restrictions...')
        self.__plans.select_plan(self.plan_name)

        derivable = self.__plan_details.is_plan_derivable()
        if derivable:
            raise CVWebAutomationException(
                'Newly created plan can be derived by default')

        options_available = ['Override required',
                             'Override optional', 'Override not allowed']
        expected_values = {
            "Allow plan to be overridden": True,
            "Storage pool": choice(options_available),
            "RPO": choice(options_available),
            "Backup content": choice(options_available)
        }
        self.log.info(f'Expected values : {expected_values}')

        self.__plan_details.edit_plan_override_restrictions(expected_values)

        self.__admin_console.refresh_page()
        if not self.__plan_details.is_plan_derivable():
            raise CVWebAutomationException(
                'Plan is not derivable even after Allowing the plan override')

        ui_values = self.__plan_details.get_override_restrictions()
        assert expected_values == ui_values, f'Validation failed for Override restrictions. {expected_values} != {ui_values}'

    def validate_plan_details_loading(self, storage_name=None):
        """Method to validate if plan can be loaded"""
        plan_name = "DEL Automated plan- " + str(randint(0, 100000))
        if not storage_name:
            storage_name = sample(list(self.commcell.storage_pools.all_storage_pools.keys()), 1)[0]
        self.commcell.plans.add(plan_name=plan_name, plan_sub_type='Server', storage_pool_name=storage_name)
        self.log.info("Validating plan details loading..")
        self.__navigator.navigate_to_plan()
        self.__plans.select_plan(plan_name)

        available_panels = self.__plan_details.plan_tiles()
        self.commcell.plans.refresh()
        self.commcell.plans.delete(plan_name)

        if len(available_panels) < 3:
            raise CVWebAutomationException('Plan details page is not loading!')

        self.log.info('Plan details page loaded successfully!')

    def validate_action_associate_to_company(self, plan, company):
        """Method to validate associate to company action from action menu"""
        self.__navigator.navigate_to_plan()
        self.__plans.associate_to_company(plan, company)

    @PageService()
    def validate_schedule_properties(self, schedule, properties):
        """Method to validate schedule properties"""
        # remove double digit from timings 05:45 am to 5:45 am
        if properties.get('StartTime'):
            hour, minutes = properties['StartTime'].split(':')
            properties['StartTime'] = f'{int(hour)}:{minutes}'

        # check if all the property set in the schedule
        if not all(str(property).lower() in schedule.lower() for property in properties.values()):
            raise CVWebAutomationException(
                f'Schedules property not matching: {schedule}, Expected values : {properties}')

    @PageService()
    def validate_create_schedule(self, properties):
        """Method to create schedule for plan and validates creation"""
        self.log.info('Validating schedule creation...')
        prev_schedules = self.__rpo.get_schedules()
        self.__rpo.create_schedule(properties)
        self.__admin_console.refresh_page()
        self.__admin_console.wait_for_completion()

        new_schedules = self.__rpo.get_schedules()

        # check if one extra schedule showing up on screen
        if len(new_schedules) != len(prev_schedules) + 1:
            raise CVWebAutomationException('Failed to add new schedule!')

        # validate properties of newly created schedule
        self.validate_schedule_properties(
            list(set(prev_schedules) ^ set(new_schedules))[0], properties)
        self.log.info(f'Schedule creation validation completed! {properties}')

    @PageService()
    def validate_edit_schedule(self, index, properties):
        """Method to edit a schedule and validate"""
        self.log.info('Validating schedule edit...')
        self.__rpo.edit_schedule(index, properties)
        self.__admin_console.refresh_page()
        self.__admin_console.wait_for_completion()

        self.validate_schedule_properties(
            self.__rpo.get_schedules()[index - 1], properties)

    @PageService()
    def validate_delete_schedule(self, index):
        """Method to validate schedule deletion"""
        self.log.info('Validating schedule deletion...')
        prev_schedules = self.__rpo.get_schedules()
        self.__rpo.delete_schedule(index)
        self.__admin_console.refresh_page()
        self.__admin_console.wait_for_completion()

        prev_schedules.pop(index - 1)
        if self.__rpo.get_schedules() != prev_schedules:
            raise CVWebAutomationException('Schedule deletion failed!')

    @PageService()
    def validate_plan_association(self, file_server_name: str, plan_name: str) -> tuple:
        """Method to validate plan assoc from UI and API

        Args:
            file_server_name (str) : File server client name

            plan_name (str) : plan name
        """
        backupset = self.commcell.clients.get(file_server_name).agents.get(
            'File System').backupsets.get('defaultBackupSet')

        # associate via UI
        backupset.plan = None  # remove existing plan
        ui_status = self.file_server_helper.associate_plan_to_file_server(
            plan_name, file_server_name)

        # associate via API
        backupset.plan = None  # remove existing plan
        api_status = self._sdk_plan_helper.validate_backupset_association(
            plan_name, file_server_name, 'defaultBackupSet')

        return ui_status, api_status

    @PageService()
    def validate_appl_soln_edits(self, plan_name: str, solutions: list) -> tuple:
        """Method to validate applicable solution edits from Plan details page

        Args:
            plan_name (str) : plan name

            solutions (list) : list of applicable solutions
        """
        # edit via UI
        self.log.info(
            f'Setting applicable solutions {solutions} on plan : {plan_name}...')
        try:
            self.__plans.select_plan(plan_name)
            self.__plan_details.edit_applicable_solns(solutions)
            self.__admin_console.refresh_page()
            self.log.info(
                f'Applicable solutions set to => {self.__plan_details.get_applicable_solns()}')
            ui_status = sorted(
                self.__plan_details.get_applicable_solns()) == sorted(solutions)
        except Exception as err:
            self.log.info(f'Applicable Solution Edit Failed via UI: [{err}]')
            ui_status = False

        # edit via API
        api_status = self._sdk_plan_helper.validate_applicable_solution_edit(
            plan_name, solutions)

        return ui_status, api_status

    def __convert_to_24_hr(self, hour: int) -> str:
        """Helper Method to convert 24 hour format to am | pm"""
        if hour < 12:
            return f"{hour}am"
        elif hour == 12:
            return "12pm"
        elif hour == 24:
            return "12am"
        else:
            return f"{hour - 12}pm"

    def __generate_time_slots(self) -> list:
        """Helper function to generate random time slots for backup window"""
        slots = []
        start = 1
        while start < 24:
            end = randint(start + 1, 24)
            slots.append(f"{self.__convert_to_24_hr(start)}-{self.__convert_to_24_hr(end)}")
            start = end + 2

        return slots

    def __remove_duplicate_slots_from_backup_window(self, backup_window: dict) -> dict:
        """Helper function to remove duplicate slots from backup window"""
        seen_values = []

        for key, values in backup_window.items():
            filtered_values = []
            for value in values:
                # if value is found for second time, then ignore the element
                if value not in seen_values:
                    filtered_values.append(value)
                    seen_values.append(value)
            backup_window[key] = filtered_values

        return backup_window

    def generate_blackout_window_config(self, max_days: int = 3) -> dict:
        """
            Method to generate dummy backup window

            Args:
                max_days    :   Max Number of days to generate blackout window

            Return Example:
                backup_window = {
                    'Monday' : ['All day'],
                    'Tuesday' : ['2am-6am', '1pm-6pm'],
                    'Wednesday' : ['5am-2pm'],
                    'Saturday' : ['2am-5am', '9am-12pm', '2pm-6pm', '9pm-12am']
                }
        """
        days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        num_days = randint(1, max_days)
        random_days = sample(days, num_days)
        random_blackout_window = {day: self.__generate_time_slots() for day in random_days}
        backup_window = self.__remove_duplicate_slots_from_backup_window(random_blackout_window)
        all_day = choice([day for day in days if day not in random_days])  # select any full day
        backup_window[all_day] = ['All day']
        self.log.info(f'Generated random backup window => {backup_window}')
        return backup_window

    @PageService()
    def is_plan_associated_with_company(self, plan_name: str, company_name: str) -> bool:
        """
            Method to validate plan association with company

            Args:
                plan_name       :   Plan name
                company_name    :   Company name
        """
        self.log.info(f'Validating plan: [{plan_name}] association with company {company_name}...')

        # go to plan details > company tab
        self.__navigator.navigate_to_plan()
        self.__rtable.access_action_item(plan_name, "Associate to company")

        # company alias is shown in UI, so need to get the alias from company name
        company_alias = self.commcell.organizations.get(company_name).domain_name
        status = self.__rtable.is_entity_present_in_column(column_name='Company',
                                                           entity_name=company_alias)

        return status

    @PageService()
    def validate_plan_association_to_company(self, plan_name: str, company_name: str, old_plan: str = None) -> None:
        """
            Method to validate plan association with company from plan details page

            Args:
                plan_name       :   Plan name
                company_name    :   Company name
                old_plan        :   Old plan name, that is already in association with company
        """
        self.__navigator.navigate_to_plan()
        self.__plans.associate_to_company(plan_name, [company_name])

        if old_plan and not self.is_plan_associated_with_company(old_plan, company_name):
            raise CVTestStepFailure(
                'Old plan got removed from the association, after associating a new plan with company')

        if not self.is_plan_associated_with_company(plan_name, company_name):
            raise CVTestStepFailure('Failed to associate new plan with the company from plan details page')

        self.log.info('Plan association with company validated successfully!')

    @PageService()
    def validate_plan_disassociation_from_company(self, plan_name: str, company_name: str) -> None:
        """
            Method to validate plan disassociation from company from plan details page

            Args:
                plan_name       :   Plan name
                company_name    :   Company name
        """
        self.__navigator.navigate_to_plan()
        company_alias = self.commcell.organizations.get(company_name).domain_name
        self.__plans.disassociate_from_company(plan_name, company_alias)
        if self.is_plan_associated_with_company(plan_name, company_name):
            raise CVTestStepFailure('Failed to disassociate plan from plan details page')

    @PageService()
    def validate_plan_assoc_with_fs_client(self, file_server_name: str, plan_name: str,
                                           default_backupset_name: str = 'defaultBackupSet') -> None:
        """
            Method to validate plan association with file server client

            Args:
                file_server_name        :   File server client name
                plan_name               :   Plan name
                default_backupset_name  :   Default backupset name
        """
        # associate plan to file server client
        self.log.info('Associating plan with file server client...')
        self.__navigator.navigate_to_file_servers()
        self.validate_plan_association(file_server_name, plan_name)

        self.log.info('Plan associated with file server client successfully')

        # disassociate plan from file server client from plan details page
        self.log.info('Disassociating plan from file server client from plan details page...')
        self.__plans.select_plan(plan_name)
        self.__plan_details.disassociate_plan(file_server_name, default_backupset_name)

        backup_set_obj = self.commcell.clients.get(file_server_name).agents.get('File System').backupsets.get(
            default_backupset_name
        )
        if backup_set_obj.plan and backup_set_obj.plan.plan_name.lower() != plan_name.lower():
            raise CVTestStepFailure('Failed to disassociate plan from file server client from plan details page')

        self.log.info('Plan disassociated from file server client successfully')

    @PageService()
    def run_auxiliary_copy_job(self,
                               plan_name,
                               copy_name=None):
        """
            Method to run auxiliary copy job from backup destinations page

            Args:
                plan_name: Name of the plan
                copy_name: Name of the copy to run auxiliary copy job on; 'None' to run on all copies
                            
        :return:
                job_id: Job ID of the auxiliary copy job
        """
        self.log.info(f"Running Aux Copy job on plan {plan_name} and copy {copy_name}")
        self.__navigator.navigate_to_plan()
        self.__plans.select_plan(plan_name)
        self.__admin_console.access_tab(self.__props['label.nav.storagePolicy'])
        self.__plan_details.run_auxiliary_copy(copy_name)
        
        # Get jobid from hyperlink in toast message
        job_id = self.__alert.get_jobid_from_popup(hyperlink=True)

        return job_id

    def plans_lookup(self, entity_type: str, plan: str, entity_name: str = None) -> list:
        """
        Method to look up for plans listed in various places in the CC.

        Args:
            entity_type (str)   : The type of entity ('FILESERVER' or 'VMGROUP').
            plan (str)          : The plan name to search for within the plans dropdown.
            entity_name (str)   : The name of the entity. If not provided, a random entity will be chosen.

        Returns:
            list: A list of plans found in the dropdowns.
        """
        self.log.info(f"Starting plans lookup for entity_type: {entity_type}")

        if entity_type.upper() == 'FILESERVER':
            self.__navigator.navigate_to_file_servers()
            self.__admin_console.access_tab(self.__admin_console.props['label.nav.servers'])
            if not entity_name:
                entity_name = choice(self.__fs.get_all_file_servers())
            self.__rtable.access_action_item(entity_name, self.__admin_console.props['label.globalActions.associatePlan'])
            plans_list = self.__rdropdown.get_values_of_drop_down(drop_down_id="subclientPlanSelection", search=plan)
            if not plans_list:
                raise CVWebAutomationException(
                    f'{plan} not listed in the regions dropdown for entity type {entity_type}')
            self.__admin_console.click_button_using_text(self.__admin_console.props['action.cancel'])

        elif entity_type.upper() == 'VMGROUP':
            self.__navigator.navigate_to_vm_groups()
            if not self.__vm_group.list_vm_groups():
                raise Exception('No VM groups added. Please add a vm group to continue')
            if not entity_name:
                entity_name = choice(self.__vm_group.list_vm_groups())
            self.__vm_group.select_vm_group(entity_name)
            self.__rpanel_info.edit_tile_entity(self.__admin_console.props['label.plan'])
            plans_list = self.__rdropdown.get_values_of_drop_down(drop_down_label='Plan', search=plan)
            if not plans_list:
                raise CVWebAutomationException(
                    f'{plan} not listed in the regions dropdown for entity type {entity_type}')
        else:
            raise ValueError("Invalid entity type")

        return plans_list
    