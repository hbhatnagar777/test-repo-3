from selenium.webdriver.common.by import By
"""
This module provides the function or operations that can be used to run
basic operations on security page.

To initialize the class variables, pass the instance object to the appropriate
definition of AdminConsoleInfo

Call the required definition using the instance object, with no arguments to
be passed, only the flags needs to be passed into the method call while calling
the member function.

Class:

   SecurityMain() -> Roles() -> object()

        __init__()

Functions:

add_security_role()                         -- Adds a security role
edit_security_role()                        -- Edits a security role
delete_security_role()                      -- Delete a security role
verify_permissions()                        -- Verifies permissions are selected/deselected
verify_enable_role_and_visible_to_all()     -- Verifies state of enable role
                                               and visible to all checkboxes
get_available_permissions()                 -- Gets all available permissions
_generate_sample_list()                     -- Gets a random selection of elements from
                                               the given list
_generate_random_categories()               -- Generates a random list of categories
generate_random_permissions()               -- Generates a random list of permissions
roles_lookup()                              -- looks up roles listed in various places in the CC
"""
from Web.AdminConsole.GlobalConfigManager import constants
from AutomationUtils import logger
from Web.AdminConsole.AdminConsolePages.Roles import Roles
from random import choice, sample, randint
from Web.Common.exceptions import CVWebAutomationException
from Web.AdminConsole.Components.table import Rtable
from Web.AdminConsole.Components.panel import RPanelInfo, RDropDown
import time, random
from Web.Common.page_object import PageService
from Web.AdminConsole.AdminConsolePages import Companies, Users


class RolesMain:
    """
        Helper for securities page
    """

    def __init__(self, admin_console=None, commcell=None, csdb=None):
        """
            Initializes the security helper module
            :param
                admin_console -- the admin_console object
                commcell -- comcell object
                csdb -- csdb object
        """
        self.driver = admin_console.driver
        self.__admin_console = admin_console
        self.__navigator = admin_console.navigator
        self.__roles = Roles(admin_console)
        self.csdb = csdb
        self.commcell = commcell
        self.log = logger.get_log()
        if not self.driver:
            raise Exception('Driver is not provided')
        self._role_name = None
        self._new_role_name = None
        self._list_of_permissions = None
        self._list_of_permissions_to_edit = None
        self.roles_obj = None
        self.service_commcells = None

        self._enable_role = True
        self._visible_to_all = False
        self._all_permissions = None
        self.__rpanel = RPanelInfo(admin_console, "Permissions")
        self.__rtable = Rtable(admin_console)
        self.random_string = str(time.time()).split('.')[0]
        self.__company = Companies.Companies(admin_console)
        self.__rdropdown = RDropDown(self.__admin_console)
        self.__user = Users.Users(self.__admin_console)

    @property
    def role_name(self):
        """ Gets the role name"""
        return self._role_name

    @role_name.setter
    def role_name(self, value):
        """ Sets the role_name"""
        self._role_name = value

    @property
    def new_role_name(self):
        """ Gets the role name"""
        return self._new_role_name

    @new_role_name.setter
    def new_role_name(self, value):
        """ Sets the role_name"""
        self._new_role_name = value

    @property
    def enable_role(self):
        """ Gets the list of permissions used while editing the role"""
        return self._enable_role

    @enable_role.setter
    def enable_role(self, value):
        """ Sets the list of permissions used while editing the role"""
        self._enable_role = value

    @property
    def visible_to_all(self):
        """ Gets the list of permissions used while editing the role"""
        return self._visible_to_all

    @visible_to_all.setter
    def visible_to_all(self, value):
        """ Sets the list of permissions used while editing the role"""
        self._visible_to_all = value

    def add_security_roles(self, number_of_permissions, negative_case=False):
        """
        Adds the security roles

        Args:
            negative_case   (bool)  -   if True, will test negative scenario also
        """
        self.roles_obj = Roles(self.__admin_console)
        self.__navigator.navigate_to_roles()
        self.__admin_console.wait_for_completion()

        self.get_available_permissions()
        self._list_of_permissions = self.generate_random_permissions(number_of_permissions)

        if self.__roles.is_role_exists(self.role_name):
            self.log.info("Role already exists")
            return
        self.roles_obj.add_role(
            self.role_name,
            self._list_of_permissions,
            self.enable_role,
            self.visible_to_all,
            service_commcells=self.service_commcells
        )
        self.csdb.execute(f"SELECT NAME FROM UMROLES WHERE NAME = '{self.role_name}'")
        if not [roles[0] for roles in self.csdb.fetch_all_rows() if roles[0] != '']:
            raise CVWebAutomationException('[DB] Role not found in database after creation')
        if negative_case:
            self.log.info("Validating negative case adding existing role name")
            self.__navigator.navigate_to_roles()
            try:
                self.roles_obj.add_role(self.role_name, self._list_of_permissions)
                raise Exception("Expected alert for existing role, got no errors")
            except Exception as exp:
                if 'already in use' in str(exp).lower() and self.role_name.lower() in str(exp).lower():
                    self.log.info("Validated negative role creation case successfully")
                else:
                    self.log.info(f"Got different error: {exp}")
                    raise exp
            self.__admin_console.refresh_page()

    def create_gcm(self, service_commcell=None) -> str:
        """Test"""
        self.role_name = f"GCMRoles{self.random_string}"
        self.visible_to_all = None
        if service_commcell:
            self.service_commcells = service_commcell
        else:
            self.service_commcells = ['All']

        self.add_security_roles(2)
        return self.role_name + constants.GLOBAL_ENTITIES_EXT

    def edit_security_role(self, number_of_permissions, negative_case=False):
        """
        Edits the security role

        Args:
            negative_case   (bool)  -   if True, will test negative scenario also
        """
        if negative_case:
            self.log.info("Validating negative case updating existing role name")
            self.__navigator.navigate_to_roles()
            existing_role_name = 'Master'
            try:
                self.__roles.edit_role(self.role_name, existing_role_name)
                raise Exception("Expected alert for existing role, got no errors")
            except Exception as exp:
                if 'already in use' in str(exp).lower() and existing_role_name.lower() in str(exp).lower():
                    self.log.info("Validated negative role updation case successfully")
                else:
                    self.log.info(f"Got different error: {exp}")
                    raise exp
            self.__admin_console.refresh_page()

        self.__navigator.navigate_to_roles()
        edit_roles = dict()
        edit_roles["Add"] = self.generate_random_permissions(
            number_of_permissions, negatives=self._list_of_permissions
        )
        edit_roles["Remove"] = self._list_of_permissions

        self.__roles.edit_role(self.role_name, self.new_role_name, edit_roles)
        self._list_of_permissions = edit_roles["Add"]

    def delete_security_role(self):
        """ Deletes the security role """
        self.driver.back()
        self.__admin_console.wait_for_completion()
        self.roles_obj.action_delete_role(self.new_role_name)

        if self.__roles.is_role_exists(self.new_role_name):
            raise Exception(f"Role {self.new_role_name} was not deleted")
        else:
            self.log.info(f"Role {self.new_role_name} is successfully deleted")

    def validate_security_role(self):
        """Validate security role."""
        self.__navigator.navigate_to_roles()
        self.__roles.select_role(self.role_name)
        displayed_permissions_list = []
        for category, permissions_list in self.__roles.get_permissions_tree().items():
            displayed_permissions_list += permissions_list

        for permission in self._list_of_permissions:
            if permission not in displayed_permissions_list:
                self.log.error(f'expected: {self._list_of_permissions}')
                self.log.error(f'got {displayed_permissions_list}')
                raise Exception("Selected permission is not in the displayed permissions list")

    def verify_permissions(self, permissions, status="added"):
        """
        Method to validate permissions added/removed to the role.

        permissions (list): List of permissions to verify
        status       (str): Pass as "added" or "removed" to verify
                            if permissions are added or removed
        """

        self.roles_obj.checkbox_select("showSelected")

        for permission in permissions:

            if isinstance(permission, str):

                if 'Operations on Storage Policy' in permission:
                    permission = "Operations on Storage Policy \\  Copy"

                if status.lower() == "added":
                    self.log.info(f"Checking if permission {permission} is {status}")
                    if not self.roles_obj.check_if_entity_exists("xpath",
                                                                 f"//div[@title='{permission}']"):
                        raise Exception(f"The chosen permission {permission} was not associated with the role."
                                        " Please check the logs.")

                elif status.lower() == "removed":
                    self.log.info(f"Checking if permission {permission} is {status}")
                    if self.roles_obj.check_if_entity_exists("xpath",
                                                             f"//div[@title='{permission}']"):
                        raise Exception(f"The permission {permission} to be removed is still associated "
                                        "with the role. Please check the logs.")

            elif isinstance(permission, dict):

                for key, value in permission.items():

                    self.verify_permissions(value, status)

    def verify_enable_role_and_visible_to_all(self):
        """
        Method to validate state of "enable role" and "visible to all"
            checkboxes against setter values
        """
        enable_role_status = self.driver.find_element(By.XPATH, 
            "//input[@id='rolesEnabled']").is_selected()
        visible_to_all_status = self.driver.find_element(By.XPATH, 
            "//input[@id='visibleToAll']").is_selected()

        if not(self.enable_role == enable_role_status):
            raise Exception("Enable role does not match input.")

        if not (self.visible_to_all == visible_to_all_status):
                raise Exception("Visible to all does not match input.")

    def get_available_permissions(self):
        """ Get all categories and permissions listed on the add role pane """
        self._all_permissions = self.commcell.roles.get('Tenant Admin').permissions['permission_list'][:80:]

    def _generate_sample_list(self, source_list):
        """Generates a sample with random elements from the given list

        Args:
            source_list (list): List of any items from which you need a random sample

        Returns:
            sample_list(list) : List of random items
        """
        list_length = len(source_list)
        no_of_items = choice(range(0, list_length))
        sample_list = sample(source_list, no_of_items)
        return sample_list

    def _generate_random_categories(self):
        """Generates a list of random categories to be selected"""
        all_categories = []
        for item in self._all_permissions:
            for key, value in item.items():
                all_categories.append(key)

        self._all_categories = self._generate_sample_list(all_categories)

    def generate_random_permissions(self, no_of_permissions, all_permissions=None, negatives=None):
        """Generates a list of random permissions to be selected

        Args:
            no_of_permissions   (int)   -   number of random permissions

            all_permissions (list): List of permissions from which random permissions are
                                    to be selected
                             E.g.[
                                    "Access Policies",
                                    {"Developer Tools":["Workflow",
                                                        {"Datasource":["Add Datasource",
                                                                        "Edit Datasource"]
                                                        }]
                                    },
                                    {"Monitoring Policy":["Edit Monitoring Policy",
                                                          "Search Share"]
                                    }
                                ]
            negatives   (list): List of permissions to avoid

        Returns:
                random_list (list) : List of random permissions
        """
        if not all_permissions:
            all_permissions = self._all_permissions
        if negatives:
            all_permissions = list(set(all_permissions) - set(negatives))

        sample_list = sample(all_permissions, no_of_permissions)
        return sample_list

    @PageService()
    def __get_data_for_validation(self, query, company_name):
        """Fetches the role data from UI and DB for validation purpose"""
        self.__roles.reset_filters() # clear filters before fetching data
        self.csdb.execute(query)
        db_data = {roles[0] for roles in self.csdb.fetch_all_rows() if roles[0] != ''}
        ui_data = set(self.__roles.list_roles(company_name))
        
        if db_data != ui_data:
            self.log.info(f'DB Roles : {sorted(db_data)}')
            self.log.info(f'UI Roles : {sorted(ui_data)}')
            data_missing_from_ui = db_data - ui_data
            extra_entities_on_ui = ui_data - db_data
            raise CVWebAutomationException(f'Mismatch found between UI and DB\nData missing from UI : {data_missing_from_ui}\
                                           Extra entities on UI : {extra_entities_on_ui}')
        self.log.info('Validation completed')
    
    @PageService()
    def validate_listing_company_filter(self):
        """Method to validate company filter"""
        self.log.info(f"Validating company filter..")
        self.__navigator.navigate_to_roles()

        self.__get_data_for_validation(query= 'SELECT NAME FROM UMROLES WHERE FLAGS&0X004 = 0', company_name= 'All')
        self.__get_data_for_validation(query= 'SELECT NAME FROM UMROLES WHERE FLAGS&0X004 = 0 AND ID NOT IN (SELECT ENTITYID FROM APP_COMPANYENTITIES WHERE ENTITYTYPE = 120)', company_name= 'CommCell')

        self.csdb.execute('SELECT ID, HOSTNAME FROM UMDSPROVIDERS WHERE SERVICETYPE=5 AND ENABLED=1 AND FLAGS=0')
        company_details = self.csdb.fetch_all_rows()
        if len(company_details) > 5: company_details = sample(company_details, 5)
        for id, company_name in company_details:
            self.__get_data_for_validation(query= f"SELECT NAME FROM UMROLES WHERE FLAGS&0X004 = 0 AND ID IN (SELECT ENTITYID FROM APP_COMPANYENTITIES WHERE ENTITYTYPE = 120 AND COMPANYID = {id})",
                                           company_name= company_name)
        self.log.info("Company filter validation completed")
    
    @PageService()
    def validate_listing_role_deletion(self, role_name=None):
        """Method to validate the role deletion"""
        if not role_name:
            role_name = f"DEL Automated Role - {str(randint(0, 100000))}"
            self.commcell.roles.add(role_name, sample(self.commcell.roles.get(role_name= 'Tenant Admin').permissions['permission_list'], 10))
        self.log.info("Validating role deletion..")
        self.__navigator.navigate_to_roles()
        self.__roles.action_delete_role(role_name= role_name)

        self.driver.implicitly_wait(10)
        if self.__roles.is_role_exists(role_name):
            raise CVWebAutomationException('[UI] Role found on ui after deletion')

        self.csdb.execute(f"SELECT NAME FROM UMROLES WHERE NAME = '{role_name}'")
        if [roles[0] for roles in self.csdb.fetch_all_rows() if roles[0] != '']:
            raise CVWebAutomationException('[DB] Role found in database after deletion')
        self.driver.implicitly_wait(0)
        self.log.info('Delete role validation completed')
        
    @PageService()
    def validate_listing_edit_role_name(self, old_name=None, new_name=None, delete_flag=False):
        """Method to validate edit role name"""
        if not old_name:
            old_name, new_name = (
                f"DEL Automated role - {str(randint(0, 100000))}",
                f"DEL Automated role - {str(randint(0, 100000))}",
            )
            permissions = sample(self.commcell.roles.get(role_name= 'Tenant Admin').permissions['permission_list'], 5)
            self.log.info(f'Creating role with permissions : {permissions}')
            self.commcell.roles.add(old_name, permissions)
        self.log.info("Validating edit role name...")
        self.__navigator.navigate_to_roles()
        self.__roles.select_role(old_name)
        self.__roles.edit_role_name(new_name)
        self.__admin_console.wait_for_completion()
        self.__navigator.navigate_to_roles()

        if self.__roles.is_role_exists(old_name):
            raise CVWebAutomationException('[UI] Old role name is showing up on UI')

        if not self.__roles.is_role_exists(new_name):
            raise CVWebAutomationException('[UI] New role name is not showing up on UI')
        self.commcell.roles.refresh()
        if delete_flag:
            self.commcell.roles.delete(new_name)
        self.log.info('Edit role name validation completed')
        
    @PageService()
    def validate_listing_simple_role_creation(self, role_name= None, permissions= None):
        """Method to validate role creation"""
        if not role_name:
            role_name = f"DEL Automated - {str(randint(0, 100000))}"
            permissions = sample(self.commcell.roles.get(role_name= 'Tenant Admin').permissions['permission_list'], 10)
        self.log.info("Validating role creation...")
        self.__navigator.navigate_to_roles()
        self.__roles.add_role(role_name, permissions= permissions)
        self.__admin_console.wait_for_completion()
        self.log.info("Role created successfully...")
        self.__navigator.navigate_to_roles()

        self.csdb.execute(f"SELECT NAME FROM UMROLES WHERE NAME = '{role_name}'")
        if not [roles[0] for roles in self.csdb.fetch_all_rows() if roles[0] != '']:
            raise CVWebAutomationException('[DB] Role not found in database after creation')

        if not self.__roles.is_role_exists(role_name):
            raise CVWebAutomationException('[UI] Role not found on UI after creation')
        self.commcell.roles.refresh()
        self.commcell.roles.delete(role_name)
        self.log.info('Create Role validation completed')

    @PageService()
    def listing_page_search(self, role_name):
        """Method to validate a role in listing page"""
        self.__navigator.navigate_to_roles()
        if self.__roles.is_role_exists(role_name):
            self.log.info('listing page search validation completed for the role')
        else:
            raise CVWebAutomationException('role not listed in listing page')

    def __get_roles_from_panel(self, panel_name: str, role: str) -> list:
        """
        Retrieves roles from a specified panel in admin console.

        Args:
            panel_name (str): The name of the panel to navigate to (e.g., 'Operators', 'Security').
            role (str)      : The role name to search for within the roles dropdown.

        Returns:
            list: A list of roles found in the specified panel's dropdown.
        """
        RPanelInfo(self.__admin_console).edit_tile(panel_name)
        roles = self.__rdropdown.get_values_of_drop_down(drop_down_label='Roles', search=role)
        if not roles:
            raise CVWebAutomationException(
                f'{role} not listed in the roles dropdown for entity type COMPANY in {panel_name} panel')
        self.__admin_console.click_button_using_text(self.__admin_console.props['action.cancel'])
        return roles

    def roles_lookup(self, entity_type: str, role: str, entity_name: str = None) -> list:
        """
        Method to look up roles listed in various places in the CC.

        Args:
            entity_type (str)   : The type of entity ('COMPANY' or 'USER').
            role (str)          : The role name to search for within the roles dropdown.
            entity_name (str)   : The name of the entity. If not provided, a random entity will be chosen.

        Returns:
            list: A list of roles found in the dropdowns.
        """
        self.log.info(f"Starting roles lookup for entity_type: {entity_type}")

        if entity_type.upper() == 'COMPANY':
            self.__navigator.navigate_to_company()
            if not entity_name:
                entity_name = random.choice(self.__company.get_active_companies())
            self.__company.access_company(entity_name)

            # Fetch roles from both panels
            roles_list = self.__get_roles_from_panel(self.__admin_console.props['label.operators'], role) + \
                         self.__get_roles_from_panel(self.__admin_console.props['label.nav.security'], role)
            roles_list = sum(([item] if not isinstance(item, list) else item for item in roles_list), [])

        elif entity_type.upper() == 'USER':
            self.__navigator.navigate_to_users()
            if not entity_name:
                entity_name = random.choice(self.__user.list_users())
            self.__user.open_user(entity_name)
            self.__admin_console.access_tab(self.__admin_console.props['label.user.AssociatedEntities'])
            self.__admin_console.click_button_using_text(self.__admin_console.props['pageHeader.addEntityAssociation'])
            self.__rdropdown.select_drop_down_values(drop_down_label='Entity type', values=['Commcell'])
            self.__rdropdown.select_drop_down_values(values=["Commcell"], drop_down_id='entityTypeHierarchy')
            roles_list = self.__rdropdown.get_values_of_drop_down(drop_down_label='Roles', search=role)
            if not roles_list:
                raise CVWebAutomationException(
                    f'{role} not listed in the regions dropdown for entity type {entity_type}')
            self.__admin_console.click_button_using_text(self.__admin_console.props['action.cancel'])

        else:
            raise ValueError("Invalid entity type")

        return roles_list
