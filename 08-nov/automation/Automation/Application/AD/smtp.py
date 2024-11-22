# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------
"""
This module is use to send general emails with smtp library
"""
import mimetypes
import os
import random
import string
import codecs
import glob

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.audio import MIMEAudio
from email.mime.base import MIMEBase
from email.mime.image import MIMEImage
from email.mime.application import MIMEApplication
from email import encoders
import smtplib

from Application.AD.baselibs import tc
from AutomationUtils import logger
from .adconstants import WEBFIlENAME, STRINGTYPE

log_ = logger.get_log()
def get_file_with_group(folder,extlist, group):
    """ 
    get file form local folder and group it 
    Args:
        folder    string local folder with files
        extlist    list    extneion whic will filter the file list
        group    num    group the files
    Returns:
        filegroup     list     file name in each group
    Exceptions:
    """
    if not folder[-1] in ["\\", "/"]:
        folder = folder+"/"
    log_.debug(f"will get all files in {folder}")
    files = [os.path.join(dp, f) for dp, dn, filenames in os.walk(folder) for f in filenames]
    log_.debug(f"there are total {len(files)} files in folder {folder}")
    if extlist:
        files = [_ for _ in files if _.split(".")[1] in extlist]
        log_.debug(f"get the following files with extion {extlist}:\n{files}")

    left = len(files)%group
    filegroup = list(zip(*(iter(files),)*group))
    filegroup.append(files[(len(files)-left):])
    log_.debug(f"here is the filegroup {filegroup}")
    return filegroup

class SmtpOps():
    """
    This is general smtp library to send email through smtp server
    """

    def __init__(self, servername, username=None, password=None):
        """
        initial class
        Args:
            servername    string    smtp server name
            username    string    username to connect to smtp server (optional)
            password    string    password to connect to smpt server (optinal)
        Returns:
        Exceptions:
        """
        self.server = servername
        self.user = username
        self.passwd = password
        self.from_ = "anyone@anywhere.com"
        self.ptime = tc()
        self.log = logger.get_log()

    def email_ts1k(self, toaddrs, fromaddr=None):
        """
        send 1k email
        Args:
            toaddr    string     to addresses
            fromaddr    string    email address where the email come from (optional)
        Returns:
            emailinfo     dict     an email defined in the dict
        Exceptions:
        """
        timestamp = tc()
        subject = "Timestamp::%s" % str(timestamp)
        body = "Email is generated from Python script.\nTime stamp is %s" % str(timestamp)
        if not fromaddr:
            fromaddr = self.from_
        emails, msg = self._email_simple_builder(toaddrs, fromaddr, subject, body)
        self._smtp_send(msg, emails, fromaddr)
        emailinfo = {}
        emailinfo['Subject'] = subject
        emailinfo['body'] = body
        emailinfo['msg'] = msg
        emailinfo['from'] = fromaddr
        emailinfo['emails'] = emails
        emailinfo['ts'] = str(timestamp)
        return emailinfo

    def email_mimeemail(self, toaddrs, fromaddr=None, subject=None,
                        body=None, filenames=None, timestamp=True):
        """
        send mime email
        Args:
            toaddr    string     to addresses
            fromaddr    string    email address where the email come from (optional)
            subject     string    email subject
            body    string    emali body string
            filename     string    file to attached
            timestamp    boolean    add time stamp to the email or not
        Returns:
        Exceptions:
        """
        if not fromaddr:
            fromaddr = self.from_
    
        if filenames is not None:
            emails, msg, timestamp = \
            self._email_mime_builder_attach(toaddrs, fromaddr, subject=subject,
                                            body=body, filenames=filenames,
                                            timestamp=timestamp)
        else:
            emails, msg, timestamp = \
            self._email_mime_builder(toaddrs, fromaddr, subject=subject,
                                     body=body, timestamp=timestamp)
        self._smtp_send(msg.as_string(), emails, fromaddr)
        emailinfo = {}
        emailinfo['Subject'] = subject
        emailinfo['body'] = None
        emailinfo['msg'] = msg.as_string()
        emailinfo['from'] = fromaddr
        emailinfo['emails'] = emails
        emailinfo['ts'] = timestamp
        return emailinfo

    def email_folder2email(self, toaddrs, folder, fromaddr= None,
                           extlist=None, group=5, atta=False):
        """
        send email with files in a folder
        Args:
            toaddr    string     to addresses
            folder     stirng    the local folder where the files stored
            extlist    list    which file exentions will be send
            group    num    each individual email will include group count files
            atta    boolean    send as a attachment or embend email
        Returns:
        Exceptions:
        """
        self.log.debug(f"will send all files in folder {folder} to {toaddrs}")
        filegroup = get_file_with_group(folder, extlist, group)
        filesizes = []
        emaillist = []

        for i in range(len(filegroup)):
            timestamp = tc()
            if not atta:
                extlist = WEBFIlENAME
                self.log.debug("send email with embended")
                body, filesize = self.__webfile2mimebody(filegroup[i], extlist)
                subject = "Email: Folder %s convert to HTML at %s" % (folder, str(timestamp))
                filenames = None
            else:
                body, filesize = self.__file2attach(filegroup[i])
                self.log.debug("send email with attachment")
                subject = "Email: Folder %s convert to attachment at %s" % (folder, str(timestamp))
                filenames = filegroup[i]
            filesizes += filesize
            if len(filesize) != len(filegroup[i]):
                self.log.debug(f"Current there are {filegroup[i]}")
            emaillist.append((subject, filesize))
            self.email_mimeemail(toaddrs, fromaddr, subject=subject, body=body,
                                 filenames=filenames)
        self.log.debug("create folder email report")
        reportstring = self.__folder_report(filegroup, filesizes, emaillist,
                                            group, atta)
        if atta:
            subject = "Email: Folder %s convert to attachment Report" % folder
        else:
            subject = "Email: Folder %s convert to HTML Report" % folder
        self.email_mimeemail(toaddrs, subject=subject,
                             body=[(reportstring, "plain")])
    def _smtp_send(self, msg, toaddrs, fromaddr):
        """
        send email with smtp library
        Args:
            msg    string    email message
            toaddr    string     to addresses
            fromaddr    string    email address where the email come from (optional)
        Returns:
        Exceptions:
        """
        smtp_ins = smtplib.SMTP(self.server)
        retcode = smtp_ins.sendmail(fromaddr, toaddrs, msg)
        if retcode != {}:
            self.log.debug(f"return code is not empty: {retcode}")
        return retcode

    def _email_simple_builder(self, toaddrs, fromaddr, subject=None, body=None):
        """
        build email based on dict
        Args:
            toaddr    string     to addresses
            fromaddr    string    email address where the email come from
            subject     stirng    email subject
            body    stirng    email body
        Returns:
        Exceptions:
        """
        msgstring = ""
        timestamp = tc()
        if not subject:
            if "Timestamp::" in subject:
                msgstring = "Subject:%s\n" % (subject)
            else:
                msgstring = "Subject:%s Timestamp::%s\n" % (subject, str(timestamp))
        else:
            msgstring = f"Subject:Timestamp::{str(timestamp)}\n"
        
        if body:
            msgstring = "%s\n%s" % (msgstring, body)
        emails, rdict, tostring = self.__recipient_builder(toaddrs)

        msg = ("From: %s\r\n%s%s" % (fromaddr, tostring, msgstring))
        return emails, msg

    def _email_mime_builder(self, toaddrs, fromaddr, subject=None, body=None, timestamp=True):
        """
        build mime email based on dict
        Args:
            toaddr    string     to addresses
            fromaddr    string    email address where the email come from
            subject     stirng    email subject
            body    stirng    email body
            timestamp    boolean    include Time stamp or not
        Returns:
        Excpetoins:
        """
        msg = MIMEMultipart()
        msg['From'] = fromaddr
        emails, rdict, _ = self.__recipient_builder(toaddrs)
        msg['To'] = ', '.join(rdict['To'])
        msg['CC'] = ', '.join(rdict['CC'])
        msg['BCC'] = ', '.join(rdict['BCC'])

        if subject:
            if "timestamp::" in subject:
                msg['Subject'] = subject
                timestamp = subject.split("timestamp::")[1]
            else:
                timestamp = tc()
                if timestamp:
                    msg['Subject'] = "%s timestamp::%s" % (subject, str(timestamp))
                else:
                    msg['Subject'] = subject
        else:
            timestamp = tc()
            msg['Subject'] = "Email:Mime email at timestamp::%s" % str(timestamp)

        if body:
            if isinstance(body, str):
                text = MIMEText(body, 'plain')
                msg.attach(text)
            else:
                for entry in body:
                    text = MIMEText(entry[0], entry[1])
                    msg.attach(text)
        else:
            text = MIMEText("This is Mime email from python script", 'plain')
            msg.attach(text)
        return emails, msg, str(timestamp)

    def _email_mime_builder_attach(self, toaddrs, fromaddr, subject=None,
                                   body=None, filenames=None, timestamp=True):
        """
        build mime email based on dict with attachment
        Args:
             toaddr    string     to addresses
            fromaddr    string    email address where the email come from
            subject     stirng    email subject
            body    stirng    email body
            timestamp    boolean    include Time stamp or not
            filenames     list    attachmetns files
        """
        self.log.debug("create mime body with attachment")
        msg = MIMEMultipart()
        msg['From'] = fromaddr
        emails, rdict, tostring = self.__recipient_builder(toaddrs)
        msg['To'] = ', '.join(rdict['To'])
        msg['CC'] = ', '.join(rdict['CC'])
        msg['BCC'] = ', '.join(rdict['BCC'])

        if subject:
            if "timestamp::" in subject:
                msg['Subject'] = subject
                timestamp = subject.split("timestamp::")[1]
            else:
                timestamp = tc()
                if timestamp:
                    msg['Subject'] = "%s timestamp::%s" % (subject, str(timestamp))
                else:
                    msg['Subject'] = subject
        else:
            timestamp = tc()
            msg['Subject'] = "Email:Mime email at timestamp::%s" % str(timestamp)
        if body:
            for entry in body:
                text = MIMEText(entry[0], entry[1])
                msg.attach(text)
        else:
            text = MIMEText("This is Mime email from python script", 'plain')
            msg.attach(text)

        if filenames:
            for filename in filenames:
            # Guess the content type based on the file's extension.  Encoding
            # will be ignored, although we should check for simple things like
            # gzip'd or compressed files.
                ctype, encoding = mimetypes.guess_type(filename)
                if not ctype or encoding:
            # No guess could be made, or the file is encoded (compressed), so
            # use a generic bag-of-bits type.
                    ctype = 'application/octet-stream'
                maintype, subtype = ctype.split('/', 1)
                if maintype not in ['text', 'image', 'audio', 'application']:
                    pass
                if maintype == 'text':
                    with open(filename, 'r', encoding='utf-8') as filehandle:
            # Note: we should handle calculating the charsetzZz
                        attachment = MIMEText(filehandle.read(), '_subtype=subtype')
                elif maintype == 'image':
                    with open(filename, 'rb') as filehandle:
                        attachment = MIMEImage(filehandle.read(), _subtype=subtype)
                elif maintype == 'audio':
                    with open(filename, 'rb') as filehandle:
                        attachment = MIMEAudio(filehandle.read(), _subtype=subtype)
                elif maintype == 'application':
                    with open(filename, 'rb') as filehandle:
                        attachment = MIMEApplication(filehandle.read(), _subtype=subtype)
                else:
                    with open(filename, 'rb') as filehandle:
                        attachment = MIMEBase(filehandle.read(), subtype)
            # Encode the payload using Base64
                    encoders.encode_base64(attachment)
                attachment.add_header("Content-Disposition", "attachment", filename=filename)
                msg.attach(attachment)
        return emails, msg, str(timestamp)

    def __folder_report(self, filegroup, filesizes, emaillist, group, atta):
        """
        generate file report based on the files in the folder
        Args:
            filegroup    list    flies in each individual email
            filesize    num     size of files
            emaillist    list    emails sent
            group    num    each individual email will include group count files
            atta    boolean    send as a attachment or embend email
        Returns:
            reportstring    string    detail of the report
        Exceptions:
        """
        totalsize = 0
        for filesize in filesizes:
            totalsize += filesize[1]
        if atta:
            reportstring = """
There are total %s emails sent out.\n Total %s files attached as attachment.\n Total file size is %s
""" % (len(filegroup)+1, len(filesizes), totalsize)
        else:
            reportstring = """
There are total %s emails sent out.\n Total %s files attached as html.\n Total file size is %s
""" % (len(filegroup)+1, len(filesizes), totalsize)

        for entry in emaillist:
            filesizestring = ""
            if group != 1:
                for filename in entry[1]:
                    filesizestring = "%s%s\t\t%s\n" % (filesizestring, filename[0],
                                                       filename[1])
            else:
                filesizestring = "%s%s\t\t%s\n" % (filesizestring, entry[1][0][0],
                                                   entry[1][0][1])
            linestring = "\n\n%s\n\n%s" % (entry[0], filesizestring)
            reportstring += linestring
        return reportstring

    def __webfile2mimebody(self, files, extlist):
        """
        conver web file to mime body
        Args:
            files    list    filename list
            extlist    list    extensions will use
        Returns:
            mimecontent    string    mimecontent with files
            filesize    num    size of the files
        Exceptions:
        """
        mimecontent = []
        filesize = []
        for filename in files:
            if filename.split('.')[-1].lower()  in extlist:
                with open(filename, 'r') as f: fc = f.read()
                fileline = "%s\n%s\n%s\n" % ("*"*40, filename, "*"*40)
                mimecontent.append((fileline, "plain"))
                mimecontent.append((fc, 'html'))
                filesize.append((filename, len(fc)))
            else:
                self.log.debug("filename is %s" % filename)
        return mimecontent, filesize

    def __file2attach(self, files):
        """
        covner tile to attachment
        Args:
            files    list     file will be convert
        Returns:
            mimecontent    string    mimecontent with files
            filesize    num    size of the files
        Excpetions:
        """
        mimestring = "Python script to send email in folder\n"
        filesize = []
        for filename in files:
            size = os.stat(filename).st_size
            mimestring += "%s\t\t%s\n" % (filename, size)
            filesize.append((filename, size))
        mimecontent = [(mimestring, "plain")]
        return mimecontent, filesize

    def __recipient_builder(self, toaddrs):
        """
        build recipient string
        Args:
            toaddrs    list    receipt list
        Returns:
            eamils    list     email address list
            rdict    dict    deatil of all receipients
            tostring    string    stirng use to send email
        Exceptions:
        """
        tostring = ""
        rdict = {"To":[], "CC":[], "BCC":[]}
        toaddrs = toaddrs.split(';')
        for emailentry in toaddrs:
            if emailentry.startswith("CC"):
                rdict['CC'] = emailentry[3:].split(",")
            elif emailentry.startswith("BCC"):
                rdict['BCC'] = emailentry[4:].split(",")
            else:
                rdict['To'].append(emailentry)
        emails = []
        if rdict['To'] != []:
            recipientstring = "To: %s\r\n" % ', '.join(rdict['To'])
            tostring = tostring+recipientstring
            emails = emails+rdict['To']
        if rdict['CC'] != []:
            recipientstring = "CC: %s\r\n" % ', '.join(rdict['CC'])
            tostring = tostring+recipientstring
            emails = emails+rdict['CC']
        if rdict['BCC'] != []:
            recipientstring = "BCC: %s\r\n" % ', '.join(rdict['BCC'])
            tostring = tostring+recipientstring
            emails = emails+rdict['BCC']
        return emails, rdict, tostring
