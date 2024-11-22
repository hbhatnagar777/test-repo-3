import os
import time
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import subprocess
import graph_analysis as graph
import json
import base64
from tool_helper import *
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))))
from cvpysdk.commcell import Commcell
from cvpysdk.security.user import Users
'''
Please run this python file using the command 'python locust_tool.py' in the terminal.
It will ask the hostname (eg: #####), users (eg: 3) and spawn rate (eg: 1) and email-id(s) 
(eg: v@commvault.com, s@commvault.com).
It then ask the username and password to access the commcell and begin execution.
It will then give the list of apis that can be executed and prompt you to provide the numbers
corresponding to the api. Enter the api numbers in the sequence in which they must be executed.
Enter stop when you have provided sufficient number of APIs. 
Reports will be sent to email provided. It will contain median time of execution, successful requests
and failed requests.
'''

# Create a temporary json file to store variables for locust execution
jsonfile = open("variable.json", "r")
variables = json.load(jsonfile)
jsonfile.close()

load_unload('w',variables)

# gets the present date and time
cmd = str(time.asctime(time.localtime(time.time()))).replace(" ", "_").replace(":", "_")

# User inputs for headless execution of locust
hostname = str(input("Hostname: "))
threads = str(input("Number of threads: "))
numThreads = str(input("Spawn rate: "))
minutes = str(input("Enter Run Time in Minutes: "))
seconds = int(minutes)*60
mailList = input("Enter the email addresses to send report to: ").split(", ")

# Storing username and password for logging into the commcell
variables = load_unload('r')
variables["username"] = input("Enter username: ")
variables["password"] = input("Enter password: ")
commcell_object = Commcell(hostname, variables["username"], variables["password"])

check = Users(commcell_object)

for i in range(1, int(threads)+1):
    if Users.has_user(check,"locust_user"+str(i)):
        username=Users.get(check,"locust_user"+str(i))
        user_object_split = str(username).split('"')
        variables["locust_user_list"].append(user_object_split[-2])
        variables["locust_user_id"][user_object_split[-2]] = username.user_id
    else:
        username = Users.add(check, "locust_user"+str(i), "locust"+str(i)+"@cv.com", password=variables["password"],
                                local_usergroups=["master"])
        user_object_split = str(username).split('"')
        variables["locust_user_list"].append(user_object_split[-2])
        variables["locust_user_id"][user_object_split[-2]] = username.user_id
load_unload('w', variables)

# Stores all the generated reports to folder CSV_Reports
path = os.getcwd()
if not os.path.exists('CSV_Reports'):
    os.makedirs('CSV_Reports')
os.system('cd CSV_Reports & mkdir '+str(cmd)+' & cd ..')

# get automation path
process = subprocess.Popen('locust -f \"tool_executable.py\" --csv='+cmd+' --headless --host http://'+hostname+' -u '+threads+' -r '+numThreads+' --run-time '+minutes+'m')
time.sleep(int(seconds))
process.kill()

graph.generate_avg(str(cmd)+"_stats.csv",str(cmd)+"_avg.png")
graph.generate_med(str(cmd)+"_stats.csv",str(cmd)+"_med.png")
graph.generate_req(str(cmd)+"_stats.csv",str(cmd)+"_req.png")
graph.generate_fail(str(cmd)+"_stats.csv",str(cmd)+"_fail.png")

time.sleep(2)
os.system('move *.csv CSV_Reports\\'+str(cmd))
os.system('move '+str(cmd)+'*.png CSV_Reports\\'+str(cmd))

time.sleep(10)

# Email is generated consisting of the CSV stats report and charts
fromaddr = "locust@commvault.com"
toaddr = mailList

msg = MIMEMultipart()

msg['From'] = fromaddr
msg['To'] = ", ".join(toaddr)
msg['Subject'] = "Locust Testing"

body = '''Hi,

Please find the report for the latest locust run.

Thank you!
'''

msg.attach(MIMEText(body, 'plain'))

filename = str(cmd)+"_stats.csv"
avgname = str(cmd)+"_avg.png"
medname = str(cmd)+"_med.png"
reqname = str(cmd)+"_req.png"
failname = str(cmd)+"_fail.png"
file_list = [filename, avgname,medname,reqname,failname]

for f in file_list:

    attachment = open(str(path)+'\\CSV_Reports\\'+str(cmd)+'\\'+str(f), "rb")
    part = MIMEBase('application', 'octet-stream')
    part.set_payload(attachment.read())
    encoders.encode_base64(part)
    part.add_header('Content-Disposition', "attachment; filename= %s" % f)
    msg.attach(part)

server = smtplib.SMTP("mail.commvault.com")
text = msg.as_string()
server.sendmail(fromaddr, toaddr, text)
server.quit()

variables = load_unload('r')

if int(variables["flag"]) == 1:
    process = subprocess.Popen('locust -f \"tool_executable.py\" --headless --host http://'+hostname+' -u '+threads+' -r '+numThreads+' --run-time '+minutes+'m')
    time.sleep(int(seconds))
    process.kill()

commcell_object = Commcell(hostname, variables["username"], variables["password"])
check = Users(commcell_object)
for i in range(len(variables["locust_user_list"])):
    username = Users.delete(check, variables["locust_user_list"][i],new_user="admin")


os.remove("temp_var.json")

