# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Helper file for maintaining Network Constants.

Any constant values related to Network goes in this file.

"""


KEEP_ALIVE_SECONDS = 180
"""int:     Default value for keep alive interval."""

TUNNEL_INIT_SECONDS = 30
"""int:     Default value for tunnel init interval."""

FORCE_SSL = False
"""boolean:     Default value for force incoming SSL."""

IS_LOCKDOWN = False
"""boolean:     Default value for lockdown proxy."""

IS_DMZ = False
"""boolean:     Default value for proxy."""

BIND_OPEN_PORTS_ONLY = False
"""boolean:     Default value for bind all services to open ports only."""

IS_ROAMING_CLIENT = False
"""boolean:     Default value for roaming client option."""

TUNNEL_CONNECTION_PORT = [8403, 8408]
"""int:     Default value for tunnel port if client is installed on Instance001."""

CLIENT_GROUP_NAME = ['CG_47155', 'CG_47156', 'CG_47157', 'CG_47158', 'CG_51479']
"""str:     names for various client groups based on Test case ID."""

CS_CLIENT_GROUP_NAME = [
    'CG_47155_CS',
    'CG_47156_CS',
    'CG_47157_CS',
    'CG_47158_CS']
"""str:     names for various client groups based on Test case ID."""

NEWTWORK_TIMEOUT_SEC = 30
"""int:     default value for delay in network test cases."""

OUTGOING_CONNECTION_PROTOCOL = {
    0: 'HTTP',
    1: 'HTTPS',
    2: 'HTTPS_AuthOnly',
    3: 'RAW_PROTOCOL'
}
"""dict:    dictionary for all types of outgoing connection protocols"""
