# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""
This module provides the function or operations that can be performed on the
Destination Section on the Restore Wizard of VSA Hypervisors

"""

from selenium.common.exceptions import NoSuchElementException, ElementClickInterceptedException
from selenium.webdriver.common.by import By

from VirtualServer.VSAUtils.VirtualServerConstants import HypervisorDisplayName
from Web.AdminConsole.Components.dialog import RModalDialog
from Web.AdminConsole.Components.wizard import Wizard
from Web.AdminConsole.Components.table import Rtable
from Web.AdminConsole.Components.core import TreeView


class ConfigureVMProvisioningSetting:
    """
    Class to Configure VM Provisioning setting to be used for Auto-Scale and On-Demand Provisioning
    """

    def __init__(self, admin_console, vm_provisioning_options):
        self.__admin_console = admin_console
        self.__vm_provisioning_options = vm_provisioning_options
        self.__vm_provisioning_wizard = Wizard(self.__admin_console)
        self.__rtable_obj = Rtable(self.__admin_console)

    def configure_settings(self):
        """

        """
        saved_provisioning_dialog = False

        while not saved_provisioning_dialog:
            current_provisioning_step = self.__vm_provisioning_wizard.get_active_step()

            if current_provisioning_step == "Server And Resource Groups":
                self.azure_basic_configuration()
            if current_provisioning_step == "Server Group And IAM":
                self.aws_basic_configuration()
            elif current_provisioning_step == "Region":
                self.region_configuration()
            elif current_provisioning_step == "Availability Zone":
                self.availability_zone_configuration()
            elif current_provisioning_step == "Access Nodes":
                self.access_nodes_settings()
            elif current_provisioning_step == "Domain Credentials":
                self.domain_credential_settings()
            elif current_provisioning_step == "Advanced Settings":
                self.advanced_settings()
            elif current_provisioning_step == "Summary":
                self.__vm_provisioning_wizard.click_submit()
                saved_provisioning_dialog = True

    def aws_basic_configuration(self):
        """
        Configures basic AWS settings for VM provisioning, including server group, IAM role,
        default system settings, and public IP creation
        """
        self.__admin_console.log.info("Selecting AWS Server group, IAM Role & other basic configurations ")

        if self.__vm_provisioning_options.get('server_group', None):
            self.__vm_provisioning_wizard.select_drop_down_values(id="serverGroup",
                                                                  values=[self.__vm_provisioning_options
                                                                          ['server_group']])

        if self.__vm_provisioning_options.get('iam_role', None):
            self.__vm_provisioning_wizard.select_drop_down_values(id="IAMDropdown",
                                                                  values=[self.__vm_provisioning_options
                                                                          ['iam_role']])

        if self.__vm_provisioning_options.get('system_default_settings', False):
            self.__vm_provisioning_wizard.enable_toggle(label=self.__admin_console.props["label.setAsDefaultPolicy"])
        else:
            self.__vm_provisioning_wizard.disable_toggle(label=self.__admin_console.props["label.setAsDefaultPolicy"])

        if self.__vm_provisioning_options.get('create_public_ip', False):
            self.__vm_provisioning_wizard.enable_toggle(label=self.__admin_console.props["label.publicIPAddress"])
        else:
            self.__vm_provisioning_wizard.disable_toggle(label=self.__admin_console.props["label.publicIPAddress"])

        self.__vm_provisioning_wizard.click_next()

    def azure_basic_configuration(self):
        """

        """
        self.__admin_console.log.info("Selecting Azure Server group, Resource group & other basic configurations ")

        if self.__vm_provisioning_options.get('ServerGroup', None):
            self.__vm_provisioning_wizard.select_drop_down_values(id="serverGroup",
                                                                  values=[self.__vm_provisioning_options
                                                                          ['ServerGroup']])

        if self.__vm_provisioning_options.get('ResourceGroup', None):
            self.__vm_provisioning_wizard.select_drop_down_values(id="resourceGroupDropdown",
                                                                  values=[self.__vm_provisioning_options
                                                                          ['ResourceGroup']])

        if self.__vm_provisioning_options.get('SetAsSystemDefaultSetting', False):
            self.__vm_provisioning_wizard.enable_toggle(label=self.__admin_console.props["label.setAsDefaultPolicy"])
        else:
            self.__vm_provisioning_wizard.disable_toggle(label=self.__admin_console.props["label.setAsDefaultPolicy"])

        if self.__vm_provisioning_options.get('EnablePublicIP', False):
            self.__vm_provisioning_wizard.enable_toggle(label=self.__admin_console.props["label.publicIPAddress"])
        else:
            self.__vm_provisioning_wizard.disable_toggle(label=self.__admin_console.props["label.publicIPAddress"])

        self.__vm_provisioning_wizard.click_next()

    def region_configuration(self):
        """

        """
        self.__admin_console.log.info("Configuring Azure Regions for VM Provisioning setting")

        for region_info in self.__vm_provisioning_options.get("RegionSpecificInfo", []):
            self.__vm_provisioning_wizard.click_button(name=self.__admin_console.props['label.add'])

            add_region_dialog = RModalDialog(self.__admin_console,
                                             title=self.__admin_console.props['label.autoScaleAddRegion'])
            add_region_dialog.select_dropdown_values(drop_down_id='azureRegionDropdown',
                                                     values=[region_info['RegionName']])
            add_region_dialog.select_dropdown_values(drop_down_id='vmNetworks',
                                                     values=[region_info['NetworkName']])
            add_region_dialog.select_dropdown_values(drop_down_id='subnet',
                                                     values=[region_info['SubNetName']], partial_selection=True)
            add_region_dialog.select_dropdown_values(drop_down_id='securityGroup',
                                                     values=[region_info['NSGName']])

            add_region_dialog.click_submit()

        self.__vm_provisioning_wizard.click_next()

    def availability_zone_configuration(self):
        """
        Configures AWS Availability Zones for VM provisioning settings.
        """
        self.__admin_console.log.info("Configuring AWS Availability Zones for VM Provisioning setting")

        if self.__vm_provisioning_options.get('default_vpc', False):
            self.__vm_provisioning_wizard.enable_toggle(label=self.__admin_console.props["label.defaultSecurityGroup"])
        else:
            self.__vm_provisioning_wizard.disable_toggle(label=self.__admin_console.props["label.defaultSecurityGroup"])

        for az_info in self.__vm_provisioning_options.get("AZSpecificInfo", []):
            self.__vm_provisioning_wizard.click_button(name=self.__admin_console.props['label.add'])

            edit_region_dialog = RModalDialog(self.__admin_console,
                                              title=self.__admin_console.props['label.editRegion'])
            current_zone = self.__admin_console.driver.find_element(By.ID, 'availabilityZone').get_attribute('value')
            edit_region_dialog.click_button_on_dialog(aria_label='Browse')
            self.__admin_console.wait_for_completion()
            availability_zone_modal = RModalDialog(admin_console=self.__admin_console, title='Select availability zone')
            zone_tree_view = TreeView(self.__admin_console, xpath=availability_zone_modal.base_xpath)
            zone_tree_view.select_items(items=[az_info['AvailabilityZone']])
            if current_zone == az_info['AvailabilityZone']:
                availability_zone_modal.click_cancel()
            else:
                availability_zone_modal.click_submit()

            edit_region_dialog.select_dropdown_values(drop_down_id='vmNetworks',
                                                      values=[az_info['VPC']])
            edit_region_dialog.select_dropdown_values(drop_down_id='subnet',
                                                      values=[az_info['Subnet']], partial_selection=True)
            edit_region_dialog.select_dropdown_values(drop_down_id='securityGroups',
                                                      values=[az_info['SecurityGroup']])

            if az_info.get("KeyPair", False):
                edit_region_dialog.enable_toggle(label=self.__admin_console.props["label.enableKeyPair"])
                confirm_key_pair_dialog = RModalDialog(self.__admin_console,
                                                       title=self.__admin_console.props['label.confirmKeyPair'])
                confirm_key_pair_dialog.click_button_on_dialog('Yes')
                edit_region_dialog.select_dropdown_values(drop_down_id='keyPair',
                                                          values=[az_info['KeyPair']])
            else:
                edit_region_dialog.enable_toggle(label=self.__admin_console.props["label.enableKeyPair"])
                confirm_key_pair_dialog = RModalDialog(self.__admin_console,
                                                       title=self.__admin_console.props['label.confirmKeyPair'])
                confirm_key_pair_dialog.click_button_on_dialog('No')
            edit_region_dialog.click_submit()

        self.__vm_provisioning_wizard.click_next()

    def access_nodes_settings(self):
        """
        Configures access nodes details and settings for VM provisioning, specific to AWS and Azure.
        """

        if self.__vm_provisioning_options.get('HypervisorName') == HypervisorDisplayName.AMAZON_AWS.value:
            self.__admin_console.log.info("Configuring AWS Access nodes details & settings")

            if self.__vm_provisioning_options.get('AccessNodeSettings', None):

                access_node_settings = self.__vm_provisioning_options['AccessNodeSettings']

                if access_node_settings.get('InstanceType', None):
                    self.__vm_provisioning_wizard.disable_toggle(
                        label=self.__admin_console.props['label.autoSelectInstanceType'])
                    self.__vm_provisioning_wizard.select_drop_down_values(id="instanceType",
                                                                          values=[access_node_settings['InstanceType']])
                if access_node_settings.get('ChooseSizeWithJob', False):
                    self.__vm_provisioning_wizard.enable_toggle(
                        label=self.__admin_console.props['label.chooseInstanceTypeWithJob'])
                else:
                    self.__vm_provisioning_wizard.disable_toggle(
                        label=self.__admin_console.props['label.chooseInstanceTypeWithJob'])

                if access_node_settings.get('CustomImage', None):
                    self.__vm_provisioning_wizard.enable_toggle(
                        label=self.__admin_console.props['label.createCustomImage'])

                    if self.__rtable_obj.is_entity_present_in_column(self.__admin_console.props['label.vmProvImage'],
                                                                     access_node_settings['CustomImage']):
                        self.__rtable_obj.select_rows([access_node_settings['CustomImage']])
                        self.__vm_provisioning_wizard.click_button(
                            name=self.__admin_console.props['label.delete'].upper())

                    self.__vm_provisioning_wizard.click_button(name=self.__admin_console.props['label.add'])
                    custom_img_dialog = RModalDialog(self.__admin_console,
                                                     'Custom image')

                    custom_img_dialog.select_radio_by_id(access_node_settings['CustomImageOS'].lower())
                    custom_img_dialog.select_dropdown_values(drop_down_id='AMISelection',
                                                             values=[access_node_settings[
                                                                         'CustomImage']])

                    custom_img_dialog.click_submit()


        else:
            self.__admin_console.log.info("Configuring Azure Access nodes details & settings")

            if self.__vm_provisioning_options.get('AccessNodeSettings', None):
                self.__vm_provisioning_wizard.disable_toggle(
                    label=self.__admin_console.props['label.createCustomImage'])
                access_node_settings = self.__vm_provisioning_options['AccessNodeSettings']

                if access_node_settings.get('VMSize', None):
                    self.__vm_provisioning_wizard.disable_toggle(
                        label=self.__admin_console.props['label.autoSelectVMSize'])
                    self.__vm_provisioning_wizard.select_drop_down_values(id="vmSizeDropdown",
                                                                          values=[access_node_settings['VMSize']])
                if access_node_settings.get('ChooseSizeWithJob', False):
                    self.__vm_provisioning_wizard.enable_toggle(label=self.__admin_console.props[
                        'label.customSizeForJobLaunch'])

                else:
                    try:
                        self.__vm_provisioning_wizard.enable_toggle(
                            label=self.__admin_console.props['label.autoSelectVMSize'])
                    except ElementClickInterceptedException:
                        self.__admin_console.log.info("Auto VM Size toggle disabled due to Custom Image")

                if access_node_settings.get('CustomImage', None):
                    self.__vm_provisioning_wizard.enable_toggle(
                        label=self.__admin_console.props['label.createCustomImage'])

                    if self.__rtable_obj.is_entity_present_in_column(self.__admin_console.props['label.vmProvGlobalOS'],
                                                                     access_node_settings['CustomImage'][
                                                                         'CustomImageOS'].upper()):
                        self.__rtable_obj.select_rows([access_node_settings['CustomImage']['CustomImageOS'].upper()])
                        self.__vm_provisioning_wizard.click_button(
                            name=self.__admin_console.props['label.delete'].upper())

                    self.__vm_provisioning_wizard.click_button(name=self.__admin_console.props['label.add'])
                    custom_img_dialog = RModalDialog(self.__admin_console,
                                                     self.__admin_console.props['label.customImage'])
                    select_img_tree = TreeView(self.__admin_console, '(' + custom_img_dialog._dialog_xp + ')')
                    custom_img_path = access_node_settings['CustomImage']["CustomImageName"].split('/')

                    custom_img_dialog.select_radio_by_id(access_node_settings['CustomImage']['CustomImageOS'].lower())
                    for path_node in custom_img_path[:-1]:
                        select_img_tree.expand_node(path_node)
                        self.__admin_console.wait_for_completion()
                    select_img_tree.select_item_by_label(custom_img_path[-1])

                    custom_img_dialog.click_submit()

                else:
                    self.__vm_provisioning_wizard.disable_toggle(
                        label=self.__admin_console.props['label.createCustomImage'])

        if self.__vm_provisioning_options.get('AutoScaleMaxNoOfVMs', None):
            self.__vm_provisioning_wizard.fill_text_in_field(id='maxNoOfAccessNodes',
                                                             text=self.__vm_provisioning_options['AutoScaleMaxNoOfVMs'])

        if self.__vm_provisioning_options.get('AutoScaleNodeOS', None):
            self.__vm_provisioning_wizard.select_radio_button(label=self.__vm_provisioning_options['AutoScaleNodeOS'])

        self.__vm_provisioning_wizard.click_next()

    def domain_credential_settings(self):
        """

        """
        if self.__vm_provisioning_options.get("DomainSettings", None):
            self.__vm_provisioning_wizard.enable_toggle(label=self.__admin_console.props['label.addDomainCredentials'])
            domain_settings = self.__vm_provisioning_options['DomainSettings']

            try:
                self.__vm_provisioning_wizard.select_drop_down_values(id='credentials',
                                                                      values=[domain_settings['DomainCredName']])
            except NoSuchElementException:
                self.__admin_console.log.error("Credential with name {} could not be found, creating a new one"
                                               .format(domain_settings['DomainCredName']))

                self.__vm_provisioning_wizard.click_add_icon()

                if domain_settings.get('DomainCredDetail', None):
                    credential_dialog = RModalDialog(self.__admin_console,
                                                     self.__admin_console.props['label.addCredential'])

                    credential_dialog.fill_text_in_field('name', domain_settings['DomainCredName'])
                    credential_dialog.fill_text_in_field('userAccount', domain_settings['DomainCredDetail']['Username'])
                    credential_dialog.fill_text_in_field('password', domain_settings['DomainCredDetail']['Password'])
                    credential_dialog.click_submit()

                else:
                    self.__admin_console.log.error("Failed to get details for domain account from input, "
                                                   "please provide account details in input JSON")

            self.__vm_provisioning_wizard.fill_text_in_field(label=self.__admin_console.props['label.domainName'],
                                                             text=domain_settings['DomainName'])

            if domain_settings.get('OUPath', None):
                self.__vm_provisioning_wizard.fill_text_in_field(
                    label=self.__admin_console.props['label.organizationalPath'], text=domain_settings['OUPath'])

        self.__vm_provisioning_wizard.click_next()

    def advanced_settings(self):
        """

        """
        if self.__vm_provisioning_options.get('NetworkGateway', None):
            self.__vm_provisioning_wizard.fill_text_in_field(label=self.__admin_console.props['label.networkGateway'],
                                                             text=self.__vm_provisioning_options['NetworkGateway'])

        if self.__vm_provisioning_options.get('HypervisorName') == HypervisorDisplayName.AMAZON_AWS.value:
            self.__vm_provisioning_wizard.clear_text_in_field(label=self.__admin_console.props['label.userApproval'])

        for workflow_type, workflow in self.__vm_provisioning_options.get('Workflows', {}).items():
            self.__vm_provisioning_wizard.click_add_icon(index=0)
            workflow_dialog = RModalDialog(self.__admin_console, "Add workflow")

            workflow_dialog.select_dropdown_values(drop_down_id='workflowType', values=[workflow_type])
            workflow_dialog.select_dropdown_values(drop_down_id='workflow', values=[workflow])
            workflow_dialog.click_submit()

        for tag_name, tag_value in self.__vm_provisioning_options.get('Tags', {}).items():
            self.__vm_provisioning_wizard.click_add_icon(index=1)
            tag_dialog = RModalDialog(self.__admin_console, self.__admin_console.props['label.addTag'])

            tag_dialog.fill_text_in_field('key', tag_name)
            tag_dialog.fill_text_in_field('value', tag_value)
            tag_dialog.click_submit()

        self.__vm_provisioning_wizard.click_next()
