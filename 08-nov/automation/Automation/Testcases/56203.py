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
from Server.JobManager.jobmanager_helper import JobManager
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
        self.datasource_type = dynamic_constants.FILE_SYSTEM_DSTYPE
        self.name = "DM2 - OwnershipTransfer - Verify handler Creation & Deletion after transfer in FS datasource for AD Users"

        self.properties = None
        self.timestamp = None
        self.commcell_obj = None
        self.user_helper = None
        self.role_helper = None
        self.role_obj = None
        self.user_obj = None
        self.new_user_obj = None
        self.share_user_obj = None
        self.security_dict = None
        self.user_commcell = None
        self.new_user_commcell = None
        self.share_user_commcell = None
        self.datasource_id = None
        self.datasource_obj = None
        self.schema = []
        self.total_crawlcount = 0
        self.total_crawlcount_after_trn = 0
        self.input_data = []
        self.user = None
        self.new_user = None
        self.share_user = None
        self.password = None
        self.role_name = None
        self.handler_obj = None
        self.accessnode_client_obj = None
        self.accessnode_clientid = None
        self.handler_name = None
        self.permission_list = dynamic_constants.DCUBE_USER_PERMISSION_LIST
        self.tcinputs = {
            "DataSourcename": None,
            "IndexServer": None,
            "Column": None,
            "username1": None,
            "username2": None,
            "username3": None,
            "password": None,
            "domain": None,
            "IncludedirectoriesPath": None,
            "DoincrementalScan": None,
            "UserName": None,
            "Password": None,
            "PushonlyMetadata": None,
            "Accessnodeclient": None
        }

    def setup(self):
        """Setup function of this test case"""
        self.commcell_obj = self._commcell
        self.user_helper = UserHelper(self.commcell_obj)
        self.timestamp = calendar.timegm(time.gmtime())
        self.role_helper = RoleHelper(self.commcell_obj)
        self.role_name = f"Dm2OwnershipRole_{self.timestamp}"
        self.user = self.tcinputs['username1']
        self.new_user = self.tcinputs['username2']
        self.share_user = self.tcinputs['username3']
        self.handler_name = f"Handler1_{self.timestamp}"
        self.password = self.tcinputs['password']

        self.role_obj = self.role_helper.create_role(self.role_name,
                                                     self.permission_list, None, False, False)
        self.security_dict = {'assoc1': {
            'commCellName': [self.commcell_obj.commserv_name],
            'role': [self.role_name]
        }}

        self.log.info("Security association Prepared : %s", str(self.security_dict))
        domain_length = len(self.tcinputs['domain'])
        domain_length = domain_length + 1
        self.log.info("Checking for AD users already exists or not. if exists, deleting it")
        if self.commcell_obj.users.has_user(self.user):
            self.user_helper.delete_user(self.user, new_user="admin")
        if self.commcell_obj.users.has_user(self.new_user):
            self.user_helper.delete_user(self.new_user, new_user="admin")
        if self.commcell_obj.users.has_user(self.share_user):
            self.user_helper.delete_user(self.share_user, new_user="admin")
        self.log.info("Going to create new Users")
        self.user_helper.create_user(
            user_name=self.user[domain_length:], email=f"test{self.id}_1@test.com", full_name="Test User Created by Dm2 Automation",
            password=self.password, security_dict=self.security_dict, domain=self.tcinputs['domain'])

        self.user_helper.create_user(
            user_name=self.new_user[domain_length:], email=f"test{self.id}_2@test.com", full_name="Test User Created by Dm2 Automation",
            password=self.password, security_dict=self.security_dict, domain=self.tcinputs['domain'])

        self.user_helper.create_user(
            user_name=self.share_user[domain_length:], email=f"test{self.id}_3@test.com",
            full_name="Test User Created by Dm2 Automation",
            password=self.password, security_dict=self.security_dict, domain=self.tcinputs['domain'])

        self.log.info("Trying to get New commcell object for created user1 : %s", str(self.user))
        self.user_commcell = Commcell(self.inputJSONnode['commcell']['webconsoleHostname'], self.user, self.password)

        self.tcinputs['DataSourcename'] = self.tcinputs['DataSourcename'] + \
            str(self.timestamp)
        self.log.info("Going to create File System Datasource via Rest API : %s",
                      str(self.tcinputs['DataSourcename']))

        self.accessnode_client_obj = self.user_commcell.clients.get(
            self.tcinputs['Accessnodeclient'])
        self.log.info("Client object Initialised")
        self.accessnode_clientid = self.accessnode_client_obj.client_id
        self.log.info("Accessnode Client id : %s", str(self.accessnode_clientid))

        prop_name = ['includedirectoriespath', 'doincrementalscan', 'username', 'password', 'pushonlymetadata',
                     'accessnodeclientid', 'createclient', 'candelete', 'appname', 'excludefilters',
                     'minumumdocumentsize', 'maximumdocumentsize']
        prop_value = [self.tcinputs['IncludedirectoriesPath'], self.tcinputs['DoincrementalScan'],
                      self.tcinputs['UserName'], self.tcinputs['Password'], self.tcinputs['PushonlyMetadata'],
                      self.accessnode_clientid, "archiverClient", "true", "DATACUBE", "", "0", "52428800"]
        self.properties = [{"propertyName": prop_name[x], "propertyValue": prop_value[x]}
                           for x in range(0, len(prop_name))]

        self.user_commcell.datacube.datasources.add(
            self.tcinputs['DataSourcename'],
            self.tcinputs['IndexServer'],
            self.datasource_type, self.properties)
        self.log.info("File system datasource created successfully")

        self.datasource_obj = self.user_commcell.datacube.datasources.get(
            self.tcinputs['DataSourcename'])
        self.datasource_id = self.datasource_obj.datasource_id
        self.log.info("Created DataSource id : %s", str(self.datasource_id))

        self.log.info("Going to start crawl job for this data source")
        self.crawl_jobid = self.datasource_obj.start_job()
        self.log.info("Started crawl job with id : %s", str(self.crawl_jobid))
        if self.crawl_jobid is None:
            raise Exception("Something went wrong with datasource start job")

        self.log.info("Going to Monitor crawl job for this data source")
        job_manager = JobManager(_job=self.crawl_jobid, commcell=self.user_commcell)
        if job_manager.wait_for_state('completed', 10, 60, True):
            self.log.info("Job completed")
        else:
            self.log.error("Crawl job for FS datasource failed")
            raise Exception("Crawl job for FS datasource failed")
        self.log.info("Going to Get Status for this data source")
        datasource_status = self.datasource_obj.get_status()
        self.total_crawlcount = datasource_status['status']['totalcount']
        if self.total_crawlcount is not None and self.total_crawlcount == 0:
            raise Exception("Total crawled data count is zero. Please check")
        self.log.info("Crawled Data Count : %s", str(self.total_crawlcount))
        self.log.info("Reduce crawl count by 1 as root folder will not get pushed")
        self.total_crawlcount = self.total_crawlcount - 1
        self.log.info("Going to create new handler : %s", self.handler_name)
        self.datasource_obj.ds_handlers.add(self.handler_name, search_query=['*'])
        self.log.info("Handler created successfully")

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
            self.log.info("Execute the handler to get data from this datasource %s", self.handler_name)
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
            self.log.info("Going to delete handler created by old user %s", self.handler_name)
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

            self.log.info("Going to share datasource with other user : %s", self.share_user)
            self.share_user_obj = self.commcell_obj.users.get(self.share_user)
            share_user_id = self.share_user_obj.user_id
            self.datasource_obj.share(permission_list=[
                dynamic_constants.VIEW_PERMISSION, dynamic_constants.EXECUTE_PERMISSION,
                dynamic_constants.EDIT_PERMISSION, dynamic_constants.SHARE_PERMISSION],
                operation_type=dynamic_constants.SHARE_ADD,
                user_id=share_user_id, user_name=self.share_user, user_type=dynamic_constants.USER_ASSOCIATION_TYPE)
            self.log.info("Datasource shared successfully with user : %s", self.share_user)
            self.share_user_commcell = Commcell(
                self.inputJSONnode['commcell']['webconsoleHostname'], self.share_user, self.password)
            self.datasource_obj = self.share_user_commcell.datacube.datasources.get(self.tcinputs['DataSourcename'])
            self.log.info("Shared user able to see datasource :%s", self.tcinputs['DataSourcename'])
            self.log.info("Going to try deleting datasource by shared user")
            try:
                self.share_user_commcell.datacube.datasources.delete(self.tcinputs['DataSourcename'])
            except SDKException as er:
                if "doesn't have permission on datasourceId" not in er.exception_message:
                    raise Exception("Shared user is able to delete datasource even though no delete permission exists")
                else:
                    self.log.info("Unable to delete datasource by shared user as expected")
            self.log.info("Do soft delete of data by shared user")
            self.datasource_obj.delete_content()
            self.handler_obj = self.datasource_obj.ds_handlers.get("default")
            self.log.info("Execute default handler and cross verify whether count is zero now")
            response_out = self.handler_obj.get_handler_data(handler_filter=dynamic_constants.SOLR_FETCH_ONE_ROW)
            total_docs = response_out['numFound']
            if int(total_docs) != 0:
                raise Exception("Soft delete didn't happen correctly. Total docs {0}".format(total_docs))
            self.log.info("Soft delete success. Total doc is Zero now")
            self.log.info("Going to delete datasource by new user %s", self.new_user)
            self.new_user_commcell.datacube.datasources.delete(self.tcinputs['DataSourcename'])
            self.log.info("Refresh the datasources and check for its presence")
            self.new_user_commcell.datacube.datasources.refresh()
            if self.new_user_commcell.datacube.datasources.has_datasource(self.tcinputs['DataSourcename']):
                raise Exception("Datasource delete failed for new user. Please check")
            self.log.info("Datasource deleted successfully by new user")
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
                self.user_helper.delete_user(user_name=self.new_user, new_user="admin")
                self.user_helper.delete_user(user_name=self.share_user, new_user="admin")
            if self.role_helper is not None:
                self.role_helper.delete_role(self.role_name)
