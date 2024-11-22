# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""File for handling all the exceptions for the Kubernetes Automation package.

__EXCEPTION_DICT__:
    A python dictionary for holding all the exception messages for a specific event or class.

    Any exceptions to be raised from the Automation in a module should be added to this dictionary.

    where,

        -   the key is the module name or the class name where the exception is raised

        -   the value is a dictionary:

            -   key is a unique ID to identify the exception message

            -   value is the exception message


KubernetesException:
    Class inheriting the "Exception" Base class for raising
    a specific exception for the Kubernetes Automation package.

    The user should create an instance of the KubernetesException class:

        **KubernetesException(exception_module, exception_id, exception_message)**

        where,

            -   exception_module:   the module in which the exception is being raised

                -   key in the __EXCEPTION_DICT__

            -   exception_id:       unique ID which identifies the message for the Exception

            -   exception_message:  additional message to the exception

                -   only applicable if the user wishes to provide an additional message to the
                    exception along with the message already present as the value for the
                    exception_module - exception_id pair

"""

# Common dictionary for all exceptions among the Kubernetes automation

__EXCEPTION_DICT__ = {
    'TestScenario': {
        '101': 'Not all test scenarios passed',
        '102': 'Cluster health not optimal.'
    },

    'BackupOperations': {
        '101': 'Incorrect Backup type selected',
    },

    'RestoreOperations': {
        '101': 'Kubernetes Full Application Restore failed.',
        '102': 'Kubernetes Namespace-Level Restore failed.',
        '103': 'Kubernetes Application Files Restore to FileSystem destination failed.',
        '104': 'Kubernetes Application Files Restore to PersistentVolumeClaim failed.',
        '105': 'Kubernetes Manifest Files Restore to FileSystem destination failed.',

    },

    'ValidationOperations': {
        '101': 'File comparison with diff failed.',
        '102': 'File comparison with cksum.',
        '103': 'MD5 hash comparison failed.',
        '104': 'Command failed to execute.',
        '105': 'Resource not cleaned up.',
        '106': 'JPR validation failed.',
        '107': 'Log matching failed.',
        '108': 'Resource comparison failed.',
        '109': 'RestoreModifier not applied correctly.',
        '110': 'Files not found in restore browse',
        '111': 'Pods not in running state',
        '112': 'NodeSelector not assigned'
    },

    'APIClientOperations': {
        '101': 'Entity not found.',
        '102': 'Command execution failed.'
    },

    'HelmOperations': {
        '101': 'Repository path or repository name not provided',
        '102': 'Helm Command failed to execute',
        '103': 'Username & Password required for remote client helm operations',
        '104': 'Please check whether helm command line tool is installed & configured on PATH variable in the machine',
        '105': 'Version info response from helm command is not valid'
    },

    'RestoreModifierOperations': {
        '101': 'Either of name, namespace, kind, labels, or field is required',
        '102': 'Incorrect values for Modifier object',
        '103': 'Incorrect values for RestoreModifier object',
        '104': 'Invalid values for Selector object',
        '105': 'Modifier deletion failed'
    }

}


class KubernetesException(Exception):
    """Exception class for raising exception specific to a module."""

    def __init__(self, exception_module, exception_id, exception_message=""):
        """Initialize the KubernetesException class instance for the exception.

            Args:

                exception_module (str)   --  name of the module where the exception was raised

                exception_id (str)       --  id of the exception specific to the exception_module

                exception_message (str)  --  additional message about the exception

            Returns:

                object - instance of the SDKException class of type Exception

        """
        self.exception_module = str(exception_module)
        self.exception_id = str(exception_id)
        self.exception_message = __EXCEPTION_DICT__[exception_module][exception_id]

        if exception_message:
            if self.exception_message:
                self.exception_message = '\n'.join([self.exception_message, exception_message])
            else:
                self.exception_message = exception_message

        Exception.__init__(self, self.exception_message)
