# -*- coding: utf-8 -*-

# ---------------------------------------------------------------------------
# Copyright ©2016 Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# ---------------------------------------------------------------------------

"""Main file that maps the commcell agent's to automation directories

AGENTS_MAP:     Python dictionary for maintaining a map between commcell agent and
                    directory name which holds the automation testcases of this agent

"""

AGENTS_MAP = {
    "File System": "FileSystem",
    "Virtual Server": "VirtualServer",
    "NAS": "NAS",
    "SAP HANA": "SapHana",
    "sap for oracle": "SapOracle",
    "Oracle" : "Oracle"
}
