# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

This testcase does indexing operations like playback, browse, restore, synthetic full and
compaction and prepares a report on the time taken between two service packs

TestCase:
    __init__()                  --  Initializes the TestCase class

    setup()                     --  All testcase objects are initializes in this method

    run()                       --  Contains the core testcase logic and it is the one executed

    test_playback()             --  Tests play

    tear_down()                 --  Cleans the data created for Indexing validation

"""

import traceback
import time
import re

from datetime import datetime

from AutomationUtils import commonutils
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.database_helper import MSSQL

from Indexing.database import index_db
from Indexing.helpers import IndexingHelpers

from cvpysdk.exception import SDKException


class TestCase(CVTestCase):
    """This testcase does indexing operations like playback, browse, restore, synthetic full and
    compaction and prepares a report on the time taken between two service packs"""

    def __init__(self):
        """Initializes test case class object"""

        super(TestCase, self).__init__()
        self.name = 'Indexing - Performance comparison report'

        self.tcinputs = {
            'Mode': None,  # Example: test or report
            'CSDBUsername': None,
            'CSDBPassword': None,
            'HistoryDBServer': None,
            'HistoryDBUsername': None,
            'HistoryDBPassword': None,
            'RestorePath': None,
            'JobsInfo': None,  # Example: [["Job 1", "Description 1"], ["Job 2", "Description 2"]]
            'ValidJobsCount': None,  # Number of jobs to pick for test
            'LowerSP': None,  # Example: 30. Used only during report
            'HigherSP': None  # Example: 32. Used only during report
            # Optional 'Tests': None # Example: "playback,browse,restore,compaction,synthetic_full"
            # Optional 'WarningThreshold': None # Default: 10
            # Required - Client, Agent, Backupset and Subclient Name inputs
        }

        self.storage_policy = None
        self.cs_name = None
        self.cs_hostname = None
        self.cs_db = None
        self.history_db = None

        self.cl_machine = None
        self.cl_delim = None
        self.isc = None
        self.isc_sp = None
        self.idx_db = None

        self.tests = ['playback', 'browse', 'restore', 'synthetic_full', 'compaction']
        self.current_stats = []
        self.attempt = None
        self.low_sp = None
        self.high_sp = None
        self.oldest_cycle_timestamp = None

        self.job_types = {
            '2': 'Full',
            '4': 'Incremental',
            '8': 'Synthetic Full',
            '16': 'Differential'
        }

        self.test_types = {
            'playback': 'Playback time',
            'browse': 'Find time',
            'restore': 'Restore - Restore vector time',
            'synthetic_full': 'Synthetic full - Restore vector time',
        }

        self.tests_name = {
            'million_items': ['Playback of 1 million items', ''],
            'browse_latest_filter': ['Latest cycle find with filter', ''],
            'browse_oldest_filter': ['Oldest cycle find with filter', ''],
            'restore_latest': ['Latest cycle', ''],
            'restore_oldest': ['Oldest cycle', ''],
            'sfull_rv_time': ['Restore vector time', '']
        }

    def setup(self):
        """All testcase objects are initializes in this method"""

        perf_tests = self.tcinputs.get('Tests', None)
        if perf_tests is not None:
            self.tests = perf_tests.split(',')
            self.tests = [test.strip().lower() for test in self.tests]

        self.cs_name = self.commcell.commserv_name
        self.cs_hostname = self.commcell.commserv_hostname

        db_server_name = self.cs_hostname + '\\Commvault'

        self.cs_db = MSSQL(
            db_server_name, self.tcinputs.get('CSDBUsername'), self.tcinputs.get('CSDBPassword'), 'CommServ'
        )
        self.log.info('Connected to CS DB %s', db_server_name)

        history_db_server = self.tcinputs.get('HistoryDBServer')
        history_db_username = self.tcinputs.get('HistoryDBUsername')
        history_db_password = self.tcinputs.get('HistoryDBPassword')

        self.history_db = MSSQL(
            history_db_server, history_db_username, history_db_password, 'HistoryDB'
        )
        self.log.info('Connected to history DB')

        self.create_stats_table()

        self.idx_help = IndexingHelpers(self.commcell)
        indexing_level = self.idx_help.get_agent_indexing_level(self.agent)
        entity_obj = self.subclient if indexing_level == 'subclient' else self.backupset

        self.log.info('Getting Index DB object')
        self.idx_db = index_db.get(entity_obj)

        self.isc = self.idx_db.index_server
        self.isc_machine = self.idx_db.isc_machine
        self.isc_delim = self.isc_machine.os_sep
        self.isc_sp = self.isc.service_pack

        self.log.info('DB Path: [{0}]'.format(self.idx_db.db_path))

        self.attempt = self.get_last_attempt(self.isc_sp) + 1
        self.oldest_cycle_timestamp = self.get_oldest_cycle_time()
        self.mode = self.tcinputs.get('Mode')

    def run(self):
        """Contains the core testcase logic and it is the one executed"""

        try:
            self.log.info('Running following performance tests {0}'.format(self.tests))
            self.log.info('Current attempt ID: {0}'.format(self.attempt))
            self.log.info('Current Index server: {0}'.format(self.isc.client_name))
            self.log.info('Index Server service pack: {0}'.format(self.isc_sp))

            self.log.info('*************** [%s] mode ***************', self.mode)

            if self.mode == 'report':
                self.log.info('This run is to send report only')
                self.send_email()
                return

            for test in self.tests:
                test = test.lower()
                method_name = 'test_' + test

                self.log.info('Running test: ' + method_name)
                self.log.info('Killing CVODS processes before test')
                self.isc_machine.kill_process('CVODS')

                if hasattr(self, method_name):
                    try:
                        getattr(self, method_name)()
                    except Exception as e:
                        self.log.error('Got exception while running test [%s]', e)
                        self.log.error(str(traceback.format_exc()))
                else:
                    self.log.error('Invalid test name')

        except Exception as exp:
            self.log.error('Test case failed with error: ' + str(exp))
            self.result_string = str(exp)
            self.status = constants.FAILED
            self.log.error(str(traceback.format_exc()))

    def test_playback(self):
        """Runs the playback test and collects the playback time taken"""

        self.log.info('***** Running playback test *****')

        self.log.info('Aging checkpoints')
        self.age_checkpoints(self.idx_db.backupset_guid)

        self.log.info('Deleting DB')
        self.idx_db.delete_db()
        time.sleep(30)

        self.log.info('***** Initiating playback *****')
        while not self.idx_db.is_upto_date:
            self.log.info('DB is not upto date')
            time.sleep(60)

        self.log.info('***** DB is upto date *****')

        jbs_file = self.idx_db.db_path + self.isc_delim + 'JobStats.csv'
        self.log.info('Reading job stats file: [{0}]'.format(jbs_file))

        lines = self.isc_machine.read_csv_file(jbs_file)
        total_commands = 0
        total_time = 0
        jobs_checked = 1

        for line in lines:
            job_type = self.job_types[line['Job Type']]
            job_id = line['Job Id']
            deleted_items = int(line['Deleted Folders']) + int(line['Deleted Files'])
            added_items = line['Added Files'] if line['Job Type'] != '8' else line['Total Commands']
            deleted_items_fmt = self.format_number(deleted_items)
            added_items_fmt = self.format_number(added_items)
            comments = f'Added {added_items_fmt} Deleted {deleted_items_fmt} Job {job_type} ID {job_id}'

            total_commands += int(line['Total Commands'])
            total_time += float(line['Seconds To Playback'])

            self.update_stat('playback', f'job_{jobs_checked}', line['Seconds To Playback'], comments)

            if jobs_checked == int(self.tcinputs.get('ValidJobsCount')):
                self.log.info('Exiting as [%s] jobs are measured', jobs_checked)
                break

            jobs_checked += 1

        if total_commands:
            self.log.info('Total commands in all jobs [%s]', total_commands)
            self.log.info('Total time taken [%s]', total_time)
            pt_1m_items = (total_time * 1000000) / total_commands
            self.update_stat('playback', 'million_items', str(pt_1m_items), '')

        self.push_stats_database()
        self.log.info('***** Playback tests completed *****')

    def test_restore(self):
        """Runs the restore test and collects the restore vector creation time taken"""

        self.log.info('***** Running restore vector tests *****')
        self.log.info('Starting latest cycle restore job')

        rst_path = self.tcinputs.get('RestorePath')
        rst_job = self.subclient.restore_out_of_place(
            self.cs_name, rst_path, ['\\'],
            fs_options={
                'no_image': True
            }
        )
        rst_job_id = rst_job.job_id
        time_taken = self.get_restore_vector_time(rst_job_id, 'restore')

        self.update_stat('restore', 'restore_latest', time_taken, '')
        self.push_stats_database()

        try:
            self.log.info('Killing restore job')
            rst_job.kill()
        except Exception as e:
            self.log.error('Failed to kill restore job. Ignoring [%s]', e)
            pass

        self.log.info('Starting oldest cycle restore job')

        rst_job = self.subclient.restore_out_of_place(
            self.cs_name, rst_path, ['\\'],
            to_time=commonutils.convert_to_formatted_time(self.oldest_cycle_timestamp),
            fs_options={
                'no_image': True
            }
        )

        rst_job_id = rst_job.job_id
        time_taken = self.get_restore_vector_time(rst_job_id, 'restore')

        self.update_stat('restore', 'restore_oldest', time_taken, '')
        self.push_stats_database()

        try:
            self.log.info('Killing restore job')
            rst_job.kill()
        except Exception as e:
            self.log.error('Failed to kill restore job. Ignoring [%s]', e)
            pass

        self.log.info('***** Restore tests completed *****')

    def test_synthetic_full(self):
        """Runs the synthetic full job test and collects the time taken for RV creation"""

        self.log.info('***** Running synthetic full job test *****')

        self.log.info('Starting synthetic full job')

        sfull_job = self.subclient.backup('Synthetic_full')
        sfull_job_id = sfull_job.job_id

        time_taken = self.get_restore_vector_time(sfull_job_id, 'synthetic_full')

        self.log.info('Time taken for SFULL restore vector creation: ' + time_taken)
        self.update_stat('synthetic_full', 'sfull_rv_time', time_taken, '')
        self.push_stats_database()

        self.log.info('***** Synthetic full job tests completed *****')

        try:
            self.log.info('Killing synthetic full job')
            sfull_job.kill()
        except Exception as e:
            self.log.error('Failed to kill synthetic full job. Ignoring [%s]', e)
            pass

    def test_compaction(self):
        """Runs the compaction test and collects the compaction  time taken"""

        self.log.info('***** Running Compaction test *****')
        self.log.info('Running index checkpoint job')
        self.idx_db.checkpoint_db(by_all_index_backup_clients=False)

        self.log.info('Running compaction operation')
        compaction_job = self.idx_db.compact_db()

        if not compaction_job:
            self.log.error('Failed to compact the DB. Exiting test')
            return

        time.sleep(10)
        self.log.info('Getting compaction time from IndexServer.log')

        log_lines = self.read_log('IndexServer.log', ['secs to compact DB', self.idx_db.db_guid])

        self.log.info(log_lines)

        if not log_lines:
            self.log.info('Cannot get compaction time. Exiting test')
            return

        self.log.info('Got compaction time')
        line = log_lines[-1]
        matches = re.findall('\[([0-9.]+)\]', line)
        time_taken = matches[0]

        self.log.info('Time taken for compaction operation: ' + time_taken)
        self.update_stat('compaction', 'compaction', time_taken, '')
        self.push_stats_database()

        self.log.info('***** Compaction tests completed *****')

    def test_browse(self):
        """Runs the find test and collects the find time taken"""

        self.log.info('***** Running browse test *****')

        start_time = time.time()
        attempts = 1

        while attempts <= 5:
            self.log.info('Doing latest cycle filtered find operation. Attempt [{0}/5]'.format(attempts))
            try:
                self.backupset.find({
                    'filters': [('FileName', '*a*')],
                    'page_size': 1000
                })
                break
            except SDKException as e:
                self.log.error('Browse request timed out. Error [{0}]'.format(e))
                attempts += 1
                time.sleep(10)
                continue

        stop_time = time.time()
        diff = self.limit_decimals(stop_time - start_time)

        self.log.info('Time taken for latest cycle filtered find operation: [%s]', diff)
        self.update_stat('browse', 'browse_latest_filter', str(diff), '')

        self.log.info('Doing oldest cycle filtered find operation')

        start_time = time.time()
        self.backupset.find({
            'filters': [('FileName', '*a*')],
            'page_size': 1000,
            'to_time': self.oldest_cycle_timestamp
        })
        stop_time = time.time()
        diff = self.limit_decimals(stop_time - start_time)

        self.log.info('Time taken for oldest filtered find operation: [%s]', diff)
        self.update_stat('browse', 'browse_oldest_filter', str(diff), '')

        self.push_stats_database()

        self.log.info('***** Browse tests completed *****')

    def create_stats_table(self):
        """Creates the two tables required to store the performance statistics"""

        resp = self.history_db.execute("SELECT * FROM INFORMATION_SCHEMA.TABLES "
                                       "WHERE TABLE_NAME = 'IndexingPerfStats'")

        if len(resp.rows) == 0:
            self.history_db.execute('''
                CREATE TABLE [dbo].[IndexingPerfStats](
                    [id] [bigint] IDENTITY(1,1) NOT NULL,
                    [attempt] [bigint] NOT NULL,
                    [service_pack] [varchar](max) NULL,
                    [test] [varchar](max) NULL,
                    [name] [varchar](max) NULL,
                    [value] [float] NULL,
                    [comments] [varchar](max) NULL
                )
            ''')

            self.log.info('Indexing performance stats table created successfully')
        else:
            self.log.info('Indexing performance stats table already exists')

    def push_stats_database(self):
        """Pushes the collected data to the DB"""

        self.log.info('Pushing stats to database')
        query = "insert into IndexingPerfStats (attempt, service_pack, test, name, value, comments) values "

        self.log.info(self.current_stats)

        for stat in self.current_stats:
            values = "','".join(
                [str(self.attempt), self.isc_sp, stat['test'], stat['name'], stat['value'], stat['comments']]
            )
            query += "('" + values + "'),"

        final_query = query[:-1]
        self.log.info('Inserting records: ' + final_query)
        self.history_db.execute(final_query)

        self.current_stats = []

    def update_stat(self, test, name, value, comments):
        """Records the collected stat in memory"""

        stats = {
            'test': test,
            'name': name,
            'value': value,
            'comments': comments
        }

        self.log.info('Adding stats: %s', stats)
        self.current_stats.append(stats)

    def get_last_attempt(self, service_pack):
        """Gets the last attempt for the current service pack of the current run"""

        self.log.info('Getting last performance test attempt ID for SP: [%s]', service_pack)
        resp = self.history_db.execute("select max(attempt) as 'attempt' from IndexingPerfStats "
                                       "where service_pack = '{0}'".format(self.isc_sp))
        attempt = resp.rows[0][0]

        if attempt is None:
            return 1
        else:
            return int(attempt)

    def get_log_file_path(self, name):
        """Gets the log file path on IndexServer MA for the given log name"""

        return self.isc_machine.join_path(self.isc.log_directory, name)

    def get_oldest_cycle_time(self):
        """Gets the oldest cycle's job end time"""

        query = ("select top 1 servEndDate from jmbkpstats where appid = {0}"
                 " and fullCycleNum = (select fullcyclenum from jmbkpstats where "
                 "jobid = (select min(jobid) from archfile where appid = {0} and "
                 "filetype = 2)) order by jobid asc".format(self.subclient.subclient_id))

        resp = self.cs_db.execute(query)
        self.log.info(query)
        self.log.info(resp.rows)
        end_time = int(resp.rows[0][0])
        self.log.info('Oldest cycle end time is [%s]', end_time)
        return end_time

    def read_log(self, name, words):
        """Reads the log files for the given words"""

        log_file_path = self.get_log_file_path(name)
        self.log.info('Log file path [%s]', log_file_path)

        lines = self.isc_machine.find_lines_in_file(log_file_path, words)

        if not isinstance(lines, list):  # When result is one line, it is a string instead of list.
            lines = [lines]

        clean_lines = []

        for line in lines:
            if not line or '[]' in line:
                continue
            clean_lines.append(line)

        return clean_lines

    def age_checkpoints(self, backupset_guid):
        """Ages all the checkpoints of the DB"""

        query = "delete from archfile where name like '%{0}%'".format(backupset_guid)
        self.log.info('Age checkpoint query: [{0}]'.format(query))
        self.cs_db.execute(query)

    @staticmethod
    def limit_decimals(value, digits=3):
        """Returns a number with restricted numbers after decimal point"""

        format_specifier = '{0:.' + str(digits) + 'f}'
        return format_specifier.format(value)

    @staticmethod
    def format_number(num, units=None, divide_by=1000):
        """Formats the given number with units"""

        if units is None:
            units = ['', 'K', 'M', 'T']

        try:
            num = int(num)
        except ValueError:
            num = 0

        unit = ''
        for unit in units:
            if num < divide_by:
                return '{0}{1}'.format(int(num), unit)

            num /= divide_by

        return '{0}{1}'.format(int(num), unit)

    def get_time_from_logs(self, words, log_file='Browse.log'):
        """Gets the time value for the log line"""

        while True:
            self.log.info('Looking for words {0}'.format(words))
            log_lines = self.read_log(log_file, words)
            self.log.info(log_lines)

            if log_lines:
                break
            else:
                self.log.info('Words not found. Trying again.')
                time.sleep(60)

        line = log_lines[-1]
        if isinstance(line, list):
            line = ' '.join(line)

        matches = re.findall('[0-9]+\/[0-9]+ [0-9]+\:[0-9]+\:[0-9]+', line)
        time_raw = matches[0]
        time_format = '%m/%d %H:%M:%S'

        return datetime.strptime(time_raw, time_format)

    def get_restore_vector_time(self, job_id, job_type):
        """Gets the time taken to create restore vector"""

        time.sleep(10)
        self.log.info('Job ID for restore vector creation [{0}]'.format(job_id))
        job_id_search = ' {0} '.format(job_id)

        if job_type == 'restore':
            end_text = 'Time taken to create restore'
        else:
            end_text = 'Successfully created restore vector at'

        self.log.info('Checking if restore vector creation STARTED in Browse.log')
        start_time = self.get_time_from_logs([job_id_search, 'Received Browse Request From Client'])
        self.log.info('Got time [%s]', start_time)

        self.log.info('Checking if restore vector creation ENDED in Browse.log')
        end_time = self.get_time_from_logs([job_id_search, end_text])
        self.log.info('Got time [%s]', end_time)

        time_diff = end_time-start_time
        return str(time_diff.seconds)

    def get_test_start_time(self, service_pack):
        """Gets the start time of the test"""

        resp = self.history_db.execute("""select test, MIN(time) as 'start_time' from 
        indexingprocessstats where service_pack = '{0}' and name = 'IndexServer' and 
        attempt = (select max(attempt) from indexingprocessstats where service_pack = '{0}')
        group by test""".format(service_pack))

        start_times = []
        test_names = []

        for row in resp.rows:
            test_name = row['test']
            start_time = row['start_time']

            start_times.append(start_time)
            test_names.append(test_name)

        return start_times, test_names

    def get_compare_results(self):
        """Runs query to compares the performance stat results"""

        resp = self.history_db.execute(
            f"select max(attempt) from IndexingPerfStats where service_pack = '{self.low_sp}'"
        )
        low_sp_attempt = str(resp.rows[0][0])
        self.log.info(f'Low SP\'s latest attempt [%s]', low_sp_attempt)

        resp = self.history_db.execute(
            f"select max(attempt) from IndexingPerfStats where service_pack = '{self.high_sp}'"
        )
        high_sp_attempt = str(resp.rows[0][0])
        self.log.info(f'High SP\'s latest attempt [%s]', high_sp_attempt)

        resp = self.history_db.execute(f"""
 select 

  ips1.name,
  ROUND(ips1.value, 2),
  ROUND(ips2.value, 2),
  ROUND(((ips2.value - ips1.value)/ips1.value)*100,2),
  ips1.test

  from IndexingPerfStats ips1
 join IndexingPerfStats ips2 on ips1.name = ips2.name
 where ips1.service_pack = '{self.low_sp}' and ips2.service_pack = '{self.high_sp}'
 and ips1.attempt = '{low_sp_attempt}' and ips2.attempt = '{high_sp_attempt}'
        """)

        return resp.rows

    def build_table_perf_stats(self):
        """Generates HTML for the performance stats table"""

        html = f"""<table border="1"><tr>
        <th>Test</th>
        <th>SP{self.low_sp}</th>
        <th>SP{self.high_sp}</th>
        <th>% Change</th>
        <th>Comments</th>
        </tr>"""

        rows = self.get_compare_results()
        jobs_info = self.tcinputs.get('JobsInfo')
        warning_threshold = int(self.tcinputs.get('WarningThreshold', 10))
        last_test_type = ''

        jobs_i = 1
        for job in jobs_info:
            self.tests_name[f'job_{jobs_i}'] = job
            jobs_i += 1

        for row in rows:
            test_id = row[0]
            low_sp_value = row[1]
            high_sp_value = row[2]
            change = round(row[3], 2)
            test_type = row[4]

            state_table = {
                0: ['darkGreen', '&#9660;'],  # decreased
                1: ['#a96500', '&#9650;'],  # increased
                2: ['red', '&#9650;'],  # increased
                3: ['darkGreen', '&#10004;'],  # tick
            }

            state = 0
            if abs(change) <= 5:
                state = 3
            elif change > 0:
                state = 2 if change > warning_threshold else 1

            hsp_color = state_table[state][0]
            icon = f'<span style="color:{hsp_color}">{state_table[state][1]}</span>'

            test_name = test_id
            comments = ''
            if test_id in self.tests_name:
                test_name = self.tests_name[test_id][0]
                comments = self.tests_name[test_id][1]

            if last_test_type != test_type:
                test = test_type
                if test_type in self.test_types:
                    test = self.test_types[test_type]
                html += f'<tr><th colspan="5" style="background-color: #62a0d0; padding: 5px 10px">{test}</th></tr>'

            html += '<tr>'
            html += f'<td>{test_name}</td>'
            html += f'<td>{low_sp_value}s</td>'
            html += f'<td>{high_sp_value}s</td>'
            html += f'<td style="color:{hsp_color};">{icon} {change}%</td>'
            html += f'<td>{comments}</td>'
            html += '</tr>'

            last_test_type = test_type

        html += '</table>'

        return html

    def build_email(self):
        """Generates the HTML for the email report"""

        if self.low_sp is None or self.high_sp is None:
            self.log.info('Stats not available for one of the SP. Not building report')
            return ''

        html = """<style>table{border-collapse: collapse;} th{  
        background: #2c5e84; color: #fff; } th, td{ padding: 10px; } </style>"""

        html += '<h2>SP{0} vs SP{1} Performance Stats</h2>'.format(self.low_sp, self.high_sp)
        html += self.build_table_perf_stats()

        html += '<h3>Setup</h3>'
        html += 'MA: {0}'.format(self.isc.client_hostname)

        return html

    def send_email(self):
        """Sends the report email"""

        self.log.info('Building report and sending email')

        self.low_sp = str(self.tcinputs.get('LowerSP'))
        self.high_sp = str(self.tcinputs.get('HigherSP'))

        self.log.info('Comparing service packs [%s] and [%s]', self.low_sp, self.high_sp)

        html = self.build_email()

        sp_text = ''
        if self.low_sp is not None and self.high_sp is not None:
            sp_text = ' - SP{0} vs SP{1}'.format(self.low_sp, self.high_sp)

        from AutomationUtils.mailer import Mailer
        mailer = Mailer(mailing_inputs={}, commcell_object=self.commcell)
        mailer.mail('Indexing performance comparison' + sp_text, html)

    def tear_down(self):
        """Cleanup operation"""
        self.name = self.name + ' - SP' + self.isc_sp

        self.isc_machine.disconnect()
