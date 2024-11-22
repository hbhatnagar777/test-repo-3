# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Helper file for performing Name Change related operations on Commcell and Clients

NameChangeHelper is the only class defined in this file.

NameChangeHelper:
    __init__()                                  --  Initializes instance of the NameChangeHelper
                                                    class

    change_commserve_display_name()             --  Changes the display name of the commserver

    change_client_display_name()                --  Changes the display name of the client

    change_commserver_hostname_for_client()     --  Changes the commserver hostname on the client

    change_client_hostname()                    --  Changes the hostname of the client

    change_client_name()                        --  Changes the client name

    change_commserver_hostname_remote_clients() --  Changes the commserver hostname on the
                                                    commserver and clients

    change_commserver_hostname_after_dr()       --  Changes the commserver hostname on the given
                                                    clients

    change_client_domain_name()                 --  Changes the domain name of the clients

"""
import re
import time
from cvpysdk.name_change import OperationType
from AutomationUtils.idautils import CommonUtils
from AutomationUtils.options_selector import OptionsSelector
from AutomationUtils.machine import Machine


class NameChangeHelper():
    """Helper class to provide Name Change related operations on Commcell and Clients"""

    def __init__(self, testcase_obj):
        """ Initializes instance of the NameChangeHelper class

        Args:
            testcase_obj (obj)    -- Testcase object

        """
        self._commcell = testcase_obj.commcell
        self.log = testcase_obj.log
        self.options = OptionsSelector(self._commcell)
        self.serverbase = CommonUtils(self._commcell)

    def change_commserve_display_name(self, new_name):
        """ Changes the display name of the commserver

            Args:
                new_name(str)   --  The new commserver display name to be updated

            Returns:
                None

            Raises:
                Exception:
                    -   If failed to update the commserver display name

        """

        self.log.info(
            "New commserver display name should be: %s", new_name)

        name_change_object = self._commcell.name_change
        name_change_object.display_name = new_name

        # Validation starts
        self._commcell.clients.get(self._commcell.commserv_hostname).refresh()
        updated_name = self._commcell.clients.get(self._commcell.commserv_hostname).display_name
        self.log.info(
            "The updated display name of the commserver is: %s",
            updated_name)

        if updated_name.lower() == new_name.lower():
            self.log.info(
                "Verified commserver display name change, from the DB")
        else:

            raise Exception("Commserver display update failed.")

    def change_client_display_name(self, client_name, new_name):
        """ Changes the display name of the client

            Args:
                client_name(str)    --  The client for which display name should be changed

                new_name(str)       --  The new client display name to be updated

            Returns:
                None

            Raises:
                Exception:
                    -   If failed to update the client display name

        """

        client_object = self._commcell.clients.get(client_name)
        name_change_object = client_object.name_change
        name_change_object.display_name = new_name

        # Validation starts
        client_object.refresh()
        self.log.info(
            "Verifying if client display name is updated, from the DB")
        updated_name = client_object.display_name

        self.log.info(
            "The updated display name of the client is: %s",
            updated_name)

        if updated_name.lower() == new_name.lower():
            self.log.info(
                "Verified client display name change, from the DB")
        else:
            raise Exception("Client display name not updated.")

    def change_commserver_hostname_for_client(self, client_name, new_commserver_hostname):
        """ Changes the commserver hostname on the client

            Args:
                client_name(str)            --  The client for which commserver hostname
                                                should be changed

                new_commserver_hostname(str)--  The new commserver hostname to be updated

            Returns:
                None

            Raises:
                Exception:
                    -   If failed to update the commserver hostname on the client

        """

        self.log.info(
            "New commserver hostname of the client should be: %s", new_commserver_hostname)

        client_object = self._commcell.clients.get(client_name)
        name_change_object = client_object.name_change
        dict_params = {
            'operation': OperationType.COMMSERVER_HOSTNAME.value,
            'CommserverHostname': new_commserver_hostname
        }
        name_change_object.hostname = dict_params

        self.log.info("Waiting for 180 sec for client services to restart")
        time.sleep(180)

        # Validation starts
        client_object.refresh()
        self.log.info(
            "Verifying if client's commserver hostname is updated, from the DB")
        updated_hostname = client_object.commcell_name

        self.log.info(
            "The updated commserver hostname of the client is: %s", updated_hostname)

        if updated_hostname.lower() == new_commserver_hostname.lower():
            self.log.info(
                "Verified the client's commserver hostname change, from the DB")
        else:
            raise Exception("Client's commserver hostname update failed.")

        self.log.info("Checking registry of the client: %s", client_name)
        machine_object = Machine(client_object)
        commserver_hostname_in_registry = machine_object.get_registry_value(
            "CommServe", "sCSHOSTNAME")

        self.log.info(
            "The commserver hostname for the client '%s' in "
            "registry is: %s", client_name, commserver_hostname_in_registry)

        if new_commserver_hostname.lower() == commserver_hostname_in_registry.lower():
            self.log.info(
                "The client's '%s' registry sCSHOSTNAME has been updated", client_name)
        else:
            raise Exception("The client's '%s' registry sCSHOSTNAME has NOT "
                            "been updated", client_name)

        self.log.info(
            "Running check readiness for the client: %s", client_name)
        self.serverbase.check_client_readiness([client_name])
        self.log.info(
            "Check readiness Passed for the client: %s",
            str(client_name))

    def change_client_hostname(self, client_name, new_client_hostname):
        """ Changes the hostname of the client

            Args:
                client_name(str)            --  The client for which hostname should be changed

                new_client_hostname(str)    --  The new client hostname to be updated

            Returns:
                None

            Raises:
                Exception:
                    -   If failed to update the client hostname

        """
        self.log.info(
            "New client hostname should be: %s", new_client_hostname)

        client_object = self._commcell.clients.get(client_name)
        name_change_object = client_object.name_change
        dict_params = {
            'operation': OperationType.CLIENT_HOSTNAME.value,
            'ClientHostname': new_client_hostname
        }
        name_change_object.hostname = dict_params

        self.log.info("Waiting for 180 sec for client services to restart")
        time.sleep(180)

        # Validation starts
        client_object.refresh()
        self.log.info(
            "Verifying if client name is updated, from the DB")
        updated_client_hostname = client_object.client_hostname

        self.log.info(
            "The updated client hostname is: %s", updated_client_hostname)

        if updated_client_hostname.lower() == new_client_hostname.lower():
            self.log.info(
                "Verified the client's hostname change, from the DB")
        else:
            raise Exception("Client's hostname update failed.")

        self.log.info("Checking registry of the client: %s", client_name)
        machine_object = Machine(client_object)
        sub_key = machine_object.join_path("Machines", client_name)
        client_hostname_in_registry = machine_object.get_registry_value(sub_key, "sHOSTNAME")

        self.log.info(
            "The hostname for the client '%s' in registry"
            " is: %s", client_name, client_hostname_in_registry)

        if new_client_hostname.lower() == client_hostname_in_registry.lower():
            self.log.info(
                "The client's '%s' registry sHOSTNAME has been updated", client_name)
        else:
            raise Exception("The client's '%s' registry sHOSTNAME has NOT been "
                            "updated"% client_name)

        self.log.info(
            "Running check readiness for the client: %s",
            client_name)
        self.serverbase.check_client_readiness([client_name])
        self.log.info(
            "Check readiness Passed for the client: %s",
            client_name)

    def change_client_name(self, old_client_name, new_name):
        """ Changes the name of the client

            Args:
                old_client_name(str)    --  The client for which name should be changed

                new_name(str)           --  The new client name to be updated

            Returns:
                None

            Raises:
                Exception:
                    -   If failed to update the client name

        """
        self.log.info("New client name should be: %s", new_name)

        client_object = self._commcell.clients.get(old_client_name)
        name_change_object = client_object.name_change
        name_change_object.client_name = new_name

        self.log.info("Waiting for 180 sec for client services to restart")
        time.sleep(180)

        # Validation starts
        client_object.refresh()
        self._commcell.clients.refresh()
        self.log.info("Verifying if client's name is updated, from the DB")
        self._commcell.clients.has_client(new_name)
        self.log.info("Client name update in the DB, has been verified")

        self.log.info("Checking registry of the client: %s", new_name)
        machine_object = Machine(client_object)
        client_name_in_registry = machine_object.get_registry_value(
            "", "sPhysicalNodeName")

        self.log.info(
            "The client name for the client '%s' in registry"
            " is: %s", new_name, client_name_in_registry)

        if new_name.lower() == client_name_in_registry.lower():
            self.log.info(
                "The client's '%s' registry sPhysicalNodeName has been updated", new_name)
        else:
            raise Exception("The client's '%s' registry sPhysicalNodeName has"
                            " NOT been updated" % new_name)

        self.log.info(
            "Running check readiness for the client: %s", str(new_name))
        self.serverbase.check_client_readiness([new_name])
        self.log.info(
            "Check readiness Passed for the client: %s", str(new_name))

    def change_commserver_hostname_remote_clients(
            self, new_commserver_hostname, clients):
        """ Changes the commserver hostname on the commserver and remote clients

            Args:
                clients (list)              --  The list of client for which commserver hostname
                                                should be changed

                new_commserver_hostname(str)--  The new client hostname to be updated

            Returns:
                None

            Raises:
                Exception:
                    -   If failed to update the commserver hostname on the commserver and clients

        """
        self.log.info("New commserver hostname should be: %s", new_commserver_hostname)

        name_change_object = self._commcell.name_change
        dict_params = {
            'operation': OperationType.COMMSERVER_HOSTNAME_REMOTE_CLIENTS.value,
            'newName': new_commserver_hostname}
        name_change_object.hostname = dict_params

        self.log.info("Waiting for 180 sec for client services to restart")
        time.sleep(180)

        # Validation starts
        self._commcell.refresh()
        self.log.info("Verifying if the commserver hostname for the client is updated, "
                      "from the DB")
        updated_commserver_name = self._commcell.commserv_hostname

        if updated_commserver_name.lower() == new_commserver_hostname.lower():
            self.log.info(
                "Verified the commserver hostname change, from the DB")
        else:
            raise Exception(
                "Commserver hostname change failed on commserver.")

        for client in clients:
            self.log.info("Checking registry of the client: %s", client)
            client_object = self._commcell.clients.get(client)
            machine_object = Machine(client_object)
            commserver_hostname_in_registry = machine_object.get_registry_value(
                "CommServe", "sCSHOSTNAME")

            self.log.info(
                "The commserver hostname in client '%s' registry "
                "is: %s", client, commserver_hostname_in_registry)

            if new_commserver_hostname.lower() == commserver_hostname_in_registry.lower():
                self.log.info(
                    "The client's '%s' registry sCSHOSTNAME has been updated", client)
            else:
                raise Exception(
                    "The client's '%s' registry sCSHOSTNAME has NOT been updated"% client)

        self.log.info("Running check readiness for all the clients")
        self.serverbase.check_client_readiness(clients)
        self.log.info("Check readiness Passed for the clients")

    def change_commserver_hostname_after_dr(
            self, new_commserver_hostname, old_commserver_hostname, clients):
        """ Changes the commserver hostname on the clients (after disater recovery option)

            Args:
                clients(list)               --  The list of clients for which commserver hostname
                                                should be changed

                new_commserver_hostname(str)--  The new commserver hostname to be updated

                old_commserver_hostname(str)--  The old commserver hostname on the clients

            Returns:
                None

            Raises:
                Exception:
                    -   If failed to update the commserver hostname on the clients

        """
        self.log.info(
            "Commserver hostname on the clients should be: %s", new_commserver_hostname)
        client_ids = []
        for client in clients:
            client_object = self._commcell.clients.get(client)
            client_id = client_object.client_id
            self.log.info(
                "Client id for client '%s' is: %s",
                client,
                client_id)

            client_ids.append(client_id)

        name_change_object = self._commcell.name_change
        dict_params = {
            'operation': OperationType.COMMSERVER_HOSTNAME_AFTER_DR.value,
            'oldName': old_commserver_hostname,
            'clientIds': client_ids
        }
        name_change_object.hostname = dict_params

        self.log.info("Waiting for 180 sec for client services to restart")
        time.sleep(180)

        # Validation starts
        for client in clients:
            client_object = self._commcell.clients.get(client)
            client_object.refresh()
            self.log.info(
                "Verifying if client's commserver hostname is updated, from the DB")
            updated_commserver_name = client_object.commcell_name

            self.log.info(
                "The updated commserver hostname of the client is: %s",
                updated_commserver_name)

            if updated_commserver_name.lower() == new_commserver_hostname.lower():
                self.log.info(
                    "Verified the client '%s's commserver hostname change, from the DB",
                    client)
            else:
                raise Exception(
                    "Commserver hostname change for the client '%s' failed" % client)

            self.log.info("Checking registry of the client: %s", client)
            machine_object = Machine(client_object)
            commserver_hostname_in_registry = machine_object.get_registry_value(
                "CommServe", "sCSHOSTNAME")

            self.log.info(
                "The commserver hostname in client '%s' registry is: %s",
                client,
                commserver_hostname_in_registry)

            if new_commserver_hostname.lower() == commserver_hostname_in_registry.lower():
                self.log.info(
                    "The client '%s's registry sCSHOSTNAME has been updated", client)
            else:
                raise Exception(
                    "The client '%s's registry sCSHOSTNAME has NOT been updated" % client)

        self.log.info("Running check readiness for all the clients")
        self.serverbase.check_client_readiness(clients)
        self.log.info("Check readiness Passed for the clients")

    def change_client_domain_name(self, client_list, old_domain, new_domain):
        """ Changes the commserver hostname on the commserver and clients

            Args:
                client_list(list)--  The list of clients for which commserver hostname should be
                                    changed

                new_domain(str)  --  The new client domain name to be updated

                old_domain(str)  --  The old domain name of the client

            Returns:
                None

            Raises:
                Exception:
                    -   If failed to update the commserver hostname on the commserver and clients

        """
        self.log.info(
            "The domainname on the clients should be: %s", new_domain)
        dict_params = {
            'oldDomain': old_domain,
            'newDomain': new_domain
        }
        name_change_object = self._commcell.name_change
        name_change_object.domain_name = dict_params

        self.log.info("Waiting for 180 sec for client services to restart")
        time.sleep(180)

        # Validation starts
        for clients in client_list:
            client_object = self._commcell.clients.get(clients)
            client_object.refresh()
            updated_client_hostname = client_object.client_hostname
            self.log.info(
                "The updated client hostname is: %s",
                updated_client_hostname)
            updated_domain_name = re.findall("\.(.*)", updated_client_hostname)

            if updated_domain_name[0].lower() == new_domain.lower():
                self.log.info(
                    "Verified the client '%s's domain name change, from the DB", clients)
            else:
                raise Exception(
                    "Client domain name change for the client '%s' failed" % clients)

            self.log.info("Checking registry of the client: %s", clients)
            machine_object = Machine(client_object)
            sub_key = machine_object.join_path("Machines", clients)
            client_hostname_in_registry = machine_object.get_registry_value(sub_key, "sHOSTNAME")

            self.log.info(
                "The client hostname in client '%s' registry is: %s",
                clients,
                client_hostname_in_registry)
            updated_domain_in_registry = re.findall("\.(.*)", client_hostname_in_registry)

            if new_domain.lower() == updated_domain_in_registry[0].lower():
                self.log.info(
                    "The client '%s's registry sHOSTNAME has been updated", clients)
            else:
                raise Exception(
                    "The client '%s's registry sHOSTNAME has NOT been updated" % clients)

        self.log.info("Running check readiness for the client")
        self.serverbase.check_client_readiness(client_list)
        self.log.info("Check readiness Passed for the client")
