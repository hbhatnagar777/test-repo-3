""""Main file for executing this test case

TestCase is the only class defined in this file.

TestCase: Class for executing this test case

TestCase:
    __init__()      --  initialize TestCase class

    setup()         --  setup function of this test case

    run()           --  run function of this test case

    tear_down()     --  tear down function of this test case

"""

from AutomationUtils.cvtestcase import CVTestCase
from Server.regions_helper import RegionsHelper
from cvpysdk import commcell, regions
from Web.Common.page_object import handle_testcase_exception, TestStep
from Web.Common.exceptions import CVTestStepFailure


class TestCase(CVTestCase):
    """Class for executing this test case"""
    test_step = TestStep()

    def __init__(self):
        """Initializes test case class object

                    Properties to be initialized:

                        name            (str)       --  name of this test case

                """
        super(TestCase, self).__init__()
        self.name = "Workload Region of VM"
        self.tcinputs = {
            "VM": None,
            "region_1": None,
            "hypervisor": None,
            "region_2":None,
            "commcell": None,
            "region_3": None
        }
        """
        Note: make sure all the three regions are not same.
        """

    def setup(self):
        """Setup function of this test case"""
        self.commcell = commcell.Commcell(self.inputJSONnode['commcell']["webconsoleHostname"],
                                          self.inputJSONnode['commcell']['commcellUsername'],
                                          self.inputJSONnode['commcell']['commcellPassword'])
        self.helper = RegionsHelper(self.commcell)
        self.region_id = {"client_group":int(regions.Regions(self.commcell).get(self.tcinputs["region_1"]).region_id),
                          "HyperV":int(regions.Regions(self.commcell).get(self.tcinputs["region_2"]).region_id),
                          "commcell":int(regions.Regions(self.commcell).get(self.tcinputs["region_3"]).region_id)}
        self.cg_name = self.helper.get_VM_client_group(self.tcinputs["VM"])

    def edit_region(self, entity_type, entity_name, region_type, region_name=None, response1= None):
        """Method to edit region of the entity"""
        self.helper.edit_region_of_entity(entity_type=entity_type,
                                          entity_name=entity_name,
                                          entity_region_type=region_type,
                                          region_name=region_name)
        response = self.helper.get_region_of_entity(entity_type=entity_type,
                                                    entity_name=entity_name,
                                                    entity_region_type=region_type)
        if response == response1:
            self.log.info("validation successfull")
            return response
        else:
            raise Exception("validation failed, response returned is %s, expected response is %s."% (response,response1))

    def calculate_region(self, region_type, entity_type, entity_name, response):
        """Method to validate calculate region for the entity"""
        region = self.helper.calculate_region_of_entity(entity_region_type=region_type,
                                                        entity_type=entity_type,
                                                        entity_name=entity_name)
        if region == response:
            self.log.info("validation completed")
        else:
            raise Exception("validation failed, response returned is %s, expected reponse is %s" % (region, response))

    @test_step
    def set_region_assoc_entities(self):
        """ method to set the workload region to one of VM's client groups, HyperV and commcell entity"""
        try:
            response1 = self.edit_region(entity_type="CLIENT_GROUP",
                                             entity_name=self.cg_name[0],
                                             region_type="WORKLOAD",
                                             region_name=self.tcinputs["region_1"],
                                             response1=self.region_id["client_group"])

            response2 = (self.edit_region(entity_type="CLIENT",
                                             entity_name=self.tcinputs["hypervisor"],
                                             region_type="WORKLOAD",
                                             region_name=self.tcinputs["region_2"],
                                             response1=self.region_id["HyperV"]))

            response3 = (self.edit_region(entity_type="COMMCELL",
                                              entity_name=self.tcinputs["commcell"],
                                              region_type="WORKLOAD",
                                              region_name=self.tcinputs["region_3"],
                                              response1=self.region_id["commcell"]))
            return [response1,response2,response3]
        except Exception as exp:
            raise CVTestStepFailure from exp

    @test_step
    def validate_calculate_region_for_vm(self, entity_type,entity_name,response):
        """
        calculated workload region should be same as response
        """
        try:
            self.edit_region(entity_type="CLIENT",
                             entity_name=self.tcinputs["VM"],
                             region_type="WORKLOAD")
            if entity_type == "CLIENT_GROUP":
                # setting None to every client group associated with VM
                for i in range(len(entity_name)):
                    self.edit_region(entity_type=entity_type,
                                     entity_name=entity_name[i],
                                     region_type="WORKLOAD")
            else:
                self.edit_region(entity_type=entity_type,
                                 entity_name=entity_name,
                                 region_type="WORKLOAD")
            self.calculate_region(region_type="WORKLOAD",
                                  entity_type="CLIENT",
                                  entity_name=self.tcinputs["VM"],
                                  response=response)
        except Exception as exp:
            raise CVTestStepFailure from exp

    def run(self):
        """ run function of this test case """
        try:
            # Pick a VM and set the workload region to None
            self.edit_region(entity_type= "CLIENT",
                             entity_name=self.tcinputs["VM"],
                             region_type="WORKLOAD")

            response = self.set_region_assoc_entities()

            self.calculate_region(region_type="WORKLOAD",
                                  entity_type="CLIENT",
                                  entity_name=self.tcinputs["VM"],
                                  response=response[1])

            self.validate_calculate_region_for_vm(entity_type="CLIENT",
                                                  entity_name=self.tcinputs["hypervisor"],
                                                  response=response[0])

            self.validate_calculate_region_for_vm(entity_type="CLIENT_GROUP",
                                                  entity_name=self.cg_name,
                                                  response=response[2])

        except Exception as exp:
            handle_testcase_exception(self,exp)

    def tear_down(self):
        """Tear down function of this test case"""
        self.commcell.logout()

