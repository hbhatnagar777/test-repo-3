#  -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""constants file to maintain all the constants used by media agent test cases"""

# List of server types used for creating cloud libraries
CLOUD_LIBRARIES = {
    "Direct Glacier": {
        "mountPath": "",
        "serverType": 53,
        "loginName": "",
        "password": ""
    },
    "Amazon S3 Glacier": {
        "mountPath": "",
        "serverType": 2,
        "loginName": "",
        "password": ""
    },
    "MSFT Azure Storage Archive Tier": {
        "mountPath": "",
        "serverType": 3,
        "loginName": "",
        "password": ("")
    },
    "MSFT Azure Storage Hot-Archive Tier": {
        "mountPath": "",
        "serverType": 3,
        "loginName": "",
        "password": ("")
    },
    "MSFT Azure Storage Cool-Archive Tier": {
        "mountPath": "",
        "serverType": 3,
        "loginName": "",
        "password": ("")
    },
    "OCI Archive": {
        "mountPath": "",
        "serverType": 28,
        "loginName": (""),
        "password": ""
    },
    "Oracle Archive": {
        "mountPath": "",
        "serverType": 22,
        "loginName": (""),
        "password": ""
    },
}

CLOUD_SERVER_TYPES = {
    'alibaba cloud object storage service': 23,
    'amazon glacier': 53,
    'amazon s3': 2,
    'at&t synaptic storage': 10,
    'caringo castor': 51,
    'china mobile onest': 16,
    'ddn wos': 54,
    'dell dx object storage platform': 52,
    'emc atmos': 9,
    'google cloud storage': 19,
    'hds hitachi content platform': 12,
    'huawei object storage': 24,
    'inspur cloud object storage': 29,
    'microsoft azure storage': 3,
    'openstack object storage': 14,
    'oracle cloud infrastructure archive storage': 28,
    'oracle cloud infrastructure archive storage classic': 22,
    'oracle cloud infrastructure object storage': 26,
    'oracle cloud infrastructure object storage (s3 compatible)': 25,
    'oracle cloud infrastructure object storage classic': 28,
    'rackspace cloud files': 5,
    'telefonica open cloud object storage': 27,
    'verizon cloud storage': 18,
    'vmware vcloud air object storage': 20,
    'hpe store': 59,
    's3 compatible storage': 40
}
DUMMY_DATA = {
    'dummy_data': 'dummy data for test case'
}

HYPERSCALE_CONSTANTS = {
    'vertical_scaleout_add_disk_success': 'configured',
    'Add_Bricks_Success': 'successfully added bricks to volume'
}

DEVICE_ACCESS_TYPES = {
    'WRITE': 2,
    'READ': 4,
    'READWRITE': 6,
    'PREFERRED': 8,
    'DATASERVER_IP': 16,
    'DATASERVER_SAN': 32,
    'CCM_READ_ONLY': 64,
    'DATASERVER_ISCSI': 128,
}

DEDUPLICATION_STORE_FLAGS = {
    'IDX_SIDBSTORE_FLAGS_DDB_NEEDS_AUTO_RESYNC' : 33554432,
    'IDX_SIDBSTORE_FLAGS_DDB_UNDER_MAINTENANCE' : 16777216,
    'IDX_SIDBSTORE_FLAGS_PRUNING_ENABLED'   :   536870912,
    'IDX_SIDBSTORE_FLAGS_DDB_VERIFICATION_INPROGRESS' : 67108864
}