# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Helper file to maintain all the constants used by REST API test cases"""

import os
import AutomationUtils.constants as AC
from AutomationUtils import config

ENVIRONMENT_FILE = os.path.join(AC.AUTOMATION_DIRECTORY, 'Server',
                                'RestAPI', 'PostmanCollections',
                                'JSONAuto.environment.json')
"""str:     Path for the location of environment file"""

COLLECTION_FILE = os.path.join(AC.AUTOMATION_DIRECTORY, 'Server',
                               'RestAPI', 'PostmanCollections')
"""str:     Path for the location of postman collection files"""

TEMP_ENVIRONMENT_FILE = os.path.join(AC.AUTOMATION_DIRECTORY, 'Server',
                                     'RestAPI', 'PostmanCollections',
                                     'JSONAuto_modified.environment.json')
"""str:     Path for the location of temporary environment file"""

NEWMAN_LOG_LOCATION = os.path.join(AC.LOG_DIR, 'NewmanLogFiles')
"""str:     Path for generating newman log files"""

config_json = config.get_config()
try:
    CREATE_REPORTS = config_json.PostmanVariables.createRestApiReport
except Exception :
    CREATE_REPORTS = False
"""bool:    Whether generate RESTAPI reports or not"""
"""Set createRestApiReport as true in config only after installing newman reporter htmlextra"""
"""Command to install reporter : “npm install -g newman-reporter-htmlextra” """

RESTAPI_REPORT_PATH = os.path.join(AC.LOG_DIR, 'RESTAPIReports')
"""str:     Path for generating HTML reports"""
