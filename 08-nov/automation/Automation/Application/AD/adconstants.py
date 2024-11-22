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

ADCONSTANTLIST = ["AD_GROUP_MAPPER", "AD_OU_MAPPER", "AD_USER_MAPPER",\
                 "AD_TYPE_MAPPER", "AD_CATEGORY_TYPES",\
                 "AD_OBJECT_CLASS_MAPPER", "AD_OBJECT_CLASS_PRE_MAPPER",\
                 "AD_UGO_ATTRIBUTELIST", "AD_USER_OBJECT_CLASS"]
AZUREADCONSTANTLIST = [ "AadGraphTypeUrl", "AadTypeAttribute", "AadIndexMeta",
                        "AadTypeRelationship"]

CURRENTFOLDER = os.path.dirname(os.path.realpath(__file__))
CONSTANT_DEFINE_FILE = os.path.join(CURRENTFOLDER, "constants.json")

with open(CONSTANT_DEFINE_FILE, 'r') as fh:
    CONSTANT_DEFINE = json.load(fh)

for adconstant in ADCONSTANTLIST+AZUREADCONSTANTLIST:
    globals()[adconstant] = CONSTANT_DEFINE[adconstant]


for type_ in AadTypeAttribute:
    AadTypeAttribute[type_]['all'] = []
    AadTypeAttribute[type_]['all'] += AadTypeAttribute[type_]['other']
    AadTypeAttribute[type_]['all'] += AadTypeAttribute[type_]['readonly']
    AadTypeAttribute[type_]['all'] += AadTypeAttribute[type_]['new']
