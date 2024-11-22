from selenium.webdriver.common.by import By
import time
from cvpysdk.commcell import Commcell
from AutomationUtils.cvtestcase import CVTestCase
from random import randint
from selenium.common.exceptions import NoSuchElementException
from Server.Security.securityhelper import SecurityHelper
from AutomationUtils.options_selector import OptionsSelector
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.Common.exceptions import CVTestCaseInitFailure
from Web.Common.page_object import TestStep, handle_testcase_exception
import datetime
from selenium.webdriver.common.keys import Keys
from Web.AdminConsole.Components.table import Rtable
from Web.AdminConsole.Components.dialog import RModalDialog
from Web.AdminConsole.Components.panel import RDropDown
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec
from selenium.common.exceptions import TimeoutException, ElementNotInteractableException

"""
This testcase is used to verify the user security associations in the adminconsole.
In adminconsole , we login as MSP admin and add associations to the msp user and user group and validate the Database for the association entries
The same steps are repeated as a tenant admin
Inputs : 
totalcount (int): number of association peruser optional
total_asc_perdialog (int): The number of associations to add when dialog is open . optional
tenant_admin_entities (list) :  Tenant admin entities
"""


class TestCase(CVTestCase):
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Verify add associations feature on commcell\company user\\user group from adminconsole"
        self.browser = None
        self.admin_console = None
        self.navigator = None
        self.tcinputs = {
        }
        self.option = None
        self.admin_page = None
        self.roles = None
        self.entity_types = ""
        self.securityhelper = None
        self.total_association_data = {
            "userdata": {}, "usergroupdata": {}
        }
        self.company = None

    def init_tc(self):
        """Initializes pre-requisites for this test case"""
        try:
            self.fl = True
            self.roles_obj = self.commcell.roles
            self.roles = list(self.commcell.roles.all_roles.keys())
            for i in range(len(self.roles)):
                self.roles[i] = self.roles[i].title()
            self.commcell_name = self.commcell.commserv_name
            self.mspentities = ["Alert", "Commcell", "Identity servers", "Media Agent", "Plan", "Role", "Server",
                                "Server group",
                                "User", "Usergroup", "Workflow"]
            self.tenant_admin_entities = self.tcinputs.get("tenant_admin_entities",
                                                           ["Alert", "Plan"])  # , "Role", "Server",
            self.entity_map = {
                "alertName": "Alert",
                "workflowName": "Workflow",
                "userGroupName": "Usergroup",
                "providerDomainName": "Identity servers",
                "userName": "User",
                'roleName': 'Role',
                'commCellName': 'Commcell',
                'clientGroupName': 'Server group',
                'clientName': 'Server',
                'planName': 'Plan'
            }
            self.dialog_open = True
            organizations = self.commcell.organizations
            company = "company_" + str(datetime.datetime.now())
            organizations.add(company, company + "@company.com", company, company)
            self.log.info("Organization created " + company)
            self.company = company
            self.passwd = self.inputJSONnode['commcell']['commcellPassword']
            self.tenant_admin = self.company + "\\" + self.company
            users = self.commcell.users
            users.refresh()
            admin_obj = users.get(self.tenant_admin)
            admin_obj.update_user_password(self.passwd, self.passwd)
        except Exception as exception:
            raise CVTestCaseInitFailure(exception)

    def wait_for_element_to_be_clickable(self, element_id, wait_time=30):
        try:
            WebDriverWait(self.admin_console.driver, wait_time).until(
                ec.element_to_be_clickable((By.XPATH, element_id)))
        except TimeoutException:
            raise Exception(f"Element id {element_id} is not clickable")

    def navigate_to_user(self, username):
        """Navigate to user from user page"""
        self.__table.access_link(username)
        try:
            frame = self.admin_console.driver.find_element(By.XPATH, "//*[@id='cc-iframe']")
            self.admin_console.driver.switch_to.frame(frame)
        except NoSuchElementException:
            pass
        self.wait_for_element_to_be_clickable("//a//span[text()='Associated entities']")
        self.admin_console.driver.find_element(By.XPATH, "//a//span[text()='Associated entities']").click()

    def type_and_select(self, value):
        """Type and select the value from dropdown"""
        elem = self.admin_console.driver.find_element(By.XPATH, 
            '//div//label[text()="Name"]//ancestor::div[@role="combobox"]//input')
        elem.send_keys(Keys.CONTROL, 'a')
        elem.send_keys(Keys.BACKSPACE)
        elem.send_keys(value)
        time.sleep(3)
        try:
            if self.admin_console.driver.find_element(By.XPATH, "//li[@id='autocomplete-option-0']"):
                self.wait_for_element_to_be_clickable("//li[@id='autocomplete-option-0']")
                elem = self.admin_console.driver.find_element(By.XPATH, "//li[@id='autocomplete-option-0']")
                if elem.text.lower() == value.lower():
                    elem.click()
                else:
                    elem = self.admin_console.driver.find_element(By.XPATH, "//li[@id='autocomplete-option-1']")
                    if elem.text.lower() == value.lower():
                        elem.click()
                    else:
                        self.log.info(f"Value {value} not present in both the options")
                        raise NoSuchElementException(value)
        except NoSuchElementException:
            self.log.info("Value not found : {}".format(value))
            raise Exception("Value wasn't present")

    def delete_and_type(self, element, value):
        """DELETE AND TYPE THE TEXT"""
        element.send_keys(Keys.CONTROL, 'a')
        element.send_keys(Keys.BACKSPACE)
        element.send_keys(value)

    def select_entity(self, entity, tenant_admin):
        """Select the entity from dropdown"""
        time.sleep(3)
        self.wait_for_element_to_be_clickable("//div[@id='entityType']//ancestor::div[contains(@class, 'dd-wrapper')]")
        self.admin_console.driver.find_element(By.XPATH, 
            "//div[@id='entityType']//ancestor::div[contains(@class, 'dd-wrapper')]").click()
        if not tenant_admin:
            time.sleep(3)
            inp = self.admin_console.driver.find_element(By.XPATH, "//input[@id='entityTypeSearchInput']")
            try:
                self.delete_and_type(inp, entity)
                time.sleep(3)
                xp = f".//ul//li/div/*[translate(text(),  'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz')='{entity.lower()}']"
                self.wait_for_element_to_be_clickable(xp)
                try:
                    self.admin_console.driver.find_element(By.XPATH, xp).click()
                except:
                    self.admin_console.driver.find_element(By.XPATH, 
                        "//div[@class='MuiListItemText-root']//span").click()
                time.sleep(3)
            except:
                self.admin_console.driver.find_element(By.XPATH, 
                    "//div[@id='entityType']//ancestor::div[contains(@class, 'dd-wrapper')]").click()
        else:
            xp = f".//ul//li/div/*[translate(text(),  'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz')='{entity.lower()}']"
            self.wait_for_element_to_be_clickable(xp)
            try:
                self.admin_console.driver.find_element(By.XPATH, xp).click()
            except:
                self.admin_console.driver.find_element(By.XPATH, "//div[@class='MuiListItemText-root']//span").click()
            time.sleep(3)

    def select_role(self, role):
        """SELECT THE ROLE FROM DROPDOWN"""
        self.admin_console.driver.find_element(By.XPATH, 
            "//div[@id='rolesList']//ancestor::div[contains(@class, 'dd-wrapper')]").click()
        time.sleep(2)
        try:
            try:
                inp = self.admin_console.driver.find_element(By.XPATH, "//input[@id='rolesListSearchInput']")
                self.delete_and_type(inp, role)
            except NoSuchElementException:
                pass
            time.sleep(2)
            xp = f".//ul//li/div/*[translate(text(),  'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz')='{role.lower()}']"
            self.wait_for_element_to_be_clickable(xp)
            try:
                self.admin_console.driver.find_element(By.XPATH, xp).click()
            except:
                self.admin_console.driver.find_element(By.XPATH, "//div[@class='MuiListItemText-root']//span").click()
            time.sleep(3)
        except Exception as e:
            self.log.error(e)
            self.admin_console.driver.find_element(By.XPATH, 
                "//div[@id='rolesList']//ancestor::div[contains(@class, 'dd-wrapper')]").click()

    def validate_db(self, user, flag, count, username):
        """VALIDATE THE DATABASE FOR THE ASSOCIATIONS"""
        flag = 1 if flag else 0
        col1, res = self.option.exec_commserv_query(
            f"""select entityType1,entityid1,roleid from UMSecurityAssociations where isuser={flag} and userOrGroupId={user}""")
        self.log.info("Total row count {}".format(len(res)))
        self.log.info("Added association count {}".format(count))
        if flag:
            data = self.total_association_data.get('userdata').get(username)
        else:
            data = self.total_association_data.get('usergroupdata').get(username)
        self.log.info("Entity data added for the user {} : {}".format(username, data))
        for i in data:
            self.log.info("fetching role id from cvpysdk {}".format(i))
            role_id = self.roles_obj.get(i[2]).role_id
            if i[0] == "Commcell":
                self.log.info(['1', '2', str(role_id)])
                if ['1', '2', str(role_id)] not in res:
                    raise Exception("DB validation failed for {} {}".format(i, ['1', '2', str(role_id)]))
            else:
                id_selector = self.object_map[i[0]][1]
                entity_id = eval(f"self.object_map[i[0]][0].get(i[1]).{id_selector}")
                if not [self.object_map[i[0]][2], str(entity_id), str(role_id)] in res:
                    if self.object_map[i[0]][2] == '61':
                        continue
                    raise Exception("DB validation failed for entry {} values {}".format(i, [self.object_map[i[0]][2],
                                                                                             str(entity_id),
                                                                                             str(role_id)]))
                self.log.info([self.object_map[i[0]][2], str(entity_id), str(role_id)])
        return res

    def add_association(self, entity, value, role, tenant_admin=False):
        """Add a single association after the dialog is open"""
        time.sleep(2)
        self.log.info("Adding assocation for Entity : {} Entity value : {} Role : {}".format(entity, value, role))
        try:
            self.select_entity(entity, tenant_admin)
            self.type_and_select(value)
            self.select_role(role)
            time.sleep(2)
            try:
                self.wait_for_element_to_be_clickable(
                    "//div[@class='entityAssociations-add']//button")
                self.admin_console.driver.find_element(By.XPATH, 
                    "//div[@class='entityAssociations-add']//button").click()
            except ElementNotInteractableException:
                self.log.info("Add button not clickable")
            try:
                if self.admin_console.driver.find_element(By.XPATH, 
                        "//div[contains(text(),'Association already exists!')]"):
                    self.log.info("Entity already exists")
                    return False
            except NoSuchElementException:
                return True
        except Exception as e:
            self.log.info(e)
            return False

    def click_save(self):
        """Click save button on the dialog of associations"""
        try:
            # If dialog is open and the save button is present
            if not self.fl and self.admin_console.driver.find_element(By.XPATH, "//button[@type='submit']"):
                disable = self.admin_console.driver.find_element(By.XPATH, "//button[@type='submit']").get_attribute(
                    "disabled")
                if not disable:
                    self.wait_for_element_to_be_clickable("//button[@type='submit']")
                    self.admin_console.driver.find_element(By.XPATH, "//button[@type='submit']").click()
                    self.fl = True
                    self.admin_console.unswitch_to_react_frame()
                    try:
                        WebDriverWait(self.driver, 5).until(ec.presence_of_element_located((
                            By.XPATH, "//div[@class='growl']/div/div/div")))
                        notification_text = self.driver.find_element(By.XPATH, 
                            "//div[@class='growl']/div/div/div").text
                        if not notification_text:
                            WebDriverWait(self.driver, 5).until(ec.presence_of_element_located((
                                By.XPATH, "//div[@class='growl']/div/div/div")))
                            notification_text = self.driver.find_element(By.XPATH, 
                                "//div[@class='growl']/div/div/div").text
                        if notification_text != "":
                            self.log.info("Message : {}".format(notification_text))
                    except TimeoutException:
                        return ""
                else:
                    raise NoSuchElementException("element not found save button")
        except NoSuchElementException:
            self.log.error("Save button not clickable")
            self.wait_for_element_to_be_clickable("//div[normalize-space()='Cancel']")  # Click cancel button
            self.admin_console.driver.find_element(By.XPATH, "//div[normalize-space()='Cancel']").click()
            self.fl = True

    def add_multi_association(self, is_user, data, tenant_admin=False):
        """Add the association to the user and validate the DB
            is_user : True if its a user
            data : (list) Users or Usergroup
            tenant_admin : (boolean) True if the user is a tenant admin
        """
        if is_user:
            self.navigator.navigate_to_users()
        else:
            self.navigator.navigate_to_user_groups()
        if not tenant_admin:
            entity_list = self.mspentities
        else:
            entity_list = self.tenant_admin_entities
        for i in data:
            try:
                self.log.info("Moving to the {} user's page".format(i))
                self.navigate_to_user(i)
                total_count = self.tcinputs.get('totalcount', 1)
                count = 0
                self.admin_console.wait_for_completion()
                currentrows = self.__table.get_total_rows_count()
                user_id = self.admin_console.driver.current_url.split("/")[6]
                association_input = []
                try:
                    association_input = self.securityhelper.generate_random_entity_dict(no_of_assoc=total_count * 1)
                except Exception as e:
                    self.log.info(e)
                association_count = 0
                log_count = 0
                while count < total_count:
                    self.log.info("Count : {}".format(count))
                    if self.fl:
                        self.admin_console.wait_for_completion(wait_time=600)
                        time.sleep(6)
                        self.__table.access_toolbar_menu("Add association")
                        self.fl = False  # Dialog opened
                    entity = ''
                    assoc = ''
                    entity_name = ''
                    role = ''
                    if association_count < len(association_input):
                        # If the association generated is enough
                        entity = self.entity_map.get(list(association_input.get(f'assoc{association_count}').keys())[0])
                        if entity and (entity in entity_list):
                            entity_name = association_input.get(f'assoc{association_count}').get(
                                list(association_input.get(f'assoc{association_count}').keys())[0])[0]
                            role = association_input.get(f'assoc{association_count}').get('role')[0].title()
                            log_count = association_count
                    else:
                        self.log.info("Single entity creation")
                        assoc = None
                        try:
                            assoc = self.securityhelper.generate_random_entity_dict()
                        except Exception as e:
                            self.log.info(e)
                        if assoc:
                            entity = self.entity_map.get(list(assoc.get('assoc0').keys())[0])
                            if entity and (entity in entity_list):
                                entity_name_list = assoc.get('assoc0').get(list(assoc.get('assoc0').keys())[0])
                                entity_name = entity_name_list[0]
                                role = assoc.get('assoc0').get('role')[0]
                                log_count = 0
                    if entity and entity_name and role:
                        # IF the entity , entity and role all the valid according to the specification
                        flag = self.add_association(entity, entity_name, role, tenant_admin)
                        if flag:
                            count += 1
                            if is_user:
                                if i in self.total_association_data['userdata']:
                                    self.total_association_data['userdata'][i].append([entity, entity_name, role])
                                else:
                                    self.total_association_data['userdata'][i] = [[entity, entity_name, role]]
                            else:
                                if i in self.total_association_data['usergroupdata']:
                                    self.total_association_data['usergroupdata'][i].append([entity, entity_name, role])
                                else:
                                    self.total_association_data['usergroupdata'][i] = [[entity, entity_name, role]]
                        else:
                            self.log.error("Could not add the association in UI : {}".format(
                                association_input[f'assoc{log_count}']))
                            # raise Exception("Could not add the association in UI : {}".format(association_input[f'assoc{association_count}']))
                    else:
                        association_count += 1
                        continue
                    if count and count % self.tcinputs.get("total_asc_perdialog", 2) == 0 and not self.fl:
                        self.click_save()
                    association_count += 1
                self.click_save()
                self.admin_console.wait_for_completion()
                totalrows = self.__table.get_total_rows_count()
                if total_count > (totalrows - currentrows):
                    self.log.error("Some of the association failed in backend with a toast message")
                self.validate_db(user_id, is_user, totalrows - currentrows, i)
                time.sleep(3)
                if is_user:
                    self.log.info("Moving to the users page")
                    self.navigator.navigate_to_users()
                else:
                    self.log.info("Moving to usergroups page")
                    self.navigator.navigate_to_user_groups()
            except Exception as e:
                raise Exception(e)
        self.fl = True
        self.log.info("Add association completed")

    def cleanup(self):
        """DELETE THE ENTITIES CREATED """
        self.commcell = Commcell(self.inputJSONnode['commcell']['webconsoleHostname'],
                                 self.inputJSONnode['commcell']['commcellUsername'],
                                 self.inputJSONnode['commcell']['commcellPassword'])
        organizations = self.commcell.organizations
        company = organizations.get(self.company)
        company.deactivate()
        organizations.delete(self.company)
        users = self.commcell.users
        users.delete(self.user_list[1], new_user=self.inputJSONnode['commcell']['commcellUsername'])
        usergrps = self.commcell.user_groups
        usergrps.delete(self.usergroup_list[1], new_user=self.inputJSONnode['commcell']['commcellUsername'])

    def create_user_usergroups(self):
        """Create the user and groups for the association addition"""
        users = self.commcell.users
        company_user = self.company + "\\company_user"
        users.add(company_user, company_user + "company.com", password=self.passwd)
        usergroups = self.commcell.user_groups
        company_user_group = self.company + "\\company_usergroup"
        usergroups.add(company_user_group)
        local_user = "temp_user" + str(randint(0, 1000))
        local_usergrp = "temp_usergrp" + str(randint(0, 1000))
        usergroups.add(local_usergrp)
        users.add(local_user, local_user + "company.com", password=self.passwd)
        self.user_list = [company_user, local_user]
        self.usergroup_list = [company_user_group, local_usergrp]

    def run_tc(self, username, password, user, usergroup, tenant_admin=False):
        """Login to adminconsole to validate the user and usergroup association"""
        self.option = OptionsSelector(self.commcell)
        self.browser = BrowserFactory().create_browser_object()
        self.browser.open()
        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
        self.admin_console.login(username=username,
                                 password=password, stay_logged_in=True)
        self.commcell = Commcell(self.commcell.webconsole_hostname, username, password)
        self.object_map = {
            "Alert": [self.commcell.alerts, "alert_id", '64'],
            "Workflow": [self.commcell.workflows, "workflow_id", '83'],
            "Usergroup": [self.commcell.user_groups, "user_group_id", '15'],
            "Identity servers": [self.commcell.domains, "domain_id", '61'],
            "User": [self.commcell.users, "user_id", '13'],
            'Role': [self.commcell.roles, "role_id", '120'],
            'Commcell': [self.commcell, "commcell_id", '1'],
            'Server group': [self.commcell.client_groups, "clientgroup_id", '28'],
            'Server': [self.commcell.clients, "client_id", '3'],
            'Plan': [self.commcell.plans, "plan_id", "158"]
        }
        self.navigator = self.admin_console.navigator
        self.__table = Rtable(self.admin_console)
        self.securityhelper = SecurityHelper(self.commcell)
        self.driver = self.admin_console.driver
        self._dialog = RModalDialog(self.admin_console)
        self.__drop_down = RDropDown(self.admin_console)
        self.add_multi_association(True, [user], tenant_admin)
        self.add_multi_association(False, [usergroup], tenant_admin)
        self.admin_console.logout_silently(self.admin_console)

    def run(self):
        try:
            self.init_tc()
            self.create_user_usergroups()
            user_list = self.user_list
            usergroup_list = self.usergroup_list
            self.run_tc(self.inputJSONnode['commcell']['commcellUsername'],
                        self.inputJSONnode['commcell']['commcellPassword'], user_list[1], usergroup_list[1], False)
            self.run_tc(self.tenant_admin,
                        self.inputJSONnode['commcell']['commcellPassword'], user_list[0], usergroup_list[0], True)
        except Exception as e:
            raise Exception(e)
        finally:
            Browser.close_silently(self.browser)
            self.cleanup()
