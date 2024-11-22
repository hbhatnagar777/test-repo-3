# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Main module which contains

IdxCLI: The main class to use idxCLI tool to interact with the Index DB, logs and other features.

IdxCLI:

    __init__()                      --  Initializes the idxCLI class

    run_idx_cli()                   --  Runs IdxCLI with input file passed

    do_db_compaction()              --  Performs the compaction operation

    do_db_consistency_check()       --  Performs DB consistency check

    do_tools_shutdown_index_server()    --  Shuts down the IndexServer process gracefully

    do_table_export_all_tables()    --  Performs DB consistency check

    do_tools_calculate_metrics()    --  Calculate Index Server Load Metrics

    do_rfc_upload()                 --  Upload file to Remote File Cache

    do_rfc_download()               --  Download file from Remote File Cache

    do_anomaly_check()              --  Starts the anomaly detection operation

    do_delete_index_db()            --  Deletes the index DB

"""

from AutomationUtils import commonutils
from AutomationUtils import logger
from AutomationUtils.machine import Machine


class IdxCLI:
    """The main class to use idxCLI tool to interact with the Index DB, logs and other features."""

    def __init__(self, index_server_client):
        """Initializes the idxCLI class

            Args:
                index_server_client     (obj)     --    The CvPySDK client object of the index server client

        """

        self.log = logger.get_log()

        self.index_server_client = index_server_client
        self.index_server_machine = Machine(self.index_server_client)
        self.index_server_delim = self.index_server_machine.os_sep
        self.index_server_instance = self.index_server_client.instance
        self.index_server_install_dir = self.index_server_client.install_directory

        self.index_server_base_dir = self.index_server_delim.join([
            self.index_server_install_dir, 'Base'
        ])

        self.index_server_temp_dir = self.index_server_delim.join([
            self.index_server_base_dir, 'Temp'
        ])

        self._create_token_file()

    def _create_token_file(self):
        """Creates the token file to use idxcli tool"""

        if self.index_server_machine.os_info == 'WINDOWS':
            working_dir = self.index_server_base_dir
        else:
            path = self.index_server_machine.execute_command('pwd')
            working_dir = path.formatted_output.strip()

        token_file = self.index_server_delim.join([
            working_dir, 'idxtoken.txt'
        ])

        self.log.info('Creating token file for login [%s]', token_file)
        self.index_server_machine.create_file(token_file, '729d2c3e')

    def _create_input_file(self, command):
        """Creates the input file with the command to execute

            Args:
                command     (str)   --  The command to be added to the input file

            Returns:
                str     --      The file path of the created input file

        """

        random_string = commonutils.get_random_string(length=4)
        name = f'input_{random_string}.txt'
        file_path = self.index_server_delim.join([
            self.index_server_temp_dir, name
        ])

        self.index_server_machine.create_file(file_path, command)
        return file_path

    def run_idx_cli(self, command):
        """Runs IdxCLI with input file passed

            Args:
                command     (str)       --      The idxcli command for the operation to be performed

            Returns:
                str - The contents of the output file after execution.

        """

        input_file = self._create_input_file(command)
        output_file = f'{input_file}.out.txt'

        if self.index_server_machine.os_info == 'WINDOWS':

            command = (
                'start-process '
                '-filepath "idxcli.exe" '
                '-wait '
                f'-workingDirectory "{self.index_server_base_dir}" '
                f'-ArgumentList "-vm {self.index_server_instance} -in `"{input_file}`" "'
            )

        else:

            command = '{0}/IdxCLI -vm {1} -in {2}'.format(
                self.index_server_base_dir, self.index_server_instance, input_file
            )

        self.log.info('Executing IdxCLI [%s]', command)
        self.index_server_machine.execute_command(command)

        self.log.info('Execution completed. Removing input file')
        self.index_server_machine.delete_file(input_file)

        if self.index_server_machine.check_file_exists(output_file):
            out = self.index_server_machine.read_file(output_file)
            self.index_server_machine.delete_file(output_file)
        else:
            self.log.info('Output file does not exist. Possibly command did not run.')
            out = ''

        return out

    def do_db_compaction(self, db_path):
        """Performs the compaction operation

            Args:
                db_path     (str)       --      The path of the DB to compact

            Returns:
                bool    --      True/False on successful completion of the operation

        """

        command = 'MAINMENU_DB_MENU "{0}" DBMENU_COMPACT'.format(db_path)
        out = self.run_idx_cli(command)

        return 'SUCCESS' in out

    def do_db_consistency_check(self, db_path):
        """Performs DB consistency check

            Args:
                db_path     (str)       --      The path of the index DB

            Returns:
                bool    --     True/False on successful operation

        """

        command = 'MAINMENU_DB_MENU "{0}" DBMENU_CONSISTENCYCHECK'.format(db_path)
        out = self.run_idx_cli(command)

        return 'SUCCESS' in out

    def do_tools_shutdown_index_server(self):
        """Shuts down the IndexServer process gracefully

            Returns:
                bool    --     True/False on successful operation

        """

        command = 'MAINMENU_TOOLS_MENU TOOLSMENU_SHUTDOWNIS'
        out = self.run_idx_cli(command)

        return 'succeeded' in out

    def do_table_export_all_tables(self, db_path, export_directory):
        """Performs DB consistency check

            Args:
                db_path     (str)       --      The path of the index DB

                export_directory (str)  --     The directory on the IndexServer machine to save the exported CSV files.

            Returns:
                dict    --     Dictionary of all the exported table names and it's full CSV file path.

        """

        export_directory = commonutils.remove_trailing_sep(export_directory, self.index_server_delim)
        db_path = commonutils.remove_trailing_sep(db_path, self.index_server_delim)

        command = 'MAINMENU_TABLE_MENU "{0}" TABLEMENU_EXPORT_ALL_TABLES "{1}"'.format(db_path, export_directory)
        self.run_idx_cli(command)

        csv_files = {}
        export_directory_out = commonutils.add_trailing_sep(
            export_directory + db_path[-1], self.index_server_delim
        )

        self.log.info('Scanning [%s] for exported CSV files', export_directory_out)
        scan_list = self.index_server_machine.get_files_in_path(export_directory_out)

        export_directory_out = export_directory_out.lower()

        for file_path in scan_list:
            file_path_temp = file_path.lower()
            file_name = file_path_temp.replace(export_directory_out, '')

            csv_files[file_name] = file_path

        return csv_files

    def do_tools_calculate_metrics(self):
        """Calculate Index server load and metrics

            Returns:
                bool    --      True/False if operation failed
        """

        command = 'MAINMENU_TOOLS_MENU TOOLSMENU_CALCULATE_METRICS'
        out = self.run_idx_cli(command)

    def do_rfc_upload(self, running_job_id, subfolder, input_file, compress="N"):
        """Upload input_file to running job ID Remote FIle Cache

            Args:
                running_job_id {string} -- Job ID

                subfolder {string} -- Directory to upload to

                input_file {string} -- Path to input_file to upload

            Returns:
                None/Exception
        """
        self.log.info("Uploading file to RFC")

        # MAINMENU_TOOLS_MENU TOOLSMENU_UPLOAD_RFC_FILES <runningjobId> <commCellId> <subFolder> <inputFile> <compress>
        command = 'MAINMENU_TOOLS_MENU TOOLSMENU_UPLOAD_RFC_FILES {0} 2 "{1}" "{2}" {3}'.format(running_job_id, subfolder, input_file, compress)
        out = self.run_idx_cli(command)

        if 'Success' not in out:
            raise Exception(out)
        else:
            self.log.info(out)

    def do_rfc_download(self, job_id, subfolder, output_folder):
        """Download sub folder to output_folder

            Args:
                job_id {str} -- Job ID

                subfolder {string} -- RFC Sub folder

                output_folder {string} -- Path to download to

            Returns:
                None/Exception
        """
        self.log.info("Downloading from RFC")

        # MAINMENU_TOOLS_MENU TOOLSMENU_DOWNLOAD_RFC_FILES <jobId> <commCellId> <subFolder> <outputFolder>
        command = 'MAINMENU_TOOLS_MENU TOOLSMENU_DOWNLOAD_RFC_FILES {0} 2 "{1}" "{2}"'.format(job_id, subfolder, output_folder)
        out = self.run_idx_cli(command)

        if 'Success' not in out:
            raise Exception(out)
        else:
            self.log.info(out)

    def do_anomaly_check(self, job_stats_path, job_id, client_name):
        """Starts the anomaly detection operation

            Args:
                job_stats_path          (str)       --      The job stats file to trigger anomaly detection

                job_id                  (str)       --      The job ID to trigger anomaly check

                client_name             (str)       --      The client name to anomaly check

        """

        self.log.info('Starting anomaly check detection')

        command = f'MAINMENU_TOOLS_MENU TOOLSMENU_START_ANOMALY_CHECK "{job_stats_path}" {job_id} {client_name}'
        out = self.run_idx_cli(command)

        self.log.info(out)

    def do_delete_index_db(self, backupset_guid, db_guid):
        """Deletes the index DB

            Args:
                backupset_guid          (str)       --      The backupset GUID of the DB

                db_guid                 (str)       --      The DB GUID of the DB

        """

        self.log.info('Deleting index DB [%s:%s]', backupset_guid, db_guid)

        if self.index_server_machine.os_info == 'WINDOWS':
            command = (
                'start-process '
                '-filepath "idxcli.exe" '
                '-wait '
                f'-workingDirectory "{self.index_server_base_dir}" '
                f'-ArgumentList "-vm {self.index_server_instance} -op delete -dbid {backupset_guid}:{db_guid} -job 123"'
            )

        else:
            command = '{0}/IdxCLI -vm {1} -op delete -dbid {2}:{3} -job 123'.format(
                self.index_server_base_dir, self.index_server_instance,
                backupset_guid, db_guid
            )

        self.log.info('Executing IdxCLI [%s]', command)
        self.index_server_machine.execute_command(command)
