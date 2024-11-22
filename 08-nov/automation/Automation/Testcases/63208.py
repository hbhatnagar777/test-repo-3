# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Main file for executing this test case

This testcase verifies if browse aggregate and topbottom query works as expected.

TestCase:
    __init__()                  --  Initializes the TestCase class

    setup()                     --  All testcase objects are initializes in this method

    run()                       --  Contains the core testcase logic, and it is the one executed

    scan_files()                --  Scans the subclient content for the list of files created

    send_browse_request()       --  Sends the browse request with the aggregate and top bottom queries

    expected_result()           --  The expected result for the aggregate queries

"""
import json

from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine

from Indexing.testcase import IndexingTestcase
from Indexing.helpers import IndexingHelpers


class TestCase(CVTestCase):
    """This testcase verifies if browse aggregate and topbottom query works as expected.

        Steps:
            1) Create 2 subclients
            2) Create testdata which varied file sizes
            3) Run FULL, INC, INC backups
            4) Collect the information on the min, max, sum, avg of files, total number of files, top files by size
            5) Do a latest browse from backupset level with aggregate query for the above aggregate info
            6) Verify if the results are same as expected

    """

    def __init__(self):
        """Initializes test case class object"""

        super(TestCase, self).__init__()
        self.name = 'Indexing - Aggregate and Top bottom query'

        self.tcinputs = {
            'TestDataPath': None,
            'StoragePolicy': None,
        }

        self.cl_machine = None
        self.idx_tc = None
        self.idx_help = None
        self.top_bottom_count = 5
        self.files = {}

    def setup(self):
        """All testcase objects are initialized in this method"""

        self.cl_machine = Machine(self.client, self.commcell)

        self.idx_tc = IndexingTestcase(self)
        self.idx_help = IndexingHelpers(self.commcell)

        self.backupset = self.idx_tc.create_backupset('aggregate_query', for_validation=False)

        self.subclient_1 = self.idx_tc.create_subclient(
            name='sc1_aggr',
            backupset_obj=self.backupset,
            storage_policy=self.tcinputs.get('StoragePolicy'),
            delete_existing_testdata=True
        )

        self.subclient_2 = self.idx_tc.create_subclient(
            name='sc2_aggr',
            backupset_obj=self.backupset,
            storage_policy=self.tcinputs.get('StoragePolicy'),
            delete_existing_testdata=False
        )

    def run(self):
        """Contains the core testcase logic"""

        self.idx_tc.new_testdata(self.subclient_1.content, large_files=(10240, 1024000), count=5)
        self.idx_tc.new_testdata(self.subclient_2.content, large_files=(10240, 1024000), count=5)

        self.idx_tc.run_backup_sequence(
            self.subclient_1, ['full', 'edit', 'incremental'], verify_backup=False
        )

        self.idx_tc.run_backup_sequence(
            self.subclient_2, ['full', 'edit', 'incremental'], verify_backup=False
        )

        self.scan_files(self.subclient_1)
        self.scan_files(self.subclient_2)

        self.log.info('***** List of files collected *****')
        self.log.info(self.files)

        self.log.info('***** Sending aggregate and top bottom browse request *****')
        response = self.send_browse_request()

        self.log.info('***** Parsing browse response [%s] *****', response)
        results = self.parse_response(response)
        self.log.info('***** Actual results [%s] *****', json.dumps(results))

        self.log.info('***** Getting expected results *****')
        e_results = self.expected_result()
        self.log.info('***** Expected results [%s] *****', e_results)

        if results != e_results:
            raise Exception('Mismatch in aggregate query result(s)')

        self.log.info('***** Successfully verified aggregate and top bottom query results *****')

    def scan_files(self, subclient):
        """Scans the subclient content for the list of files created

            Args:
                subclient       (obj)   --      The subclient obj to collect the files list

            Returns:
                None

        """

        self.log.info('Collecting files for subclient [%s]', subclient.name)
        for path in subclient.content:
            self.log.info('Collecting files under path [%s]', path)
            items = self.cl_machine.scan_directory(path)
            for item in items:
                if item['type'] == 'file':
                    self.files[item['path']] = int(item['size'])

    def send_browse_request(self):
        """Sends the browse request with the aggregate and top bottom queries"""

        request = {
            'path': '/**/*',
            '_custom_queries': [
                {
                    'type': 'AGGREGATE',
                    'queryId': 'count_query',
                    'aggrParam': {
                        'aggrType': 'COUNT'
                    },
                    'whereClause': [{
                        'criteria': {
                            'field': 'Flags',
                            'dataOperator': 'IN',
                            'values': ['file']
                        },
                        'connector': 'AND'
                    }]
                },
                {
                    'type': 'AGGREGATE',
                    'queryId': 'min_query',
                    'aggrParam': {
                        'aggrType': 'min',
                        'field': 'FileSize',
                    },
                    'whereClause': [{
                        'criteria': {
                            'field': 'Flags',
                            'dataOperator': 'IN',
                            'values': ['file']
                        },
                        'connector': 'AND'
                    }]
                },
                {
                    'type': 'AGGREGATE',
                    'queryId': 'max_query',
                    'aggrParam': {
                        'aggrType': 'max',
                        'field': 'FileSize',
                    },
                    'whereClause': [{
                        'criteria': {
                            'field': 'Flags',
                            'dataOperator': 'IN',
                            'values': ['file']
                        },
                        'connector': 'AND'
                    }]
                },
                {
                    'type': 'AGGREGATE',
                    'queryId': 'sum_query',
                    'aggrParam': {
                        'aggrType': 'SUM',
                        'field': 'FileSize',
                    },
                    'whereClause': [{
                        'criteria': {
                            'field': 'Flags',
                            'dataOperator': 'IN',
                            'values': ['file']
                        },
                        'connector': 'AND'
                    }]
                },
                {
                    'type': 'AGGREGATE',
                    'queryId': 'avg_query',
                    'aggrParam': {
                        'aggrType': 'avg',
                        'field': 'FileSize',
                    },
                    'whereClause': [{
                        'criteria': {
                            'field': 'Flags',
                            'dataOperator': 'IN',
                            'values': ['file']
                        },
                        'connector': 'AND'
                    }]
                },
                {
                    'type': 'TOPBOTTOM',
                    'queryId': 'tb_query',
                    'topBottomParam': {
                        'count': self.top_bottom_count,
                        'field': 'FileSize',
                        'ascending': False,
                    },
                    'whereClause': [{
                        'criteria': {
                            'field': 'Flags',
                            'dataOperator': 'IN',
                            'values': ['file']
                        },
                        'connector': 'AND'
                    }]
                }
            ],
            '_raw_response': True
        }

        self.log.info('Browse request [%s]', request)
        dummy_var, response = self.backupset.find(request)

        return response

    def parse_response(self, response):
        """Parses the query results from the browse response

            Args:
                response    (dict)      --      The browse response received

            Returns:
                (dict)  --  List of the query results with query id as the key

        """

        results = {}

        for browse_response in response.get('browseResponses', {}):
            if browse_response['respType'] != 0 or 'browseResult' not in browse_response:
                self.log.error('Skipping response type [%s]', browse_response['respType'])
                continue

            browse_result = browse_response['browseResult']
            query_id = browse_result.get('queryId')
            self.log.info('Got query response for [%s] - [%s]', query_id, browse_result)

            if 'aggrResultSet' in browse_result and browse_result['aggrResultSet']:
                results[query_id] = int(browse_result['aggrResultSet'][0].get('result', 0))

            if 'dataResultSet' in browse_result and browse_result['dataResultSet']:
                items = []
                for data_result in browse_result['dataResultSet']:
                    item = data_result.get('path').lower()
                    items.append(item)

                results[query_id] = items

        return results

    def expected_result(self):
        """The expected result for the aggregate queries"""

        results = {}

        current_min = 0
        current_max = 0
        total_sum = 0
        for file in self.files:
            current_min = min(current_min, self.files[file])
            current_max = max(current_max, self.files[file])
            total_sum += self.files[file]

        results['count_query'] = len(self.files)
        results['min_query'] = current_min
        results['max_query'] = current_max
        results['sum_query'] = total_sum
        results['avg_query'] = int(total_sum/len(self.files))

        top_bottom = []
        for path, size in sorted(self.files.items(), key=lambda item: item[1], reverse=True):
            top_bottom.append(path.lower())

        results['tb_query'] = top_bottom[:self.top_bottom_count]

        return results
