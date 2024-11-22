# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""
    SQL Queries for Lotus Notes Automation
"""

SQL_QUERY_DICT = {}
SQL_QUERY_DICT['GetSubclientProperties'] = """
SELECT attrName FROM APP_SubclientProp
WHERE componentNameId=%s AND attrType=%s AND modified=0 
"""
