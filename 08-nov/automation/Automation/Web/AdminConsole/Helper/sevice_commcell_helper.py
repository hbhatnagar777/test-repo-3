# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
This module provides the function or operations that can be used to run
basic operations on Service commcell page.

Class:

    ServiceCommcellMain()

Functions:

    __init__()                      --      function to initialize the class object

    create_service_commcell()       --      function to register a new service commcell

    validate_service_commcell()     --      function to validate if the service commcell is created successfully

    delete_service_commcell()       --      function to unregister a service commcell

"""
from Server.routercommcell import RouterCommcell
from Web.AdminConsole.Components.table import Table
from Web.AdminConsole.AdminConsolePages.service_commcell import ServiceCommcell
from Web.Common.exceptions import CVWebAutomationException


class ServiceCommcellMain(object):
    """
        Helper for service commcell page
    """

    def __init__(self, admin_console, csdb=None, commcell=None):
        """
            Initializes the company helper module

            Args:
                admin_console   (object)        --  AdminConsole class object

                csdb            (Object)        --  CommServe database object

                commcell        (Object)        --  CommServe object
        """

        self.__csdb = csdb
        self.__admin_console = admin_console
        self.__commcell = commcell
        self.__table = Table(self.__admin_console)
        self.__log = admin_console.log
        self.__service_commcell = ServiceCommcell(self.__admin_console)
        self.router_commcell = RouterCommcell(commcell)
        self.__host_name = None
        self.__user_name = None
        self.__password = None
        self.__register_as_IdP = False

    @property
    def host_name(self):
        """ Get Host name"""
        return self.__host_name

    @host_name.setter
    def host_name(self, value):
        """ Set Host name"""
        self.__host_name = value

    @property
    def user_name(self):
        """ Get User name"""
        return self.__user_name

    @user_name.setter
    def user_name(self, value):
        """ Set User name"""
        self.__user_name = value

    @property
    def password(self):
        """ Get Password"""
        return self.__password

    @password.setter
    def password(self, value):
        """ Set Password"""
        self.__password = value

    @property
    def configure_as_IdP(self):
        """ Get flag for configure as IdP"""
        return self.__register_as_IdP

    @configure_as_IdP.setter
    def configure_as_IdP(self, value):
        """ Set flag for configure as IdP"""
        self.__register_as_IdP = value

    def create_service_commcell(self):
        """Method to register a new service"""
        self.__admin_console.navigator.navigate_to_service_commcell()
        self.router_commcell.get_service_commcell(self.host_name, self.user_name, self.password)
        self.__service_commcell.register_commcell(self.host_name, self.user_name, self.password, self.configure_as_IdP)

    def validate_service_commcell(self):
        """Method to validate the service commcell"""
        service_commcells = self.__service_commcell.get_service_commcells()
        cs_name = self.router_commcell.service_commcell.commserv_name
        hostname = self.router_commcell.service_commcell.commserv_hostname
        if cs_name not in service_commcells:
            raise CVWebAutomationException("Registered commcell not in table!")
        elif hostname.lower().strip() != \
                service_commcells[cs_name]["Service CommCell host name"].lower().strip():
            raise CVWebAutomationException("Registered commcell has different hostname!")

    def delete_service_commcell(self):
        """Method to delete the service commcell"""
        self.__service_commcell.delete_registered_commcell(self.host_name)
