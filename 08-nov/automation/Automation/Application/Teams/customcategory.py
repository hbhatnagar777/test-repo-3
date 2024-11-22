# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Main file for Custom category related operations

CustomCategory is the only class defined in this file.

CustomCategory: Class for representing a CustomCategory.

CustomCategory:
========
    __init__()                  --  Initializes CustomCategory object.
    add_rule()                  -- Add a rule to custom category.
"""


class CustomCategory:

    custom_json = {
        "name": None,
        "conditions": []
    }

    def __init__(self, name):
        """Initializes the helper object.
                    Args:
                        name (str)  - Name of the custom category.
        """
        self.custom_json['name'] = name

    def add_rule(self, field_name, field_operator, value):
        """
            Add a rule to the custom category.
            Args:
                field_name  (enum)  --  Field name such as Display name, SMTP address etc.
                field_operator  (enum)  -- Filed operator such as Contains, Startswith, created time etc.
                value  (str)        --  value of the fields such as name , Date etc.
        """

        condition_json = {'rId': 0, "fieldSource": "TM_KnownFields", "fieldNumber": 0, "fieldName": None, "mask": "",
                          "fieldOperator": 0, "fieldType": 0, "CCRuleName": None, "CCRuleOperator": None,
                          "CCRuleType": "String", "CCRuleMask": None, 'fieldNumber': field_name.value,
                          'fieldName': " ".join(field_name.name.split('_')), 'mask': value, 'fieldOperator': field_operator.value}

        if field_name.value == 4:
            condition_json['fieldType'] = 1
        else:
            condition_json['fieldType'] = 5
        condition_json['CCRuleName'] = " ".join(field_name.name.split('_'))
        condition_json['CCRuleOperator'] = field_operator.name
        condition_json['CCRuleMask'] = value
        self.custom_json['conditions'].append(condition_json)


