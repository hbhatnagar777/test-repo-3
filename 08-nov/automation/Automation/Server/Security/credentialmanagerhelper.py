# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Main file for performing credential Manager operations on Commcell

CredentialHelper is the only class defined in this file

CredentialHelper:    Provides functionality to create,modify and delete credential accounts.


CredentialHelper:

    __init__()                      --  Initialiazes the CredentialHelper object

    refresh()                       --  Refresh the CredentialHelper properties

    add()                           --  Creates the Credential account

    has_credential()                --  Checks whether the Credential account exists

    delete()                        --  Deletes the Credential account

    update_credential_name()        --  Updates the Credential account with new credential name

    update_user_credential()        --  Updates the Credential account's username and password

    update_credential_owner()       --  Updates the Credential account's owner

    update_credential_description() --  Updates the Credential account's description

    update_security_property()      --  Updates the Credential account's security properties


"""
# Python standard library imports
import inspect

# Helper suite imports
from cvpysdk.credential_manager import Credentials
from AutomationUtils import logger


class CredentialHelper:
    """Credential Helper class to perform credential manager related operations"""

    def __init__(self, commcell, credential=None):
        """Initializes CredentialHelper Class object"""
        self._commcell = commcell
        self.log = logger.get_log()
        self._credentials = None
        self._credential = None
        self.refresh()

        if credential:
            if self._credentials.has_credential(credential):
                self._credential = self._credentials.get(credential)

    def refresh(self):
        """Refresh the CredentialHelper properties"""
        self._credentials = Credentials(self._commcell)

    def add(self, account_type, credential, username, password, description=None):
        """Creates the Credential account

        Args:
            account_type        (str)   -- Credential account type
                                            Eg : Windows, linux

            credential          (str)   -- Credential account name

            username            (str)   -- credential account username

            password            (str)   -- Credential account password

            description         (str)   -- Description about the credential account


        Returns:
            Credential object

        Raises:
            Exception:
                if credential account fails to create

        """
        try:
            self.log.info("Creating credential %s with account type %s", credential, account_type)
            self._credentials.add(account_type, credential, username, password, description=description)
            self.log.info("Created Credential %s successfully", credential)
            return self._credentials.get(credential)

        except Exception as excp:
            self.log.error("Failed to create credential account %s", credential)
            raise Exception("\n [{0}] [{1}]".format(inspect.stack()[0][3], str(excp)))

    def has_credential(self, credential):
        """Checks whether the Credential account exists

        Args:
            Credential          (str)   -- Credential account name

        Returns:
            True or False

        Raises:
            Exception:
                If fails to check whether the credential account exists on the commcell

        """
        try:
            self.log.info("Checks whether the credential account with name [%s] exists on this Commcell", credential)
            return self._credentials.has_credential(credential)

        except Exception as excp:
            raise Exception("\n [{0}] [{1}]".format(inspect.stack()[0][3], str(excp)))

    def delete(self, credential):
        """Deletes the Credential account

        Args:
            credential          (str)   -- Credential account name

        Raises:
              Exception:
                If fails to delete the credential account

        """
        try:
            self.log.info("Deleting credential %s", credential)
            self._credentials.delete(credential_name=credential)
            self.log.info("Deleted Credential %s successfully", credential)

        except Exception as excp:
            self.log.error("Failed to delete credential account %s", credential)
            raise Exception("\n [{0}] [{1}]".format(inspect.stack()[0][3], str(excp)))

    def update_credential_name(self, credential, new_credential_name):
        """Updates the Credential account with new credential name

        Args:
            credential          (str)   -- Credential account name

            new_credential_name (str)   -- New name for the credential account name

        Raises:
              Exception:
                If fails to update the credential account name
                If credential doesnt exists

        """
        try:
            # self.refresh()
            self._credential = self._credentials.get(credential)
            self._credential.credential_name = new_credential_name
            self.log.info("Successfully updated with new credential name %s", new_credential_name)

        except Exception as excp:
            self.log.error("Failed to update Credential account [%s] with new name [%s]", credential,
                           new_credential_name)
            raise Exception("\n [{0}] [{1}]".format(inspect.stack()[0][3], str(excp)))

    def update_user_credential(self, credential, username, password):
        """Updates the Credential account's username and password

        Args:
            credential          (str)   -- Credential account name

            username            (str)   -- Credential account username

            password            (str)   -- Credential account password

        Raises:
            Exception:
                If fails to update the credential account details

        """
        try:
            self._credential = self._credentials.get(credential)
            self._credential.update_user_credential(uname=username, upassword=password)
            self.log.info("Successfully updated with new username and password for credential %s", credential)

        except Exception as excp:
            self.log.error("Failed to update new username and password for credential %s", credential)
            raise Exception("\n [{0}] [{1}]".format(inspect.stack()[0][3], str(excp)))

    def update_credential_description(self, credential, description):
        """Updates the Credential account's description

        Args:
            credential              (str)   -- Credential account name

            description             (str)   -- Credential account description

        Raises:
            Exception:
                If fails to update the Credential description

        """
        try:
            # self.refresh()
            self._credential = self._credentials.get(credential)
            self._credential.credential_description = description
            self.log.info("Successfully updated credential [%s] with description [%s]", credential, description)

        except Exception as excp:
            self.log.error("Failed to update description of credential %s", credential)
            raise Exception("\n [{0}] [{1}]".format(inspect.stack()[0][3], str(excp)))

    def update_security_property(self, credential, user_or_groupname, is_user=True):
        """Updates the Credential account's security properties

        Args:
            credential              (str)   -- Credential account name

            user_or_groupname       (str)   -- User or UserGroupName

            is_user                 (int)   -- Set value as True for user, Set value as False for usergroup
        """
        try:
            self._credential = self._credentials.get(credential)
            self._credential.update_securtiy(user_or_groupname, is_user=is_user)
            self.log.info("Successfully updated security property of credential [%s]", credential)

        except Exception as excp:
            self.log.error("Failed to update security property of credential %s", credential)
            raise Exception("\n [{0}] [{1}]".format(inspect.stack()[0][3], str(excp)))
