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

    verify_logging()            --  Verifies if the log lines are logged as expected in CVDotNetContainer.log

    set_debug_level()           --  Sets the debug level of CVDotNetContainer service

"""
import time

from AutomationUtils.cvtestcase import CVTestCase
from Platform.helpers import cvdnc_testcase


class TestCase(CVTestCase):
    """This testcase verifies if the service developed using CVDotNetContainer is working as expected."""

    def __init__(self):
        """Initializes test case class object"""

        super(TestCase, self).__init__()
        self.name = 'CVDotNetContainer - Logging and misc tests'

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

        self.log.info('***** Verifying MISC operations *****')

        response = self.help.request('GET', 'Misc/Exception')
        self.help.verify(response, status=500, content_type='')

        response = self.help.request('GET', 'Misc/QueryString', params={
            'userGuid': sample_data['userGuid'],
            'comment': sample_data['comment']
        })
        self.help.verify(response)
        assert (response.json()['userGuid'] == sample_data['userGuid'] and
                response.json()['comment'] == sample_data['comment']), \
            f'Query string not received as expected. [{response.text}]'

        response = self.help.request('POST', 'Misc/FormData', data={
            'userGuid': sample_data['userGuid'],
            'comment': sample_data['comment']
        })
        self.help.verify(response)
        assert (response.json()['userGuid'] == sample_data['userGuid'] and
                response.json()['comment'] == sample_data['comment']), \
            f'Form data not received as expected. [{response.text}]'

        response = self.help.request('GET', 'Misc/PasswordOut')
        self.help.verify(response)
        assert 'password' not in response.json(), 'Password field not stripped in the output'

        response = self.help.request('GET', 'Misc/CustomHeader', params={
            'headerName': 'X-Hello',
            'headerValue': 'World'
        })
        self.help.verify(response, content_type='')
        assert 'X-Hello' in response.headers and response.headers['X-Hello'] == 'World', \
            'Header not set in response as expected'

        self.log.info('***** Verifying LOGGING operation *****')

        rand_id = self.help.random_guid()[:5]
        response = self.help.request('GET', 'Misc/Logs', params={
            'randGuid': rand_id
        })
        self.help.verify(response, content_type='')
        self.verify_logging(rand_id=rand_id, expected_lines='3')

        self.set_debug_level()
        time.sleep(30)

        rand_id = self.help.random_guid()[:5]
        response = self.help.request('GET', 'Misc/Logs', params={
            'randGuid': rand_id
        })
        self.help.verify(response, content_type='')
        self.verify_logging(rand_id=rand_id, expected_lines='6')

    def verify_logging(self, rand_id, expected_lines):
        """Verifies if the log lines are logged as expected in CVDotNetContainer.log

            Args:
                rand_id         (str)   --      The random string to look for verification in the log file

                expected_lines  (str)   --      The expected number of log lines with the random ID

        """

        time.sleep(5)
        log_file = f'{self.host_cl.log_directory}/CVDotNetContainer.log'
        self.log.info('Log file path [%s]', log_file)
        out = None

        if self.setup_data['deployment'].lower() == 'vm':
            out = self.help.exec(f'(get-content -path "{log_file}" | select-string -pattern "{rand_id}" | Measure-Object -line).Lines')

        if self.setup_data['deployment'].lower() == 'container':
            out = self.help.exec(f'docker exec cvdnc_cnt cat "{log_file}" | grep {rand_id} | wc -l')

        lines_found = out.formatted_output
        self.log.info('Found log lines [%s]', lines_found)

        if lines_found != expected_lines:
            self.log.error('Mismatch in actual and expected log lines')

    def set_debug_level(self, log_level='10'):
        """Sets the debug level of CVDotNetContainer service

            Args:
                log_level       (str)   --      The log level to set for CVDotNetContainer

        """

        reg_name = 'CVDOTNETCONTAINER'

        if self.setup_data['deployment'].lower() == 'vm':
            self.log.info('Increasing debug level')
            self.host_machine.set_logging_debug_level(reg_name, log_level)

            self.log.info('Restarting CVPlatformService')
            self.host_cl.restart_service(f'CVPlatformService({self.host_cl.instance})')

        if self.setup_data['deployment'].lower() == 'container':
            reg_path = '/etc/CommVaultRegistry/Galaxy/Instance001/EventManager/.properties'

            self.log.info('Deleting debug level')
            self.help.exec(f'docker exec cvdnc_cnt sed -i /{reg_name}/Id {reg_path}')

            self.log.info('Setting debug level')
            out = self.help.exec(f'docker exec cvdnc_cnt bash -c \' echo "{reg_name}_DEBUGLEVEL {log_level}" >> {reg_path}\'')
            if out.exit_code != 0:
                raise Exception('Failed to set debug level on the container')

            self.log.info('Restarting CvDotNetContainer services')
            self.help.exec('docker exec cvdnc_cnt commvault restart -service CVDotNetContainer')
