"""
Module for Salesforce Monitoring Page

SalesforceAnomalyAlerts:

            access_history_page()             :         Accesses the history section on the monitoring page

            delete_default_alert()            :         Deletes the default alert created at the time of organization
                                                        creation

            backup()                          :         Runs backup

            create_alert()                    :         Creates an Anomaly Alert based on the parameters provided

            get_alert_info()                  :         Retrieves the rules of the alert triggered on a given job


"""

from Web.AdminConsole.Components.dialog import RModalDialog
from Web.AdminConsole.Components.page_container import PageContainer
from Web.AdminConsole.Components.panel import RPanelInfo, RDropDown, RModalPanel
from Web.AdminConsole.Components.table import Rtable
from selenium.webdriver.common.by import By
from .base import SalesforceBase
from .constants import ALERT_TYPE_MAPPING
from Web.Common.page_object import PageService, WebAction


class SalesforceAnomalyAlerts(SalesforceBase):
    """Class for Salesforce Monitoring page"""

    def __init__(self, admin_console, commcell):
        """
            Init method for this class

            Args:
                admin_console (Web.AdminConsole.Helper.AdminConsoleBase.AdminConsoleBase): Object of AdminConsole class

            Returns:
                None:
        """
        super().__init__(admin_console, commcell)
        self.__admin_console = admin_console
        self.__driver = admin_console.driver
        self.__admin_console.load_properties(self)
        self.__page_container = PageContainer(self.__admin_console)
        self.__rdialog = RModalDialog(self.__admin_console)
        self.__rpanel = RPanelInfo(self.__admin_console)
        self.__rmodpanel = RModalPanel(self.__admin_console)
        self.__rdropdown = RDropDown(self.__admin_console)
        self.__rtable = Rtable(self.__admin_console)

    @WebAction()
    def access_history_page(self):
        """
            Accesses the alert history section on the monitoring page
        """
        self.__page_container.click_on_button_by_id("history")

    @WebAction()
    def delete_default_alert(self):
        """
            Deletes the default alert created at the time of organization creation
        """
        self.__rtable.access_action_item(entity_name="All Objects",
                                         action_item=self.__admin_console.props["action.delete"])

    @WebAction()
    def __retrieve_radio_options(self):
        """
            Retrieves the selected parameter type from alert rule box i.e. Number or Percentage
        """
        xpath = "//span[contains(@class,'radio-btn') and contains(@class,'Mui-checked')]//input"
        parameter_type = self.__driver.find_element(By.XPATH, xpath).get_attribute('value')
        key_list = list(ALERT_TYPE_MAPPING.keys())
        val_list = list(ALERT_TYPE_MAPPING.values())
        return key_list[val_list.index(parameter_type)]

    @PageService()
    def _click_on_backup(self, org_name):
        """
        Method to click on backup

        Args:
            org_name (str)  --  Name of org to click on backup for
        """
        self.__page_container.access_page_action(self.__admin_console.props['label.globalActions.backup'])

    @PageService()
    def backup(self, org_name, backup_type="Incremental", wait_for_job_completion=True):
        """
        Runs backup

        Args:
            org_name (str)              --  Name of the organization to be backed up
            backup_type (str)           --  "Full" or "Incremental", case insensitive
            wait_for_job_completion (bool) --  if True, waits for current job and any automatic job that launches
                                            if False, just returns job id of full/incremental job run

        Returns:
            (tuple)                     --  (job_id, ) or (full_job_id, incremental_job_id)

        Raises:
            Exception                   --  if wait_for_job_completion is True and waiting for full/automatic
                                            incremental job encounters an error
        """
        return super().backup(org_name, backup_type, wait_for_job_completion)

    @PageService()
    def create_alert(self, objects, criterias, parameter_type, condition, value):
        """
            Creates a new alert
            Args:
                objects (list): List of objects on which the alert is being created
                criterias (list): List of criterias from Added, Deleted and Modified upon which alert will be triggered
                parameter_type (string): Determines whether the condition value will be a number or percentage
                condition (list): Determines the condition type from Greater than, Equals or Less than
                value (string): Value used for the condition parameter to trigger an alert
        """
        self.__rpanel.click_button(self.__admin_console.props["label.anomalyAlert.config.new"])
        self.__admin_console.wait_for_completion()
        self.__rdropdown.select_drop_down_values(values=objects, drop_down_id="objectNames",
                                                 case_insensitive_selection=True)
        self.__rdropdown.select_drop_down_values(values=criterias, drop_down_id="criterias",
                                                 case_insensitive_selection=True)
        self.__rdialog.select_radio_by_value(ALERT_TYPE_MAPPING[parameter_type])
        self.__rdropdown.select_drop_down_values(values=condition, drop_down_id="conditionType",
                                                 case_insensitive_selection=True)
        self.__rmodpanel.fill_input(text=value, id="conditionParameter")
        self.__rdialog.click_submit()

    @PageService()
    def get_alert_info(self, job_id):
        """
            Retrieves the rules and object on which the alert has been triggered by a particular job
            Args:
                job_id (string): Job ID of the incremental job which triggers the alert
            Returns:
                A list of the parameters which defines the triggered alert
        """
        self.__rtable.access_link_without_text(job_id, self.__admin_console.props["label.sfseeding.viewModal.save"])
        criteria_list = self.__rdropdown.get_selected_values(drop_down_id="criterias", expand=False)
        parameter_type = self.__retrieve_radio_options()
        condition_type = self.__rdropdown.get_selected_values(drop_down_id="conditionType", expand=False)
        value = self.__rdialog.get_input_details(input_id="conditionParameter")
        self.__rdialog.click_cancel()
        obj_name = self.__rtable.get_column_data(column_name="Object name")
        return obj_name, criteria_list, parameter_type, condition_type, value
