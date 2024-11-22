from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from time import sleep
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage

import json
with open(r'emails.json') as json_file:
    data = json.load(json_file)
    
service_pack = data['service_pack']
email_cc = data['email_cc']
print(f'Email cc: {email_cc}')
url = data['url']

option = webdriver.ChromeOptions()
option.add_argument('headless')
option.add_argument("window-size=1920,1080")
driver = webdriver.Chrome(options=option)
driver.maximize_window()
driver.get(url)

def take_screenshot():
    xpath = "//*[contains(@class, 'collapse-down')]//ancestor::div[contains(@ng-repeat, 'group')]"
    element = driver.find_elements(By.XPATH, xpath)[-1] # pick the last opened dropdown    
    desired_y = (element.size['height'] / 8) + element.location['y'] # bring up the list to the top
    current_y = (driver.execute_script('return window.innerHeight') / 2) + driver.execute_script('return window.pageYOffset')
    scroll_y_by = desired_y - current_y
    driver.execute_script("window.scrollBy(0, arguments[0]);", scroll_y_by)
    element.screenshot('Screenshot.png')

def send_screenshot(email_id, pendingcases):
    fromaddr = data["sender_email_adress"]
    toaddr = [email_id]
    msg = MIMEMultipart()

    msg['From'] = fromaddr
    msg['To'] = ", ".join(toaddr)
    msg['Cc'] = ", ".join(email_cc)
    msg['Subject'] = f"Attention! You have {pendingcases} test cases pending for {service_pack}"

    email_template = r"""
    <!DOCTYPE html>
    <html lang="en" lang="en">
        <head>
            <meta content="text/html; charset=" />
            <style>
                img {
                    width: auto;
                    height: auto;
                }
            </style>
        </head>
        <body>
            <h2 style="color:red;">Please check the failures/No Run. Repeat defaulters will be reached out for Root Cause. All cases should be part of scheduled runs</h2>
            <img src="cid:Screenshot.png" alt="Pending Testcase">

            <p style="color:green;">Thank you!</p>
        </body>
    </html>
    """
    msg.attach(MIMEText(email_template, 'html'))
    
    fp = open('Screenshot.png', 'rb')
    msp_image = MIMEImage(fp.read())
    fp.close()
    msp_image.add_header('Content-ID', '<Screenshot.png>')
    msg.attach(msp_image)

    server = smtplib.SMTP("mail.commvault.com")
    server.sendmail(msg['From'], toaddr + email_cc, msg.as_string())
    server.quit()

user_and_pending_count = dict()
xpath = "//*[contains(@class, 'list-group-item ng-binding')]" # list of users xpath
i = 1
WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.XPATH, f"({xpath})[{i}]"))) # waiting for first user testcase details to load up
sleep(10)
for element in driver.find_elements(By.XPATH, xpath):
    try:
        temp = element.text.strip().split(' ', 1)[1].rsplit(' ', 1) # username and failure count
        user_and_pending_count[temp[0]] = temp[1].lstrip('[').rstrip(']') 
        WebDriverWait(driver, 30).until(EC.element_to_be_clickable((By.XPATH, f"({xpath})[{i}]"))) # wait for dropdown to be clickable  
        element.click() # Index wise open list of testcase for user, one after another
        sleep(5)
        take_screenshot()
        email_id = data[temp[0]]
        print(f'Sending an email to: {email_id}')
        send_screenshot(email_id= email_id, pendingcases= user_and_pending_count[temp[0]])
        WebDriverWait(driver, 30).until(EC.element_to_be_clickable((By.XPATH, f"({xpath})[{i}]")))
        element.click() # close list
    except Exception as e:
        print(e)
    i += 1
driver.quit()