# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------


"""
ACCT1 to verify XBSA (GuassDB) Multinode Database
Steps:
    1. Install Commvault Software on Roach Client (Cloud Apps Package)
    2. Create a new pseudo client having GaussDB instance
    3. On the roach client, add a link to CV XBSA library so that roach is able to use it for backups and restore.
    4. Login to any data node and create following file: /srv/BigData/mppdb/medialist and roach client IPs as content.
    5. Trigger full backup to Commvault.
    6. Trigger incremental backup to commvault using backup key of prior full backup.
    7. Try browse and verify backup info at data node level is matching with that of application level backup info.
    8. Start the cluster and check the status of cluster.

Note:
    1. User should have commvault software on roach client and GaussDB installation on data nodes. Machines should be
       pre-configured for doing xbsa backups and restore.
    2. The test case should work fine if machines(roach clients and data nodes) have the necessary configurations.

TestCase is the only class defined in this file.
TestCase: Class for executing this test case

TestCase:
    __init__()                                   --  Initializes TestCase class

    create_db_instance()                         --  Creates multinode database instance

    add_link()                                   --  Add a link to CV XBSA library on roach client

    create_medialist()                           --  Creates medialist on the data node

    run_backup()                                 --  Runs backup command from the data node

    verify_backup()                              --  Verify backup info on data node and application level

    run_restore()                                --  Runs restore command from the data node

    start_cluster()                              --  Starts the cluster

    check_cluster_status()                       --  Check status of the cluster

    delete_instance()                            --  Delete instance which gets created during execution of test case

    run()                                        --  Run function for this testcase

    tear_down()                                  --  Tear down function for this testcase

Sample Input:
"70373": {
    "XbsaClients": ["ip-10-145-3-12"],
    "Plan": "ServerPlan",
    "RoachClientName": "ip-10-145-3-12",
    "DataNodeName": "10.145.3.10",
    "DataNodeUsername": "******",
    "DataNodePassword": "******",
    "RoachClientsIp": ["10.145.3.12"],
}
"""
import re
import time

from AutomationUtils.cvtestcase import CVTestCase
from AutomationUtils.machine import Machine
from Web.AdminConsole.Components.core import TreeView
from Web.AdminConsole.Components.table import Rtable
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.adminconsole import AdminConsole
from Web.Common.page_object import TestStep, handle_testcase_exception
from Web.AdminConsole.Databases.db_instances import DBInstances
from Web.AdminConsole.Databases.db_instance_details import DBInstanceDetails


class TestCase(CVTestCase):
    test_step = TestStep()

    def __init__(self):
        """
        Initializes test case class object
        """
        super(TestCase, self).__init__()
        self.name = "ACCT1 to verify XBSA (GuassDB) Multinode Database"
        self.browser = None
        self.admin_console = None
        self.treeview = None
        self.credential_manager = None
        self.rtable = None
        self.db_instance_details = None
        self.db_instance = None
        self.data_node_machine = None
        self.roach_client_machine = None
        self.output = None
        self.error = None
        self.job = None
        self.backup_key = None
        self.db_client_name = None
        self.db_server = None
        self.instance_name = None
        self.db_name = None
        self.regex_pattern = None
        self.tc_time = None

        self.tcinputs = {
            "XbsaClients": None,
            "Plan": None,
            "RoachClientName": None,
            "DataNodeName": None,
            "DataNodeUsername": None,
            "DataNodePassword": None,
            "RoachClientsIp": None,
        }

    def setup(self):
        """
        Method to setup test variables
        """
        self.roach_client_machine = Machine(machine_name=self.tcinputs['RoachClientName'],
                                            commcell_object=self.commcell)

        self.data_node_machine = Machine(machine_name=self.tcinputs["DataNodeName"],
                                         username=self.tcinputs["DataNodeUsername"],
                                         password=self.tcinputs["DataNodePassword"])

        self.tc_time = int(time.time())
        self.db_client_name = f"client_{self.tc_time}"
        self.db_server = "GaussDB"
        self.instance_name = f"instance_{self.tc_time}"
        self.db_name = "postgres"
        self.regex_pattern = r'\x1b\[A\x1b\[2K|\x1b\[6;1H'

        self.browser = BrowserFactory().create_browser_object()
        self.browser.open()
        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname, enable_ssl=True)
        self.admin_console.login(
            username=self.inputJSONnode['commcell']['commcellUsername'],
            password=self.inputJSONnode['commcell']['commcellPassword'],
            stay_logged_in=True
        )

        self.db_instance = DBInstances(admin_console=self.admin_console)
        self.db_instance_details = DBInstanceDetails(admin_console=self.admin_console)
        self.treeview = TreeView(admin_console=self.admin_console)
        self.rtable = Rtable(admin_console=self.admin_console)

    @test_step
    def create_db_instance(self):
        """
        Method to create new multinode database instance.
        """
        self.admin_console.navigator.navigate_to_db_instances()
        self.db_instance.add_multinode_database_instance(
            client_name=self.db_client_name,
            xbsa_clients=self.tcinputs['XbsaClients'],
            database_server=self.db_server,
            instance_name=self.instance_name,
            database_name=self.db_name,
            plan=self.tcinputs['Plan'],
        )
        self.commcell.refresh()
        self.log.info('Created Multinode Database Instance')

    @test_step
    def add_link(self):
        """
        This method will add a link to CV XBSA library on roach client so that roach is able to use
        it for backups and restore.
        """
        self.output = self.roach_client_machine.execute_command("sudo -i -u rdadmin bash -c 'cd lib; "
                                                                "ln -s /opt/commvault/Base64/libCvXbsa.so "
                                                                "./libxbsa64.so'")

        # There might be a case where link already exists, except for that case if any command fails in the
        # above execute command we will raise exception
        if self.output.exit_code == 1 and self.output.exception_message != 'File exists':
            self.log.error("Creation of link file CV XBSA library on roach client failed")
            self.error = (f"Error received from roach client while executing the add link command: \n"
                          f"Exception: {self.output.exception}\nTerminal Output: {self.output.output}")
            raise Exception(self.error)

        self.log.info("Successfully added the link to CV XBSA library on roach client")

    @test_step
    def create_medialist(self):
        """
        Method to create medialist on the data node, adding roach client IPs as content to the medialist file.
        """
        content = " ".join(self.tcinputs["RoachClientsIp"])

        command = ("source ${BIGDATA_HOME}/mppdb/.mppdbgs_profile; "
                   "cd /srv/BigData/mppdb; "
                   f"echo {content} | fmt -w1 > medialist; ")

        self.output = self.data_node_machine.execute_command("sudo -i -u omm bash -c " + f"'{command}'")
        if self.output.exit_code != 0:
            self.log.error("Creation of medialist on data node failed")
            self.error = (f"Error received from data node while executing the create medialist command:\n"
                          f"Exception: {self.output.exception}\nTerminal Output: {self.output.output}")
            raise Exception(self.error)

        self.log.info("Successfully created medialist on the data node")

    def process_datanode_output(self, output):
        """
        This method will process the terminal output that we receive from remote machine after the executing
        the command. Terminal output may contain some regex expression and some useless lines. This method
        will clean the output for better processing and readability of terminal output.
        """
        output = output.splitlines()
        res_output = []
        for x in output:
            cleaned_string = re.sub(self.regex_pattern, '', x)
            res_output.append(cleaned_string)

        res_output = [line for line in res_output if line.strip()]
        res_output = [line for line in res_output if not line.startswith("Current progress: 0.00%")]
        res_output = [line for line in res_output if not line.startswith("Current progress: 100.00%")]

        return res_output

    def wait_for_job_completion(self):
        """
        This method will wait for completion of any active jobs of the instance on command center.
        """
        jobs = self.commcell.job_controller.active_jobs(client_name=self.db_client_name)
        for job_id in jobs:
            self.job = self.commcell.job_controller.get(job_id)
            self.job.wait_for_completion()

    @test_step
    def run_backup(self, config_setting, backup_level, backup_key=None):
        """
        Method to run command line backup from the data node.
        """
        media_destination = (f"CVOBConfigSetting={config_setting},"
                             "CvInstanceName=Instance001,"
                             f"CvBackupLevel={backup_level}")

        command1 = "source ${BIGDATA_HOME}/mppdb/.mppdbgs_profile; "

        command2 = ("python3 \\$GPHOME/script/GaussRoach.py -t backup "
                    "--master-port 55002 --media-type NBU "
                    "--media-destination " + f'"{media_destination}" '
                    "--metadata-destination /home/omm/metadata --parallel-process 1 --nbu-on-remote "
                    "--nbu-media-list /srv/BigData/mppdb/medialist --client-port 5000")

        if backup_level == 'INCR':
            if backup_key is None:
                raise Exception('Prior backup key is required for incremental backup')
            else:
                command2 += f" --prior-backup-key {backup_key}"

        self.output = self.data_node_machine.execute_command("sudo -i -u omm bash -c " + f"'{command1 + command2}'")

        if self.output.exit_code != 0:
            self.error = (f"Error received from data node while executing the {backup_level} backup command: \n"
                          f"Exception: {self.output.exception}\nTerminal Output: {self.output.output}")
            raise Exception(self.error)

        output = self.process_datanode_output(self.output.output)

        match = [line for line in output if line.startswith("[MASTER]Backup operation SUCCESSFUL.")]
        if len(match) == 0:
            self.log.error(f"{backup_level} Backup Failed.")
            self.error = "\n".join(output)
            self.error = (f"Error received from data node while executing the {backup_level} backup command:\n"
                          f"{self.error}")
            raise Exception(self.error)

        self.backup_key = match[0].split(":")[1].strip()
        self.wait_for_job_completion()

        self.log.info(f"Backup Successful. {backup_level} Backup ran successfully having backup id: %s",
                      self.backup_key)

    @test_step
    def verify_backup(self):
        """
        Method to verify backup. To verify backup key with that of application level and data node level.
        """
        # First verify backup on data node level : Using command to check backup information
        # Output will list all the backup timestamps of full/incr backups.
        command = ("source ${BIGDATA_HOME}/mppdb/.mppdbgs_profile; "
                   "python3 $GPHOME/script/GaussRoach.py -t show --all-backups "
                   "--metadata-destination /home/omm/metadata")

        self.output = self.data_node_machine.execute_command("sudo -i -u omm bash -c " + f"'{command}'")
        if self.output.exit_code != 0:
            self.error = (f"Error received from data node while browsing backup information:\n"
                          f"Exception: {self.output.exception}\nTerminal Output: {self.output.output}")
            raise Exception(self.error)

        # remove regex expressions from the output and get the backup key
        output = self.output.output.splitlines()
        bkp_key = "-1"
        bkp_status = "FAILED"
        for line in reversed(output):
            line = re.sub(self.regex_pattern, '', line)
            if line.startswith('|'):
                strs = line.split('|')
                bkp_key = strs[2].strip() if len(strs) > 2 else "-1"
                bkp_status = strs[10].strip() if len(strs) > 10 else "FAILED"
                break

        if bkp_key != self.backup_key:
            self.log.error("Backup verification failed. Backup key info is not present on data node")
            raise Exception("Backup key info is not present on data node")

        if bkp_status in ['NA', 'FAILED', 'CORRUPTED']:
            self.log.error(f"Backup verification failed. Backup status on data node is {bkp_status}")
            raise Exception(f"Backup status on data node is {bkp_status}")

        # Second verify backup on application level (verify from command center).
        self.admin_console.navigator.navigate_to_db_instances()
        self.rtable.reload_data()
        self.db_instance.select_instance(DBInstances.Types.MULTINODE_DATABASE, self.instance_name)
        self.db_instance_details.access_restore()
        self.treeview.expand_path(path=[self.instance_name, 'roach', self.backup_key])

        self.log.info("Backup is verified. It was successfully completed")

    @test_step
    def run_restore(self, config_setting, backup_key=None):
        """
        Method to initiate command line restore from the data node.
        """
        media_destination = (f"CVOBConfigSetting={config_setting}," 
                             "CvInstanceName=Instance001")

        command1 = "source ${BIGDATA_HOME}/mppdb/.mppdbgs_profile; "

        command2 = ("python3 \\$GPHOME/script/GaussRoach.py -t restore --clean " +
                    "--master-port 55002 --media-type NBU " +
                    "--media-destination " + f'"{media_destination}" ' +
                    "--metadata-destination /home/omm/metadata --backup-key " + f'{backup_key} ' +
                    "--nbu-on-remote --nbu-media-list /srv/BigData/mppdb/medialist " +
                    "--client-port 5000 --parallel-process 1"
                    )

        self.output = self.data_node_machine.execute_command("sudo -i -u omm bash -c " + f"'{command1 + command2}'")
        if self.output.exit_code != 0:
            self.log.error("Restore Failed.")
            self.error = (f"Error received from data node while executing the restore command:\n"
                          f"Exception: {self.output.exception}\nTerminal Output: {self.output.output}")
            raise Exception(self.error)

        output = self.process_datanode_output(self.output.output)
        match = [line for line in output if line.startswith("[MASTER] Restore SUCCESSFUL.")]

        self.wait_for_job_completion()

        if len(match) == 2:
            self.log.info("Restore Successful.")
        else:
            self.log.error("Restore Failed.")
            self.error = "\n".join(output)
            self.error = (f"Error received from data node while executing the restore command:\n"
                          f"{self.error}")
            raise Exception(self.error)

    @test_step
    def start_cluster(self):
        """
        Method to start the cluster.
        """
        command = ("source ${BIGDATA_HOME}/mppdb/.mppdbgs_profile; "
                   "python3 $GPHOME/script/GaussRoach.py -t start")

        self.output = self.data_node_machine.execute_command("sudo -i -u omm bash -c " + f"'{command}'")

        if self.output.exit_code != 0:
            self.log.error("Starting of cluster failed.")
            self.error = (f"Error received from data node while executing the start cluster command:\n"
                          f"Exception: {self.output.exception}\nTerminal Output: {self.output.output}")
            raise Exception(self.error)

        self.log.info("Cluster started successfully.")

    @test_step
    def check_cluster_status(self):
        """
        Method to check status of the cluster.
        """
        command = ("source ${BIGDATA_HOME}/mppdb/.mppdbgs_profile; "
                   "gs_om -t status")

        self.output = self.data_node_machine.execute_command("sudo -i -u omm bash -c " + f"'{command}'")

        if self.output.exit_code != 0:
            self.error = (f"Error received from data node while executing the check cluster status command:\n"
                          f"Exception: {self.output.exception}\nTerminal Output: {self.output.output}")
            raise Exception(self.error)

        self.log.info("Status of cluster: %s", self.output.output)

    @test_step
    def delete_instance(self):
        """
        Method to delete created instance
        """
        self.admin_console.navigator.navigate_to_db_instances()
        self.rtable.reload_data()
        self.db_instance.select_instance(DBInstances.Types.MULTINODE_DATABASE, self.instance_name)
        self.db_instance_details.delete_instance()
        self.log.info("Deleted the multinode database instance that was created during execution of the test case")

    def run(self):
        try:
            # create new instance
            self.create_db_instance()

            # add link on roach client
            self.add_link()

            # create medialist on data node
            self.create_medialist()

            # run full backup
            self.run_backup(config_setting=f"sCVXBSAConfig_{self.instance_name}_{self.db_name}",
                            backup_level="FULL")

            # verify full backup
            self.verify_backup()

            # run incremental backup
            self.run_backup(config_setting=f"sCVXBSAConfig_{self.instance_name}_{self.db_name}",
                            backup_level="INCR",
                            backup_key=self.backup_key)

            # verify incremental backup
            self.verify_backup()

            # run restore
            self.run_restore(config_setting=f"sCVXBSAConfig_{self.instance_name}_{self.db_name}",
                             backup_key=self.backup_key)

            # start cluster
            self.start_cluster()

            # Check cluster status
            self.check_cluster_status()

        except Exception as exp:
            handle_testcase_exception(self, exp)

    def tear_down(self):
        self.delete_instance()
        AdminConsole.logout_silently(self.admin_console)
        Browser.close_silently(self.browser)
