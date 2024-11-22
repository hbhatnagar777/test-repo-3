from AutomationUtils.cvtestcase import CVTestCase
from Web.Common.page_object import handle_testcase_exception, TestStep
from Server.RestAPI.Locust.Locust_testcase import locust_helper
from AutomationUtils import database_helper
from AutomationUtils.options_selector import OptionsSelector

class TestCase(CVTestCase):
    """Class for executing this test case"""
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object
            Properties to be initialized:
                name            (str)       --  name of this test case
        """
        super(TestCase, self).__init__()
        self.name = "Create subclients in Bulk for load testing"
        self.fileName = __file__
        self.check_readiness = False
        self.clients = []
        self.plan_ids = []
        self.tcinputs = {
            "plans" : []
        }

    def setup(self):
        """Setup function of this test case"""
        
        self.csdb = database_helper.CommServDatabase(self.commcell)
        
        self.inputs = {
            "webserver": self.inputJSONnode['commcell']['webconsoleHostname'],
            "username": self.inputJSONnode['commcell']['commcellUsername'],
            "password": self.inputJSONnode['commcell']['commcellPassword'],
            "threads": self.tcinputs.get("threads", "15"),
            "spawnRate": self.tcinputs.get("spawnRate", "5"),
            "minutes": self.tcinputs.get("minutes", "10"),
            "email": self.inputJSONnode['email']['receiver'],
            "fileName": self.fileName,
            "apiList": "create_subclients",
            "create_subclients":{
                "plan_ids": "",
                "clients": ""
            }
        }
        self.clients = list(self.commcell.clients.file_server_clients)
        
        if self.tcinputs.get('check_readiness', False): # if check readiness is specified, only ready clients will be picked
            self.clients = self.get_ready_clients(self.clients)
            self.log.info(f'Clients which passed check readiness : {self.clients}')
        
        plan_ids = list()
        for plan in self.tcinputs['plans']: plan_ids.append(self.commcell.plans.get(plan).plan_id)
        
        self.inputs["create_subclients"]["clients"]  = ','.join(map(str, self.clients))
        self.inputs["create_subclients"]["plan_ids"] = ','.join(map(str, plan_ids))
        
        self.initial_subclient_count = self.check_subclient_count()
        self.log.info(f'Subclient count before starting the run : {self.initial_subclient_count}')
        
    def run(self):
        """Run function of this test case"""
        try:
            self.log.info('Starting Locust Run...')
            locust_instance = locust_helper.Locust_Helper(self.inputs)
            locust_instance.locust_execute()
            self.log.info('Locust Run finished')
        except Exception as exp:
            handle_testcase_exception(self, exp)
            
    def tear_down(self):
        self.final_subclient_count = self.check_subclient_count()
        self.log.info(f'Total subclients created during the testcase run : {self.final_subclient_count - self.initial_subclient_count}')
        self.log.info('Please re-run the testcase, if more subclients are needed')
    
    def get_ready_clients(self, clients):
        """Checking readiness for available clients"""
        options_selector = OptionsSelector(self.commcell)
        return options_selector.get_ready_clients( clients, validate=False)[0]
    
    def check_subclient_count(self):
        """Checking subclient count in commcell"""
        self.csdb.execute('SELECT COUNT(1) FROM APP_Application WITH (NOLOCK)')
        return int(self.csdb.fetch_one_row()[0])
