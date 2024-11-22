from cvpysdk.commcell import Commcell

cc = Commcell(webconsole_hostname = "harshcs.testlab.commvault.com", commcell_username = "admin", commcell_password = "Commvault!12")

print(cc.clients)

client = cc.clients.get("test-gcp-1")
agent = client.agents.get("Virtual Server")

print(agent.instances)
instance = agent.instances.get("Google Cloud Platform")

print(instance.backupsets)

backupset = instance.backupsets.get("defaultBackupSet")
sc = backupset.subclients.get("active-vm-group")

