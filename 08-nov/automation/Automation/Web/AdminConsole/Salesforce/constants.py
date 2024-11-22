# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""
Main file for all the constants for Salesforce Automation
"""
from enum import Enum


class RestoreTarget(Enum):
    """Constants for Restore Target radio buttons"""
    SALESFORCE = 'Salesforce Instance'
    DATABASE = 'Database'
    FILE_SYSTEM = 'File system'


class ReactRestoreTarget(Enum):
    """Constants for Restore Target radio buttons"""
    SALESFORCE = 'salesforce'
    DATABASE = 'database'
    FILE_SYSTEM = 'fileSystem'


class RestoreType(Enum):
    """Constants for restore type on Select Restore Type page"""
    OBJECT_LEVEL = 'Object level restore'
    RECORD_LEVEL = 'Record level restore'
    METADATA = 'Metadata restore'
    SANDBOX = 'Sandbox seeding'


class SeedRecordType(Enum):
    """Constants for record type on Seeding Config page"""
    ALL_RECORDS = 'All records'
    RECENT_RECORDS = 'Most recently updated N records'
    UPDATED_DAYS = 'Records updated in the last N days'
    SQL = 'SQL where clause'


class CompareType(Enum):
    """Constants for compare type on Compare page"""
    OBJECT = "Object compare"
    METADATA = "Metadata compare"


class CompareChangeType(Enum):
    """Constants for compare change type on Compare page"""
    ADDED = "Added"
    DELETED = "Deleted"
    MODIFIED = "Modified"
    TOTAL_FIRST = "Total first job"
    TOTAL_SECOND = "Total second job"


class ColumnOperation(Enum):
    """Constants for Simplified filter operations"""
    CONTAINS = "contains"
    DOES_NOT_CONTAIN = "does not contain"
    DOES_NOT_EQUAL_TO = "does not equal to"
    ENDS_WITH = "ends with"
    EQUALS_TO = "equals to"
    IS_NOT_NULL = "is not null"
    IS_NULL = "is null"
    STARTS_WITH = "starts with"
    BETWEEN = "between"
    GREATER_THAN = "greater than"
    GREATER_THAN_OR_EQUAL_TO = "greater than or equal to"
    LESS_THAN = "less than"
    LESS_THAN_OR_EQUAL_TO = "less than or equal to"
    NOT_BETWEEN = "not between"


class GroupOperation(Enum):
    """Constants for Simplified filter group level operations"""
    ALL = "all"
    ANY = "any"


class ParentLevel(Enum):
    """Constants for selecting parent objects to restore"""
    ALL = 'All parents'
    NONE = 'No parents'


class DependentLevel(Enum):
    """Constants for selecting child objects to restore"""
    ALL = 'All children'
    IMMEDIATE = 'Immediate children only'
    NONE = 'No children'


class SalesforceEnv(Enum):
    """Constants for Salesforce environment type"""
    PRODUCTION = 'Production'
    SANDBOX = 'Sandbox'


class RecordLevelVersion(Enum):
    """Constants for Record Level Versions"""
    LATEST = 'label.showLatestVersion'
    ALL = 'label.showAllVersions'
    DELETED = 'label.showDeletedRecords'


class FieldMapping(Enum):
    """Constants to map objects across orgs"""
    SKIP = 'Skip mapping fields'
    CV_EXTERNAL_ID = 'Use CVExternalId to map all objects'
    DESTINATION = 'Use destination field mappings'
    SOURCE = 'Use source field mappings'

class GDPRRequestType(Enum):
    """Constants for GDPR Request Type"""
    DELETION = 'Deletion'
    MODIFICATION = 'Modification'


# Dictionary containing form field names for database form
DATABASE_FORM = {
    'cache_path': 'downloadCachePath',
    'db_type': 'dbType',
    'db_host_name': 'dbHost',
    'db_instance': 'dbInstance',
    'db_name': 'dbName',
    'db_port': 'dbPort',
    'db_user_name': 'dbUsername',
    'db_password': 'dbPassword'
}
MONTH_SHORT_NAMES = {
    'january': 'Jan',
    'february': 'Feb',
    'march': 'Mar',
    'april': 'Apr',
    'may': 'May',
    'june': 'Jun',
    'july': 'Jul',
    'august': 'Aug',
    'september': 'Sep',
    'october': 'Oct',
    'november': 'Nov',
    'december': 'Dec'
}
# Dictionary containing form field names for old database form
OLD_DATABASE_FORM = {
    'cache_path': 'downloadCachePath',
    'db_type': 'addSfDbType_isteven-multi-select',
    'db_host_name': 'databaseHost',
    'db_instance': 'serverInstanceName',
    'db_name': 'databaseName',
    'db_port': 'databasePort',
    'db_user_name': 'dbUserName',
    'db_password': 'dbPassword'
}

# Dictionary containing mapping of the Anomaly Alert parameter type to it's ID
ALERT_TYPE_MAPPING = {
    'Number': '1',
    'Percentage': '2'
}

# Field name of destination client for restore to Salesforce/File System
DESTINATION_CLIENT = 'DestClient'
RDESTINATION_CLIENT = 'destinationOrganization'
ACCOUNT_TYPE = "Cloud Account"
VENDOR_TYPE = "Salesforce Connected App"
