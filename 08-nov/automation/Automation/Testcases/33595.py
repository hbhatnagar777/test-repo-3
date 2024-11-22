# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

Test cases to validate client group basic Acceptance test cases.

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()                  --  initialize TestCase class

    validate_clients_in_cg(clientgroup,
                           expected)
                                --  Validate number of clients in client group from API output

    run()                       --  run function of this test case
"""

# Test Suite imports
from AutomationUtils.cvtestcase import CVTestCase
from Server.serverhelper import ServerTestCases
from AutomationUtils.options_selector import CVEntities, OptionsSelector

class TestCase(CVTestCase):
    """Class for creating/deleting commcell entities"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "[Acceptance]: Client Group - Basic acceptance"
        self.applicable_os = self.os_list.WINDOWS
        self.product = self.products_list.COMMSERVER
        self.feature = self.features_list.CLIENTGROUP
        self.show_to_user = True

    def run(self):
        """Main function for test case execution."""

        try:
            tc = ServerTestCases(self)
            entities = CVEntities(self)
            db = OptionsSelector(self.commcell)

            def validate_clients_in_cg(clientgroup, expected):
                ''' Validate number of clients in client group from API output

                    Args:

                        clientgroup     (client group object)   -- Client group object

                        expected        (int)                   -- Number of clients expected in
                                                                    client group

                    Raises
                        Assertion
                            - if number of clients in client group do not match the expected
                                number.
                '''
                clients = len(clientgroup.associated_clients)

                self.log.info("Number of associated clients = %s", str(clients))
                self.log.info("Number of expected associated clients = %s", str(expected))

                assert int(clients) == int(expected), "Client count mismatch"

            # Get smart inputs for client
            client = db.get_client() if self.client.client_id == 2 else self.client.client_name

            tc.log_step("""Test Case 1.
                            ( Actual test case as defined in QC )
                                a. Create empty client group and validate.
                                b. Add one client to the Group and validate.
                                c. Remove the added client from the Group and validate.
                                d. Create client group using the following Qscript command
                                      qoperation execscript -sn CreateClientGroup
                                      -si 'group_name' -si 'group_description'
                                      and validate DB
                                e. Delete client group and validate.
                            """, 200)

            # Creating client group without any client association
            props = entities.create({'clientgroup':{'default_client': False}})

            clientgroup = props['clientgroup']['object']

            entities.update_clientgroup(clientgroup, clients_to_add=client)

            validate_clients_in_cg(clientgroup, 1)

            entities.update_clientgroup(clientgroup, clients_to_remove=client)

            validate_clients_in_cg(clientgroup, 0)

            # To do:
            # Add support for qoperation execscript once the support for token is
            # added by sdk team for qcommands.
            #

            entities.delete(props)

            tc.log_step("""Test Case 2.
                            ( Test case as automated in old suite )
                                a. Create client group with minimum 2 clients
                                b. Remove the added client from the Group
                                c. Rename the client group
                        """, 200)

            # Creating client group with two clients
            clients = db.get_client(num=2)

            props = entities.create({'clientgroup':{'clients': clients}})

            clientgroup = props['clientgroup']['object']
            name = props['clientgroup']['name']

            entities.update_clientgroup(clientgroup, clients_to_remove=clients[0])

            entities.update_clientgroup(clientgroup, '_'.join([name, 'rename']))

        except AssertionError as aserr:
            self.log.error("Validation failed. Error: {0}".format(aserr))
            tc.fail(aserr)
        except Exception as excp:
            tc.fail(excp)
        finally:
            entities.cleanup()
