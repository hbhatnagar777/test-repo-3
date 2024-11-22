# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Helper class for Teams related operations

    TeamsClientHelper:

        __init__()                              --  Initialize the TeamsClientHelper object

        create_client()                         --  Creates Teams client

        delete_client()                         --  Deletes the given Teams client
"""

from AutomationUtils import logger
from Application.Teams.teams_constants import TeamsConstants
import AutomationUtils.config as config
from Web.AdminConsole.Hub.office365_apps import Office365Apps
from Web.AdminConsole.Hub import constants
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.cvbrowser import BrowserFactory, Browser

Azure = config.get_config().Azure


class TeamsClientHelper:
    """ Helper class to perform Teams related operations"""

    def __init__(self, commcell):
        """
        Initialize the OneDriveSDGHelper object
        Args:
            commcell    -   Instance of commcell class
        """
        self.commcell = commcell
        self.log = logger.get_log()

    def create_client(self, client_name, server_plan, cloud_region=TeamsConstants.CloudRegion.Default,**kwargs):
        """
        Creates OneDrive client
        Args:
            client_name(str)        --  Name of the client to be created
            server_plan(str)        --  Name of the Server plan to be used
            cloud_region (Enum)     -- Type of the cloud region
        **kwargs(dict)      --  Dictionary of other parameters to be used
            index_server(str)       --  Name of the index server to be used
            access_nodes_list(list) --  List of access nodes to be used
        Returns:
            Client(object)          --  Instance of client class that was created
        """
        self.log.info(f'Creating a new client with name [{client_name}]')
        app_id = ""
        directory_id = ""
        secret = ""
        if cloud_region.value == 1:
            app_id = Azure.App.ApplicationID
            directory_id = Azure.App.DirectoryID
            secret = Azure.App.ApplicationSecret
        elif cloud_region.value == 4:
            app_id = Azure.Gcc.ApplicationID
            directory_id = Azure.Gcc.DirectoryID
            secret = Azure.Gcc.ApplicationSecret
        elif cloud_region.value == 5:
            app_id = Azure.GccHigh.ApplicationID
            directory_id = Azure.GccHigh.DirectoryID
            secret = Azure.GccHigh.ApplicationSecret
        else:
            raise Exception("Invalid cloud region")

        self.commcell.clients.\
            add_teams_client(client_name=client_name,
                                   server_plan=server_plan,
                                   azure_directory_id=directory_id,
                                   azure_app_id=app_id,
                                   azure_app_key_id=secret,
                                   index_server=kwargs.get('index_server'),
                                   access_nodes_list=kwargs.get('access_nodes_list'),
                                   cloud_region=cloud_region.value)
        self.client = self.commcell.clients.get(client_name)

        self.log.info(f'New client Created - [{client_name}]')
        return self.client

    def delete_client(self, client_name):
        """
        Deletes the given teams client
        Args:
            client_name(str)        --  Name of the client
        """
        self.log.info(f'Request received to remove client - [{client_name}]')
        if self.commcell.clients.has_client(client_name):
            self.commcell.clients.delete(client_name)
        self.log.info(f"Successfully deleted client - [{client_name}]")

    def acquire_token(self, app_name, command_center_user, password, cloud_region=TeamsConstants.CloudRegion.Default):
        browser = BrowserFactory().create_browser_object()
        try:
            browser.open()
            admin_console = AdminConsole(browser, self.commcell.webconsole_hostname)
            admin_console.login(command_center_user, password)
            navigator = admin_console.navigator
            office365app = Office365Apps(admin_console, constants.O365AppTypes.teams, is_react=True)
            global_admin = ""
            password = ""
            app = ""
            if cloud_region.value == 1:
                global_admin = Azure.App.User
                password = Azure.Password
                app = Azure.App.ApplicationID
            elif cloud_region.value == 4:
                global_admin = Azure.Gcc.User
                password = Azure.Gcc.Password
                app = Azure.Gcc.ApplicationID
            elif cloud_region.value == 5:
                global_admin = Azure.GccHigh.User
                password = Azure.GccHigh.Password
                app = Azure.GccHigh.ApplicationID
            else:
                raise Exception("Invalid cloud region")
            navigator.navigate_to_office365()
            office365app.access_office365_app(app_name)
            office365app.acquire_token(app, global_admin, password)
            self.log.info("Token acquired successfully")
        except Exception as ex:
            self.log.info(ex)
        finally:
            AdminConsole.logout_silently(admin_console)
            Browser.close_silently(browser)

