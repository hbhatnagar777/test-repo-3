
"""

This class's instance is passed as __gen in templating engine, so we can acess the methods using __gen

"""

import exrex
from faker import Faker
from AutomationUtils import logger


class Generator:

    """
    Generator for generator values for the apis

    """

    def __init__(self):
        self.variables = dict({})
        self.fake = Faker()
        self.log = logger.get_log()

    def gen_regex(self, regex_str):
        """
        generate string based on given regex
        regex_str (str) - regex for which the string has to be generated
        """
        return exrex.getone(regex_str)

    def email(self):
        """returns a fake email"""
        return self.fake.email()

    def set_value(self, variable, value):
        """sets the value for the given variable"""
        try:
            self.variables[variable] = value
        except Exception as exp:
            raise Exception("error while setting attribute : ", exp)

    def domain_name(self):
        """sets fake domain name"""
        rand_url = self.fake.url()
        domain_name = rand_url.split('/')[2]
        return domain_name

    def get_value(self, variable):
        """get the value for the give variable"""
        if variable in self.variables:
            return self.variables[variable]
