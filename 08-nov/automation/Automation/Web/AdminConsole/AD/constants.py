# -*- coding: utf-8 -*-s
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
from enum import Enum

ACADCONSTANTLIST = ["AC_AD_PAGE_MAPPER"]
ACAZUREADCONSTANTLIST = ["AC_AZUREAD_BROWSE_FOLDER_MAPPER", "AC_AZUREAD_BROWSE_DELETE_MAPPER"]

CURRENTFOLDER = os.path.dirname(os.path.realpath(__file__))
CONSTANT_DEFINE_FILE = os.path.join(CURRENTFOLDER, "constants.json")

with open(CONSTANT_DEFINE_FILE, 'r') as fh:
    CONSTANT_DEFINE = json.load(fh)

for adconstant in ACADCONSTANTLIST+ACAZUREADCONSTANTLIST:
    globals()[adconstant] = CONSTANT_DEFINE[adconstant]

class ADconstants(Enum):
    EAST_US_2 = "East US 2"