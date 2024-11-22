# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------


"""Test Case for HSX to test absence of drill hole reg keys
Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()                      --  initialize TestCase class


Sample input json
"62732": {
            "ControlNodes": {
              "MA1": "name",
              "MA2": "name",
              "MA3": "name"
            },
            "StoragePoolName": "name",
         }

"""

from HyperScale.HyperScaleUtils.base_test_cases.drill_hole_test_case import DrillHoleTestCase

class TestCase(DrillHoleTestCase):
    """Hyperscale test class for HSX to test absence of drill hole reg keys"""

    def __init__(self):
        """Initialization function"""
        super(TestCase, self).__init__()
        self.name = "Test Case for HSX to test absence of drill hole reg keys"
