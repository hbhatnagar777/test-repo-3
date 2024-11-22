from AutomationUtils.cvtestcase import CVTestCase
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.adminconsole import AdminConsole
from Web.AdminConsole.Bigdata.instances import Instances, SplunkServer
from Web.Common.page_object import handle_testcase_exception
from cvpysdk.job import Job


class TestCase(CVTestCase):

    def __init__(self):
        """
        Initializes test case class object
        """
        super().__init__()
        self.browser = None
        self.name = "Splunk cluster CRUD"
        self.admin_console = None
        self.instances = None
        self.browse = None
        self.splunkobj = None

    def setup(self):
        """
        Method to set_up test variables
        """
        self.browser = BrowserFactory().create_browser_object()
        self.browser.open()
        self.admin_console = AdminConsole(self.browser, self.commcell.webconsole_hostname)
        self.admin_console.login(
            username=self.inputJSONnode['commcell']['commcellUsername'],
            password=self.inputJSONnode['commcell']['commcellPassword'],
            stay_logged_in=True
        )
        self.admin_console.navigator.navigate_to_big_data()
        self.admin_console.wait_for_completion()
        self.instances = Instances(self.admin_console)
        self.splunkobj = SplunkServer(self.admin_console)
        if self.instances.is_instance_exists(self.tcinputs['Name']):
            self.instances.delete_instance_name(self.tcinputs['Name'])

    def run(self):
        try:
            self.splunkobj = self.instances.add_splunk_server()
            inputs = {
                'Plan': self.tcinputs['Plan'],
                'Name': self.tcinputs['Name'],
                'Master_node': self.tcinputs['Master_node'],
                'Uri': self.tcinputs['Uri'],
                'Username': self.tcinputs['Username'],
                'Password': self.tcinputs['Password'],
                'Nodes': self.tcinputs['Nodes'],
                'Indexes': self.tcinputs['Indexes'],
                'Backup_type': self.tcinputs['Backup_type']
            }
            self.splunkobj.add(inputs)
            job_id = self.splunkobj.backup(self.tcinputs['Backup_type'])
            job = Job(self.commcell, job_id)
            job.wait_for_completion()
            self.admin_console.navigator.navigate_to_big_data()
            self.instances.delete_instance_name(self.tcinputs['Name'])
            self.admin_console.wait_for_completion()
        except Exception as exp:
            handle_testcase_exception(self, exp)
        finally:
            AdminConsole.logout_silently(self.admin_console)
            Browser.close_silently(self.browser)
