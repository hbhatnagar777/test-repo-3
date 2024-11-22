
# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""
This module is used to handle outlook owa operations from browse
"""
from time import sleep

from selenium.webdriver.common.by import By

from AutomationUtils import logger
from Web.AdminConsole.AD.page_ops import check_element, page_ops, check_title, right_click

from Application.AD.exceptions import ADException

log_ = logger.get_log()

def wc_preview_email(driver):
    """
    check web cosnole preview page
    """
    email_ = {}
    emailfieldmapper = {"from" : "fromVal",
                        "date" : "SentTime",
                        "to" : "toVal",
                        "cc" : "ccval",
                        "bcc" : "bccVal"}
    header_ = check_element(driver, "id", "header")
    log_.debug(f"preview email header is {header_}")
    content_ = check_element(driver, "id", "content")
    emailcontent_ = check_element(content_, "id", "emailcontent")
    emailheader_ = check_element(emailcontent_, "id", "emailTopHeader")
    # get email subject
    try:
        email_['subject'] = check_element(emailheader_, "class",
                                          "previewSubjectDiv").text.\
                                          split("Subject:")[1].strip()
    except:
        email_['subject'] = None

    # get email common feilds
    for _ in emailfieldmapper:
        try:
            email_[_] = check_element(emailheader_, "id",
                                      emailfieldmapper[_]).text.strip()
        except:
            email_[_] = None


    # get email body
    try:
        body_iframe = check_element(emailcontent_, "id", "emailPreviewIframe")
        driver.switch_to.frame(body_iframe)
        email_['body'] = check_element(driver, "tag", "HTML").get_attribute("innerHTML")
        driver.switch_to.default_content()
    except:
        email_['body'] = None

    # get email attachment
    attachments_ = check_element(driver, "id", "Attachment")
    attafiles = attachments_.find_elements(By.ID, "AttachDiv")
    if len(attafiles) == 0:
        email_['attachment'] = None
    else:
        att_files = {}
        for _ in attafiles:
            filename = _.text
            log_.debug(f"get the following attchment {filename}")
            link_ = check_element(_, "tag", "a").get_attribute("href")
            driver.get(link_)
            att_files[_] = link_
        email_['attachment'] = att_files
    return email_

def email_compare(src, des):
    """
    compare the emails between original and quick look preview
    """
    result = True
    fields = ['subject', "from", "to", "cc", "date"]
    nomatch_fields = []
    for _ in fields:
        if isinstance(src[_], str) and isinstance(des[_], str):
            if src[_].strip() == des[_].strip():
                log_.debug(f"the email preview {_} field have same value {src[_]}")
            else:
                log_.warning(f"""
field {_} is not match, source email is {src[_]}, des email is {des[_]}""")
                nomatch_fields.append(_)
        else:
            if src[_] == des[_]:
                log_.debug(f"the email preivew {_} field have same {src[_]}")
            else:
                log_.warning(f"""
field {_} is not match, source email is {src[_]}, des email is {des[_]}""")
                nomatch_fields.append(_)
    # check email body
    log_.debug(f"source email body is {src['body']}")
    log_.debug(f"destination email body is {des['body']}")
    if nomatch_fields != ["to", 'date']:
        result = False
    return result, nomatch_fields

def quicklink_removeexchange(link):
    """
    This will remove exchange server from the quick link url
    """
    url = link.split("URL=")[1]
    url = url.replace("%3a", ":").replace("%2f", "/").\
                replace("%3f", "?").replace("%26", "&").\
                replace("%3d", "=")
    return url

class OutlookOWA():
    """
    This class will used to get email information from Exchange owa page
    """

    def __init__(self, driver, **owainfo):
        """
        initial class
        Args:
            driver       object      selenium web driver
            owainfo      dict        owa access information, inlcude
                                url : url to access owa
                                username : login user name
                                password : password
        """
        self.driver_ = driver
        self.owainfo = owainfo
        self.log = logger.get_log()

    def login(self, skip=False):
        """
        login the owa page
        Args:
        Returns:
        Exceptions:
            101    can't open he owa page
            102    can't login the owa page
        """
        self.log.info("start to login outlook owa page")
        self.log.debug(f"open the owa url {self.owainfo['url']}")
        self.driver_.get(self.owainfo["url"])
        self.log.debug(f"wait the page loading")
        sleep(10)
        if check_element(self.driver_, "id", "username"):
            if skip:
                self.log.debug("maybe the session is time out, check the screenshot")
                skip = False

        if skip:
            self.log.debug("outlook owa already opened before, skip login")
        else:
            if not check_title(self.driver_, "Outlook Web App"):
                raise ADException("owa", "101",
                                  f"here is the owa url {self.owainfo['url']}")
            webpageinput_ = [{"etype" : "id", "evalue" : "username",
                              "input" : self.owainfo['username']},
                             {"etype" : "id", "evalue" : "password",
                              "input" : self.owainfo['password']},
                             {"etype" : "tag", "evalue" : "input",
                              "eargs" : {"attribute" : {"type" : "submit"}},
                              "action" : "click"}]
            self.log.debug("start to login the owa page")
            page_ops(self.driver_, webpageinput_)
            self.log.debug("wait the login page")
            # may need additional handle for the first time login page
            sleep(5)
            if not check_title(self.driver_, "Outlook Web App", match="include"):
                raise ADException("owa", "102",
                                  f"""
login user name is {self.owainfo['username']}, password is {self.owainfo['password']}""")
            self.log.info("login the user owa page")

    def current_page_check(self, sections='emailpreview'):
        """
        check current owa page content
        Args:
            sections    list/string    email sections need to check, include
                                        loginuser, userinboxcount, userfolders,
                                        emailslist, emailpreview
        Returns:
            returnvalues     dict/obj    return dict based on secions.
                                        if there is only one section, just return the obj
        Exceptions:
            201    list page subject and from is not match
        """
        if isinstance(sections, str):
            if sections == "all":
                sections = ["loginuser", "userinboxcount", "userfolders",
                            "emailslist", "emailpreview"]
            else:
                sections = [sections]
        returnvalues = {}
        if "loginuser" in sections:
            self.log.debug("start to check individual email sections")
            self.log.debug("check login users")
            loginuser_ = check_element(self.driver_, "id", "aUserTile")
            self.log.debug(f"Login user title is {loginuser_.text}")
            returnvalues["loginuser"] = loginuser_.text
        if "userinboxcount" in sections:
            self.log.debug("check mail and inbox count")
            alertbar_ = check_element(self.driver_, "id", "divAlertBarContainer")
            emailininbox = int(alertbar_.text.split('Mail')[1].\
                               split('Inbox')[1].split('Items')[0].strip())
            self.log.debug(f"There are {emailininbox} emails in mail inbox")
            returnvalues['userinboxcount'] = emailininbox
        if "userfolders" in sections:
            self.log.debug("check email folders")
            mailtree_ = check_element(self.driver_, "id", "mailtree")
            all_links = mailtree_.find_elements(By.TAG_NAME, "a")
            emailfolders = {}
            for _ in all_links[1:]:
                foldername = _.text.split("(")
                if len(foldername) > 1:
                    foldername = "(".join(foldername[:-1]).strip()
                else:
                    foldername = _.text
                emailfolders[foldername] = _
            self.log.debug(f"there are {len(all_links)} folders. There are {emailfolders.keys()}")
            returnvalues['userfolders'] = emailfolders
        if "emailslist" in sections:
            self.log.debug("check emails")
            emailpanel_ = check_element(self.driver_, "id", "divMainView")
            emaillistpanel_ = check_element(emailpanel_, "class", "lvContainer")
            emaillistview_ = check_element(emaillistpanel_, "id", "divViewport")
            emailsubject = emaillistview_.find_elements(By.ID, "vr")
            emailfrom = emaillistview_.find_elements(By.ID, 'sr')
            if len(emailsubject) != len(emailfrom):
                raise ADException('owa', "201", f"""
found {len(emailsubject)} subjects and {len(emailfrom)} from""")
            #self.log.debug(len(emailsubject), len(emailfrom))
            returnvalues["emailslist"] = emailsubject
        if "emailpreview" in sections:
            self.log.debug("check email preview")
            previewemail = {}
            emailpanel_ = check_element(self.driver_, "id", "divMainView")
            emailpreviewpanel_ = check_element(emailpanel_, "class", "lvRPContainer")
            emailpreviewtopic_ = check_element(emailpreviewpanel_, "id", "divConvTopic")
            previewemail['subject'] = emailpreviewtopic_.text
            emailpreviewbody_ = check_element(emailpreviewpanel_, "id", "divItmPrts")
            previewemail['from'] = check_element(emailpreviewbody_, "id", "spnFrom").text.strip()
            try:
                previewemail['to'] = check_element(emailpreviewbody_, "id", "divTo").text.strip()
            except:
                previewemail['to'] = None
            try:
                previewemail['cc'] = check_element(emailpreviewbody_, "id", "divCc").text.strip()
            except:
                previewemail['cc'] = None
            previewemail['date'] = check_element(emailpreviewbody_, "id", "spnSent").text.strip()
            previewbody_ = check_element(emailpreviewbody_, "id", "divBdy")
            #check attachment inside <div id="divWellAttach"
            self.log.debug("start to check quicklook link")
            quicklink = check_element(previewbody_, "linktext", "Quick Look")
            if quicklink:
                self.log.debug("found the quicklink url in the eamil")
                previewemail["quicklook"] = quicklink.get_attribute('href')
            else:
                self.log.debug("no quick look link found")
                previewemail['quicklook'] = None
            previewemail['body'] = previewbody_.get_attribute("innerHTML")
            returnvalues['emailpreview'] = previewemail
            self.log.debug(f"the email preview information is {previewemail}")


        if len(sections) == 1:
            returnvalues = returnvalues[sections[0]]
        return returnvalues

    def getemailslist(self):
        """
        get all emails from current folder
        Args:
        Returns:
            allemails    list    email element objects
        Exceptions:

        todo:
            need to hanlde if the folder is empty
        """
        self.log.debug("start to get more emails")
        # this is for the inbox only, need to check the other folders
        count_ = self.current_page_check("userinboxcount")
        self.log.debug(f"There are {count_} email in inbox")
        emailpanel_ = check_element(self.driver_, "id", "divMainView")
        scrollbar_ = check_element(emailpanel_, "id", "divScrollbar")
        allemails = []
        clickpoint = 0
        lastemailcount = 0
        loop_ = 0
        self.log.debug(f"check the first email in the page")
        preview_ = self.current_page_check()
        allemails.append(preview_)
        self.log.debug("")
        while len(allemails) < count_:
            emails = self.current_page_check("emailslist")
            emailcount = len(emails)
            self.log.debug(f'found {emailcount} email link in current page')
            if emailcount < lastemailcount:
                self.log.debug("see a new page count started, let check")
                clickpoint -= lastemailcount-emailcount
            i = clickpoint

            for email_ in emails[clickpoint+1:]:
                # if subject is empty, need handle
                i += 1
                try:
                    email_.click()
                    sleep(2)
                    if email_.text != "":
                        self.log.debug(f'start to check {i+1} emails')
                        preview_ = self.current_page_check()
                        allemails.append(preview_)
                        clickpoint = i
                except:
                    self.log.debug("click for next page")
                    scrollbar_.click()
                    sleep(3)
                    break
            lastemailcount = emailcount
            loop_ += 1
            self.log.debug(f"this is the {loop_} click loop, total {len(allemails)} emails")
            # default value is  int(count_/10), use 3 in this case for demo
            if loop_ > int(count_/10) and count_ > 10:
                self.log.debug(f"""
something wrong, there should be {count_} emails, 
get {len(allemails)} emails after {loop_} click loop""")
                break
        self.log.debug(f" collect total {len(allemails)} emails from current folder")
        return allemails

    def folderclean(self, folder="Inbox"):
        """
        clean owa folder emails
        Args:
            folder     string    folder name to operation, default is inbox
        Returns:
        Exceptions:
        """
        if folder != "Inbox":
            # change the folder
            pass
        emaillistviews_ = check_element(self.driver_, "id", "divViewport")
        emailsubject = emaillistviews_.find_elements(By.ID, "vr")
        self.log.debug(f"get list from {len(emailsubject)}")
        for _ in emailsubject:
            self.log.debug(f"will delete the email with subject {_.text}")
            right_click(self.driver_, _)
            sleep(1)
            check_element(self.driver_, "tag", "div",
                          **{"attribute" : {"cmd": "delete"}}).click()
