from AutomationUtils.database_helper import CommServDatabase
from AutomationUtils import database_helper

import xml.etree.ElementTree as ET
from Web.Common.exceptions import CVTestStepFailure

class Verification:
    """
       Utility class for managing cloud application instances in a Commvault environment.
       Provides methods for validating properties, fetching data from a database, and performing deletion validation.
    """
    def __init__(self, commcell, log, app_name):
        self.commcell = commcell
        self.log = log
        self.app_name = app_name
        database_helper.set_csdb(CommServDatabase(commcell))

    def delete_validation(self):
        """Validates if client is completely deleted using cvpysdk"""
        self.log.info(f"Checks if client:{self.app_name} exists using cvpysdk.")
        self.commcell.clients.refresh()
        if self.app_name.lower() in self.commcell.clients.all_clients:
            self.log.info(f"Force deleting client:[{self.app_name}] using cvpysdk")
            self.commcell.clients.delete(self.app_name)
            self.log.info("Deletion occurred successfully")

    def _fetch_app_properties(self, repo_group=None):
        """
        Fetches app properties from CSDB
        Args:
            repo_group            (str)   -- Name of the repository group
        Returns:
            props                 (dict)  -- Properties of the app
        """
        props = {}
        db_props = {}
        csdb = database_helper.get_csdb()
        query = f"select attrName,attrVal from APP_InstanceProp where componentNameId = " \
                f"(select id from APP_InstanceName where name = '{self.app_name}');"
        csdb.execute(query)
        for result in csdb.fetch_all_rows(True):
            db_props[result.get("attrName")] = result.get("attrVal")
        props['access_nodes'] = []
        props['app_display_name'] = db_props.get('Cloud Apps Instance Display Name')
        props['app_type'] = db_props.get('Cloud Apps Instance Type')
        for proxy_server in ET.fromstring(db_props.get('Git App Proxy Clients')).findall(
                'proxyServers'):
            props['access_nodes'].append(proxy_server.get('clientName'))
        root = ET.fromstring(db_props.get('Git App Staging Path Details'))
        props['staging_path'] = root.get('stagingPath')
        props['token_name'] = db_props.get('Git App User Name')
        if repo_group is None:
            repo_group = "default"
        query = f"select attrName,attrVal from APP_SubClientProp where componentNameId = (select " \
                f"id from APP_Application where instance=(select id from APP_InstanceName " \
                f"where name = '{self.app_name}') and subclientName='{repo_group}');"
        csdb.execute(query)
        db_props = {}
        for result in csdb.fetch_all_rows(True):
            db_props[result.get("attrName")] = result.get("attrVal")
        props['organization_name'] = db_props.get('Git App Account Name')
        props['plan'] = db_props.get('Associated Plan')
        return props

    def _verify_property(self, key, csdb_value, actual_value):
        """
        Verifies and raises exception with proper message
        Args:
            key                   (str)   -- Property attribute
            csdb_value            (str)   -- Value fetched from csdb
            actual_value          (str)   -- Value entered by user/tc
        Raises:
            Exception:
                If failed to match csdb and actual value for a key
        """
        self.log.info(f"For Attribute:[{key}], the properties are "
                      f"User input: [{actual_value}] "
                      f"csdb value:[{csdb_value}]")
        if str(csdb_value) != str(actual_value):
            error_msg = f"User input: [{actual_value}] is not matching with " \
                        f"csdb value:[{csdb_value}] for Attribute:[{key}]"
            raise CVTestStepFailure(error_msg)

    def app_properties_validation(self, app_props):
        """
        Validates if client properties are being set as provided
        Args:
            app_props              (dict)   -- App properties set by user/tc
        """
        csdb_app_props = self._fetch_app_properties(app_props.get("repository_group"))
        if app_props.get('app_display_name') is not None:
            self._verify_property("App Display Name", csdb_app_props.get('app_display_name'),
                              app_props.get('app_display_name'))
        if app_props.get('app_type') is not None:
            self._verify_property("App Type", csdb_app_props.get('app_type'), app_props.get('app_type'))
        if app_props.get("organization_name") is not None:
            self._verify_property("Organization Name", csdb_app_props.get('organization_name'),
                                  app_props.get('organization_name'))
        if app_props.get("token_name") is not None:
            self._verify_property("Token Name", csdb_app_props.get('token_name'),
                                  app_props.get('token_name'))
        if app_props.get("plan_name") is not None:
            self._verify_property("Plan Id", csdb_app_props.get('plan'),
                                  self.commcell.plans.get(app_props.get('plan_name')).plan_id)
        if app_props.get("access_nodes") is not None:
            sorted_access_nodes_csdb = sorted(csdb_app_props.get('access_nodes'))
            sorted_access_nodes_app = sorted(app_props.get('access_nodes'))
            self._verify_property("Access Nodes", sorted_access_nodes_csdb,
                                  sorted_access_nodes_app)
        if app_props.get("staging_path") is not None:
            self._verify_property("Staging Path", csdb_app_props.get('staging_path'),
                                  app_props.get('staging_path'))

