# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Test Case for validating CVEntity Cache for device page

TestCase:   Class for executing this test case

TestCase:

    __init__()      --  initialize TestCase class

    setup()         --  initializes pre-requisites for test case

    run()           --  run function of this test case

"""
import threading
from AutomationUtils import constants
from AutomationUtils.cvtestcase import CVTestCase
from Server.RestAPI import entitycache


class TestCase(CVTestCase):
    """Test case class validating CVEntity Cache for vmgroup page"""

    def __init__(self):
        """Initializes test case class object"""
        super(TestCase, self).__init__()
        self.name = ("vmgroup page entitycache testing")
        self.applicable_os = self.os_list.WINDOWS
        self.product = self.products_list.COMMSERVER
        self.feature = self.features_list.RESTAPI
        self.tcinputs = {
        }

    def setup(self):
        """Initializes pre-requisites for test case"""
        webconsole = self.inputJSONnode['commcell']['webconsoleHostname']
        self.helper = entitycache.EntityCacheHelper(
            self.commcell, self.client, webconsole, 'server', self.log)
        self.helper.stop_service()

    def run(self):
        """ Main function for test case execution.
        This Method validates Server page entity cache.
        Raises:
            SDKException:
                if it fails to validate Entity Cache
        """
        try:
            validate_list_start = []
            validate_list = []
            iterations = 2
            number_of_threads = 100
            for i in range(iterations):
                if i == 0:
                    query = (self.helper.browser_urls + self.helper.limit +
                             self.helper.start_5 + self.helper.fl_sub_query)
                else:
                    query = (self.helper.browser_urls + self.helper.limit +
                             self.helper.start_0 + self.helper.fl_sub_query)
                cachecount_before = self.helper.validatelogs
                response = self.helper.calculate(query, True)
                cachecount_after = self.helper.validatelogs
                if cachecount_after >= cachecount_before:
                    self.log.info("Request is sent to EntityCache")
                else:
                    raise Exception("""Number of log lines before {%s} and after {%s}
                     request are same or less. Means request is not sent to
                      Cache""" % (cachecount_before, cachecount_after))

                if 'clientProperties' in response:
                    for value in response['clientProperties']:
                        if 'client' in value:
                            if 'clientName' in value['client']:
                                if i == 0:
                                    validate_list_start.append(
                                        value['client']['clientName'])
                                else:
                                    validate_list.append(
                                        value['client']['clientEntity']['clientName'])
                if len(validate_list_start) <= 5:
                    self.log.info("we cannot validate start as we have less number of VMGroups")
                    break
            if validate_list_start and validate_list:
                if validate_list[5:len(validate_list)] == validate_list_start[:-5]:
                    self.log.info("start validation is successful")
                else:
                    self.log.error(
                        "List is not started correctly, actual list {} : start list{}".format(
                            validate_list, validate_list_start))
                    raise Exception("List is not sorted correctly with descending order")

            for i in range(iterations):
                if i == 0:
                    query = (self.helper.browser_urls + self.helper.limit + self.helper.start_0 +
                             self.helper.sort_des_query + self.helper.fl_sub_query)
                else:
                    query = (self.helper.browser_urls + self.helper.limit + self.helper.start_0 +
                             self.helper.sort_asc_query + self.helper.fl_sub_query)

                validate_list = []
                response = self.helper.send_validate_log_count(query)
                if 'clientProperties' in response:
                    for value in response['clientProperties']:
                        if 'client' in value:
                            if 'clientEntity' in value['client']:
                                validate_list.append(value['client']['clientEntity'])
                if len(validate_list) > 0:
                    sorted_list = validate_list
                    if i == 0:
                        sorted_list = sorted(sorted_list, reverse=True)
                        if sorted_list == validate_list:
                            self.log.info("List is sorted correctly with descending order")
                        else:
                            self.log.error("List is not sorted correctly with descending order")
                            raise Exception("List is not sorted correctly with descending order")
                    else:
                        sorted_list = sorted(sorted_list)
                        if sorted_list == validate_list:
                            self.log.info("List is sorted correctly with ascending order")
                        else:
                            self.log.error("List is not sorted correctly with ascending order")
                            raise Exception("List is not sorted correctly with ascending order")

            url = self.helper.browser_urls + self.helper.hf_refresh + self.helper.start_0
            self.log.info("URL used %s" % url)
            cachecount_before = self.helper.validatelogs

            response = self.helper.calculate(url, True)
            cachecount_after = self.helper.validatelogs
            if cachecount_after >= cachecount_before:
                self.log.info("Request is sent to EntityCache")
            else:
                raise Exception("""Number of log lines before {%s} and after {%s}
                     request are same or less. Means request is not sent to
                      Cache""" % cachecount_before, cachecount_after)
            if len(response['subClientProperties']) <= 0:
                self.log.error("response contains more number of rows")
                raise Exception("response contains more number of rows")

            for self.helper.iter in range(iterations):
                if self.helper.iter == 0:
                    self.helper.stop_service(True)
                    validate = False
                else:
                    self.helper.stop_service()
                    validate = True

                url = (self.helper.browser_urls +
                       self.helper.limit +
                       self.helper.start_0)
                self.log.info("URL used %s" % url)
                response = self.helper.send_validate_log_count(url)
                if validate and len(response['subClientProperties']
                                    ) > 20 and len(response['subClientProperties']) > 90:
                    self.log.error("response contains more number of rows")
                    raise Exception("response contains more number of rows")

                url = (self.helper.browser_urls +
                       self.helper.fl_query +
                       self.helper.start_0)
                self.log.info("URL used %s" % url)
                response = self.helper.send_validate_log_count(url)
                if 'clientProperties' in response:
                    if 'client' in response['clientProperties'][0]:
                        self.log.info("subclientProperties are available")
                if 'clientProperties' in response:
                    if 'ActivePhysicalNode' in response['clientProperties'][0]:
                        self.log.error("ActivePhysicalNode are available")

                if 'clientProperties' in response:
                    if 'clientprops' in response['clientProperties'][0]:
                        self.log.error("vsaSubclientProp are available")

                self.helper.constraint_dict['client'] = "test"
                fq_query = self.helper.construct_query(self.helper.constraint_dict)
                url = (self.helper.browser_urls +
                       fq_query +
                       self.helper.start_0)
                self.log.info("URL used %s" % url)
                response = self.helper.send_validate_log_count(url)
                if response is None:
                    self.log.error("Response is none for the query")
                    raise Exception("Response is none for the query")
                flag, resturnlist = self.helper.validate_vmgroup_response(
                    response, self.helper.constraint_dict, complete=True)
                if validate and flag:
                    self.log.error("Validation Failed")
                    raise Exception("Validation failed")

                self.helper.constraint_dict = {
                    'subclient': '', 'client': '', 'instance': '', 'search': ''}
                self.helper.constraint_dict['search'] = "test"
                fq_query = self.helper.construct_query(self.helper.constraint_dict)
                url = (self.helper.browser_urls +
                       fq_query +
                       self.helper.start_0)
                self.log.info("URL used %s" % url)
                response = self.helper.send_validate_log_count(url)
                if response is None:
                    self.log.error("Response is none for the query")
                    raise Exception("Response is none for the query")
                flag, resturnlist = self.helper.validate_vmgroup_response(
                    response, self.helper.constraint_dict, complete=True)
                if validate and flag:
                    self.log.error("Validation Failed")
                    raise Exception("Validation failed")

                thread_list = []
                self.helper.responsetimes = []
                url = self.helper.browser_urls + self.helper.sort + self.helper.start_0
                self.log.info("base Url is %s" % self.helper.browser_urls)
                self.log.info("Parameters passed are %s" %
                              str([self.helper.sort, self.helper.start_0]))
                for newthread in range(number_of_threads):
                    lib_thread = threading.Thread(
                        target=self.helper.calculate, name="server", args={url, })
                    lib_thread.daemon = False
                    lib_thread.start()
                    thread_list.append(lib_thread)

                for threadobj in thread_list:
                    threadobj.join()
                self.log.info("Response times in seconds are {}".format(
                    str(self.helper.responsetimes)))
                self.log.info("Maximun Response time in seconds %s" %
                              max(self.helper.responsetimes))
                self.log.info("Minimum Response time in seconds %s" %
                              min(self.helper.responsetimes))
                self.log.info("Average Response time in seconds {}".format(
                    str(sum([count for count in self.helper.responsetimes if isinstance(
                        count, int) or isinstance(count, float)]) / len(self.helper.responsetimes))))
                if self.helper.iter == 1:
                    if max(self.helper.responsetimes) >= 60:
                        self.log.error(
                            "request %s took more than 60 seconds even mongodb is up" %
                            url)
                        raise Exception(
                            "request %s took more than 60 seconds even mongodb is up" %
                            url)
                if len(self.helper.failed_requests) > 0:
                    self.log.error("There are failed requests %s" %
                                   self.helper.failed_requests)
                    raise Exception("There are failed requests %s" %
                                    self.helper.failed_requests)

        except Exception as excp:
            self.log.error('Failed with error: ' + str(excp))
            self.result_string = str(excp)
            self.status = constants.FAILED
        
