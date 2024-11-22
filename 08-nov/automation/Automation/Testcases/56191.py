# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()      --  initialize TestCase class

    setup()         --  setup function of this test case

    run()           --  run function of this test case

    tear_down()     --  tear down function of this test case

"""
import calendar
import time

from cvpysdk.exception import SDKException
from cvpysdk.commcell import Commcell
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from Server.Security.userhelper import UserHelper
from Server.Security.securityhelper import RoleHelper
from dynamicindex.utils import constants as dynamic_constants


class TestCase(CVTestCase):
    """Class for executing this test case"""

    def __init__(self):
        """Initializes test case class object

            Properties to be initialized:

                name            (str)       --  name of this test case

                tcinputs        (dict)      --  test case inputs with input name as dict key
                                                and value as input type

        """
        super(TestCase, self).__init__()
        self.datasource_type = dynamic_constants.OPEN_DATASOURCE_DSTYPE
        self.name = "DM2 - OwnershipTransfer - Verify handler Creation & Deletion after transfer in Open datasource"

        self.properties = None
        self.timestamp = None
        self.commcell_obj = None
        self.user_helper = None
        self.role_helper = None
        self.role_obj = None
        self.user_obj = None
        self.share_user_obj = None
        self.new_user_obj = None
        self.security_dict = None
        self.user_commcell = None
        self.new_user_commcell = None
        self.share_user_commcell = None
        self.datasource_id = None
        self.datasource_obj = None
        self.schema = []
        self.total_crawlcount = 0
        self.input_data = []
        self.user = None
        self.new_user = None
        self.share_user = None
        self.password = "Pass_56191"
        self.role_name = None
        self.handler_obj = None
        self.handler_name = None
        self.permission_list = dynamic_constants.DCUBE_USER_PERMISSION_LIST
        self.tcinputs = {
            "DataSourcename": None,
            "IndexServer": None,
            "Column": None
        }

    def setup(self):
        """Setup function of this test case"""
        self.commcell_obj = self._commcell
        self.user_helper = UserHelper(self.commcell_obj)
        self.timestamp = calendar.timegm(time.gmtime())
        self.role_helper = RoleHelper(self.commcell_obj)
        self.role_name = f"Dm2OwnershipRole_{self.timestamp}"
        self.user = f"TestUser1_56191_{self.timestamp}"
        self.new_user = f"TestUser2_56191_{self.timestamp}"
        self.share_user = f"TestUser3_56191_{self.timestamp}"
        self.handler_name = f"Handler1_{self.timestamp}"
        self.role_obj = self.role_helper.create_role(self.role_name,
                                                     self.permission_list, None, False, False)
        self.security_dict = {'assoc1': {
            'commCellName': [self.commcell_obj.commserv_name],
            'role': [self.role_name]
        }}

        self.log.info("Security association Prepared : %s", str(self.security_dict))

        self.user_helper.create_user(
            user_name=self.user, email=f"test{self.id}_1_{self.timestamp}@test.com", full_name="Test User Created by Dm2 Automation",
            password=self.password, security_dict=self.security_dict)

        self.user_helper.create_user(
            user_name=self.new_user, email=f"test{self.id}_2_{self.timestamp}@test.com", full_name="Test User Created by Dm2 Automation",
            password=self.password, security_dict=self.security_dict)

        self.user_helper.create_user(
            user_name=self.share_user, email=f"test{self.id}_3_{self.timestamp}@test.com", full_name="Test User Created by Dm2 Automation",
            password=self.password, security_dict=self.security_dict)

        self.log.info("Trying to get New commcell object for created user1 : %s", str(self.user))
        self.user_commcell = Commcell(self.inputJSONnode['commcell']['webconsoleHostname'], self.user, self.password)

        self.tcinputs['DataSourcename'] = self.tcinputs['DataSourcename'] + \
            str(self.timestamp)
        self.log.info("Going to create Open Datasource via Rest API : %s",
                      str(self.tcinputs['DataSourcename']))
        prop_name = ['candelete', 'appname']
        prop_value = ["true", "DATACUBE"]
        self.properties = [{"propertyName": prop_name[x], "propertyValue": prop_value[x]}
                           for x in range(0, len(prop_name))]
        self.user_commcell.datacube.datasources.add(
            self.tcinputs['DataSourcename'],
            self.tcinputs['IndexServer'],
            self.datasource_type, self.properties)
        self.log.info("Open datasource created successfully")

        self.datasource_obj = self.user_commcell.datacube.datasources.get(
            self.tcinputs['DataSourcename'])

        self.datasource_id = self.datasource_obj.datasource_id
        self.log.info("Created DataSource id : %s", str(self.datasource_id))

        Fieldnames = self.tcinputs['Column'].split(",")
        fieldlist = {
            "fieldName": "",
            "type": "string",
            "indexed": True,
            "stored": True,
            "multiValued": False,
            "searchDefault": True,
            "autocomplete": False
        }
        for x in Fieldnames:
            fieldlist['fieldName'] = x
            self.schema.append((fieldlist))
            self.log.info("Schema formed : %s", str(self.schema))
            self.log.info("Calling update schema API to create column : %s", str(x))
            self.datasource_obj.update_datasource_schema(self.schema)
            self.schema.clear()

        self.log.info("Calling import data on this datasource")
        for x in range(10):
            fieldlist = {
                Fieldnames[0]: str(x),
                Fieldnames[1]: "DatacubeAutomationUser_" + str(x)
            }
            self.total_crawlcount = self.total_crawlcount + 1
            self.input_data.append((fieldlist))

        self.log.info("Import Data formed : %s", str(self.input_data))
        self.datasource_obj.import_data(self.input_data)
        self.log.info("Import Data done successfully")
        self.log.info("Total document count : %s", str(self.total_crawlcount))
        self.log.info("Going to create new handler : %s", self.handler_name)
        self.datasource_obj.ds_handlers.add(self.handler_name, search_query=['*'])
        self.log.info("Execute the newly created handler to get data from this datasource")
        self.handler_obj = self.datasource_obj.ds_handlers.get(self.handler_name)
        response_out = self.handler_obj.get_handler_data(handler_filter=dynamic_constants.SOLR_FETCH_ONE_ROW)
        self.log.info("Handler Data  : %s", str(response_out))
        total_docs = response_out['numFound']
        if self.total_crawlcount != int(total_docs):
            self.log.info("Handler returned wrong number of docs")
            raise Exception("Handler document count mismatched. Actual {0} Expected {1}"
                            .format(total_docs, self.total_crawlcount))
        self.log.info("Total crawl count and Handler execution count matched %s", str(total_docs))

    def run(self):
        """Run function of this test case"""
        try:
            self.log.info("Going to do ownership transfer by deleting the user")
            self.user_helper.delete_user(user_name=self.user, new_user=self.new_user)
            self.log.info("Get commcell object for new user")
            self.new_user_commcell = Commcell(
                self.inputJSONnode['commcell']['webconsoleHostname'], self.new_user, self.password)
            self.log.info("------------------------- Ownership Transfer verification starts--------------------------")
            if not self.new_user_commcell.datacube.datasources.has_datasource(self.tcinputs['DataSourcename']):
                raise Exception("New user doesn't have datasource associated")
            self.log.info("New user have datasource associated as : %s", self.tcinputs['DataSourcename'])
            self.log.info("Execute handler created by old user : %s", self.handler_name)
            self.datasource_obj = self.new_user_commcell.datacube.datasources.get(
                self.tcinputs['DataSourcename'])
            self.handler_obj = self.datasource_obj.ds_handlers.get(self.handler_name)
            response_out = self.handler_obj.get_handler_data(handler_filter=dynamic_constants.SOLR_FETCH_ONE_ROW)
            self.log.info("Handler Data  : %s", str(response_out))
            total_docs = response_out['numFound']
            if self.total_crawlcount != int(total_docs):
                self.log.info("Handler returned wrong number of docs")
                raise Exception("Handler document count mismatched. Actual {0} Expected {1}"
                                .format(total_docs, self.total_crawlcount))
            self.log.info("Total crawl count and Handler execution count matched %s", str(total_docs))
            self.log.info("Delete the handler created by old user : %s", self.handler_name)
            self.datasource_obj.ds_handlers.delete(self.handler_name)
            self.log.info("Going to refresh handlers list and cross verify whether deleted handler exists")
            self.datasource_obj.ds_handlers.refresh()
            if self.datasource_obj.ds_handlers.has_handler(self.handler_name):
                raise Exception("Handler not deleted correctly")
            self.log.info("Handler deleted successfully - %s", self.handler_name)
            self.handler_name = self.handler_name + "_2"
            self.log.info("Going to create new handler : %s", self.handler_name)
            self.datasource_obj.ds_handlers.add(self.handler_name, search_query=['*'])
            self.log.info("Handler created. Going to cross verify it by executing")
            self.handler_obj = self.datasource_obj.ds_handlers.get(self.handler_name)
            response_out = self.handler_obj.get_handler_data(handler_filter=dynamic_constants.SOLR_FETCH_ONE_ROW)
            self.log.info("Handler Data  : %s", str(response_out))
            total_docs = response_out['numFound']
            if self.total_crawlcount != int(total_docs):
                self.log.info("Handler returned wrong number of docs")
                raise Exception("Handler document count mismatched. Actual {0} Expected {1}"
                                .format(total_docs, self.total_crawlcount))
            self.log.info("Total crawl count and Handler execution count matched %s", str(total_docs))
            self.log.info("Going to share handler with other user : %s", self.share_user)
            self.share_user_obj = self.commcell_obj.users.get(self.share_user)
            share_user_id = self.share_user_obj.user_id
            self.handler_obj.share(permission_list=[
                dynamic_constants.VIEW_PERMISSION, dynamic_constants.EXECUTE_PERMISSION,
                dynamic_constants.EDIT_PERMISSION, dynamic_constants.SHARE_PERMISSION],
                operation_type=dynamic_constants.SHARE_ADD,
                user_id=share_user_id, user_name=self.share_user, user_type=dynamic_constants.USER_ASSOCIATION_TYPE)
            self.log.info("Sharing of handler succeeded : %s", self.handler_name)

            self.log.info("Going to get commcell object for shared user : %s", self.share_user)
            self.share_user_commcell = Commcell(
                self.inputJSONnode['commcell']['webconsoleHostname'], self.share_user, self.password)
            self.log.info("Going to execute the handler %s", self.handler_name)
            self.datasource_obj = self.share_user_commcell.datacube.datasources.get(
                self.tcinputs['DataSourcename'])
            self.handler_obj = self.datasource_obj.ds_handlers.get(self.handler_name)
            response_out = self.handler_obj.get_handler_data(handler_filter=dynamic_constants.SOLR_FETCH_ONE_ROW)
            self.log.info("Handler Data  : %s", str(response_out))
            total_docs = response_out['numFound']
            if self.total_crawlcount != int(total_docs):
                self.log.info("Handler returned wrong number of docs")
                raise Exception("Handler document count mismatched. Actual {0} Expected {1}"
                                .format(total_docs, self.total_crawlcount))
            self.log.info("Total crawl count and Handler execution count matched %s", str(total_docs))
            self.log.info("Try to delete handler and cross verify permission issue for shared user")
            try:
                self.datasource_obj.ds_handlers.delete(self.handler_name)
            except SDKException as er:
                if "Current user doesn't have delete permission" not in er.exception_message:
                    raise Exception("Handler deleted by shared user though user doesn't have any permission")
            self.log.info("Shared user is not able to delete handler as exepcted")
            self.log.info("Going to delete the datasource by new user: %s", self.tcinputs['DataSourcename'])
            self.new_user_commcell.datacube.datasources.delete(self.tcinputs['DataSourcename'])
            self.log.info("Datasource deleted successfully by new user - %s", self.new_user)
            self.log.info("------------------------- Ownership Transfer verification Ends--------------------------")

        except Exception as exp:
            self.log.error('Failed to execute test case with error: %s', exp)
            self.result_string = str(exp)
            self.log.exception(exp)
            self.status = constants.FAILED

    def tear_down(self):
        """Tear down function of this test case"""
        if self.status == constants.PASSED:
            if self.user_helper is not None:
                self.user_helper.delete_user(user_name=self.user, new_user="admin")
                self.user_helper.delete_user(user_name=self.new_user, new_user="admin")
                self.user_helper.delete_user(user_name=self.share_user, new_user="admin")
            if self.role_helper is not None:
                self.role_helper.delete_role(self.role_name)
