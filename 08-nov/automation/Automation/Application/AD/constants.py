# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""
This library is used to define all AD related mapper

The constants are defined in constants.json file

"""
__all__ = []

import json
import os
from AutomationUtils.constants import AUTOMATION_UTILS_PATH

ADCONSTANTLIST = ["AD_GROUP_MAPPER", "AD_OU_MAPPER", "AD_USER_MAPPER",\
                 "AD_TYPE_MAPPER", "AD_CATEGORY_TYPES",\
                 "AD_OBJECT_CLASS_MAPPER", "AD_OBJECT_CLASS_PRE_MAPPER",\
                 "AD_UGO_ATTRIBUTELIST", "AD_USER_OBJECT_CLASS"]
AZUREADCONSTANTLIST = ["AZUREAD_SUPPORTED_TYPE_MAPPER", "AZUREAD_TYPE_CREATE_PARANAME",\
                       "AZUREAD_TYPE_CREATE_KEYNAME", "AZUREAD_TYPE_CREATE_ENTRIES",\
                       "AZUREAD_TYPE_ODATA_MAPPER", "AZUREAD_INDEX_META_MAPPER",
                       "AZUREAD_DELETED_URL", "AZUREAD_TYPE_ATTRIBUTES"]

CURRENTFOLDER = os.path.dirname(os.path.realpath(__file__))
CONSTANT_DEFINE_FILE = os.path.join(CURRENTFOLDER, "constants.json")

with open(CONSTANT_DEFINE_FILE, 'r') as fh:
    CONSTANT_DEFINE = json.load(fh)

for adconstant in ADCONSTANTLIST+AZUREADCONSTANTLIST:
    globals()[adconstant] = CONSTANT_DEFINE[adconstant]

# requried for smtp library
WEBFIlENAME = ['html', 'htm', 'xml', 'txt']
OFFICEFILENAME = ['docx', 'xlsx', 'ppt', 'msg', 'doc']
KBSIZE = 1024
MBSIZE = 1024*KBSIZE
GBSIZE = 1024*MBSIZE
STRINGTYPE = ['regular', 'unicode', 'utf8']
RFC822_FIELDS = ['MIME-Version', 'Received', 'From', 'To', 'CC', 'Subject',
                 'Date', 'Message-ID', 'X-MIMETrack']

UTILS_PATH = os.path.dirname(__file__)

SCRIPT_PATH = os.path.join(AUTOMATION_UTILS_PATH, "Scripts\\Windows")

"""Path of the PowerShell file to be used to execute GPO operations"""
GPO_OPS = os.path.join(SCRIPT_PATH,'AD_GPO_ops.ps1')

"""Path of the PowerShell file to be used for user attribute operations"""
ATTRIBUTE_OPS = os.path.join(SCRIPT_PATH,'ADAttributeOperations.ps1')

RETRIEVED_FILES_PATH = os.path.join(UTILS_PATH, "RetrievedFiles")

"""Path of Powershell file to be used to perform USER related operations"""
USER_OPS=os.path.join(SCRIPT_PATH,'User_Power.ps1')

"""Path of powershell file to do Azure User related operations"""
Azure_User_Operations=os.path.join(SCRIPT_PATH,'Azure_User_Operations.ps1')

"""Path of powershell file to do os related operations"""
OS_OPS = os.path.join(SCRIPT_PATH,"AD_OS_Remote_Ops.ps1")

