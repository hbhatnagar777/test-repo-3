# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright CommVault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
Main file for all the constants of Dynamics 365 Web Automation
"""

from enum import Enum


class D365AssociationTypes(Enum):
    """
        All content types that can be associated to a Dynamics 365 CRM client
    """
    TABLE = "Table"
    INSTANCE = 'Instance'
    ALL_INSTANCES = "All Instances"


class AssocStatusTypes(Enum):
    """
        All the possible status types for any association
    """
    DELETED = "Deleted from content"
    ENABLED = "Included in backup"
    DISABLED = "Excluded from backup"
    ACTIVE = "Included in backup"


class RESTORE_TYPES(Enum):
    """
        All possible restore types for any association
    """
    IN_PLACE = "In-place"
    OOP = 'Out Of Place'


class RESTORE_RECORD_OPTIONS(Enum):
    """
        All possible restore options for record
    """
    OVERWRITE = "Overwrite"
    Skip = "Skip"


class Dynamics365(Enum):
    """
        Enum class for declaring all Dynamics 365 CRM constants
    """
    TABLE_TAB = 'Tables'
    CONTENT_TAB = 'Content'
    OVERVIEW_TAB = 'Overview'

    ALL_INSTANCES_CONTENT_NAME = "All Environments"

    DISCOVER_PROCESS_NAME = 'CVOffice365Discover'
    MAX_STREAMS_COUNT = 10
    INFRA_POOL_MAX_STREAMS = 5

    ASSOC_PARENT_COL = "Environment"
    D365_PLAN_TYPE = "Dynamics 365"

    APP_USER_LABEL = "Create Application user"


class CLOUD_REGIONS(Enum):
    DEFAULT = 'Default (Global Service)'
    GCC = 'U.S. Government GCC'
    GCC_HIGH = 'U.S. Government GCC High'


class D365FilterType(Enum):
    """
        Enum class for declaring Item Types for filtering
    """
    TABLE = 'Table'
    ROW = 'Row'


metallic_d365_plan_retention_dict = {
    '5-years': '1825 days',
    '7-years': '2555 days',
    'infinite': 'Infinite'
}

