# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
# --------------------------------------------------------------------------
""""Main file for executing this test case
TestCase is the only class defined in this file.
TestCase: Class for executing this test case
TestCase:
    __init__()      --  initialize TestCase class
    setup()         --  initial settings for the test case
    run()           --  run function of this test case
"""

import time
from Server.Network.networkhelper import NetworkHelper
from Server.Network.certificatehelper import CertificateHelper
from AutomationUtils.machine import Machine
from AutomationUtils.cvtestcase import CVTestCase


class TestCase(CVTestCase):
    """
    [Network & Firewall] : Certificate Validation
    """

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = "[Network & Firewall] : Certificate Validation"
        self.product = self.products_list.COMMSERVER
        self.show_to_user = True
        self.tcinputs = {
            "NetworkClient": None,
            "clientMachineHostname": None,
            "clientMachineUsername": None,
            "clientMachinePassword": None
        }
        self._cert = None
        self.client = None
        self._network = None
        self.cl_obj = None
        self.cl_machine = None

    def setup(self):
        """Setup function of this test case"""
        self._cert = CertificateHelper(self)
        self._network = NetworkHelper(self)
        self.client = self.tcinputs["NetworkClient"]
        self.cl_obj = self.commcell.clients.get(self.client)
        self.cl_machine = Machine(
            machine_name=self.tcinputs["clientMachineHostname"],
            username=self.tcinputs["clientMachineUsername"],
            password=self.tcinputs["clientMachinePassword"]
        )

    def run(self):
        """Run function of this test case"""
        self.log.info("[+] PHASE 1: Basic certificate operation[+]")
        self.log.info(f"Revoke all active certifcate for {self.client}")
        cert_ids = self._cert.revoke([self.client])
        self._cert.check_crl(cert_ids)

        self.log.info(f"Renew the certificate for {self.client}")
        self._cert.renew([self.client])
        self.commcell.refresh()
        time.sleep(300)
        self._network.serverbase.check_client_readiness([self.client])

        self.log.info("Deleting the certificate folder in client.")
        self._cert.revoke([self.client])
        loc = self.cl_obj.install_directory + "\\Base\\certificates"
        op = self.cl_machine.execute_command(fr'Remove-Item "{loc}" -Recurse')
        self.log.info(f"Out of command: {op.output}")
        self.log.info("Restarting services on client.")
        self.cl_machine.start_all_cv_services()
        time.sleep(300)
        self._network.serverbase.check_client_readiness([self.client])

        self.log.info("[+] PHASE 2: Modifying certificate rotation period[+]P")
        try:
            self.log.info("changing client certificate rotation period to 10 month")
            self._cert.client_certificate_rotation(10)

            self.log.info("changing CA certificate rotation period to 1 year")
            self._cert.ca_certificate_rotation(2)
        except Exception as e:
            self.log.info("Failed to update certificate rotation period")
            raise Exception(str(e))

        self.log.info("[+] PHASE 3: Renew & Revoke CA certificate")
        self.log.info("Fetching the latest CA cert id")
        self.csdb.execute("SELECT MAX(certId) FROM App_CACerts;")
        ca_cert_id = int(self.csdb.fetch_one_row()[0])
        self.log.info("Performing renew operation on CA")
        self._cert.certificate.renew([ca_cert_id])
        time.sleep(300)
        self.log.info("Fetching the latest CA cert id")
        self.csdb.execute("SELECT MAX(certId) FROM App_CACerts;")
        new_ca_cert_id = int(self.csdb.fetch_one_row()[0])
        if not (new_ca_cert_id > ca_cert_id):
            raise Exception("CA certificate does not get renewed")

        self.csdb.execute(f"SELECT id FROM APP_Client WHERE name = '{self.client}'")
        client_id = int(self.csdb.fetch_one_row()[0])

        self.log.info("Checking if client get new certificate which is signed by renewed CA")
        self.csdb.execute(f"SELECT MAX(authority) FROM App_ClientCerts WHERE clientId = {client_id};")
        authority = int(self.csdb.fetch_one_row()[0])
        if authority != new_ca_cert_id:
            raise Exception("Client does not have the certificate signed by renewed CA")

        self.log.info("Renew client certificate & checking if its get signed by new CA")
        self._cert.renew([self.client])
        self.csdb.execute(f"SELECT MAX(authority) FROM App_ClientCerts WHERE clientId = {client_id};")
        authority = int(self.csdb.fetch_one_row()[0])

        if authority != new_ca_cert_id:
            raise Exception("Client does not have the certificate signed by renewed CA")

        self._cert.certificate.revoke([ca_cert_id])
        self.log.info("[+]>>> SUCCESSFUL <<<[+]")
