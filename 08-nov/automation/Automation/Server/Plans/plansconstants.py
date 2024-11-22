# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Helper file to maintain all the constants used by Plan related operations."""

BASE_SERVER_PLAN = 'Auto-base-Server'
"""str: Plan name for base server plans"""

BASE_LAPTOP_PLAN = 'Auto-base-Laptop'
"""str: Plan name for base laptop plans"""

FULL_SERVER_PLAN = 'Auto-full-server'
"""str: Plan name for server plan for full schedule tests"""

INCREMENTAL_SERVER_PLAN = 'Auto-incremental-server'
"""str: Plan name for server plan for incremental schedule tests"""

SUBTYPE_SERVER = 'Server'
"""str: Plan subtye for server plans"""

SUBTYPE_LAPTOP = 'Laptop'
"""str: Plan subtye for Laptop plans"""

TENANT_ADMIN = 'Tenant Admin'
"""str: Tenant admin of the company who will inherit plans"""

STORAGE_SERVER_PLAN = 'Auto-Storage-Server'
"""str: Plan name for base server plans"""

SCHEDULE_SERVER_PLAN = 'Auto-Schedule-Server'
"""str: Plan name for base server plans"""

SCHEDULE_DC_PLAN = 'auto-dataclassification'
"""str: Plan name for Data Classification plan"""

SECONDARY_COPY_NAME = 'Copy - 3'
"""str: Name of the secondary copy to be added to the plan"""

DEFAULT_SUBCLIENT_NAME = 'default'
"""str: Default subclient name"""

WEEK_DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
"""list: Default subclient name"""

WEEKLY_RPO = 10080
"""int: rpoInMinutes for weekly RPO"""

DAILY_RPO = 1440
"""int: rpoInMinutes for daily RPO"""

autocopy_schedule = 'system created autocopy schedule'
"""str: System created autocopy schedule for secondary copies"""

window = [
    {
        "startTime": 50400,
        "endTime": 54000,
        "dayOfWeek": [
            5
        ]
    },
    {
        "startTime": 54000,
        "endTime": 57600,
        "dayOfWeek": [
            0
        ]
    }
]
"""list: operation window for a plan"""

full_window = [
        {
          "dayOfWeek": [
              1,
              2,
              3,
              4,
              5
          ],
          "startTime": 82800,
          "endTime": 86340
        },
        {
          "dayOfWeek": [
              5,
              0
          ],
          "startTime": 0,
          "endTime": 86340
        }
      ]
"""list: full operation window for a plan"""

dedupe_storage = 'Dedupe-storage'
"""str: dedupe storage pool name"""

non_dedupe_storage = 'Non-Dedupe-storage'
"""str: non-dedupe storage pool name"""

extended_retention_rule = (1, True, "EXTENDED_ALLFULL", 90, 0)
"""tuple: extended retention rule for storage copy"""

ndd_storage_pool = {
    "storagePolicyName": "",
    "type": 1,
    "copyName": "Primary",
    "numberOfCopies": 1,
    "clientGroup": {
        "_type_": 28,
        "clientGroupId": 0,
        "clientGroupName": ""
    },
    "storage": [
        {
            "path": "",
            "mediaAgent": {
                "_type_": 11,
                "mediaAgentName": ""
            }
        }
    ],
    "storagePolicyCopyInfo": {
        "copyType": 1,
        "isFromGui": True,
        "active": 1,
        "isDefault": 1,
        "numberOfStreamsToCombine": 1,
        "storagePolicyFlags": {
            "globalStoragePolicy": 1
        },
        "retentionRules": {
            "retainBackupDataForCycles": -1,
            "retainArchiverDataForDays": -1,
            "retainBackupDataForDays": -1,
            "retentionFlags": {
                "enableDataAging": 1
            }
        },
        "extendedFlags": {
            "globalStoragePolicy": 1
        },
        "copyFlags": {
            "preserveEncryptionModeAsInSource": 1
        },
        "library": {
            "libraryName": "",
            "_type_": 9,
            "libraryId": 0
        },
        "mediaAgent": {
            "_type_": 11,
            "mediaAgentName": ""
        }
    }
}
"""dict: payload for creating non dedupe storage pool"""

STORAGE_PATH = 'C:\\{0}\\StoragePool{1}'
"""str: Mount path for creating storage pools"""
