# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# --------------------------------------------------------------------------

"""Main file for commvault entity creation.

Entity:
=======
    __init__()      --  initialise object of Entity class

"""

import ntpath
import posixpath

from cvpysdk.commcell import Commcell

import SimpanaDefaults


class Entity(object):
    """ Class for browse operation """

    # Instance commvault pacakge is installed on
    package_instance = None

    # Commvault entity details
    commserv_name = None
    client_name = None
    agent_name = None
    backupset_name = None
    subclient_name = None

    # Commvault entity objects
    commcell = None
    client = None
    agent = None
    backupset = None
    subclient = None

    # Simpana defaults
    simpana_default_obj = SimpanaDefaults.Simpanadefaults()
    separator = None

    def __init__(
            self,
            logger_object,
            commcell_object,
            client_name,
            agent_name,
            backupset_name=None,
            subclient_name=None,
            package_instance=None
    ):
        """ Initialize the browse class instance

            Args:
                logger_object   (str)   -- Instance of Logger class

                commcell_object (obj)   -- instance of commcell class

                client_name     (str)   -- Client to perform operations on

                agent_name      (str)   -- Agent to perform operations on

                backupset_name  (str)   -- Backupset to be used

                subclient_name  (str)   -- Subclient to be used

                package_instance   (str)   -- Instance where commvault is installed

        """
        assert isinstance(commcell_object, Commcell) and isinstance(client_name, str) and isinstance(
            agent_name, str), "Commvault entity creation failed"

        try:
            Entity.commcell = commcell_object
            if Entity.commserv_name != commcell_object.commserv_name:
                Entity.commserv_name = commcell_object.commserv_name
                Entity.client_name = None
                Entity.agent_name = None
                Entity.backupset_name = None
                Entity.subclient_name = None

            if Entity.client_name != client_name:
                Entity.client = commcell_object.clients.get(client_name)
                logger_object.info("Client object created successfully")
                Entity.separator = '\\' if 'windows' in Entity.client.os_info.lower() else '/'
                Entity.client_name = client_name
                Entity.agent_name = None
                Entity.backupset_name = None
                Entity.subclient_name = None

            if Entity.agent_name != agent_name:
                Entity.agent = Entity.client.agents.get(agent_name)
                logger_object.info("Agent object created successfully")
                Entity.agent_name = agent_name
                Entity.backupset_name = None
                Entity.subclient_name = None

            if not backupset_name:
                backupset_name = Entity.agent.backupsets.default_backup_set

            if Entity.backupset_name != backupset_name:
                Entity.backupset = Entity.agent.backupsets.get(backupset_name)
                logger_object.info("Backupset object created successfully")
                Entity.backupset_name = backupset_name
                Entity.subclient_name = None

            if subclient_name and Entity.subclient_name != subclient_name:
                Entity.subclient = Entity.backupset.subclients.get(subclient_name)
                logger_object.info("subclient object created successfully")
                Entity.subclient_name = subclient_name

            if package_instance:
                Entity.package_instance = package_instance

            if not Entity.package_instance:
                Entity.package_instance = Entity.simpana_default_obj.get_local_instance_name(
                    Entity.client.install_directory)

        except Exception as exp:
            logger_object.info("Exception occurred in Entity object creation\nError: %s", exp)
            raise Exception("Exception occurred in Entity object creation")

    @staticmethod
    def _get_absolute_path(path, live_path, vsa_guid=''):
        """ Returns the absolute path of the file

        Args:
            path    (str)   -- Absolute/Relative path of the file

            live_path    (str)   -- Live path of the tool

            vsa_guid  (str)     --  Guid for VSA VM

        Returns:
            (str)   -- Absolute path of the file

        """
        if not path:
            return ''
        if Entity.client:
            if 'windows' in Entity.client.os_info.lower():
                if ntpath.isabs(path):
                    return path
            elif posixpath.isabs(path):
                if vsa_guid:
                    return '\\{0}{1}'.format(vsa_guid.rstrip("\n"), path.replace('/', '\\'))
                return path

        if live_path:
            try:
                stack = live_path.split(Entity.separator)

                for temp in path.split(Entity.separator):
                    if temp != '.':
                        if temp == '..':
                            stack.pop()
                        elif temp:
                            stack.append(temp)

                return '{0}'.format(Entity.separator).join(stack)

            except Exception:
                print('Failed to get absolute path of the file, please provide full path')
                raise Exception("Failed to get the absolute path of the file")
        else:
            print('Current working directory not set, please specify absolute path of file')
            raise Exception("Current working directory not set")
