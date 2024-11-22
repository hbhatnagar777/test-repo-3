# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

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
from Server.serverhelper import ServerTestCases
from Kubernetes.HelmHelper import HelmHelper
from Kubernetes.kubectl_helper import KubectlHelper
from AutomationUtils.machine import Machine
from Install import installer_utils
# from selenium import webdriver
# from selenium.webdriver.common.by import By
import time
from AutomationUtils import config, constants
from Web.Common.cvbrowser import BrowserFactory, Browser
from Web.AdminConsole.adminconsole import AdminConsole
from cvpysdk.commcell import Commcell


class TestCase(CVTestCase):
    """Class for executing this test case"""

    def __init__(self):
        """Initializes test case class object

            Properties to be initialized:

                name            (str)       --  name of this test case

                inputs        (dict)      --  test case inputs with input name as dict key
                                                and value as input type
                config_json        (dict)    --  inputs for dockerhub username and dockerhub password taken from config.json

                server        (object)      --  Create a ServerTestcase class object

        """
        super(TestCase, self).__init__()
        self.name = f"Deploying CS, Webserver and Command Center Image " \
            f"for {self.tcinputs.get('ImageTag')}"
        self.config_json = config.get_config()
        self.server = None
        self.remote_machine_hostname = None
        self.remote_machine_username = None
        self.remote_machine_password = None
        self.image_tag = None
        self.helm_helper = None
        self.kube_config_path = None
        self.machine_object = None
        self.namespace = None
        self.cs_client_name = None
        self.cs_username = None
        self.cs_password = None
        self.kubectl_helper = None

    def setup(self):
        """Setup function of this test case"""
        self.config_json = config.get_config()
        self.server = ServerTestCases(self)
        self.json_dict = self.config_json.Install.containerautomation
        self.remote_machine_hostname = self.json_dict["RemoteMachineHostname"]
        self.remote_machine_username = self.json_dict["RemoteMachineUsername"]
        self.remote_machine_password = self.json_dict['RemoteMachinePassword']
        self.kube_config_path = self.json_dict['K8sConfigPath']
        self.namespace = self.json_dict['Namespace']
        self.cs_client_name = self.json_dict['CSClientName']
        self.ws_client_name = self.json_dict['WSClientName']
        self.cc_client_name = self.json_dict['CCClientName']
        self.cs_username = self.json_dict['CSUsername']
        self.cs_password = self.json_dict['CSPassword']
        self.image_tag = self.tcinputs.get('ImageTag')
        self.machine_object = Machine(
            machine_name=self.remote_machine_hostname, 
            username=self.remote_machine_username,
            password=self.remote_machine_password)
        self.helm_helper = HelmHelper(
            kubeconfig=self.kube_config_path,
            repo_path='https://commvault.github.io/helm-charts',
            repo_name='commvault')
        self.kubectl_helper = KubectlHelper(
            commcell_object=self.commcell, 
            machine_name=self.remote_machine_hostname,
            user_name=self.remote_machine_username,
            password=self.remote_machine_password)

    def check_latest_image(self, minusvalue=0, pkgid=""):
        # Not currently in use
        # Checking the latest service pack and revision
        _sp_transaction = installer_utils.get_latest_recut_from_xml(self.tcinputs.get("ServicePack"))
        latest_cu = installer_utils.get_latest_cu_from_xml(_sp_transaction)
        rev_id = _sp_transaction.split('_')[-1][1:]
        sp_id = _sp_transaction.split('_')[0][2:]
        cu_id = str(int(latest_cu) - int(minusvalue))
        image_value = f"11.{sp_id}.{cu_id}.Rev{rev_id}"
        self.log.info(f"Searching for image {image_value}")
        url = (f"https://gitlab.testlab.commvault.com/eng-public/image-library/container_registry/"
               f"{pkgid}?orderBy=NAME&sort=desc&search[]={image_value}&search[]=")

        driver = webdriver.Chrome()
        driver.get(url)
        time.sleep(20)
        return_flag = 1
        try:
            value = (driver.find_element
                     (By.XPATH,
                      "/html/body/div[1]/div/div[3]/main/section/div/div/div[2]/section/div[2]/div/h1").text)
            if value == "The filter returned no results":
                self.image_tag = f"{image_value}"
                return_flag = 0
        except:
            self.log.info("Image found successfully , proceeding with the testcase")
        driver.close()
        return return_flag

    def check_pod_status(self, cs_pod):
        commserv_response = self.machine_object.execute_command \
            ('kubectl get ' + cs_pod + ' -n ' + self.namespace +
             ' -o jsonpath=\"{.status.containerStatuses[].ready}\"').output
        return commserv_response

    def set_values(cs_client_name, 
                   ws_client_name, 
                   cc_client_name, 
                   cs_username, 
                   cs_password, 
                   namespace, 
                   image_tag=None):
        value_dict = {
            "cs_hostname": 'csOrGatewayHostName=' + cs_client_name + '.' + namespace + '.svc.cluster.local',
            "username": 'secret.user=' + cs_username,
            "password": 'secret.password=' + cs_password,
            "namespace": 'global.namespace=' + namespace,
            "cs_client_name": 'clientName=' + cs_client_name,
            "ws_client_name": 'clientName=' + ws_client_name,
            "cc_client_name": 'clientName=' + cc_client_name,
            "image_tag": 'global.image.tag=' + image_tag,
            "webservername": 'webserverName=' + ws_client_name,
            "image_namespace": 'global.image.namespace=\"eng-public/image-library\"',
            "image_registry": 'global.image.registry=\"registry.testlab.commvault.com\"'}
        return value_dict

    def run(self):
        """Main function for test case execution"""
        try:
            # Adding helm repo
            self.helm_helper.add_helm_repo()
            values = self.set_values(cs_client_name=self.cs_client_name,
                                     ws_client_name=self.ws_client_name,
                                     cc_client_name=self.cc_client_name,
                                     cs_username=self.cs_username,
                                     cs_password=self.cs_password,
                                     namespace=self.namespace,
                                     image_tag=self.image_tag)

            # 1. Deploying the Config
            config_values = [values["cs_hostname"],
                             values["username"],
                             values["password"],
                             values["namespace"]]
            self.helm_helper.deploy_helm_app(helm_app_name='config',
                                             namespace=self.namespace,
                                             set_values=config_values)

            # 2. Deploying the Commserver
            commserve_values = [values["cs_client_name"],
                                values["namespace"],
                                values["image_tag"],
                                values["image_namespace"],
                                values["image_registry"]]
            
            self.helm_helper.deploy_helm_app(helm_app_name='commserve',
                                             namespace=self.namespace,
                                             set_values=commserve_values)
            
            self.log.info("Checking pod status now")

            pod_names = self.machine_object.execute_command(
                'kubectl get pod -n ' + self.namespace + ' -o name').output.split('\n')
            
            self.log.info(pod_names)
            cs_pod = None
            counter = 0
            flag = 0
            for pod in pod_names:
                if '/' + self.cs_client_name in pod:
                    cs_pod = pod
            self.log.info(cs_pod)

            while counter <= 7:
                pod_status = self.check_pod_status(cs_pod)
                self.log.info(pod_status)
                if pod_status == 'true':
                    flag = 1
                    counter = 10
                else:
                    time.sleep(300)
                    counter += 1

            if flag == 0:
                raise Exception("Installation failed. Please check logs within the pod")

            time.sleep(900)

            response = self.kubectl_helper.run_cmd_on_pod(
                command='/opt/commvault/Base/./qlogin -u ' + self.cs_username + ' -clp ' + self.cs_password + ' -gt',
                pod_name=cs_pod,
                namespace=self.namespace)
            
            if 'Error' in response:
                raise Exception("qlogin was unsuccessful with the error: " + response)
            else:
                self.log.info("qlogin was successful. The token generated was: " + response)

            qlist_response = self.kubectl_helper.run_cmd_on_pod(
                command='/opt/commvault/Base/./qlist client -tk ' + response, pod_name=cs_pod,
                namespace=self.namespace).split('\n')
            self.log.info(qlist_response)

            if self.cs_client_name in qlist_response[-1] and 'Linux' in qlist_response[-1] and \
                    'Yes' in qlist_response[-1]:
                self.log.info(qlist_response)
                self.log.info(qlist_response[-1])
                self.log.info("qlist client command execution was successful. The entities were returned correctly")
                self.log.info("CS Container creation was successful.")

            # 3. Deploying WebServer
            webserver_values = [values["ws_client_name"],
                                values["namespace"],
                                values["image_tag"],
                                values["image_namespace"],
                                values["image_registry"]]
            
            self.helm_helper.deploy_helm_app(helm_app_name='webserver',
                                             namespace=self.namespace,
                                             set_values=webserver_values)
            time.sleep(300)

            # 4. Deploying CommandCenter
            commandcenter_values = [values["cc_client_name"],
                                    values["namespace"],
                                    values["image_tag"],
                                    values["webservername"],
                                    values["image_namespace"],
                                    values["image_registry"]]
            
            self.helm_helper.deploy_helm_app(helm_app_name='commandcenter',
                                             namespace=self.namespace,
                                             set_values=commandcenter_values)
            
            time.sleep(300)

            ccinternalip = self.machine_object.execute_command(
                f'kubectl get services {self.cc_client_name}').output.split('\n')[1].split()[3]
            
            self.log.info(f"The internal ip for the the command center is {ccinternalip}")

            # Performing a check readiness login
            self.commcell = Commcell(
                webconsole_hostname=ccinternalip,
                commcell_username=self.cs_username,
                commcell_password=self.cs_password)

            self.log.info("Checking Readiness of the CS machine")
            _commserv_client = self.commcell.commserv_client

            if _commserv_client.is_ready:
                self.log.info("Check Readiness of CS successful")
            else:
                self.status = constants.FAILED
                self.log.error("Check Readiness Failed")

            # Logging into the commandcenter 
            try:
                self.factory = BrowserFactory()
                self.browser = self.factory.create_browser_object()
                self.browser.open()
                self.driver = self.browser.driver
                self.admin_console = AdminConsole(self.browser, ccinternalip)
                self.admin_console.login(self.cs_username,
                                        self.cs_password,
                                        stay_logged_in=False)
            except:
                self.log.info("Command Center login failed")

        except Exception as exp:
            self.log.error('Failed with error: %s', exp)
            self.result_string = str(exp)
            self.status = constants.FAILED

    def tear_down(self):
        """Tear down function of this test case"""
        self.helm_helper.cleanup_helm_app(helm_app_name='config', namespace=self.namespace)
        self.helm_helper.cleanup_helm_app(helm_app_name='commserve', namespace=self.namespace)
        self.helm_helper.cleanup_helm_app(helm_app_name='webserver', namespace=self.namespace)
        self.helm_helper.cleanup_helm_app(helm_app_name='commandcenter', namespace=self.namespace)
