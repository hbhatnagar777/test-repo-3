# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Main file for performing Exchange Powershell related operations.

ExchangePowerShell:

        create_database()           -   Creates a databases

        create_mailboxes()          -   Creates mailboxes on the specified database

        mountordismount_database()  -   Mount or dismount the database

        overwrite_exdb()            -   Selects the option for a database

        import_pst()                -   Imports pst to a mailbox

        get_mailbox_name()          -   Gets the names of mailboxes within the specified database

        exdbcopy_operations()       -   Suspend/resume/remove copy for a passive copy

        remove_database()           -   Removes the database

        check_mailbox()             -   Checks whether the mailbox is present or not

        get_group_type()            -   Get the type of an Exchange Online Group	PN

        exch_online_operations()    -   Perform Operations for Exchange Onine Mailbox

        get_mailbox_guid()			-	Get the GUID for the list of mailboxes

        exch_online_o365_group_operations()
                                    -   Operations for Exchange related
                                        operations on AD Group of type Office 365


        delete_exchange_online_mailbox()
                                    -   Delete an Exchange Online Mailbox

        exch_online_public_folder_ops()
                                    -   Operations for Exchange Online Public Folder

        check_online_service_account_permissions()
                                    -   Check whether the necessary permissions are present
                                        with the service account created for an Exchange Online client

        get_licensed_users()        -   Get a list of mailboxes having valid and enabled
                                        Exchange Online license assigned
"""

import os
from base64 import b64decode
from AutomationUtils import machine, logger, constants
from Application.Exchange.ExchangeMailbox import constants
from AutomationUtils.constants import LOG_DIR
from Application.Exchange.ExchangeMailbox import constants


class ExchangePowerShell(object):
    """class to run exchange powershell command """

    def __init__(self, ex_object, cas_server_name, exchange_server,
                 exchange_adminname, exchange_adminpwd, server_name, domain_name=None):
        """Initializes the ExchangePowerShell object

            Args:
                ex_object (object)      -- instance of the exchange object

                cas_server_name(str)    -- Exchange cas server name

                exchange_server(str)    -- Exchange Server name

                exchange_adminpwd(str)  -- Exchange administrator password

                exchange_adminname(str) -- Exchange administrator username

                server_name             -- Server name is the machine with commvault's package

                domain_name(str)        -- domain name

        """
        self.ex_object = ex_object
        self.log = self.ex_object.log
        self.cas_server_name = cas_server_name
        self.exchange_server = exchange_server
        self.exchange_adminname = exchange_adminname
        self.exchange_pwd = exchange_adminpwd
        self.domain_name = domain_name
        self.utils_path = constants.UTILS_PATH
        self.powershell_path = constants.SCRIPT_PATH
        self.output_files = constants.RETRIEVED_FILES_PATH
        self.host_machine = machine.Machine(server_name, self.ex_object.commcell)

    def create_database(self, database_name, db_edbfolder=None,
                        db_logfolder=None):
        """Method to create a database on the given exchange server

            Args:
                database_name(str)  -- Database name used to create
                db_edbfolder(str)   -- by default creates at C:\exchangedatabases. if given
                    creates the path given by user

                db_logfolder(str)   -- by default creates at C:\exchangedatabases. if given
                    creates the path given by user
            Returns:
                None

            Raises:
                Exception -- Any error occured while creating databases

        """
        try:
            if db_edbfolder is None and db_logfolder is None:
                db_edbfolder = os.path.join(constants.EXCHANGE_DATABASES, database_name)
                db_logfolder = os.path.join(constants.EXCHANGE_DATABASES, database_name)

            self.log.info('Creating Database using powershell.'
                          'Powershell Path %s', constants.CREATE_DATABASES)

            prop_dict = {
                "LoginPassword": self.exchange_pwd,
                "LoginUser": self.exchange_adminname,
                "DatabaseEDBFolderPath": db_edbfolder,
                "ExchangeDatabase": database_name,
                "ExchangeServer": self.exchange_server,
                "DatabaselogFolderPath": db_logfolder,
                "ExchangeCASServer": self.cas_server_name
            }
            output = self.host_machine.execute_script(
                constants.CREATE_DATABASES, prop_dict)
            if output.exit_code != 0:
                raise Exception("Failed to create databases")

        except Exception as excp:
            self.log.exception("Exception in create_databases(): %s", str(excp))
            raise excp

    def create_mailboxes(self, display_name, database_name,
                         domain_name, number_of_mailboxes=None):
        """Method to create mailboxes on the database

            Args:
                display_name(str)       -- Name  used to create mailboxes

                database_name(str)      -- Mailboxes will be created on this database

                domain_name(str)        -- Exchange domain name

                number_of_mailboxes(str)  -- Number of mailboxes to be cerated

            Returns:
                None

            Raises:
                Exception -- Any error occured while creating mailboxes

        """
        try:
            self.log.info(
                'Creating mailboxes using powershell. '
                'Powershell Path %s', constants.CREATE_MAILBOXES)
            prop_dict = {
                "LoginPassword": self.exchange_pwd,
                "LoginUser": self.exchange_adminname,
                "displayName": display_name,
                "ExchangeDatabase": database_name,
                "ExchangeServerDomain": domain_name,
                "ExchangeServerName": self.exchange_server,
                "MailboxesNumber": number_of_mailboxes,
                "ExchangeCASServer": self.cas_server_name
            }
            output = self.host_machine.execute_script(
                constants.CREATE_MAILBOXES, prop_dict)
            if output.exit_code != 0:
                raise Exception("Failed to create mailboxes")

        except Exception as excp:
            self.log.exception("Exception in create_mailboxes(): %s", str(excp))
            raise excp

    def create_mailbox(self, display_name, alias_name, smtp, database_name):
        """Method to create mailbox on the database

            Args:
                display_name(str)       -- Name  used to create mailboxes

                alias_name(str)         -- Alias name for the mailbox

                smtp(str)               -- Smtp address for the mailbox

                database_name(str)      -- Mailboxes will be created on this database

            Returns:
                None

            Raises:
                Exception -- Any error occurred while creating mailboxes

        """
        try:
            self.log.info(
                'Creating mailboxes using powershell. '
                'Powershell Path %s', constants.CREATE_MAILBOXES)
            prop_dict = {
                "LoginPassword": self.exchange_pwd,
                "LoginUser": self.exchange_adminname,
                "aliasName": alias_name,
                "displayName": display_name,
                "SMTP": smtp,
                "ExchangeServerDomain": self.domain_name,
                "ExchangeDatabase": database_name,
                "ExchangeCAServer": self.cas_server_name
            }
            output = self.host_machine.execute_script(
                constants.CREATE_MAILBOX, prop_dict)
            if output.exit_code != 0:
                raise Exception("Failed to create mailboxes")

        except Exception as excp:
            self.log.exception("Exception in create_mailbox(): %s", str(excp))
            raise excp

    def create_journal_mailbox(self, display_name, alias_name, smtp,
                               database_name):
        """Method to create exchange on premise journal mailbox

            Args:
                alias_name(str)         -- Alias Name of the mailbox

                display_name(str)       -- Name used to create mailbox

                smtp(str)               -- Smtp address for the mailbox

                database_name(str)      -- Mailboxes will be created on this database

            Returns:
                None

            Raises:
                Exception -- Any error occured while creating mailbox

        """
        try:

            self.log.info(
                'Creating mailbox content using powershell. '
                'Powershell Path  %s', constants.CREATE_JOURNAL_MAILBOX)

            prop_dict = {
                "LoginPassword": self.exchange_pwd,
                "LoginUser": self.exchange_adminname,
                "aliasName": alias_name,
                "displayName": display_name,
                "SMTP": smtp,
                "ExchangeServerDomain": self.domain_name,
                "ExchangeDatabase": database_name,
                "ExchangeCAServer": self.cas_server_name
            }
            output = self.host_machine.execute_script(constants.CREATE_JOURNAL_MAILBOX, prop_dict)
            if output.exit_code != 0:
                raise Exception("Failed to create mailboxes %s", output.output)

        except Exception as excp:
            self.log.exception("Exception in create_journal_mailbox(): %s", excp)
            raise excp

    def create_archive_mailbox(self, display_name, alias_name, smtp,
                               database_name):
        """Method to create exchange on premise archive mailbox
            Args:
                display_name(str)       -- Name used to create mailboxes

                alias_name (str)        -- Alias Name of the mailbox

                smtp(str)               -- Smtp address for the mailbox

                database_name(str)      -- Mailboxes will be created on this database

            Returns:
                None

            Raises:
                Exception -- Any error occured while creating mailbox

        """
        try:
            self.log.info(
                'Creating archive mailbox using powershell. '
                'Powershell Path %s', constants.CREATE_ARCHIVE_MAILBOX)

            prop_dict = {
                "LoginPassword": self.exchange_pwd,
                "LoginUser": self.exchange_adminname,
                "aliasName": alias_name,
                "displayName": display_name,
                "SMTP": smtp,
                "ExchangeServerDomain": self.domain_name,
                "ExchangeDatabase": database_name,
                "ExchangeCAServer": self.cas_server_name
            }
            output = self.host_machine.execute_script(constants.CREATE_ARCHIVE_MAILBOX, prop_dict)
            if output.exit_code != 0:
                raise Exception("Failed to create mailbox %s", output.output)

        except Exception as excp:
            self.log.exception("Exception in create_archive_mailbox(): %s", excp)
            raise excp

    def clean_on_premise_mailbox_contents(self, alias_name):
        """Method to clean content from exchange on premise mailbox
            Args:
                alias_name (str)    -- Alias Name of the mailbox

            Returns:
                None

            Raises:
                Exception -- Any error occurred while cleanup of mailbox

        """
        try:
            self.log.info(
                'Deleting mailbox content using powershell. '
                'Powershell Path %s', constants.CLEANUP_CONTENT_ONPREMISE)

            prop_dict = {
                "LoginPassword": self.exchange_pwd,
                "LoginUser": self.exchange_adminname,
                "aliasName": alias_name,
                "ExchangeCASServer": self.cas_server_name
            }
            output = self.host_machine.execute_script(
                constants.CLEANUP_CONTENT_ONPREMISE, prop_dict)
            if output.exit_code != 0 and "Success          : True" not in output.output:
                raise Exception("Failed to clenaup mailbox %s", output.output)

        except Exception as excp:
            self.log.exception("Exception in cleanMailboxContents(): %s", str(excp))
            raise excp

    def create_online_mailbox(self, display_name, alias_name,
                              smtp):
        """Method to create exchnage online mailboxes

            Args:
                alias_name (str)        -- Alias Name of the mailbox

                display_name(str)       -- Name  used to create mailboxes

                smtp(str)               -- Smtp address for the mailbox

            Returns:
                None

            Raises:
                Exception -- Any error occurred while creating mailboxes

        """
        try:

            self.log.info(
                'Creating mailbox content using powershell. '
                'Powershell Path  %s', constants.EXCH_ONLINE_MAILBOX_PSH_OPS)

            prop_dict = {
                "LoginPassword": self.exchange_pwd,
                "LoginUser": self.exchange_adminname,
                "aliasName": alias_name,
                "OpType": "Create",
                "displayName": display_name,
                "SMTP": smtp,
                "ExchangeServerDomain": self.domain_name
            }
            output = self.host_machine.execute_script(constants.EXCH_ONLINE_MAILBOX_PSH_OPS, prop_dict)
            if output.exit_code != 0:
                raise Exception("Failed to create mailboxes %s", output.output)

        except Exception as excp:
            self.log.exception("Exception in create_online_mailbox(): %s", excp)
            raise excp

    def delete_exchange_online_mailbox(self, mailbox_smtp):
        """
            Method to delete an Exchange Online Mailbox
            Arguments:
                mailbox_smtp        (str)-- The SMTP of the mailbox to be deleted
                OR
                mailbox_smtp        (list)--    List of Mailboxes to be deleted
            Returns:
                None
        """
        try:
            if isinstance(mailbox_smtp, str):
                mailbox_smtp = [mailbox_smtp]
            for mailbox in mailbox_smtp:
                prop_dict = {
                    "LoginPassword": self.exchange_pwd,
                    "LoginUser": self.exchange_adminname,
                    "OpType": "Delete",
                    "SMTP": mailbox,
                    "aliasName": None,
                    "ExchangeServerDomain": self.domain_name
                }
                output = self.host_machine.execute_script(
                    constants.EXCH_ONLINE_MAILBOX_PSH_OPS, prop_dict)
                self.log.info(
                    'Delete Exchange Online Mailbox PowerShell output %s',
                    output.output)
            if output.exit_code != 0:
                raise Exception("Failed to delete mailbox")
        except Exception as excp:
            self.log.exception(
                "Exception in delete exchange online mailbox: %s", excp)
            raise excp

    def send_email_online_mailbox(self, smtp_list):
        """Method to send emails to exchange online mailboxes

            Args:
                smtp_list(list)  --  List of smtp address

        """
        try:

            self.log.info('Sending emails using powershell. Powershell Path %s',
                          constants.SEND_EMAIL)
            self.log.info('Send Script path %s', constants.SEND_SCRIPT_PATH)
            userlistpath = os.path.join(constants.SEND_SCRIPT_PATH, "userlist.txt")
            userlist = open(userlistpath, 'w')
            self.log.info('Sending emails to mailboxes')

            for smtp in smtp_list:
                userlist.write(smtp)
                self.log.info('mailbox smtp %s', smtp)
                userlist.write("\n")
            userlist.close()

            admin_pwd = b64decode(constants.ADMIN_PWD.encode()).decode()

            prop_dict = {
                "SMTPSever": constants.SMTP_SERVER,
                "LoginPassword": admin_pwd,
                "LoginUser": constants.ADMIN_USER,
                "NumberOfEmails": 50,
                "RootPath": constants.SEND_SCRIPT_PATH
            }
            output = self.host_machine.execute_script(constants.SEND_EMAIL, prop_dict)
            self.log.info('Send_Email powershell output %s', output.output)

            if output.exit_code != 0:
                raise Exception("Failed to send emails")
        except Exception as excp:
            self.log.exception("Exception in send_email_online_mailbox(): %s", excp)
            raise excp

    def get_online_groups(self, group_type):
        """
        Method to fetch all the online groups according to their type specified

        group_type(str) -- type of the groups which need to be found.
            Possible Values:-

            "Microsoft 365" :- To fetch all the online microsoft 365 groups
            "Distribution List" :- To fetch all the distribution groups
            "Mail Enabled Security Group" :- To fetch all the mail-enabled security groups
            "Dynamic Distribution Group"  :- To fetch all the dynamic distribution groups
        """
        prop_dict = {
            "LoginPassword": self.exchange_pwd,
            "LoginUser": self.exchange_adminname,
            "GroupType": group_type
        }
        output = self.host_machine.execute_script(constants.GET_ALL_GROUPS, prop_dict)
        if output.exit_code != 0:
            raise Exception("Failed to get all groups with the type {0}".format(group_type))
        ResultString = output.output
        GroupList = []
        for group in ResultString.split("\r\n"):
            if group == " ":
                continue
            else:
                GroupList.append(group)
        return GroupList

    def get_o365_groups(self):
        """Method to get all office 365 groups

            Raises:
                Exception -- Any error occurred while getting groups
        """
        prop_dict = {
            "LoginPassword": self.exchange_pwd,
            "LoginUser": self.exchange_adminname,
        }
        output = self.host_machine.execute_script(constants.GET_O365_GROUPS, prop_dict)
        if output.exit_code != 0:
            raise Exception("Failed to get o365 groups %s" % output.exception_message)
        return output.output

    def mountordismount_database(self, database_name, op_type):
        """Method to mount or dismount the database

            Args:
                database_name(str)      -- Database name for mounting or dismounting

                op_type(str)            -- operation to be performed on database.
                                            Mount or dismount

            Returns:
                None

            Raises :
                Exception               --Any error occured when mounting or
                dismounting the database

        """
        try:
            self.log.info(
                'dismounting/moutning database using powershell. '
                'Powershell Path %s', constants.MOUNTDISMOUNT_EXDB)

            prop_dict = {
                "LoginPassword": self.exchange_pwd,
                "LoginUser": self.exchange_adminname,
                "ExchangeDatabase": database_name,
                "ExchangeServerName": self.exchange_server,
                "operation": op_type,
                "ExchangeCASServer": self.cas_server_name
            }
            output = self.host_machine.execute_script(
                constants.MOUNTDISMOUNT_EXDB, prop_dict)
            if output.exit_code != 0:
                raise Exception("Failed to mount or dismount the database")

        except Exception as excp:
            self.log.exception("Exception in mountordismount_database(): %s", str(excp))
            raise excp

    def overwrite_exdb(self, database_name):
        """Method to select overwrite option for the database

            Args:
                database_name(str)      -- Database name for selecting overwrite option

            Returns:
                None

            Raises:
                Exception               -- Any error occurred when selecting overwrite
                option for the database

        """
        try:
            self.log.info(
                'overwriting database using powershell. '
                'Powershell Path %s', constants.OVERWRITE)

            prop_dict = {
                "LoginPassword": self.exchange_pwd,
                "LoginUser": self.exchange_adminname,
                "ExchangeDatabase": database_name,
                "ExchangeServerName": self.exchange_server,
                "ExchangeCASServer": self.cas_server_name
            }
            output = self.host_machine.execute_script(constants.OVERWRITE,
                                                      prop_dict)
            if output.exit_code != 0:
                raise Exception("Failed to select the overwrite option for a database")

        except Exception as excp:
            self.log.exception("Exception in overwrite_exdb(): %s", str(excp))
            raise excp

    def import_pst(self, display_name, pst_path):
        """Method to import pst for a given mailbox

            Args:
                display_name(str)      -- Mailbox name to import pst

                pst_path(str)          -- Path of pst which should be a UNC path

            Returns:
                None

            Raises:
                Exception             -- Any error occurred when importing pst

        """
        try:
            self.log.info(
                'import pst using powershell. '
                'Powershell Path  %s', constants.IMPORT_PST)
            prop_dict = {
                "LoginPassword": self.exchange_pwd,
                "LoginUser": self.exchange_adminname,
                "aliasName": display_name,
                "ExchangeCAServer": self.cas_server_name,
                "PstPath": pst_path
            }
            output = self.host_machine.execute_script(
                constants.IMPORT_PST, prop_dict)
            self.log.info('import pst for mailbox %s', display_name)
            if output.exit_code != 0:
                raise Exception("Failed to import pst")

        except Exception as excp:
            self.log.exception("Exception in import_pst(): %s", str(excp))
            raise excp

    def get_mailbox_name(self, database_name, outputfilename):
        """Method to get tha mailbox names for a given database and write to a output file

        Args:
            database_name(str)      --  Database name to get the associated mailbox names

            outputfilename(str)     --  path of the outfile for write the output

        Returns:
            outputfilepath(str)     --  Returns the outfilepath which is used in test case

        Raises:
            Exception               -- Any error occurred when getting the mailbox names
            for a database

        """
        try:
            output_path = os.path.join(LOG_DIR, outputfilename)
            self.log.info(
                'getting mailbox names for the database using powershell. '
                'Powershell Path %s', constants.GET_MBNAMES)

            prop_dict = {
                "LoginPassword": self.exchange_pwd,
                "LoginUser": self.exchange_adminname,
                "ExchangeDatabase": database_name,
                "ExchangeServerName": self.exchange_server,
                "output": output_path,
                "ExchangeCASServer": self.cas_server_name
            }
            output = self.host_machine.execute_script(constants.GET_MBNAMES,
                                                      prop_dict)
            if output.exit_code != 0:
                raise Exception("Failed to get mailbox names")

            return output_path

        except Exception as excp:
            self.log.exception("Exception in get_mailbox_name(): %s", str(excp))
            raise excp

    def exdbcopy_operations(self, database_name, passive_server, op_type):
        """Method to peform operations on passive copies for database

            Args:
                database_name(str)      -- Database name for performing copy operations

                passive_server(str)     -- Server name where the copy is present

                op_type(str)            -- operation to be performed on database.
                                                    Mount or dismount
            Returns:
                None

            Raises:
                Exception               -- Any error occured during suspending/resume/removing
                database copy
        """
        try:
            self.log.info(
                'suspending/resuming/removing database copy using powershell. '
                'Powershell Path  %s', constants.EXDBCOPY_OPS)

            prop_dict = {
                "LoginPassword": self.exchange_pwd,
                "LoginUser": self.exchange_adminname,
                "ExchangeDatabase": database_name,
                "ExchangeServerName": passive_server,
                "operation": op_type,
                "ExchangeCASServer": self.cas_server_name
            }
            output = self.host_machine.execute_script(
                constants.EXDBCOPY_OPS, prop_dict)
            if output.exit_code != 0:
                raise Exception("Failed to perfrom operation on passive copy for the database")

        except Exception as excp:
            self.log.exception("Exception in exdbcopy_operations(): %s", excp)
            raise excp

    def remove_database(self, database_name, db_edbfolder=None, db_logfolder=None):
        """Method to remove database

        Args:
            database_name(str)  --Database name to be removed

            db_edbfolder(str)   -- remove the database and edb path

            db_logfolder(str)   -- remove the database and log path

        Returns:
            None

        Raises:
            Exception           -- Any error occurred while removing databases

        """
        try:
            if db_edbfolder is None and db_logfolder is None:
                db_edbfolder = os.path.join(constants.EXCHANGE_DATABASES, database_name)
                db_logfolder = os.path.join(constants.EXCHANGE_DATABASES, database_name)
            self.log.info(
                'removing database using powershell. '
                'Powershell Path %s', constants.REMOVE_DATABASE)

            prop_dict = {
                "LoginPassword": self.exchange_pwd,
                "LoginUser": self.exchange_adminname,
                "ExchangeDatabase": database_name,
                "ExchangeServerName": self.exchange_server,
                "ExchangeCASServer": self.cas_server_name,
                "DatabaseEDBFolderPath": db_edbfolder,
                "DatabaselogFolderPath": db_logfolder
            }
            output = self.host_machine.execute_script(
                constants.REMOVE_DATABASE, prop_dict)
            if output.exit_code != 0:
                raise Exception("Failed to remove databases")

        except Exception as excp:
            self.log.exception("Exception in remove_database(): %s", excp)
            raise excp

    def check_mailbox(self, mailbox_name):
        """Method to remove database

        Args:
            mailbox_name(str)  -- Check the mailbox name whether it is present or not

        Returns:
            None

        Raises:
            Exception           -- Any error occurred while checking for mailbox

        """
        try:
            self.log.info(
                'checking whether mailbox is present or not. '
                'Powershell Path %s', constants.CHECK_MAILBOX)
            flag = 0
            prop_dict = {
                "LoginPassword": self.exchange_pwd,
                "LoginUser": self.exchange_adminname,
                "MailboxName": mailbox_name,
                "ExchangeCASServer": self.cas_server_name
            }
            output = self.host_machine.execute_script(
                constants.CHECK_MAILBOX, prop_dict)
            retrieved_name = ((output.output)).split("Name")[-1].splitlines()
            for temp_mb in retrieved_name:
                temp_mb1 = temp_mb.strip()
                temp_mb1 = ''.join(temp_mb1.split())
                if temp_mb1 == mailbox_name:
                    flag = 1
                    break
            if flag != 1:
                raise Exception("Mailbox is not found")

        except Exception as excp:
            self.log.exception("Exception in check_mailbox(): %s", str(excp))
            raise excp

    def get_databases(self):
        """Method to get all databases from exchange server

            Returns:
                None

            Raises:
                Exception    -- Any error occurred while getting database

        """

        try:

            self.log.info("Checking if DB exists")

            self.log.info('Getting all databases using powershell. '
                          'Powershell Path %s', constants.GET_DATABASES)
            prop_dict = {
                "LoginPassword": self.exchange_pwd,
                "LoginUser": self.exchange_adminname,
                "ExchangeServer": self.exchange_server,
            }
            output = self.host_machine.execute_script(constants.GET_DATABASES, prop_dict)
            if output.exit_code != 0:
                raise Exception("Failed to get databases")
            return output.output

        except Exception as excp:
            self.log.exception("Exception in get_databases(): %s", str(excp))
            raise excp

    def get_group_type(self, group_name):
        """
            Method to determine whether the group is an Exchange Distribution Group
            or an Office 365 User group

            Args:
                group_name  (str)   -- The group whose type is to be determined

            Returns:
                group_type  (Enum) -- The type of the group
                                        Object of type Enum for class Office365GroupTypes

            Raises:
                Exception -- Any error occured while getting the group type
        """
        try:
            prop_dict = {
                "LoginPassword": self.exchange_pwd,
                "LoginUser": self.exchange_adminname,
                "GroupName": group_name
            }
            output = self.host_machine.execute_script(constants.AD_GROUP_TYPE, prop_dict)
            group_type = output.formatted_output[0][0]

            group_types = constants.Office365GroupType
            if group_type == group_types.DISTRIBUTION.value:
                return group_types.DISTRIBUTION
            if group_type == group_types.OFFICE365.value:
                return group_types.OFFICE365
            if group_type == group_types.ROLEGROUP.value:
                return group_types.ROLEGROUP
        except Exception as excp:
            self.log.exception("Exception in get_group_type(): %s", str(excp))
            raise excp

    def o365_group_mailbox_count(self, group_name):
        """
            Method to get a coutn of the users in an Office 365 Group

            Args:
                group_name  (str)   -- The group whose type is to be determined

            Returns:
                member_count    (int)   -- Coutn of the number of mailboxes in the group

            Raises:
                Exception -- Any error occured while getting the Office 365 Group Member Count
        """
        try:
            prop_dict = {
                "LoginPassword": self.exchange_pwd,
                "LoginUser": self.exchange_adminname,
                "GroupName": group_name
            }

            output = self.host_machine.execute_script(constants.O365_USER_COUNT, prop_dict)

            return int(output.formatted_output)
        except Exception as excp:
            self.log.exception("Exception in o365_group_mailbox_count(): %s", str(excp))
            raise excp

    def dist_group_user_count(self, group_namwe):
        """
        Method to get the number of users in an online Mailbox
            Args:
                group_name  (str)   -- The group whose type is to be determined

            Returns:
                member_cout(int) -- The number of mailboxes in the distribution

            Raises:
                Exception -- Any error occured while getting the group member count

        """
        try:
            prop_dict = {
                "LoginPassword": self.exchange_pwd,
                "LoginUser": self.exchange_adminname,
                "GroupName": group_namwe
            }
            output = self.host_machine.execute_script(constants.DIST_GROUP_MEMBER_COUNT, prop_dict)

            return int(output.formatted_output)
        except Exception as excp:
            self.log.exception("Exception in dist_group_user_count(): %s", str(excp))
            raise excp

    def get_mailbox_guid(self, mailbox_list, environment):
        """
            Method to get fetch the GUID for the list of mailboxes
            Arguments:
                mailbox_list        (list)--    List of mailboxes to fetch the GUID of
                environment         (str)--     mailbox Environment
                    Accepted Values:
                        "AzureAD" and "OnPrem:

            Returns
                mailbox_guid_sict   (dict)--    Dictionary of Mailbox GUIDs
                    Format
                        key: mailbox_alias_in_lower_case
                        value: GUID in all caps
        """
        mailbox_guid_dict = dict()
        for mailbox in mailbox_list:
            prop_dict = {
                "LoginPassword": self.exchange_pwd,
                "LoginUser": self.exchange_adminname,
                "Mailbox": mailbox if environment == "OnPrem" else mailbox + "@" + self.domain_name,
                "Environment": environment,
                "ExchangeCASServer": self.cas_server_name
            }
            try:
                self.log.info('Fetching Mailbox GUID for mailbox: {}'.format(mailbox))
                output = self.host_machine.execute_script(
                    constants.GET_MAILBOX_GUID, prop_dict)
                mailbox_guid = output.formatted_output
                mailbox_guid = mailbox_guid.replace("-", "X").upper()
                mailbox_guid_dict[mailbox.lower()] = mailbox_guid
            except Exception as ex:
                self.log.error("Exception in fetch mailbox GUID: {}".format(ex))
                raise Exception("Unable to fetch the mailbox GUIDs")

        return mailbox_guid_dict

    def exch_online_operations(self, alias_name="", smtp_address="", display_name="", op_type=""):
        """
            Method to perform operations for Exchange Online Mailbox

            Arguments:
                alias_name          (str)--     Mailbox Alias Name
                display_name        (str)--     Mailbox Display Name
                smtp_address        (str)--     Mailbox SMTP Address
                op_type             (str)--     Type of the operation to be performed
                    Possible Values
                        "CREATE"        --      To create a mailbox
                        "DELETE"        --      To delete a mailbox
                        "MODIFYSMTP"    --      To modify the SMTP Address
                        "CLEANUP"       --      To cleanup mailbox content
        """

        if op_type == "":
            raise Exception("OpType not specified")

        display_name = alias_name if display_name == "" else display_name
        smtp_address = alias_name + "@" + self.domain_name if smtp_address == "" else smtp_address

        prop_dict = {
            "LoginPassword": self.exchange_pwd,
            "LoginUser": self.exchange_adminname,
            "aliasName": alias_name,
            "OpType": op_type,
            "SMTP": smtp_address,
            "displayName": display_name,
            "ExchangeServerDomain": self.domain_name
        }
        self.log.info("Executing Operation {} using Exchange Mailbox PowerShell".format(op_type))
        try:
            output = self.host_machine.execute_script(
                constants.EXCH_ONLINE_MAILBOX_PSH_OPS, prop_dict)
            self.log.info('Exchange Online Mailbox PowerShell output %s for operation %s',
                          output.formatted_output, op_type)

            if output.exit_code != 0:
                raise Exception(
                    "Failed to perform operation {} for Exchange Mailbox".format(op_type))
        except Exception as excp:
            self.log.exception(
                "Exception in exch_online_operations: %s", excp)
            raise excp

        if op_type == "ModifySMTP":
            return "modified" + smtp_address

    def exch_online_o365_group_operations(self, op_type, group_name, group_members=None):
        """
            Method to perform operations elated to Online AD Group of type Office 365

            Arguments:
                group_name          (str)--     Name of the Group
                group_members       (list)--    List of SMTP of group member
                op_type              (str)--    The type of operation to be performed
                    Allowed Values:
                        "AddGroupMembers" --    Add members to an O365 Group
                        "Create"          --    Create an Office 365 Group
                        "MemberCount"     --    Count the number of members in an Group
                            Supported Group Types: Office 365 Group, Distribution List

            Returns:
                member_count        (int)--     In the case of OpType: MemberCount

        """
        if group_members is None:
            group_members = []
        if op_type == "":
            raise Exception('OpType not chosen')

        group_members_smtp = list()
        if op_type == "AddGroupMembers":
            if not isinstance(group_members, list) and len(group_members) == 0:
                raise Exception(
                    'For operation AddGroupMembers, the group emmebrs need to be a list of length more than 0')

            for member in group_members:
                group_members_smtp.append(member + "@" + self.domain_name)

        self.log.info(
            'Performing OPeration on Office 365 AD Group using PowerShell:  %s', constants.EXCH_ONLINE_O365_PSH_OPS)
        prop_dict = {
            "OpType": op_type,
            "LoginPassword": self.exchange_pwd,
            "LoginUser": self.exchange_adminname,
            "GroupName": group_name,
            "GroupMembers": "\",\"".join(group_members_smtp)
        }
        try:
            self.log.info('Performing Operation: {} for O365 Group'.format(op_type))
            output = self.host_machine.execute_script(
                constants.EXCH_ONLINE_O365_PSH_OPS, prop_dict)

            if op_type == "MemberCount":
                return int(output.formatted_output)

            if output.exit_code != 0:
                raise Exception(
                    "Failed to perform the operation on the Office 365 Group %s",
                    output.output)
        except Exception as excp:
            self.log.exception("Exception in exch_online_o365_group_operations(): %s", excp)
            raise excp

    def exch_online_public_folder_ops(self, op_type, public_folder_name=None, prop_dict=dict()):
        """"
            Method to perform operations for Exchange Online Public Folders

            Arguments:
                op_type                     (str)--      OpType for the operation to be performed
                    List of possible values:
                        CreatePF            --          Create the Public Folder
                        Delete              --          Delete the Public Folder
                        MailEnable          --          Mail Enable the Public Folder
                        ItemCount           --          Item count for Public Folder items
                        GetFolderIDs        --          Get the Attribute values for All Public Folder

                public_folder_name          (str)--     Name of the Public Folder
                            None for Operation Get Folder IDs

                prop_dict                   (dict)--    Prop_Dict for Public Folder operations
                    Possible Keys:
                        mail_enabled        (bool)--    For Delete Public Folder operation
                        hash_algo           (str)--     Hashing Algorithm to be used for Get Attribute ID operation
                        attribute           (str)--     Attribute value to be fetched in GetAttributeID operaiton

            Returns:

        """
        try:
            if public_folder_name is None and op_type == "CreatePF":
                public_folder_name = constants.PUBLIC_FOLDER_DEFAULT % self.ex_object.tc_object.id

            pwsh_prop_dict = {
                "LoginPassword": self.exchange_pwd,
                "LoginUser": self.exchange_adminname,
                "Attribute": prop_dict.get("attribute", None),
                "HashAlgo": prop_dict.get("hash_algo", None),
                "OpType": op_type,
                "PublicFolderName": public_folder_name,
                "MailEnabledStatus": prop_dict.get("mail_enabled", None)
            }
            output = self.host_machine.execute_script(constants.EXCH_ONLINE_PF_OPS, pwsh_prop_dict)

            if output.exit_code != 0:
                self.log.info('Exception in Exchange Online Public Folder Ops with op_type{}'.format(op_type))
                self.log.info('Prop_dict: {}'.format(prop_dict))
                raise Exception("Exception in Exchange Online Public FOlder Ops ")

            if op_type == "GetFolderIDs":
                return output.formatted_output.split('\r\n')
            elif op_type == "ItemCount":
                return int(output.formatted_output)
            elif op_type == "MailEnable":
                return output.output.split()[-1]
            elif op_type == "CreatePF":
                return public_folder_name

        except Exception as excp:
            self.log.exception("Exception in exch_online_public_folder_ops(): %s", str(excp))
            raise excp

    def check_online_service_account_permissions(self, service_account: str):
        """"
            Method to verify that necessary permissions are present with an Exchange online service account

            Arguments:
                service_account         (str)--      Service accounnt to check the permissions for

            Returns:
                service_account_permission_set
                                        (bool)--    Whether the expected permissions are present/
                                                    applied on the service account passed
        """
        try:

            pwsh_prop_dict = {
                "LoginPassword": self.exchange_pwd,
                "LoginUser": self.exchange_adminname,
                "ServiceAccount": service_account
            }
            output = self.host_machine.execute_script(constants.CHECK_SERVICE_ACCOUNT_PERMISSIONS, pwsh_prop_dict)

            if output.exit_code != 0:
                self.log.exception('Exception while checking the permission of the service account')
                raise Exception("Exception in Check Online Service Account Permissions ")
            if output.formatted_output.lower() == 'true':
                return True
            else:
                self.log.info("Expected permission not found with service account")
                self.log.info("Check Service Account permissions output: {}".format(output))
                return False
        except Exception as excp:
            self.log.exception("Exception in check_online_service_account_permissions(): %s", str(excp))
            raise excp

    def get_licensed_users(self) -> list:
        """
            Method to get a list of mailboxes with valid Exchange LIcense Assigned
        """
        try:

            prop_dict = {
                "LoginPassword": self.exchange_pwd,
                "LoginUser": self.exchange_adminname,
            }
            output = self.host_machine.execute_script(constants.LICENSED_MAILBOXES, prop_dict)

            if output.exit_code != 0:
                self.log.exception('Exception while fetching the list of licensed users')
                raise Exception("Exception in Get Licensed Exchange Users ")
            if output.formatted_output:
                arr = output.formatted_output.split("UserPrincipalName :")
                _users = [_user for _user in map(lambda x: x.strip(), arr) if _user]
                return _users
        except Exception as excp:
            self.log.exception("Exception in check_online_service_account_permissions(): %s", str(excp))
            raise excp
