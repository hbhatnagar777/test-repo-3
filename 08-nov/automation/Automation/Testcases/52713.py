# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

Test cases to validate entities creation/deletion with various input types

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()                  --  initialize TestCase class

    setup()                     --  Setup function of this test case. All test case
                                    objects shall be initialized in this module.

    run()                       --  run function of this test case

    whole_nine_yards()          -- Create and delete all supported entities without
                                    specifying any inputs

    standalone_default_props()
                                -- Create each entity separately without defining any
                                    properties. e.g create('backupset')

    standalone_specific_props()
                                -- Create each entity separately with individual
                                    properties

    standalone_target_props()
                                -- Create each entity separately with target
                                    properties only

    all_default_props()
                                -- Create all entities with default properties

    all_target_props()
                                -- Create all entities together by providing the
                                    common target properties

    all_specific_props()
                                -- Create all entities together by providing
                                    individual entity properties

    all_mixed_props()
                                -- Create all entities together by providing
                                    individual entity properties and target
                                    properties also

    all_named_props()
                                -- Create all entities by providing just the name of
                                    the entity [ Take all default inputs ]

    all_unforced()
                                -- Create all entities without force option in target
                                    properties

    validate_subclient_content_cleanup() -- Validate all possible cases where content might be cleaned up

    multiple_client_groups()    -- Create multiple client groups with default properties

    sp_copy_recreate_existing() -- Recreate existing storage policy when copy is also created on first attempt

"""

from pprint import pformat

# Test Suite imports
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.options_selector import CVEntities
from AutomationUtils.constants import ORDERED_ENTITIES

from Server.serverhelper import ServerTestCases

class TestCase(CVTestCase):
    """Class for creating/deleting commcell entities"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "Entities class validation to create/delete commcell entities"
        self.applicable_os = self.os_list.WINDOWS
        self.product = self.products_list.COMMSERVER
        self.feature = self.features_list.AUTOMATION
        self.show_to_user = True

    def run(self):
        """Main function for test case execution"""

        try:

            entities = CVEntities(self)
            tc = ServerTestCases(self)
            storagepolicyname = self.subclient.storage_policy
            mediaagent = self.subclient.storage_ma
            _client = self.client.client_name
            _sp = self.commcell.storage_policies.get(storagepolicyname)
            _library = _sp.library_name

            def sp_copy_recreate_existing():
                """ Recreate existing storage policy when copy is also created on first attempt """

                # Create the storage policy and the copy.
                _ = entities.create({
                'storagepolicy':
                    {
                        'force': False,
                        'name': 'StoragePolicy_Retry',
                        'library': _library,
                        'copy_name':'StoragePolicy_Retry_Copy',
                        'mediaagent': mediaagent
                    }
                }
                )

                # Re creation of the copy should also work fine and should report that the storage policy and copy
                # already exists instead of failing in Post Configuration.
                _ = entities.create({
                'storagepolicy':
                    {
                        'force': False,
                        'name': 'StoragePolicy_Retry',
                        'library': _library,
                        'copy_name':'StoragePolicy_Retry_Copy',
                        'mediaagent': mediaagent
                    }
                }
                )

            def whole_nine_yards():
                ''' Create and delete all supported entities without
                        specifying any inputs'''

                tc.log_step("""Create and delete all supported entities without
                                specifying any inputs.
                                Input type to create(): None""", 200)

                entity_properties = entities.create()

                entities.delete(entity_properties)

            def standalone_default_props():
                '''Create each entity separately without defining any properties'''
                for entity in ORDERED_ENTITIES:
                    tc.log_step("""Creating [{0}] without specifying target
                                    properties.
                                    Input type to create(): String""".format(str(entity)), 200)

                    entity_properties = entities.create(entity)
                    entities.delete(entity_properties)

            def standalone_specific_props():
                '''Create each entity separately with individual properties'''
                tc.log_step("""Creating standalone entities with properties
                                Input type to create(): Dictionary""", 200)

                # Create backupset
                backupset_inputs = {
                    'backupset':
                    {
                        'name': "Backupset_" + self.id,
                        'client': _client,
                        'agent': "File system",
                        'instance': "defaultinstancename",
                        'on_demand_backupset': False,
                        'force': True
                    },
                }
                backupset_props = entities.create(backupset_inputs)
                entities.delete(backupset_props)

                # Create subclient
                subclient_inputs = {
                    'subclient':
                    {
                        'name': "Subclient_" + self.id,
                        'client': _client,
                        'agent': "File system",
                        'instance': "defaultinstancename",
                        'storagepolicy': storagepolicyname,
                        'backupset': "defaultBackupSet",
                        'content': ["C:\\t1.txt", "C:\\t2.txt"],
                        'description': "Automation - Individual properties",
                        'subclient_type': None,
                        'force': True
                    },
                }

                subclient_props = entities.create(subclient_inputs)
                entities.delete(subclient_props)

                # Create disklibrary
                disklibrary_inputs = {
                    'disklibrary':
                    {
                        'name': "disklibrary_" + self.id,
                        'mediaagent': mediaagent,
                        'mount_path': entities.get_mount_path(mediaagent),
                        'username': '',
                        'password': '',
                        'cleanup_mount_path': True,
                        'force': True
                    },
                }
                disklibrary_props = entities.create(disklibrary_inputs)
                entities.delete(disklibrary_props)

                # Create storage policy
                storagepolicy_inputs = {
                    'storagepolicy':
                    {
                        'name': "storagepolicy_" + self.id,
                        'library': _library,
                        'mediaagent': mediaagent,
                        'dedup_path': None,
                        'incremental_sp': None,
                        'retention_period': 3,
                        'force': True,
                    },
                }
                storagepolicy_props = entities.create(storagepolicy_inputs)
                entities.delete(storagepolicy_props)

                # Create clientgroup by specifying client list
                clientgroup_inputs = {
                    'clientgroup':
                    {
                        'name': "clientgroup_" + self.id,
                        'clients': [_client],
                        'description': 'Automation client group',
                        'enable_backup': True,
                        'enable_restore': True,
                        'enable_data_aging': True,
                        'force': True,
                    },
                }
                clientgroup_props = entities.create(clientgroup_inputs)
                entities.delete(clientgroup_props)

                # Create clientgroup by * not specifying client in client list
                # and using option default_client set to True.
                # With this option a client should be selected by default and
                # associated with the client group.
                # Since no other entity is selected to be created with clientgroup
                # default client here would be testcase initialized client.
                clientgroup_inputs = {
                    'clientgroup':
                    {
                        'name': "clientgroup_" + self.id,
                        'default_client': True,
                        'description': 'Automation client group',
                        'enable_backup': True,
                        'enable_restore': True,
                        'enable_data_aging': True,
                        'force': True,
                    },
                }
                clientgroup_props = entities.create(clientgroup_inputs)
                entities.delete(clientgroup_props)

                # Create clientgroup by * not specifying client in client list
                # and using option default_client set to True.
                # With this option a client should be selected by default and
                # associated with the client group.
                # Since backupset entity is selected to be created with clientgroup
                # default client here would be client on which backupset will be
                # created.
                # In case any other entity is selected to be created with client
                # group, then default client will be the client for the entity
                # created first from the order defined in serverconstants
                # ORDERED_ENTITIES
                clientgroup_inputs = {
                    'clientgroup':
                    {
                        'name': "clientgroup_" + self.id,
                        'default_client': True,
                        'description': 'Automation client group',
                        'enable_backup': True,
                        'enable_restore': True,
                        'enable_data_aging': True,
                        'force': True,
                    },
                    'backupset':
                    {
                        'name': "backupset_cg" + self._id,
                        'client': self._commcell.commserv_name,
                        'on_demand_backupset': False,
                    }
                }
                clientgroup_props = entities.create(clientgroup_inputs)
                entities.delete(clientgroup_props)

                # Create clientgroup by * not specifying client in client list
                # and using option default_client set to False. Client should
                # not be selected and client group without any client association
                # should be created
                clientgroup_inputs = {
                    'clientgroup':
                    {
                        'name': "clientgroup_" + self.id,
                        'default_client': False,
                        'description': 'Automation client group',
                        'enable_backup': True,
                        'enable_restore': True,
                        'enable_data_aging': True,
                        'force': True,
                    },
                }
                clientgroup_props = entities.create(clientgroup_inputs)
                entities.delete(clientgroup_props)

            def standalone_target_props():
                '''Create each entity separately with target properties only'''

                tc.log_step("""Creating entities with target properties
                                Input type to create(): Dictionary""", 200)

                clientgroup_inputs = {
                    'target':
                    {
                        'force': True
                    },
                    'clientgroup':
                    {
                        'name': "clientgroup_" + self.id,
                        'clients': [_client],
                        'description': 'Automation client group',
                        'enable_backup': True,
                        'enable_restore': True,
                        'enable_data_aging': True,
                    },
                }
                clientgroup_props = entities.create(clientgroup_inputs)
                entities.delete(clientgroup_props)

                # Create backupset
                backupset_inputs = {'target':
                                        {
                                            'client': _client,
                                            'agent': "File system",
                                            'instance': "defaultinstancename",
                                            'force': True
                                        },
                                    'backupset':
                                        {
                                            'name': "Backupset_" + self.id,
                                            'on_demand_backupset': False,
                                        }
                                   }
                backupset_props = entities.create(backupset_inputs)
                entities.delete(backupset_props)

                # Create subclient
                subclient_inputs = {
                    'target':
                    {
                        'client': _client,
                        'agent': "File system",
                        'instance': "defaultinstancename",
                        'storagepolicy': storagepolicyname,
                        'backupset': "defaultBackupSet",
                        'force': True
                    },
                    'subclient':
                    {
                        'name': "Subclient_" + self.id,
                        'content': ["C:\\test3.txt", "C:\\test4.txt"],
                        'description': "Automation - Target properties",
                        'subclient_type': None,
                    }
                }

                subclient_props = entities.create(subclient_inputs)
                entities.delete(subclient_props)

                # Create disklibrary
                disklibrary_inputs = {
                    'target':
                    {
                        'mediaagent': mediaagent,
                        'force': True
                    },
                    'disklibrary':
                    {
                        'name': "disklibrary_" + self.id,
                        'mount_path': entities.get_mount_path(mediaagent),
                        'username': '',
                        'password': '',
                        'cleanup_mount_path': True,
                    }
                }
                disklibrary_props = entities.create(disklibrary_inputs)

                entities.delete(disklibrary_props)

                # Create storage policy
                storagepolicy_inputs = {
                    'target':
                    {
                        'library': _library,
                        'mediaagent': mediaagent,
                        'force': True
                    },
                    'storagepolicy':
                    {
                        'name': "storagepolicy_" + self.id,
                        'dedup_path': None,
                        'incremental_sp': None,
                        'retention_period': 3,
                    },
                }
                storagepolicy_props = entities.create(storagepolicy_inputs)
                entities.delete(storagepolicy_props)

            def all_default_props():
                '''Create all entities with default properties'''
                tc.log_step("""Create all entities with default properties
                                Input type to create(): list""", 200)

                all_props = entities.create(['disklibrary',
                                             'storagepolicy',
                                             'backupset',
                                             'subclient',
                                             'clientgroup'])
                entities.delete(all_props)

            def all_target_props():
                '''Create all entities together by providing the common
                    target properties'''

                tc.log_step("""Creating all entities with target properties.
                                  Target properties will be utilized, as the entity
                                  properties are not defined.
                                Input type to create(): Dictionary""", 200)

                all_inputs = {
                    'target':
                    {
                        'client': _client,
                        'agent': "File system",
                        'instance': "defaultinstancename",
                        'storagepolicy': storagepolicyname,
                        'mediaagent': mediaagent,
                        'library': _library,
                        'force': True
                    },
                    'backupset': None,
                    'subclient': {'content': ["C:\\test5.txt", "C:\\test6.txt"],},
                    'disklibrary': None,
                    'storagepolicy': None,
                    'clientgroup': None
                }
                all_props = entities.create(all_inputs)
                entities.delete(all_props)

            def all_specific_props():
                '''Create all entities together by providing individual entity
                    properties'''
                tc.log_step("""Creating all entities with specific properties
                                Input type to create(): Dictionary""", 200)

                all_inputs = {
                    'backupset':
                    {
                        'name': "Backupset_" + self.id,
                        'client': _client,
                        'agent': "File system",
                        'instance': "defaultinstancename",
                        'on_demand_backupset': False,
                        'force': True,
                    },
                    'subclient':
                    {
                        'name': "Subclient_" + self.id,
                        'client': _client,
                        'agent': "File system",
                        'instance': "defaultinstancename",
                        'storagepolicy': storagepolicyname,
                        'backupset': "defaultBackupSet",
                        'content': None,
                        'level': 1,
                        'size': 1,
                        'description': "Automation-All entities and individual props",
                        'subclient_type': None,
                        'force': True,
                    },
                    'disklibrary':
                    {
                        'name': "disklibrary_" + self.id,
                        'mediaagent': mediaagent,
                        'mount_path': entities.get_mount_path(mediaagent),
                        'username': '',
                        'password': '',
                        'cleanup_mount_path': True,
                        'force': True,
                    },
                    'storagepolicy':
                    {
                        'name': "storagepolicy_" + self.id,
                        'library': _library,
                        'mediaagent': mediaagent,
                        'dedup_path': None,
                        'incremental_sp': None,
                        'retention_period': 3,
                        'force': True,
                    },
                    'clientgroup':
                    {
                        'name': "clientgroup_" + self.id,
                        'clients': [_client],
                        'description': 'Automation client group',
                        'enable_backup': True,
                        'enable_restore': True,
                        'enable_data_aging': True,
                    },
                }
                all_props = entities.create(all_inputs)

                entities.delete(all_props)

            def all_mixed_props():
                '''Create all entities together by providing individual entity
                    properties and target properties also'''
                tc.log_step("""Creating all entities with target and specific
                                properties. With mixed configuration if the
                                entity property is defined it would override
                                target properties.
                                Input type to create(): Dictionary""", 200)

                all_inputs = {
                    'target':
                    {
                        'client': "RANDOM Unsupported string",
                        'agent': "RANDOM Unsupported string",
                        'instance': "RANDOM Unsupported string",
                        'storagepolicy': "RANDOM Unsupported string",
                        'mediaagent': "RANDOM Unsupported string",
                        'library': "RANDOM Unsupported string",
                        'force': False
                    },
                    'backupset':
                    {
                        'name': "Backupset_" + self.id,
                        'client': _client,
                        'agent': "File system",
                        'instance': "defaultinstancename",
                        'on_demand_backupset': False,
                        'force': True,
                    },
                    'subclient':
                    {
                        'name': "Subclient_" + self.id,
                        'client': _client,
                        'agent': "File system",
                        'instance': "defaultinstancename",
                        'storagepolicy': storagepolicyname,
                        'backupset': "defaultBackupSet",
                        'content': None,
                        'level': 1,
                        'size': 1,
                        'description': "Automation-All, individual and target props",
                        'subclient_type': None,
                        'force': True,
                    },
                    'disklibrary':
                    {
                        'name': "disklibrary_" + self.id,
                        'mediaagent': mediaagent,
                        'mount_path': entities.get_mount_path(mediaagent),
                        'username': '',
                        'password': '',
                        'cleanup_mount_path': True,
                        'force': True,
                    },
                    'storagepolicy':
                    {
                        'name': "storagepolicy_" + self.id,
                        'library': _library,
                        'mediaagent': mediaagent,
                        'dedup_path': None,
                        'incremental_sp': None,
                        'retention_period': 3,
                        'force': True,
                    },
                    'clientgroup':
                    {
                        'name': "clientgroup_" + self.id,
                        'clients': [_client],
                        'description': 'Automation client group',
                        'enable_backup': True,
                        'enable_restore': True,
                        'enable_data_aging': True,
                    },
                }
                all_props = entities.create(all_inputs)
                entities.delete(all_props)

            def all_named_props():
                '''Create all entities by providing just the name of the entity
                    Take all default inputs '''
                tc.log_step("""Creating all entities with specific properties,
                                providing just the name of entity.
                                Input type to create(): Dictionary""", 200)

                all_inputs = {
                    'target':
                    {
                        'client': _client,
                        'agent': "File system",
                        'instance': "defaultinstancename",
                        'storagepolicy': storagepolicyname,
                        'mediaagent': mediaagent,
                        'library': _library,
                        'force': True
                    },
                    'backupset':{'name': "Backupset_named"},
                    'subclient':{'name': "Subclient_named",
                                 'content': None,
                                 'level': 1,
                                 'size': 1},
                    'disklibrary':{'name': "disklibrary_named"},
                    'storagepolicy':{'name': "storagepolicy_named"},
                    'clientgroup':{'name': "clientgroup_named"},
                }
                all_props = entities.create(all_inputs)
                entities.delete(all_props)

            def all_unforced():
                '''Test without force (False) option in target properties '''
                tc.log_step("""Creating all entities with specific properties,
                                providing just the name of entity, and force set
                                to False. If entity exists then it would not be
                                created and would return the existing object
                                details
                                Input type to create(): Dictionary""", 200)

                all_inputs = {
                    'target':
                    {
                        'client': _client,
                        'agent': "File system",
                        'instance': "defaultinstancename",
                        'storagepolicy': storagepolicyname,
                        'mediaagent': mediaagent,
                        'library': _library,
                        'force': False
                    },
                    'backupset':{'name': '_'.join(["bkpset", self.id, "unforced"])},
                    'subclient':{'name': '_'.join(["subc", self.id, "unforced"]),
                                 'content': None,
                                 'level': 1,
                                 'size': 1},
                    'disklibrary':{'name': '_'.join(["lib", self.id, "unforced"])},
                    'storagepolicy':{'name': '_'.join(["sp", self.id, "unforced"])},
                    'clientgroup':{'name': '_'.join(["cg", self.id, "unforced"])},
                }
                created_entities = entities.create(all_inputs)

                # These entities should not be created as force is set to false.
                _ = entities.create(all_inputs)

                # Have to delete here without cleanup taking care of it as force=false will
                # not allow cleanup to delete them
                entities.delete(created_entities)

            def validate_subclient_content_cleanup():
                """ Validate all possible cases where content might be cleaned up """

                # Content should not be created in this case at all.
                _ = entities.create({
                    'subclient':
                    {
                        'force': False,
                        'content': 'skip'
                    }
                })

                # Content should not be created and should be set to C:\\temp. Content should not be deleted
                # during cleanup as entities class did not create the content.
                _ = entities.create({'subclient':{'content': ["C:\\temp"]}})

                # Regular scenario. Subclient content should be deleted during subclient cleanup
                _ = entities.create({'subclient':{'force': True}})

                # AlreadyCreated subclient should already exist.
                # Subclient content should not be created/deleted at all for this subclient
                _ = entities.create({
                    'subclient':
                    {
                        'name': "AlreadyCreated",
                        'force': False,
                        'content': 'skip'
                    }
                })

                # In this case subclient content would be created and would be set to subclient content
                # But during cleanup the subclient content would not be deleted.
                _ = entities.create({'subclient':{'force': False}})

                # Content should not be cleaned up post subclient deletion.
                _ = entities.create({'subclient':{'force': False, 'cleanup_content': False}})
                _ = entities.create({'subclient':{'force': True, 'cleanup_content': False}})
                _ = entities.create({'subclient':{'cleanup_content': False}})

            def multiple_client_groups():
                '''Create multiple client groups with default properties'''

                tc.log_step("""Create multiple client groups with default properties""", 200)

                props = entities.create_client_groups(['cg1', 'cg2', 'cg3'])

                self.log.info("Client groups created: \n {0}".format(pformat(props)))

                self.log.info("Deleting client groups")

                props = entities.delete_client_groups(props)

            #
            # Test cases to validate entities creation/deletion with various
            # input types
            #

            # Create all entities
            whole_nine_yards()

            # Create each entity separately without defining any properties
            # Delete each entity separately
            standalone_default_props()

            # Create each entity separately with individual properties
            # Delete each entity separately
            standalone_specific_props()

            # Create each entity separately with target properties only
            # Delete each entity separately
            standalone_target_props()

            # Create all entities with default properties
            # Delete all entities
            all_default_props()

            # Create all entities together by providing the common target properties
            # Delete all entities
            all_target_props()

            # Create all entities together by providing individual entity properties
            # Delete all entities created above
            all_specific_props()

            # Create all entities together by providing individual entity properties
            # and target properties also
            # Delete all entities
            all_mixed_props()

            # Create all entities by providing just the name of the entity
            # [ Take all default inputs ]
            # Delete all
            all_named_props()

            # Test without force option in target properties
            all_unforced()

            # Subclient cleanup
            validate_subclient_content_cleanup()

            # Create multiple client groups with default properties
            multiple_client_groups()

            # Validate the storage policy (including copy) when tried to create again does not fail and reports
            # that the policy copy already exits.
            sp_copy_recreate_existing()

        except Exception as excp:
            tc.fail(excp)
        finally:
            entities.cleanup()
