# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

""""Main file for executing this test case

This testcase runs Indexing processes with valgrind and collects the memory leak related log lines.

TestCase:
    __init__()                  --  Initializes the TestCase class

    setup()                     --  All testcase objects are initializes in this method

    run()                       --  Contains the core testcase logic and it is the one executed

    set_cvods_binary()          --  Replaces the original CVODS binary with the CVODS valgrind script

    reset_cvods_binary()        --  Resets the CVODS binary with the valgrind script

    upload_parser_script()      --  Uploads the parser script to the MA machine

    send_email()                --  Sends the valgrind logs email

    tear_down()                 --  Cleans the data created for Indexing validation

"""
import time

from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine
from AutomationUtils.mailer import Mailer

from Indexing.testcase import IndexingTestcase
from Indexing.helpers import IndexingHelpers


class TestCase(CVTestCase):
    """This testcase runs Indexing processes with valgrind and collects the memory leak related log lines.

        Steps:
            1) Replace CVODS binary with the valgrind script
            2) Run backups (FULL, INC, Synthetic Full) browse, restore
            3) Valgrind logs will be generated for the IndexServer and LogManager
            4) Parse the valgrind logs and collect only lines related to "blocks are definitely lost in loss record"
            5) Send the logs via email.
    """

    def __init__(self):
        """Initializes test case class object"""

        super(TestCase, self).__init__()
        self.name = 'Indexing - Valgrind'

        self.tcinputs = {
            'TestData': None,
            'StoragePolicy': None,
            'MAUserName': None,
            'MAPassword': None
            # 'OutputDir': None - The directory where the output logs will be staged
        }

        self.cl_machine = None
        self.idx_tc = None
        self.idx_help = None

        self.media_agent = None
        self.ma_machine = None
        self.cvods_orig_path = None
        self.cvods_replaced = False
        self.valgrind_dir = None

    def setup(self):
        """All testcase objects are initialized in this method"""

        self.cl_machine = Machine(self.client, self.commcell)
        self.valgrind_dir = self.tcinputs.get('OutputDir', '/valgrind')

        storage_policy = self.commcell.storage_policies.get(self.tcinputs.get('StoragePolicy'))
        sp_copy = storage_policy.get_primary_copy()

        self.media_agent = self.commcell.clients.get(sp_copy.media_agent)
        if 'windows' in self.media_agent.os_info.lower():
            raise Exception('Please use a storage policy with Linux MA as default')

        self.log.info('***** Using MediaAgent [%s] of type [%s] *****', self.media_agent.name, self.media_agent.os_info)
        self.ma_machine = Machine(
            self.media_agent.client_hostname,
            username=self.tcinputs.get('MAUserName'),
            password=self.tcinputs.get('MAPassword')
        )

        self.idx_tc = IndexingTestcase(self)
        self.idx_help = IndexingHelpers(self.commcell)

        self.backupset = self.idx_tc.create_backupset('valgrind_auto', for_validation=True)

        self.subclient = self.idx_tc.create_subclient(
            name='sc1_valgrind',
            backupset_obj=self.backupset,
            storage_policy=self.tcinputs.get('StoragePolicy')
        )

        self.idx_tc.new_testdata(self.subclient.content)

        self.log.info('***** Running dummy backup to initialize backupset *****')
        self.idx_tc.run_backup(self.subclient, 'Full', verify_backup=False)

        indexing_level = self.idx_help.get_agent_indexing_level(self.agent)
        entity_obj = self.subclient if indexing_level == 'subclient' else self.backupset
        entity_obj.refresh()
        entity_obj.index_server = self.media_agent

        self.log.info('IndexServer set at [%s] level is [%s]', indexing_level, entity_obj.index_server)

        self.upload_parser_script()

    def run(self):
        """Contains the core testcase logic"""

        try:

            self.log.info('***** Stopping MA services *****')
            self.media_agent.stop_service()

            self.log.info('***** Replacing CVODS binary *****')
            self.set_cvods_binary()

            self.log.info('***** Starting MA services *****')
            self.ma_machine.start_all_cv_services()
            time.sleep(60)

            self.idx_tc.edit_testdata(self.subclient.content)
            self.idx_tc.run_backup(self.subclient, 'Incremental', verify_backup=True)

            self.idx_tc.run_backup(self.subclient, 'Synthetic_full', verify_backup=True)

            self.idx_tc.edit_testdata(self.subclient.content)
            self.idx_tc.run_backup(self.subclient, 'Incremental', verify_backup=True)

            self.log.info('***** Stopping MA services to flush valgrind process logs to disk *****')
            self.media_agent.stop_service()
            time.sleep(60)

            logs_dict = dict()
            logs_dict['IndexServer'] = self.parse_valgrind_log('IndexServer.txt')
            logs_dict['LogManager'] = self.parse_valgrind_log('LogManager.txt')
            logs_dict['RemoteFileCacheServer'] = self.parse_valgrind_log('RemoteFileCacheServer.txt')
            logs_dict['CvStatAnalysis'] = self.parse_valgrind_log('CvStatAnalysis.txt')

            self.send_email(logs_dict)

        except Exception as exp:
            self.log.error('Failed to execute test case with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED

        finally:
            try:
                self.log.info('Stopping MA services')
                self.ma_machine.stop_all_cv_services()
            except Exception as e:
                self.log.error(e)

            attempts = 1
            while self.cvods_replaced and attempts <= 3:
                self.reset_cvods_binary()
                attempts += 1

            self.log.info('Starting MA services')
            self.ma_machine.start_all_cv_services()

    def set_cvods_binary(self):
        """Replaces the original CVODS binary with the CVODS valgrind script"""

        base_path = self.ma_machine.join_path(self.media_agent.install_directory, 'Base')
        self.cvods_orig_path = self.ma_machine.join_path(base_path, 'CVODS')

        backup_cmd = f'cp "{self.cvods_orig_path}" "{self.cvods_orig_path}.bkp"'
        self.log.info('Making a copy of CVODS [%s]', backup_cmd)
        self.ma_machine.execute_command(backup_cmd)

        self.log.info('Renaming CVODS binary')
        self.ma_machine.rename_file_or_folder(self.cvods_orig_path, self.cvods_orig_path + '.orig')

        cvods_script = f"""#!/bin/bash

appname=dummy
rawargs=\$@

while [[ \$# -gt 0 ]]; do
  case \$1 in
    -appname)
        appname="\$2"
        shift # past argument
        shift # past value
        ;;
    *)
        shift
        ;;
  esac
done

set -- "\$rawargs"  # Set the argument again

if echo "\$@" | grep -q 'LogManager\|IndexServer\|RemoteFileCacheServer\|CvStatAnalysis'
then
        cd {base_path} && valgrind --vgdb=no --leak-check=full --keep-debuginfo=yes --show-leak-kinds=all --log-file="{self.valgrind_dir}/\$appname.txt" ./CVODS.orig \$@
else
        cd {base_path} && ./CVODS.orig \$@
fi
        """

        self.ma_machine.create_file(self.cvods_orig_path, cvods_script)
        self.ma_machine.change_file_permissions(self.cvods_orig_path, '777')
        self.cvods_replaced = True

    def reset_cvods_binary(self):
        """Resets the CVODS binary with the valgrind script"""

        try:
            if not self.ma_machine or not self.cvods_replaced:
                self.log.info('CVODS binary is not replaced at all')
                return

            self.log.info('***** Replacing CVODS script with original binary *****')

            self.ma_machine.delete_file(self.cvods_orig_path)
            self.ma_machine.rename_file_or_folder(self.cvods_orig_path + '.orig', self.cvods_orig_path)
            self.log.info('CVODS binary has been renamed to original')

            orig_size = self.ma_machine.get_file_size(self.cvods_orig_path)
            bkp_size = self.ma_machine.get_file_size(self.cvods_orig_path + '.bkp')
            self.log.info('Checking if CVODS binary is restored correctly. Orig size [%s] Backup size [%s]',
                          orig_size, bkp_size)

            if orig_size == bkp_size:
                self.log.info('CVODS binary is restored without any issue')
            else:
                restore_cmd = f'cp "{self.cvods_orig_path}.bkp" "{self.cvods_orig_path}"'
                self.log.error('CVODS binary is not restored. Restoring with the backup. [%s]', restore_cmd)
                self.ma_machine.execute_command(restore_cmd)
                self.log.info('CVODS binary restore complete')

            # Reset the flag that CVODS binary is replaced with the script
            self.cvods_replaced = False

        except Exception as e:
            self.log.error(e)

    def upload_parser_script(self):
        """Uploads the parser script to the MA machine"""

        parser_script = """#!/bin/bash

logfile=\$1
outfile=\$2
found=0

if [[ -z '\$logfile' ]]
then
    echo 'Log file not provided'
    exit 1
else
    if [[ ! -f \$logfile ]]
    then
        echo 'Log file \$logfile does not exist'
        exit 1
    fi
fi

if [[ -z \$outfile ]]
then
    outfile='output.log'
fi

> \$outfile

while read -r line; do
    if [[ \$line == *'blocks are definitely lost in loss record'* ]]
    then
        found=1
        echo \$line >> \$outfile
        continue
    fi

    if [ \$found -eq 1 ]
    then
    
        if [[ \$line == *'libctreedbsunifrmat'* ]]
        then
            found=0
            echo '----------------' >> \$outfile
            echo ' ' >> \$outfile
            continue
        fi
    
        echo \$line >> \$outfile
        if [[ \$line != *'0x'* ]]
        then
            found=0
            echo '----------------' >> \$outfile
            echo ' ' >> \$outfile
        fi
    fi

done <\$logfile
"""

        try:
            self.log.info('Creating Valgrind folder [%s]', self.valgrind_dir)
            self.ma_machine.remove_directory(self.valgrind_dir)
            self.ma_machine.create_directory(self.valgrind_dir)
        except Exception as e:
            self.log.error(e)

        parser_path = self.ma_machine.join_path(self.valgrind_dir, 'parser.sh')
        self.ma_machine.create_file(parser_path, parser_script)

        self.ma_machine.change_file_permissions(parser_path, '777')

    def parse_valgrind_log(self, log_name):
        """Runs the parser script to generate the filtered log file from the valgrind logs

            Args:
                log_name        (string)    --      The name of the valgrind log file. IndexServer.txt, LogManager.txt

            Returns:
                (str)   --  The log file contents

        """

        parser_path = self.ma_machine.join_path(self.valgrind_dir, 'parser.sh')
        log_path = self.ma_machine.join_path(self.valgrind_dir, log_name)
        output_path = self.ma_machine.join_path(self.valgrind_dir, 'output.log')

        self.log.info('***** Parsing valgrind logs [%s] *****', log_path)

        try:
            items_in_dir = self.ma_machine.get_items_list(self.valgrind_dir)
            self.log.info(items_in_dir)
        except Exception as e:
            self.log.error(e)

        if not self.ma_machine.check_file_exists(log_path):
            raise Exception(f'Valgrind logs [{log_path}] not created')

        self.log.info('Deleting already existing output log')
        self.ma_machine.delete_file(output_path)

        command = f'{parser_path} {log_path} {output_path}'
        self.log.info('Parsing valgrind logs [%s]', command)
        self.ma_machine.execute_command(command)
        time.sleep(60)

        self.log.info('Reading output log [%s]', output_path)
        self.log.info('Size of output log [%s]', self.ma_machine.get_file_size(output_path))
        output = self.ma_machine.read_file(output_path)

        return output

    def send_email(self, logs_dict):
        """Sends the valgrind logs email

            Args:
                logs_dict       (dict)  --      The dictionary of log name and its logs

        """

        html = """<style>pre{background: #f7f7f7; padding: 10px !important;}</style>"""
        html += '<h3>Valgrind logs for <u>definitely lost blocks</u></h3>'

        html += '<ul>'
        for log_name in logs_dict.keys():
            html += f'<li><a href="#{log_name}">{log_name}</a></li>'
        html += '</ul>'

        for log_name, logs in logs_dict.items():
            html += f'<h3><a id="{log_name}" name="{log_name}"></a>{log_name}</h3>'
            html += f'<pre>{logs}</pre>'
            html += '<br/>'

        mailer = Mailer(mailing_inputs={}, commcell_object=self.commcell)
        mailer.mail(f'[{self.commcell.commserv_version}] - Valgrind Logs', html)
