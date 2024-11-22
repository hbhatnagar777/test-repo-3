# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""This module provides the function or operations related to permission change on AdminConsole
Entitlement Management page

PermissionReportHelper : This class provides methods for ACL/extension related operations

FSHelper
===========

__init__(driver obj)  --      initialize object of PermissionReportHelper class associated

get_acls(filename)           --      get list of user who have permissions on the file

get_extension(filename)            --      get file extension

"""

import os


class PermissionReportHelper(object):
    """PermissionReport Helper class """

    def __init__(self, driver):
        """
        Initializes the Permission Report helper module

        Args:
            driver (object) : the web driver object

        Raises:
             Exception:
                If the driver is not provided
        """
        self.driver = driver
        if not driver:
            raise Exception('Driver is not provided')

    def get_acls(self, filename):
        """
        get_acls
            #return first user ACL for the file "filename". for each element, format:  DEVEMC\admin:(ID)F

        Args:
                filename (str)  - user specified file name

        """
        try:
            acllist = os.popen("cacls %s" % filename).read().splitlines()
            return acllist[0].replace(
                filename, '').lstrip().rstrip().split(":")[0]
        except Exception as exp:
            raise Exception(exp)

    def get_extension(self, filename):
        """
        get_extension
            get file extension for file with name as "filename"
        Args:
                filename (str)  - user specified file name

        """
        try:
            # [-1] - return list last value
            security = filename.lstrip().rstrip().split(".")[-1]
            return security
        except Exception as exp:
            raise Exception(exp)
