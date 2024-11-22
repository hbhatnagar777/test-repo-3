# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""Main file for all the constants for Salesforce Automation"""
from enum import Enum


class DbType(Enum):
    """Constants for database type"""
    POSTGRESQL = 'POSTGRESQL'
    SQLSERVER = 'SQLSERVER'


CLIENT = 'ClientName'
CONTENT_VERSION = 'ContentVersion'
CONTENT_DOCUMENT = 'ContentDocument'
INFRASTRUCTURE_PARAMS = {"access_node", "cache_path", "database_host", "database_name", "db_user_name", "db_password"}
SALESFORCE_PARAMS = {"salesforce_user_name", "salesforce_user_password", "salesforce_user_token", "sandbox"}
REQUEST_LIMIT_EXCEEDED = "REQUEST_LIMIT_EXCEEDED"
EXCEEDED_QUOTA = "ExceededQuota"
TEXT = "Text"
POSTGRESQL_DEFAULT_PORT = 5432
SQLSERVER_DEFAULT_PORT = 1433
BULK_MAX_ROWS = 10000
