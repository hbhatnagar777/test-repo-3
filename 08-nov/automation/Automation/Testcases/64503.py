# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Main file for executing this test case

This testcase sets up a custom application service on VM/container and verifies if the service is accessible.

Requirements:
    A commvault client with
        - CVDotNetContainer package installed if deployment is VM.
        - docker, remote software cache configured and dockerfile, start.sh copied if deployment is container.

TestCase:
    __init__()                  --  Initializes the TestCase class

    setup()                     --  All testcase objects are initializes in this method

    run()                       --  Contains the core testcase logic and it is the one executed

    check_service()             --  Checks if service is accessible

    vm_set_registry()           --  Creates the registry entry for the service

    vm_restart_cvdnc_service()  --  Restarts the CVDotNetContainer service

    cnt_build_base_image()      --  Builds the base image using the CV installer

    cnt_build_service_image()   --  Builds the custom service image

    cnt_run_container()         --  Starts the service container

    cnt_init_svc()              --  Sets up the service controller inside the container

"""

import time
import requests

from AutomationUtils.cvtestcase import CVTestCase
from Platform.helpers import cvdnc_testcase


class TestCase(CVTestCase):
    """This testcase sets up a custom application service on VM/container and verifies if the service is accessible."""

    def __init__(self):
        """Initializes test case class object"""

        super(TestCase, self).__init__()
        self.name = 'CVDotNetContainer - Setup'

        self.tcinputs = {
            'HostMachine': None,
            'ServiceDLLPath': None,  # Required for VM deployment. The path of the controller dll file
            'Deployment': None,  # Type of deployment made - "VM" or "Container"
            'ServiceDockerDir': None  # Required for Container deployment. The directory where the dockerfile is present
        }

        self.help = None
        self.host_cl = None
        self.host_machine = None
        self.svc_port = 5005
        self.deployment = None
        self.image_name = 'cvdnc_img'
        self.container_name = 'cvdnc_cnt'
        self.svc_url = None

    def setup(self):
        """All testcase objects are initialized in this method"""

        self.help = cvdnc_testcase.CVDNCTestcase(self.commcell)
        self.help.set_host_machine(self.tcinputs.get('HostMachine'))

        self.host_cl = self.help.host_cl
        self.host_machine = self.help.host_machine

        self.deployment = self.tcinputs.get('Deployment')

    def run(self):
        """Contains the core testcase logic"""

        self.log.info('***** Setting up CVDotNetContainer in [%s] mode *****', self.deployment.upper())

        if self.deployment.lower() == 'vm':
            self.vm_set_registry()
            self.vm_restart_cvdnc_service()

        if self.deployment.lower() == 'container':
            self.cnt_build_base_image()
            self.cnt_build_service_image()
            self.cnt_run_container()
            self.cnt_init_svc()

        self.check_service()

        self.help.save_setup_data({
            'deployment': self.deployment,
            'host_machine': self.host_cl.client_name,
            'svc_url': self.svc_url,
            'container_name': self.container_name
        })

    def check_service(self):
        """Checks if service is accessible

            Returns:
                The HTTP service URL

        """

        self.svc_url = f'http://{self.host_cl.client_hostname}:{self.svc_port}/Tests'
        self.log.info('Checking if service is accessible [%s]', self.svc_url)

        out = requests.get(f'{self.svc_url}/CRUD')
        self.log.info('Service is accessible [%s]', out.text)

        return self.svc_url

    def vm_set_registry(self):
        """Creates the registry entry for the service"""

        service_name = 'TestService'
        registry_path = f'CVContainer/DotNet/{service_name}'
        svc_dll_path = self.tcinputs.get('ServiceDLLPath')

        self.log.info('***** Setting registry *****')
        self.log.info('Deleting registry [%s]', registry_path)
        try:
            self.host_machine.remove_registry(registry_path, 'sControllerDlls')
        except Exception as e:
            self.log.error('Failed to delete registry [%s]', e)

        self.log.info('Creating registry [%s] value [%s]', registry_path, svc_dll_path)
        self.host_machine.create_registry(registry_path, 'sControllerDlls', svc_dll_path, 'string')

    def vm_restart_cvdnc_service(self):
        """Restarts the CVDotNetContainer service"""

        self.log.info('***** Restarting CVPlatform services *****')

        if 'windows' in self.host_cl.os_info.lower():
            self.host_cl.restart_service(f'CVPlatformService({self.host_cl.instance})')
        else:
            self.host_cl.restart_service(f'CVDotNetContainer')

    def cnt_build_base_image(self):
        """Builds the base image using the CV installer"""

        self.log.info('Getting local remote software cache path')
        sw_cache = self.host_machine.get_registry_value(key='SoftwareCache', value='sRemoteCachePath')
        self.log.info('Software cache path [%s]', sw_cache)

        if not sw_cache:
            raise Exception(f'Remote software cache is not configured on this client [{self.host_cl.client_name}]')

        self.log.info('Getting silent_install path')
        out = self.help.exec('find /home/sw -name silent_install -type f')
        if out.exit_code != 0:
            raise Exception(f'Failed to get silent install path [{out.output}]')
        silent_install_path = out.formatted_output
        self.log.info('Silent install path [%s]', silent_install_path)

        if not silent_install_path:
            raise Exception(f'Unable to find installer the software cache [{out.output}]')

        self.help.exec(f'docker rm -f {self.container_name}')
        self.help.exec(f'docker image rm {self.image_name}')

        self.log.info('***** Creating CV base image *****')
        cmd = (f'{silent_install_path} -custompackage -type 7 -pkgs 1002 1183 -name "{self.image_name}_base" '
               f'-stagingdirectory /customstage -binarysetids 18')
        self.log.info('Command [%s]', cmd)

        # out = self.help.exec(cmd)
        if out.exit_code != 0:
            raise Exception(f'Failed to create base image [{out.output}]')

        self.log.info('Successfully created base image')

    def cnt_build_service_image(self):
        """Builds the custom service image"""

        docker_svc_dir = self.tcinputs.get('ServiceDockerDir')

        self.log.info('Deleting existing service image')
        self.help.exec(f'docker image rm {self.image_name}')

        # TODO - Automatically copy the TestService dockerfiles during automation instead of manual setup

        self.log.info('***** Building service image *****')
        out = self.help.exec(f'docker build "{docker_svc_dir}" -t {self.image_name}')

        if out.exit_code != 0:
            raise Exception(f'Failed to create service image [{out.output}]')

        self.log.info('Successfully created service image')

    def cnt_run_container(self):
        """Starts the service container"""

        self.log.info('***** Starting the service container *****')

        out = self.help.exec(f'docker run -d -p {self.svc_port}:{self.svc_port} --name {self.container_name} {self.image_name}')
        if out.exit_code != 0:
            raise Exception(f'Failed to run service container [{out.output}]')

        self.log.info('Successfully started service container')

    def cnt_init_svc(self):
        """Sets up the service controller inside the container"""

        time.sleep(30)
        self.log.info('***** Registering the controller and restarting CV services *****')
        out = self.help.exec(f'docker exec cvdnc_cnt bash /app/setup.sh')
        if out.exit_code != 0:
            raise Exception(f'Failed to register controller inside the container [{out.output}]')
        self.log.info('Successfully registered the controller [%s]', out.formatted_output)
        time.sleep(10)
