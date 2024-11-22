# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""

Main file for Server module type(s) handlers

ValidateArgs:           Raises Exception when argument type to a module is incorrect

ValidateArgsNum:        Raises Exception when number of module arguments is incorrect

ValidateReturnType:     Raise Exception when return value of a module is incorrect

argtypes():             Validate module arguments

returntype():           Validate module return type

"""

import functools

class ValidateArgs(ValueError):
    ''' Argument types of a module is incorrect '''
    def __init__(self, num_args, module_name, argument_type):
        """Initialize instance of the ValidateArgs(ValueError) class."""
        self.stderror = '[{0}] argument for {1}() is not {2}'.format(num_args,
                                                                     module_name,
                                                                     argument_type)

    def __str__(self):
        """Representation string consisting of module arguments"""
        return self.stderror

class ValidateArgsNum(ValueError):
    ''' Total number of arguments sent to module is invalid '''
    def __init__(self, module_name):
        """Initialize instance of the ValidateArgsNum(ValueError) class."""
        self.stderror = 'Incorrect number of arguments passed to {0}()'.\
                                format(module_name)

    def __str__(self):
        """Representation string consisting of a valid number of arguments."""
        return self.stderror

class ValidateReturnType(ValueError):
    ''' Return type for the module is incorrect '''
    def __init__(self, return_type, module_name):
        """Initialize instance of the ValidateReturnType(ValueError) class."""
        self.stderror = 'Incorrect return type {0} for {1}()'.format(return_type,
                                                                     module_name)

    def __str__(self):
        """Representation string consisting of a valid return type."""
        return self.stderror

def argtypes(*arg_types):
    '''Validate argument types of a given function.'''

    def check_args(test_module):
        @functools.wraps(test_module)
        def check_arg_nums(self, *_args, **_kwargs):
            if len(_args) is not len(arg_types):
                raise ValidateArgsNum(test_module.__name__)

            for num, (arg, arg_type) in enumerate(zip(_args, arg_types)):
                if arg == 'self' or arg_type == 'obj':
                    continue

                if isinstance(arg_type, tuple):
                    _flag = False
                    for _type in arg_type:
                        if type(arg) is _type and not _flag:
                            _flag = True
                else:
                    _flag = type(arg) is arg_type

                if not _flag:
                    ord_num = _argstr(num + 1)
                    raise ValidateArgs(ord_num, test_module.__name__, arg_type)

            return test_module(self, *_args)
        return check_arg_nums
    return check_args


def returntype(*return_type):
    ''' Validates the return type from module'''

    def check_return_type(test_module):
        if len(return_type) == 0:
            raise TypeError('Please provide a return type.')

        @functools.wraps(test_module)
        def wrap_return(*_args):
            if len(return_type) > 1:
                raise TypeError('Please provide 1 return type.')

            get_return_type = return_type[0]
            return_value = test_module(*_args)
            return_value_type = type(return_value)

            if return_value_type is not get_return_type:
                raise ValidateReturnType(return_value_type, test_module.__name__)

            return return_value
        return wrap_return
    return check_return_type

def _argstr(num):
    '''Returns the 'th string for int'''
    if 10 <= num % 100 < 20:
        return '{0}th'.format(num)

    _str = {1 : 'st', 2 : 'nd', 3 : 'rd'}.get(num % 10, 'th')
    return '{0}{1}'.format(num, _str)

if __name__ == '__main__':

    # Handler example
    @argtypes(int, int)
    @returntype(int)
    def add_nums(arg1, arg2):
        return arg1 + arg2
