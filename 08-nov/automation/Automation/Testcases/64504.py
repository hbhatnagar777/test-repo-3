# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Main file for executing this test case

This testcase verifies if the service developed using CVDotNetContainer is working as expected.

TestCase:
    __init__()                  --  Initializes the TestCase class

    setup()                     --  All testcase objects are initializes in this method

    run()                       --  Contains the core testcase logic and it is the one executed

"""

from AutomationUtils.cvtestcase import CVTestCase
from Platform.helpers import cvdnc_testcase


class TestCase(CVTestCase):
    """This testcase verifies if the service developed using CVDotNetContainer is working as expected."""

    def __init__(self):
        """Initializes test case class object"""

        super(TestCase, self).__init__()
        self.name = 'CVDotNetContainer - CRUD and Serialization tests'

        self.tcinputs = {}  # Inputs are loaded from the setup testcase 64503

        self.help = None
        self.host_cl = None
        self.host_machine = None
        self.svc_url = None
        self.setup_data = None

    def setup(self):
        """All testcase objects are initialized in this method"""

        self.help = cvdnc_testcase.CVDNCTestcase(self.commcell)
        self.setup_data = self.help.load_setup_data()

        self.help.set_host_machine()

        self.host_cl = self.help.host_cl
        self.host_machine = self.help.host_machine

    def run(self):
        """Contains the core testcase logic"""

        random_data = self.help.populate_random_data()
        sample_data = random_data[0]

        self.log.info('***** Verifying CRUD operations *****')

        response = self.help.request('GET', f'CRUD/{sample_data["userGuid"]}')
        self.help.verify(response)
        assert 'comment' in response.json() and 'userGuid' in response.json(), \
            f'Response not as expected [{response.json()}]'

        new_comment = self.help.random_sentence()
        sample_data['comment'] = random_data[0]['comment'] = new_comment
        response = self.help.request('PUT', f'CRUD/{sample_data["userGuid"]}', json={
            'comment': new_comment,
            'userGuid': sample_data["userGuid"]
        })
        self.help.verify(response)

        delete_data = random_data[1]
        response = self.help.request('DELETE', f'CRUD/{delete_data["userGuid"]}')
        self.help.verify(response)
        del random_data[1]

        response = self.help.request('GET', f'CRUD/{delete_data["userGuid"]}')
        self.help.verify(response, status=400)

        self.log.info('***** Verifying SERIALIZATION operations *****')

        response = self.help.request('POST', 'CRUD', headers={
            'content-type': 'application/json',
            'accept': 'application/json'
        }, json={
            'comment': self.help.random_sentence(),
            'userGuid': self.help.random_guid()
        })
        self.help.verify(response, content_type='application/json')

        response = self.help.request('POST', 'CRUD', headers={
            'content-type': 'application/json',
            'accept': 'application/xml'
        }, json={
            'comment': self.help.random_sentence(),
            'userGuid': self.help.random_guid()
        })
        self.help.verify(response, content_type='application/xml')
        assert 'databrowse_FileComment' in response.text, 'Response is not in XML output'

        response = self.help.request('POST', 'CRUD', headers={
            'content-type': 'application/xml',
            'accept': 'application/xml'
        }, data=f'<databrowse_FileComment comment="{self.help.random_sentence()}" userGuid="{self.help.random_guid()}"/>')
        self.help.verify(response, content_type='application/xml')
        assert 'databrowse_FileComment' in response.text, 'Response is not in XML output'

        response = self.help.request('POST', 'CRUD', headers={
            'content-type': 'application/xml',
            'accept': 'application/json'
        }, data=f'<databrowse_FileComment comment="{self.help.random_sentence()}" userGuid="{self.help.random_guid()}"/>')
        self.help.verify(response, content_type='application/json')
