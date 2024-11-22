# -*- coding: utf-8 -*-
# gitlab
# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Main file for performing Server related operations on Commcell

ServerTestCases:   Provides test case related operations.

ServerTestCases:
    __init__()                  --  initialize instance of the ServerTestCases class

    __repr__()                  --  Representation string for the instance of the
                                    ServerTestCases class for specific test case

    fail()                      --  Marks the test case failed and logs the errors

    log_step()                  --  Logs a message enclosed in a specific character line

    rename_remove_logfile()     --  removes and renames old logfile

    validatelogs()              --  checks number of calls in log file

    generate_email_body()       --   generates email content with headers,
                                     data and returns html string

"""

import re
from AutomationUtils import constants, database_helper


class ServerTestCases(object):
    """Server test case helper class to perform server test case related operations"""

    def __init__(self, testcase):
        """Initialize instance of the ServerTestCases class."""
        self._testcase = testcase
        self.log = self._testcase.log

    def __repr__(self):
        """Representation string for the instance of the ServerTestCases class."""
        return "ServerTestCases class instance for test case: '{0}'".format(self._testcase.name)

    def fail(self, exception, error_message=None):
        """ Marks the server test case as failed

        Args:

        exception    (Exception)  --  Exception in test case

        error_message (str)       --  Custom error message to log in case of
                                        test case failure

        Returns:
        None

        """
        if error_message is None:
            error_message = 'Test case failed with error: ' + str(exception)

        self.log.error(error_message)
        self._testcase.result_string = str(exception)
        self._testcase.status = constants.FAILED

    def log_step(self, message_string, char_length=100, char_type="="):
        """ Log a message enclosed in a character line """
        _line = char_type * char_length
        self.log.info(f'''
{_line}
{message_string}
{_line}''')

    def rename_remove_logfile(self, client_machine, validatelog,templog_dictory,substring=''):
        '''
        removes and renames old logfile
        @args:
        Client_machine (object)     -- Machine object
        validatelog (string)        -- Log file to rename / remove
        '''
        
        if client_machine.check_file_exists(validatelog):                   
            if substring is None:
                substring = ''#.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(9))
            client_machine.remove_directory(validatelog.replace(".log", "_"+substring+".log"))
            client_machine.rename_file_or_folder(validatelog, validatelog.replace(".log", "_"+substring+".log"))
        if substring:
            client_machine.copy_folder(validatelog.replace(".log", "_"+substring+".log"), templog_dictory)
        #client_machine.remove_directory(validatelog.replace(".log", "_"+substring+".log"))
    

    def validatelogs(
            self,
            client_machine,
            loglines_with_required_calls,
            validatelog,
            logstrings_to_verify):
        '''
        checks number of calls in log file
        @args
            validatelog (string) --  full path of the log to validate
        '''
        if client_machine.check_file_exists(validatelog):

            with open(validatelog) as file_obj:
                for line in file_obj:
                    found = 0
                    for key in logstrings_to_verify.keys():
                        if line.find(key) >= 0:
                            found = 1
                            loglines_with_required_calls.append(line)
                            for innerkey in logstrings_to_verify[key].keys():
                                fullkey = key + " -  [ %s ]" % innerkey
                                if line.find(fullkey) >= 0:
                                    found = 2
                                    logstrings_to_verify[key][innerkey] = logstrings_to_verify[
                                        key][innerkey] + 1
                            if found == 1:
                                logstrings_to_verify[key]['unknown'] = logstrings_to_verify[
                                    key]['unknown'] + 1

                    '''if found == 0 and re.search(
                        '\s*-\s*\[\s*\S*\.exe\s*\]',
                            line) is not None and line.lower().find("ccsdb") < 0:
                        loglines_with_required_calls.append(line)
                        for innerkey in logstrings_to_verify['Unknowncalls'].keys():
                            if re.search(innerkey, line) is not None:
                                found = 1
                                logstrings_to_verify['Unknowncalls'][innerkey] = logstrings_to_verify[
                                    'Unknowncalls'][innerkey] + 1
                        if found == 0:
                            logstrings_to_verify['Unknowncalls']['unknown'] = logstrings_to_verify[
                                'Unknowncalls']['unknown'] + 1'''
                return logstrings_to_verify
        else:
            raise Exception("file {} not found".format(validatelog))

    def generate_email_body(self, headers, data):
        '''
        generates email content with headers, data and returns html string.

        @args:

        header (str)          : Header of the mail
        data (dictionary)     : body of the mail in dictionary format
        
        '''
        style = ''' <html>
        <style type="text/css">
        table {
         border-collapse: collapse;
          width: 80%;
          text-align: middle;
          }
        table td, th {
          border: 1px solid blue;
          padding: 15px;

          }

        #summary{
            border-color: #348dd4;
        }
        #summary_head{
            color: #fff;
            text-transform: uppercase;
        }
        #summary th{
            background-color: #84E8F5;

        }
        #summary tr{
            background-color: #F7D0C6;

        }
        #summary tr:nth-child(even){
            background: #C3F5C4;

        }
        #summary tr:nth-child(odd){
            background: #D8E6FA;

        }
        header h2 {
            margin: 20px;
        }

        </style>

        <header>
            <h2>Laptop backup call statistics with CCSDB enabled:</h2>
        </header>
        <body>
        '''
        items = []
        items.append('%s<table id="summary">' % style + '<tr>')
        for tag in headers:
            items.append('<th><b>%s</th>' % tag)
        items.append('</tr>')

        for keys, values in data.items():
            index = 0
            cvdcall=False
            for item in range(len(values[0])):
                if index == 0:
                    items.append('<tr>')
                    items.append(
                        '<td rowspan="5"><strong><font color="black">%s</td>' %
                        (str(keys)))
                    if keys.find("ClientSessionWrapper::send()") >=0 or keys.find("ClientSessionWrapper::receive()") >=0:
                        cvdcall=True
                   
                else:
                    items.append('<tr>')
                for info in values:
                    update_index = index
                    for key in info.keys():
                        if update_index > 0:
                            update_index = update_index - 1
                            continue
                        if info[key] > 6:
                            if cvdcall and info[key]/2 > 1.0:
                                if key == 'unknown':
                                    if info[key]/2 > 1.0:
                                        items.append('<td><strong><font color="red">%s : %s</td>' %
                                                     (key, str(info[key]/2)))
                                    else:
                                        items.append('<td><strong><font color="Green">%s : %s</td>' %
                                                     (key, str(info[key]/2)))
                                    
                                else:
                                    if info[key]/2 > 3.0:
                                        items.append('<td><strong><font color="red">%s : %s</td>' %
                                                     (key, str(info[key]/2)))
                                    else:
                                        items.append('<td><strong><font color="Green">%s : %s</td>' %
                                                     (key, str(info[key]/2)))
                                        
                            else:
                                items.append('<td><strong><font color="red">%s : %s</td>' %
                                             (key, str(info[key])))                                
                        else:
                            if cvdcall:
                                items.append('<td><strong><font color="Green">%s : %s</td>' %
                                             (key, str(info[key]/2)))
                            else:
                                items.append('<td><strong><font color="Green">%s : %s</td>' %
                                             (key, str(info[key])))

                        break
                items.append('</tr>')
                index = index + 1

        items.append('</table>')
        items.append(
            "<br><br>Note:<br>1. If number of calls exceeds 5,"
            " please verify logs and report the issue to devteam<br>"
            "2. This is automated mail generated with automation.")
        items.append(
            "<br><br>Thanks<br>Laptop Automation Team <br>This is auto generated mail."
            " reply back to this mail is unattended.<br>")
        items.append("</body></html>")
        self.log.info('\n'.join(items))
        return '\n'.join(items)
