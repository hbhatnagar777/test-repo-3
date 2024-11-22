#!/usr/bin/env python
# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------


"""Runs all Python unit tests for cvpysdk."""

import os
import unittest

os.chdir(os.path.dirname(os.path.abspath(__file__)))
suite = unittest.defaultTestLoader.discover('.')

if __name__ == '__main__':
    unittest.TextTestRunner().run(suite)
