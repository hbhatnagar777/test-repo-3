# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""Utilities for the Laptop webconsole TestCases"""

from cvpysdk.commcell import Commcell
from Web.Common.exceptions import CVTestStepFailure
from AutomationUtils.machine import Machine
from AutomationUtils.options_selector import OptionsSelector
from AutomationUtils import logger
from Server.JobManager.jobmanager_helper import JobManager


class LaptopUtils:
    """Utilities for the Laptop webconsole TestCases"""

    def __init__(self,init_object):
        """Initialize instance of the LaptopUtils class.

        Args:
            testcase: (object) --  TestCase object

        """

        self._init_object = init_object
        if isinstance(init_object, Commcell):
            self._testcase = None
            self._commcell = init_object
        else:
            self._testcase = init_object
            self._commcell = self._testcase.commcell

        self.utility = OptionsSelector(self._commcell)
        self.job_manager = JobManager(commcell=self._commcell)
        self._log = logger.get_log()

        self.client_machine = None
        self.client_object = None
        self.subclient_obj = None
        self.source_dir  = None
        self._client_object = None
        self._machine_object = None
        self._browser_obj = None
        self._computers_obj = None
        self._os_info = None

    @property
    def browser_obj(self):
        """ Get browser_obj"""
        return self._browser_obj

    @browser_obj.setter
    def browser_obj(self, value):
        """ Set browser_obj"""
        self._browser_obj = value

    @property
    def computers_obj(self):
        """ Get computers_obj"""
        return self._computers_obj

    @computers_obj.setter
    def computers_obj(self, value):
        """ Set computers_obj"""
        self._computers_obj = value

    @property
    def client_object(self):
        """ Get client_object"""
        return self._client_object

    @client_object.setter
    def client_object(self, value):
        """ Set client_object"""
        self._client_object = value

    @property
    def machine_object(self):
        """ Get machine_object"""
        return self._machine_object

    @machine_object.setter
    def machine_object(self, value):
        """ Set machine_object"""
        self._machine_object = value

    @property
    def subclient_object(self):
        """ Get subclient_object"""
        return self._subclient_object

    @subclient_object.setter
    def subclient_object(self, value):
        """ Set subclient_object"""
        self._subclient_object = value

    @property
    def folder_path(self):
        """ Get folder_path"""
        return self._folder_path

    @folder_path.setter
    def folder_path(self, value):
        """ Set folder_path"""
        self._folder_path = value

    @property
    def os_info(self):
        """ Get Os_info"""
        return self._os_info

    @os_info.setter
    def os_info(self, value):
        """ Set Os_info"""
        self._os_info = value

    def check_clients_exists(self, input_clients, console_clients):
        """
        verify clients exists on 'My data' page

        Args:

            input_clients (list)    --  list of clients given as inputs to the tescase

            console_clients (list)  --  list of clients configured on webconsole

        """
        clients_found = []
        for each_client in input_clients:
            if each_client in console_clients:
                clients_found.append(each_client)
        if not clients_found:
            raise CVTestStepFailure("None of the clients found in the web console")
        else:
            self._log.info("Clients exists on My data page")
            return clients_found

    def create_file(self, client, client_path, file_path=None, files=0):
        """
        Create the file on given machine

        Args:

            client        (str)/(Machine object)  -- Client name or Machine object

            client_path(str)     --  directory to create the file

            file_path(str)     --   file path that has to be created

            Files(int)         --  Number of files to be created in the file

        """

        try:
            machine = self.utility.get_machine_object(client)
            client_name = machine.machine_name
            if not machine.check_directory_exists(client_path):
                machine.create_directory(client_path)
            if files:
                for i in range(files):
                    create_file = client_path + '/' + 'backupfile_'+str(i)
                    machine.create_file(create_file, "Webconsole automation test data")
            else:
                machine.create_file(file_path, "Webconsole automation test data")
            self._log.info("Test data created successfully on machine: '[{0}]' with given path {1}".
                           format(client_name, file_path))
        except Exception as excep:
            raise CVTestStepFailure(excep)

    def cleanup_testdata(self, client, file_path):
        """
        Removes the file created on given machine

        Args:

            client        (str)/(Machine object)  -- Client name or Machine object

            file_path(str)    --   file path that has to be deleted

        """
        try:
            machine = self.utility.get_machine_object(client)
            client_name = machine.machine_name
            if machine.check_file_exists(file_path):
                machine.delete_file(file_path)
                self._log.info('Successfully deleted file {0} on client: [{1}]'.format(file_path, client_name))
        except Exception as excep:
            raise CVTestStepFailure(excep)

    def generate_test_data(self, client, file_path, dirs=0, files=5):
        """Generates and adds test data at the given path with the specified options.

        Args:

            client        (str)/(Machine object)  -- Client name or Machine object

            file_path (str)   --  directory path where the data will be generated

            dirs     (int)   --  number of directories to be created
                default: 0

            files (int)     -- number of files to be created
                default: 5

        """
        try:
            machine = self.utility.get_machine_object(client)
            client_name = machine.machine_name
            self._log.info('Started creating test data on client: [{0}]'.format(client_name))
            machine.generate_test_data(file_path, dirs=dirs, files=files)
            self._log.info("Test data created successfully on machine: '[{0}]' with given path {1}".
                           format(client_name, file_path))

        except Exception as excep:
            raise CVTestStepFailure(excep)

    def remove_directory(self, client, client_path):
        """
        Removes a directory on the client.

        Args:

            client        (str)/(Machine object)  -- Client name or Machine object

            client_path(str)   -- Directory name that has to be removed

        """
        try:
            machine = self.utility.get_machine_object(client)
            client_name = machine.machine_name
            self._log.info('Started deleting directory {0} on client: [{1}]'.format(client_path, client_name))
            if machine.check_directory_exists(client_path):
                machine.remove_directory(client_path)
                self._log.info('Successfully deleted path {0} on client: [{1}]'.format(client_path, client_name))

        except Exception as excep:
            raise CVTestStepFailure(excep)

    def get_files_in_path(self, client_name, folder_path):
        """Returns the list of all the files at the given folder path.

        Args:

            client_name    (str)   -- name of the client

            folder_path    (str)   --  full path of the folder to get the list of files from

        Returns:
            list    -   list of the files present at the given path

        """
        try:
            self._log.info('Started getting list of all the files at the given folder path. {0} on client: [{1}]'
                           .format(folder_path, client_name))
            files_list = []
            machine = Machine(client_name, self._testcase.commcell)
            files_list = machine.get_files_in_path(folder_path)
            return files_list

        except Exception as excep:
            raise CVTestStepFailure(excep)

    def verify_job_status_in_gui(self, job_id, expected_state):
        """ Validate if the current job state and expected status matches

            Args:
                job_id  (str)

                expected_state(str)    -- Expected job id state.
                                          suspended/completed etc..
            Returns:
                None

        """
        try:
            job_object = JobManager(job_id, self._testcase.commcell)
            job_object.validate_job_state(expected_state)
            self._log.info("Job [{0}] is in expected state in Java gui as per webconsole".format(job_id))
        except Exception as excep:
            raise CVTestStepFailure(excep)

    def get_subclient_content_from_gui(self, client_name):
        """get the list of subclient content from cs.

            Args:

                client_name (str)  --  Machine to get the subclient content

            Returns:
                content_list(list)  -- list of subclient content.

        """
        commcell_obj = self._testcase.commcell
        client_obj = commcell_obj.clients.get(client_name)
        agent_obj = client_obj.agents.get('File System')
        backupset_obj = agent_obj.backupsets.get('defaultBackupSet')
        subclient_obj = backupset_obj.subclients.get('default')
        content_list = subclient_obj.content
        return content_list

    def run_backup_job(self, ida_utils, client_name, backup_type='Full'):
        """run the backup job on subclient.

            Args:

                ida_utils(obj)    -- instance of CommonUtils class

                client_name (str)  --  client machine where synthetic full job will run

            Returns:
                job object(object)  -- Job class instance for the backup job

        """
        commcell_obj = self._testcase.commcell
        client_obj = commcell_obj.clients.get(client_name)
        agent_obj = client_obj.agents.get('File System')
        backupset_obj = agent_obj.backupsets.get('defaultBackupSet')
        subclient_obj = backupset_obj.subclients.get('default')
        job_obj = ida_utils.subclient_backup(subclient_obj, backup_type)
        return job_obj

    def add_usergroup_permissions(self,
                                  allowed_profile,
                                  destination_folder,
                                  permission='ReadAndExecute'):
        """call the method to add required ACLS for the given folder
            Args:

                allowed_profile(str)    -- User/group  for which ACEs are required

                destination_folder(str)  -- File or folder path

                permission      (str)   --  Permission to set or remove to file

            Returns:
                None      
        """
        self._log.info("Modifying ACLS of client [{0}] on folder [{1}] with profile [{2}]"
                      .format(self._client_object.client_name, self.folder_path, allowed_profile))
        if self.os_info == "Windows":
            self.machine_object.windows_operation(
                user=allowed_profile,
                path=destination_folder,
                action='Allow',
                permission=permission,
                modify_acl=True,
                folder=True,
                inheritance=2
            )
        else:
            string_one = str('chmod +a')
            string_two= str('allow list,search,readattr,readextattr,readsecurity')

            cmd = string_one + " '" + str(allowed_profile) + ' ' + string_two + "' " + destination_folder
            output = self.machine_object.execute_command(cmd)
            if output.exit_code != 0:
                self._log.exception("Exception while adding the User to folder")
                raise Exception('Unable to add the permitted user to folder')
        self._log.info("User [{0}] is added to the folder with given permissions on [{1}]"
                      .format(allowed_profile, destination_folder))

    def deny_usergroup_permissions(self,
                                   denyed_profile,
                                   destination_folder,
                                   permission='ReadAndExecute'):
        """call the method to remove user group permissions on given folder
        
            Args:

                denyed_profile(str)    -- User/group  for which ACEs are required

                destination_folder(str)  -- File or folder path

                permission      (str)   --  Permission to set or remove to file

            Returns:

                None      

        """
        self._log.info("Denying the user/ group [{0}] permissions on folder [{1}] for the client [{2}] "
                  .format(denyed_profile, self.folder_path, self._client_object.client_name))
        if self.os_info == "Windows":
            self.machine_object.windows_operation(
                user=denyed_profile,
                path=destination_folder,
                action='Deny',
                permission=permission,
                modify_acl=True,
                folder=True,
                inheritance=2
            )
        else:
            
            string_one = str('chmod +a')
            string_two= str('deny list,search,readattr,readextattr,readsecurity')
            cmd = string_one + " '" + str(denyed_profile) + ' ' + string_two + "' " + destination_folder
            output = self.machine_object.execute_command(cmd)
            if output.exit_code != 0:
                self._log.exception("Exception while adding the User to folder")
                raise Exception('Unable to add the permitted user to folder')
           
        self._log.info("User / User group  [{0}] permissions removed from folder [{1}]"
                  .format(denyed_profile, destination_folder))

        
    def verify_browse_result(self, current_user):
        """verify browse result for the given user 
        
        Args:
        
            current_user (str) -- User name for which verifying the browse result
        
        Returns:
            None   
               
        """
        self._log.info("****** Verifying the browse result from webconsole for the given user [{0}] *****".format(current_user))
        self._computers_obj.get_client_restore_link(client_name=self._client_object.client_name, goto_link=True)
        self._log.info("Client path is : {0}".format(self.folder_path))
        self.browser_obj.navigate_to_restore_page(self.folder_path)
        browse_res = self.browser_obj.read_browse_results()
        file_found = 0
        for each_row in browse_res:
            if each_row['FolderName'] !='NA':
                file_found = 1
                self._log.info("***** User [{0}] able to browse the data [{1}] *****".format(current_user, self.folder_path))
                break
        if file_found == 0:
            exp = "User [{0}] Unable to browse the data from [{1}]"\
                .format(current_user, self.folder_path)
            self._log.exception(exp)
            raise Exception(exp)
    def verify_browse_for_denyeduser(self, denyed_user, browse_folder_path, folder_to_verify):
        """verify browse result for denyed user

        Args:
        
            current_user (str) -- User name for which verifying the browse result
       
        Returns:

            None      
       
        """
        self._log.info(" Verifying the browse result from webconsole for the owner [{0}] *****".format(denyed_user))
        self._computers_obj.get_client_restore_link(client_name=self._client_object.client_name, goto_link=True)
        self._log.info("Client path is : {0}".format(browse_folder_path))
        self.browser_obj.navigate_to_restore_page(browse_folder_path)
        browse_res = self.browser_obj.read_browse_results()
        for _each in browse_res:
            if _each['FolderName'] == folder_to_verify:
                exp = "User [{0}] able to browse the data even does not have permissions on [{1}]"\
                    .format(denyed_user, self.folder_path)
                self._log.exception(exp)
                raise Exception(exp)
                
        self._log.info("As Expected! User [{0}] Unable to browse the data [{1}]".format(denyed_user, self.folder_path))
    
        
