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

ACEXCHANGECONSTANTLIST = ["AC_EXCHANGE_CLIENT_TYPE", "AC_EXCHANGE_CLIENT_DELETE_INPUT"]

CURRENTFOLDER = os.path.dirname(os.path.realpath(__file__))
CONSTANT_DEFINE_FILE = os.path.join(CURRENTFOLDER, "constants.json")
with open(CONSTANT_DEFINE_FILE, 'r', encoding='utf-8-sig') as fh:
    CONSTANT_DEFINE = json.load(fh)

for adconstant in ACEXCHANGECONSTANTLIST:
    globals()[adconstant] = CONSTANT_DEFINE[adconstant]
