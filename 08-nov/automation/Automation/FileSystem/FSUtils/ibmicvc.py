# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
Helper file for performing IBMi File System operations through cvc
IBMiCVC: Helper class to perform cvc operations which derives from the UnixFSHelper.

IBMiCVC
==========

    __init__()              --  initializes IBMi cvc helper object

    add_kwargs()            --  append token file and security to command.

    login()                --  login to CS from IBMi command line.

    logout()               --  logout from CS through IBMi command line.

    create_sc()            --  Create subclient in specific backupSet from IBMi command line.

    update_sc()            --  Update subclient in specific backupSet from IBMi command line.

    delete_sc()            --  Delete subclient in specific backupSet from IBMi command line.

    start_backup()         --  Start backup from IBMi command line.

    job_status()           --  Get job status from IBMi command line.

    start_restore()        --  start restore from IBMi command line.

Attributes
----------

    **num_libraries**               --  The number of libraries created for this testcase
"""

import re
import time

from datetime import datetime
from FileSystem.FSUtils.unixfshelper import UnixFSHelper
from FileSystem.FSUtils.ibmihelper import IBMiHelper

class IBMiCVC(IBMiHelper):
    """Helper class to perform cvc operations"""

    def __init__(self, testcase):
        """Initialize instance of the IBMi Helper class."""
        super(IBMiCVC, self).__init__(testcase)
        self._python = str(testcase.tcinputs.get('whichPython', "python"))
        self._sdkpath = str(testcase.tcinputs.get('sdkPath', None))
        self._cs = str(testcase.inputJSONnode['commcell']['webconsoleHostname'])
        self._cs_user = str(testcase.inputJSONnode['commcell']['commcellUsername'])
        self._cs_password = str(testcase.inputJSONnode['commcell']['commcellPassword'])
        self.client_name = str(self.testcase.tcinputs.get('ClientName'))
        self.init_command = "\"{0}\" \"{1}/cvcmd/cvc.py\"".format(self._python,
                                                                  self._sdkpath)

    def add_kwargs(self, command, is_login=False, **kwargs):
        """
        Add kwargs to command and return the new command.

        Args:
            command                 (str)   : command to add kwargs

            **kwargs            (dict)  : dictionary of optional arguments
            options:
                    tokenfile       (str)    : name of token file to be created.
                        default: None

                    security_key    (str)   : 16 character encryption key.
                        default: None
        :return:
           command
        """
        if 'tokenfile' in kwargs.keys():
            if is_login:
                command = "{0} -f \"{1}/{2}\"".format(command, self._sdkpath, kwargs.get('tokenfile'))
            else:
                command = "{0} -tf \"{1}/{2}\"".format(command, self._sdkpath, kwargs.get('tokenfile'))

        if 'security_key' in kwargs.keys():
            if len(kwargs.get('security_key')) == 16:
                command = "{0} -k {1}".format(command, kwargs.get('security_key'))
            else:
                raise Exception("Length of encryption key should be of length 16 characters")
        return command

    def login(self, validate=True, **kwargs):
        """
        login to CS from IBMi command line.

        Args:
            validate            (bool)  :   Validate the login operation

            **kwargs            (dict)  : dictionary of optional arguments
            options:
                    tokenfile          (str)    : name of token file to be created.
                        default: None

                    security_key        (str)   : 16 character encryption key.
                        default: None

        return:
        command output or status.
        """
        command = "{0} login -wch {1} -u '{2}' -p '{3}' -https false".format(self.init_command,
                                                              self._cs,
                                                              self._cs_user,
                                                              self._cs_password)

        output = self.testcase.client_machine.run_ibmi_command(self.add_kwargs(command, is_login=True, **kwargs),
                                                               validate=validate)
        if not validate:
            return output.output

        if "Login Successful" in output.output:
            self.log.info("CVC Login is successful")
            return True
        else:
            raise Exception("CVC login has failed with exception [{0}]".format(output))

    def logout(self, validate=True, **kwargs):
        """
        logout from CS through IBMi command line.

        Args:
            validate            (bool)  : Validate the logout operation

            **kwargs            (dict)  : dictionary of optional arguments
            options:
                    tokenfile          (str)    : name of token file to be created.
                        default: None

                    security_key        (str)   : 16 character encryption key.
                        default: None

        return:
           command output or status.
        """
        command = "{0} logout".format(self.init_command)

        output = self.testcase.client_machine.run_ibmi_command(self.add_kwargs(command, **kwargs), validate=validate)

        if not validate:
            return output.output

        if "Logout Successful" in output.output:
            self.log.info("CVC logout is successful")
            return True
        else:
            raise Exception("CVC logout has failed with exception [{0}]".format(output))

    def create_sc(self, subclient_name,
                  content,
                  storage_policy,
                  backupset_name=None,
                  exception_content=None,
                  validate=True,
                  **kwargs):
        """
        Create subclient in specific backupSet from IBMi command line.

        Args:

            subclient_name          (str)   :   Name of the new subclient

            content                 (list)  : list of the content for this testcase

            storage_policy          (str)   :   Name of the storage policy to use

            backupset_name          (str)   : name of the backupSet.
                default: NONE

            exception_content       (list) : List of exceptions
                default : None

            validate            (bool)  : Validate subclient creation.

            **kwargs            (dict)  : dictionary of optional arguments
            options:
                    tokenfile          (str)    : name of token file to be created.
                        default: None

                    security_key        (str)   : 16 character encryption key.
                        default: None

        :return:
           command output or status.
        """
        command = "{0} subclient -create -c {1} -sc {2} -dsp {3}".format(
            self.init_command,
            self.client_name,
            subclient_name,
            storage_policy)

        if backupset_name is not None:
            command = "{0} -bk {1}".format(command, backupset_name)

        for each in content:
            command = "{0} -path \"{1}\"".format(command, each)

        if exception_content is not None:
            for each in exception_content:
                command = "{0} -excludepath \"{1}\"".format(command, each)

        output = self.testcase.client_machine.run_ibmi_command(self.add_kwargs(command, **kwargs), validate=validate)
        if not validate:
            return output.output
        if "Subclient creation completed" in output.output:
            self.log.info("CVC subclient creation is successful")
            return True
        else:
            raise Exception("CVC subclient creation has failed with exception [{0}]".format(output))

    def update_sc(self, subclient_name,
                  content=None,
                  storage_policy=None,
                  backupset_name=None,
                  exception_content=None,
                  overwrite=False,
                  validate=True,
                  **kwargs):
        """
        update subclient in specific backupSet from IBMi command line.

        Args:
            subclient_name          (str)   :   Name of the new subclient

            content                 (list)  : list of the content for this testcase

            storage_policy          (str)   :   Name of the storage policy to use

            backupset_name          (str)   : name of the backupSet.
                default: NONE

            exception_content       (list) : List of exceptions
                default : None

            overwrite              (bool) : overwrite conetnt and/or exceptions
                default : False

            validate            (bool)  : Validate subclient update operation

            **kwargs            (dict)  : dictionary of optional arguments
            options:
                    tokenfile          (str)    : name of token file to be created.
                        default: None

                    security_key        (str)   : 16 character encryption key.
                        default: None

        :return:
           command output or status.
        """
        command = "{0} subclient -update -c {1} -sc {2} -overwrite {3}".format(
            self.init_command,
            self.client_name,
            subclient_name,
            overwrite)

        if backupset_name is not None:
            command = "{0} -bk {1}".format(command, backupset_name)

        if content is not None:
            for each in content:
                command = "{0} -path \"{1}\"".format(command, each)

        if exception_content is not None:
            for each in exception_content:
                command = "{0} -excludepath \"{1}\"".format(command, each)
        if storage_policy is not None:
            command = "{0} -dsp {1}".format(command, storage_policy)

        output = self.testcase.client_machine.run_ibmi_command(self.add_kwargs(command, **kwargs),
                                                               validate=validate)

        if not validate:
            return output.output

        if "Subclient update completed" in output.output:
            self.log.info("CVC subclient update is successful")
            return True
        else:
            raise Exception("CVC subclient updation has failed with exception [{0}]".format(output))

    def delete_sc(self, subclient_name, backupset_name=None, validate=True, **kwargs):
        """
        Delete subclient in specific backupSet from IBMi command line.

        Args:
            subclient_name          (str)   :   Name of the new subclient

            backupset_name          (str)   : name of the backupSet.
                default: NONE

            validate            (bool)  : Validate subclient delete operation.
            	default: True

            **kwargs            (dict)  : dictionary of optional arguments
            options:
                    tokenfile          (str)    : name of token file to be created.
                        default: None

                    security_key        (str)   : 16 character encryption key.
                        default: None

        :return:
           command output or status.
        """
        command = "{0} subclient -delete -c {1} -sc {2}".format(
            self.init_command,
            self.client_name,
            subclient_name)

        if backupset_name is not None:
            command = "{0} -bk {1}".format(command, backupset_name)

        output = self.testcase.client_machine.run_ibmi_command(self.add_kwargs(command, **kwargs),
                                                               validate=validate)

        if not validate:
            return output.output

        if "Subclient deletion completed" in output.output:
            self.log.info("CVC: subclient deletion is successful")
            return True
        else:
            raise Exception("CVC subclientdeletion has failed with exception [{0}]".format(output))

    def start_backup(self, subclient_name,
                     backupset_name=None,
                     backup_type="full",
                     wait=False,
                     validate=True,
                     **kwargs):
        """
        start backup from IBMi command line.

        Args:
            subclient_name          (str)   :   Name of the new subclient

            backupset_name          (str)   : name of the backupSet.
                default: NONE

            backup_type             (str)   :   Name of the new subclient

            wait                    (bool)  :   wait till backup completes.
            	default: False

            validate                (bool)  : Validate the backup operation
            	default: True

            **kwargs                (dict)  : dictionary of optional arguments
            options:
                    tokenfile       (str)    : name of token file to be created.
                        default: None

                    security_key    (str)   : 16 character encryption key.
                        default: None
        :return:
           command output or status or job_id
        """
        assert backup_type.lower() in ['full', 'incremental', 'synthetic_full', 'differential'], \
            "Backup type cannot be {0}. Backup Type should be " \
            "full/incremental/synthetic_full/differential".format(backup_type)

        command = "{0} backup -c {1} -sc {2} -l {3}".format(self.init_command,
                                                            self.client_name,
                                                            subclient_name,
                                                            backup_type.lower())

        if backupset_name is not None:
            command = "{0} -bk {1}".format(command, backupset_name)

        output = self.testcase.client_machine.run_ibmi_command(self.add_kwargs(command, **kwargs),
                                                               validate=validate)

        if not validate:
            return output.output

        job_id = re.findall('<JobID>(\d+)</JobID>', output.output)
        if job_id[0] is None:
            raise Exception("CVC subclient backup has failed to start with exception [{0}]".format(output))

        job = self.job_status(job_id=job_id[0], wait=wait, **kwargs)
        self.log.info("{0} backup job#{1} is {2}".format(backup_type, job.get('id'), job.get('status')))
        return job

    def job_status(self, job_id, wait=False, validate=True, **kwargs):
        """
        Get job status from IBMi command line.

        Args:
            job_id                  (int)   :   job ID

            wait                    (bool)  : wait for job completion
                default: False

            validate                (bool)  : Validate the backup operation
                default: True

            **kwargs            (dict)  : dictionary of optional arguments
            options:
                    tokenfile       (str)    : name of token file to be created.
                        default: None

                    security_key    (str)   : 16 character encryption key.
                        default: None
        :return:
           command output or (directory with status and  job_id)
        """
        command = "{0} job_status -jid {1}".format(self.init_command, job_id)

        while True:
            output = self.testcase.client_machine.run_ibmi_command(self.add_kwargs(command, **kwargs),
                                                                   validate=validate)
            status = re.findall("<job_status>([a-zA-Z/\s]+)</job_status>", output.output)

            if not validate:
                return output.output

            if "Pending" in status[0] or "Completed" in status[0] or \
                    "Failed" in status[0] or \
                    "Completed w/ one or more errors" in status[0] or \
                    wait is False:
                break
            else:
                time.sleep(10)

        self.log.info("Job status is {0}".format(status[0]))
        job = {'id': job_id, 'status': status[0]}
        if job['id'] is not None:
            self.log.info("CVC: Job status for job ID {0} is {1}".format(job_id, status[0]))
            if "Completed" not in status[0] and wait:
                raise Exception("Job#{0} is {1}]".format(job.get('id'), job.get('status')))
            return job
        else:
            raise Exception("CVC get job status command execution has exception [{0}]".format(output))

    def start_restore(self, source_paths,
                      backupset_name,
                      destination_path=None,
                      subclient_name=None,
                      destination_client=None,
                      from_time=None,
                      to_time=None,
                      overwrite=False,
                      wait=False,
                      validate=True,
                      **kwargs):
        """
        start restore from IBMi command line.

        Args:
            source_paths            (list)  : List of source paths

            backupset_name          (str)   : name of the backupSet.

            destination_path        (str)  : destination path
                default: None

            subclient_name          (str)   : Name of the new subclient
                default: None

            destination_client      (str)   : Name of the destination client
                default: None

            from_time               (str)   : restore from time
                default: None

            to_time               (str)   : restore till time
                default: None

            wait                    (bool)  :   wait till backup completes.
                default: False

            validate                (bool)  : Validate the backup operation
                default: True

            **kwargs            (dict)  : dictionary of optional arguments
            options:
                    tokenfile       (str)    : name of token file to be created.
                        default: None

                    security_key    (str)   : 16 character encryption key.
                        default: None
        :return:
           command output or (directory with status and  job_id)
        """

        command = "{0}  restore -c {1} -bk {2} -uo {3}".format(self.init_command,
                                                               self.client_name,
                                                               backupset_name,
                                                               overwrite)

        if subclient_name is not None:
            command = "{0} -sc {1}".format(command, subclient_name)

        for each in source_paths:
            command = "{0} -path \"{1}\"".format(command, each)

        if destination_path is not None:
            command = "{0} -dp {1}".format(command, destination_path)

        if destination_client is not None:
            command = "{0} -dc {1}".format(command, destination_client)

        if from_time is not None:
            command = "{0} -ftime {1}".format(command, from_time)

        if to_time is not None:
            command = "{0} -ttime {1}".format(command, to_time)

        output = self.testcase.client_machine.run_ibmi_command(self.add_kwargs(command, **kwargs),
                                                               validate=validate)
        if not validate:
            return output.output

        job_id = re.findall('<JobID>(\d+)</JobID>', output.output)

        if job_id[0] is None:
            raise Exception("CVC subclient backup has failed to start with exception [{0}]".format(output))
        job = self.job_status(job_id=job_id[0], wait=wait, **kwargs)
        self.log.info("Restore job#{0} is {1}".format(job.get('id'), job.get('status')))
        return job

    def find(self, file_name,
             backupset_name,
             subclient_name=None,
             from_time=None,
             to_time=None,
             validate=True,
             **kwargs):
        """
        find backup object from IBMi command line.

        Args:
            file_name            (str)  : List of source paths

            backupset_name          (str)   : name of the backupSet.

            subclient_name          (str)   : Name of the new subclient
                default: None

            from_time               (str)   : restore from time
                default: None

            to_time               (str)   : restore till time
                default: None

            validate            (bool)  :   Validate the login operation
                default: True

            **kwargs            (dict)  : dictionary of optional arguments
            options:
                    tokenfile       (str)    : name of token file to be created.
                        default: None

                    security_key    (str)   : 16 character encryption key.
                        default: None
        :return:
           result
        """

        command = "{0} find -c {1} -bk {2} -f {3}".format(self.init_command,
                                                          self.client_name,
                                                          backupset_name,
                                                          file_name)

        if subclient_name is not None:
            command = "{0} -sc {1}".format(command, subclient_name)

        if from_time is not None:
            command = "{0} -ftime {1}".format(command, from_time)

        if to_time is not None:
            command = "{0} -ttime {1}".format(command, to_time)

        output = self.testcase.client_machine.run_ibmi_command(self.add_kwargs(command, **kwargs),
                                                               validate=validate)

        if not validate:
            return output.output

        self.log.info("result is {0}".format(output))
        if output.exit_code == 0:
            self.log.info("CVC: find operation output is  {0}".format(output.output))
            return output.output
        else:
            raise Exception("CVC find operation backup has failed with exception [{0}]".format(output))
