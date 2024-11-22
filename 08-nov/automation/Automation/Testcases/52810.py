# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

This testcase verifies that the "unusual job activity alert" is working for added, modified, deleted and root size
change activities.

TestCase:
    __init__()                  --  Initializes the TestCase class

    setup()                     --  All testcase objects are initializes in this method

    run()                      --  Contains the core testcase logic and it is the one executed

    populate_job_stats()  --  Generates anomalous job stats data

"""

import traceback
import time
import random

from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine

from Indexing.helpers import IndexingHelpers
from Indexing.database import index_db


class TestCase(CVTestCase):
    """This testcase verifies that the "unusual job activity alert" is working for added, modified, deleted and
    root size change activities."""

    def __init__(self):
        """Initializes test case class object"""

        super(TestCase, self).__init__()
        self.name = 'Indexing - Unusual job activity alert'

        self.tcinputs = {}

        self.cl_machine = None
        self.idx_tc = None
        self.idx_help = None
        self.index_db = None
        self.index_server_machine = None

        self.js_raw = None
        self.js_fields = None
        self.js_lines = None

        self.last_event = None

        self.anomaly_job = None
        self.anomalous_jobs = {}

    def setup(self):
        """All testcase objects are initialized in this method"""

        try:
            self.cl_machine = Machine(self.client, self.commcell)

            self.idx_help = IndexingHelpers(self.commcell)

            indexing_level = self.idx_help.get_agent_indexing_level(self.agent)
            entity_obj = self.subclient if indexing_level == 'subclient' else self.backupset
            self.index_db = index_db.get(entity_obj)

            self.js_fields = ['Total Files in Index', 'Job Id', 'Total Commands', 'Added Files', 'Deleted Folders',
                              'Deleted Files', 'Seconds To Playback', 'Start Time', 'End Time', 'Modified Files',
                              'Job Type', 'Hostname', 'Timestamp', 'Status', 'Root Size',
                              'Invalid MIME Classification', 'Number of Nodes', 'Backup Size',
                              'DDB Block Count', 'Data Written']

            self.csdb.execute("""
                select top 1 id from evMsg where subsystem='CvStatAnalysis' order by id desc
            """)
            self.last_event = self.csdb.fetch_one_row()[0]
            self.log.info('Last seen anomaly event is [{0}]'.format(self.last_event))

        except Exception as exp:
            self.log.error(str(traceback.format_exc()))
            raise Exception(exp)

    def run(self):
        """Contains the core testcase logic and it is the one executed

            Steps:
                1) Generate anomalous job stats information for added, modified, deleted and root size activities and
                note down the jobs.
                2) Add the anomalous jobs to the jobstats.csv file
                3) Restart IndexServer services
                4) Verify if anomaly events are generated for the expected jobs.

        """
        try:

            self.log.info('********** Populating data **********')
            job_stats_lines = self.populate_job_stats(count=22)
            job_stats_text = '\r\n'.join(job_stats_lines)

            try:
                self.index_db.isc_machine.delete_file(self.index_db.job_stats_file)
            except Exception as e:
                self.log.error('Failed to delete existing job stats file')

            self.log.info('********** Creating job stats file **********')
            self.index_db.isc_machine.create_file(self.index_db.job_stats_file, job_stats_text)

            self.log.info('********** Triggering anomaly detection **********')
            self.index_db.idx_cli.do_anomaly_check(
                job_stats_path=self.index_db.job_stats_file,
                job_id=self.anomaly_job,
                client_name=self.client.client_name
            )

            self.log.info('********** Waiting 10 secs for anomaly process to complete **********')
            time.sleep(10)

            self.log.info('********** Verifying if anomaly events are generated **********')
            self.csdb.execute("""
                select id from evMsg where subsystem='CvStatAnalysis' and id > '{0}'
            """.format(self.last_event))

            all_events = self.csdb.fetch_all_rows()
            self.log.info('New events {0}'.format(all_events))

            events_generated = {}
            for event in all_events:
                event_id = event[0]

                # Getting event job ID
                self.csdb.execute("""select top 1 data from evparam where evmsgid = '{0}' and position = 1""".format(
                    event_id
                ))
                job_id = self.csdb.fetch_one_row()[0]
                self.log.info('Actual anomalous job ID in the event [%s]', job_id)
                self.log.info('Expected anomalous job ID [%s]', self.anomaly_job)

                if not job_id:
                    raise Exception('No anomaly detected!')

                if int(job_id) != int(self.anomaly_job):
                    raise Exception('Anomaly event is raised for a different job')

                # Getting event type
                self.csdb.execute("""select data from evparam where evmsgid = '{0}' and position = 2""".format(
                    event_id
                ))
                anomaly_type = self.csdb.fetch_one_row()[0]
                events_generated[int(job_id)] = anomaly_type

                # Getting event description
                self.csdb.execute("""select data from evparam where evmsgid = '{0}' and position = 3""".format(
                    event_id
                ))
                anomaly_desc = self.csdb.fetch_one_row()[0]
                self.log.info('Event description [%s]', anomaly_desc)

            self.log.info('Actual events generated [%s]', events_generated)
            self.log.info('Expected events [%s]', self.anomalous_jobs)

            for job_id, anomaly_type in self.anomalous_jobs.items():
                if job_id not in events_generated:
                    raise Exception('Some expected anomaly events are not generated')

            self.log.info('********** All expected anomaly events are generated. **********')

        except Exception as exp:
            self.log.error('Test case failed with error: ' + str(exp))
            self.result_string = str(exp)
            self.status = constants.FAILED
            self.log.error(str(traceback.format_exc()))

    def populate_job_stats(self, count=20):
        """Generates anomalous job stats data"""

        self.csdb.execute("""select top 1 jobid from JMBkpStats where appId = '{0}' order by jobId desc""".format(
            self.subclient.subclient_id
        ))

        last_job_id = self.csdb.fetch_one_row()[0]
        last_total_files = 100
        last_end_time = None
        isc_name = self.index_db.index_server.client_hostname

        lines = [','.join(self.js_fields)]

        for r in range(count):
            row = []
            for field in self.js_fields:

                added_items = random.randint(100, 200)
                deleted_items = random.randint(0, 10)
                modified_items = random.randint(10, 20)
                total_items = added_items + modified_items + deleted_items
                start_time = int(time.time()) - 86400 if last_end_time is None else last_end_time + 10
                end_time = start_time + 25
                job_id = int(last_job_id) + 1
                self.anomaly_job = last_job_id
                insert_anomaly = (r == count-1)

                if field == 'Total Files in Index':
                    value = int(last_total_files) + 50
                    last_total_files = value
                    row.append(value)

                if field == 'Job Id':
                    last_job_id = job_id
                    row.append(job_id)

                if field == 'Total Commands':
                    row.append(total_items)

                if field == 'Added Files':
                    if insert_anomaly:  # Insert anomaly
                        added_items = 9999999999999
                        # self.anomalous_jobs[last_job_id] = 'Added'

                    row.append(added_items)

                if field == 'Deleted Folders':
                    row.append(0)

                if field == 'Deleted Files':
                    if insert_anomaly:  # Insert anomaly
                        deleted_items = 888888888888888
                        # self.anomalous_jobs[last_job_id] = 'Deleted'

                    row.append(deleted_items)

                if field == 'Seconds To Playback':
                    row.append(random.randint(10000, 60000) / 1000000)

                if field == 'Start Time':
                    row.append(start_time)

                if field == 'End Time':
                    last_end_time = end_time
                    row.append(end_time)

                if field == 'Modified Files':
                    if insert_anomaly:  # Insert anomaly
                        modified_items = 777777777777777
                        # self.anomalous_jobs[last_job_id] = 'Modified'

                    row.append(modified_items)

                if field == 'Job Type':
                    row.append(4)

                if field == 'Hostname':
                    row.append(isc_name)

                if field == 'Timestamp':
                    row.append(start_time * 1000)

                if field == 'Status':
                    row.append(0)

                if field == 'Root Size':
                    value = added_items * random.randint(2048, 4096)
                    if insert_anomaly:  # Insert anomaly
                        value = 6 * (1024 ** 4)  # 6TB
                        self.anomalous_jobs[last_job_id] = 'Root Size Change'

                    row.append(value)

                if field in ['Invalid MIME Classification', 'Number of Nodes', 'Backup Size',
                             'DDB Block Count', 'Data Written']:
                    row.append(0)

            row = [str(field) for field in row]
            lines.append(','.join(row))

        return lines
