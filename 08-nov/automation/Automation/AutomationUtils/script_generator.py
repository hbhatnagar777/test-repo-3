# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Helper File to generate the PowerShell / UNIX Shell script to be executed on the remote client.

    #.  This file takes the raw script path as the value for the **script** attribute

    #.  Substitutes the values in the script, with the values given by the user

    #.  Appends the footer script (for PowerShell Scripts only)

    #.  Returns / Writes the final script to a temp file, based on the options selected by the User

    #.  Machine class takes care of executing the final script on the client


Any variable in the PowerShell / Shell script should be in the format:

    **##Automation--VARIABLE_NAME--##**


For PowerShell scripts, the main function name should be in this format:

    Function FUNCTION_NAME() {

        Do Something...

    }

, and should be present at top of the PowerShell script file.

PowerShell ``Function`` keyword should always be used in this format only for the main function
that should be executed from the script, and not like ``function``.


Usage
=====

- Initialize object of the ScriptGenerator class with the machine name, and credentials file path:

    >>> script_generator = ScriptGenerator(machine_name, credentials_file)

If Machine name, and Credentials file are set to None, default value `$null` will be set


- Provide the path of the raw script, i.e., set the attribute `script` to the path of the raw file:

    >>> script_generator.script = PATH_OF_THE_RAW_SCRIPT_FILE

- Call the method `run()` with the dictionary consisting of the values to be substituted

    -   To return the contents of the script:

        >>> script_generator.run(
                data={
                    'argument1': 'value1',
                    'argument2': 'value2'
                },
                return_script=True
            )

    -   To write the script into a file, and return path of the file:

        >>> script_generator.run(
                data={
                    'argument1': 'value1',
                    'argument2': 'value2'
                },
                return_script=False
            )

    -   To further select columns from the output of the Invoke-Command cmdlet  (For Windows)

        >>> script_generator.run(
                data={
                    'argument1': 'value1',
                    'argument2': 'value2'
                },
                select_columns=[column1, column2]
            )

**Note**: Key in the dictionary should be the same name as the argument in the Script.

"""

import os
import re
import uuid

from .constants import AUTOMATION_DIRECTORY


class ScriptGenerator(object):
    """Generates the PowerShell / UNIX Shell script to be executed on the remote client."""

    def __init__(self, machine_name=None, credentials_file=None):
        """Initializes the instance of the ScriptGenerator class.

            Args:
                machine_name        (str)   --  name of the machine to run the script remotely on
                    default: None

                credentials_file    (str)   --  path of the machine credentials file
                    default: None

        """
        if credentials_file is None:
            self.machine_name = '$null'
            self.credentials_file = '$null'
        else:
            self.credentials_file = credentials_file

            if machine_name is None:
                self.machine_name = '$null'
            else:
                self.machine_name = machine_name

        self.args = None
        self.extension = None
        self._script = None
        self._script_name = None
        self._final_script = r"""
If ($ComputerName -eq $null) {
    %(function_name)s
} Else {
    $x = Get-Item WSMan:\localhost\Client\TrustedHosts
    If ($x.value.Length -gt 500) { 
        Clear-Item -Path WSMan:localhost\Client\TrustedHosts -Force
        }
    Set-Item WSMan:\localhost\Client\Trustedhosts -Value $ComputerName -Concatenate -Force
    $Credentials = Import-Clixml $CredentialsFile
    Invoke-Command -ComputerName $ComputerName -Credential $Credentials -ScriptBlock ${function:%(function_name)s} -HideComputerName%(select_columns)s
}

"""

    def _write_temp_script(self, script):
        """Writes the Final Script generated after substituting the values to a file with the
            same name as the original file under the Automation/ directory path, and
            returns the Full Path of this final script file.

            Args:
                script  (str)   --  string consisting of the script to be written to the file

            Returns:
                str     -   full path of the file to which the script has been written

                    e.g.;

                        for Windows PowerShell Script:
                            -   script_generator.script = "MakeDir.ps1"

                            output:

                                ../ContentStore/Automation/ID_MakeDir.ps1


                            -   script_generator.script = "RemoveDir.ps1"

                            output:

                                ../ContentStore/Automation/ID_RemoveDir.ps1


                        for UNIX Shell Script:
                            -   script_generator.script = "DirectoryExists.sh"

                            output:

                                ../ContentStore/Automation/ID_DirectoryExists.sh


                            -   script_generator.script = "RegistryExists.sh"

                            output:

                                ../ContentStore/Automation/ID_RegistryExists.sh

                    where,
                        **ID**:    is the unique id of the ScriptGenerator class instance

        """
        # combine the id and the script name to generate a unique script name
        # there could be cases, where 2 Automation runs or 2 test cases be launched in parallel
        # and they both do same operations on the same machine at the same time, where this
        # script could be overwritten
        file_name = os.path.join(
            AUTOMATION_DIRECTORY, '{0}_{1}'.format(uuid.uuid4().hex, self.script_name)
        )

        with open(file_name, 'wb') as f_obj:
            f_obj.write(script.encode())

        return os.path.abspath(file_name)

    @property
    def script(self):
        """Returns the script currently loaded into the instance of this class."""
        return self._script

    @property
    def script_name(self):
        """Returns the name of the script file currently loaded into the instance of this class."""
        return self._script_name

    @script.setter
    def script(self, script_path):
        """Checks if the script path given is valid or not.

            Reads the script, and loads its contents to the `script` attribute of this class.

            And sets the attribute `extension` with the extension of the given script.

        """
        if not os.path.isfile(script_path):
            raise Exception('Script is not a valid file')

        self._script_name = os.path.basename(script_path)

        with open(script_path, 'rb') as f_obj:
            self._script = f_obj.read().decode('utf-8-sig')

        self.extension = os.path.splitext(script_path)[1]

    @property
    def final_script(self):
        """Returns the value of the final script attribute(Footer script for PowerShll scripts)."""
        return self._final_script

    def get_args(self):
        """Gets the function name from the script, and generates the args dict."""
        function = re.search(r'Function (\w*)', self.script)
        function_name = function.group(1)

        self.args = {
            'function_name': function_name,
        }

        del function
        del function_name

    def generate_script(self, add_final_script, select_columns=None, http_route=False):
        """Generates the script to be executed on the client after adding the Arguments:

                $ComputerName

                $CredentialsFile

            to the script, and the Footer script if the add_final_script flag is set to True.

            Args:
                add_final_script    (bool)  --  boolean flag to specify whether the footer part
                must be added to the script or not

                    **Only applicable for PowerShell scripts for Windows**

                select_columns      (list)  --  list of columns to be further selected from the
                output of the **Invoke-Command** cmdlet

                    **Only applicable for PowerShell scripts for Windows**

                    default:    None

                http_route           (bool)  -- Set to True if the connection to machine has to via http

                        **Only applicable for PowerShell scripts for Windows**

                    default:    False

            Returns:
                str     -   script content after adding the arguments, and the footer script

        """
        if self.machine_name == '$null':
            computer_name = '$ComputerName = {0}\n'.format(self.machine_name)
        else:
            computer_name = '$ComputerName = "{0}"\n'.format(self.machine_name)

        if self.credentials_file == '$null':
            credentials_file = '$CredentialsFile = {0}\n'.format(self.credentials_file)
        else:
            credentials_file = '$CredentialsFile = "{0}"\n'.format(self.credentials_file)

        if select_columns:
            self.args['select_columns'] = " | Select {0}".format(", ".join(select_columns))
        else:
            self.args['select_columns'] = ""

        if not http_route:
            final_script = self.final_script % self.args
        else:
            temp_script = self.final_script
            skip = '$sessOptions = New-PSSessionOption -SkipCACheck -SkipCNCheck\n  Invoke-Command '
            ssl = '-UseSSL -SessionOption $sessOptions  -Credential '
            temp_list = temp_script.split('Invoke-Command')
            temp_script = temp_list[0]+skip+temp_list[1].split('-Credential')[0]+ssl+temp_list[1].split('-Credential')[1]
            final_script = temp_script % self.args

        script = self.script

        script = "{0}{1}\n{2}".format(computer_name, credentials_file, script)

        if add_final_script is True:
            script = "{0}{1}".format(script, final_script)

        return script

    @staticmethod
    def substitute_arguments(script, data):
        """Parses through the final script.

            Gets the list of all arguments to be substituted in the script.

            Substitutes the value of the argument with the value given in the `data` dict.

            Args:
                script  (str)   --  raw script consisting of the arguments to be substituted

                data    (dict)  --  dictionary consisting of the
                Script Arguments as key, and its value to be substituted

            Returns:
                str     -   final script with the values set for the Script Arguments

            Raises:
                Exception:
                    if any argument in the script is missing in the `data` dict

                    if the type of the value is not supported

        """
        arguments_list = re.findall(r'##Automation--([\w_]*)--##', script)

        for argument in arguments_list:
            if argument not in data:
                raise Exception('Argument: "{0}" is not present in the data dict'.format(argument))
            else:
                if isinstance(data[argument], bool):
                    if data[argument] is True:
                        value = '$true'
                    else:
                        value = '$false'
                elif isinstance(data[argument], (str, int)):
                    value = str(data[argument])
                elif isinstance(data[argument], list):
                    value = ''
                    for i in range(len(data[argument])):
                        if isinstance(data[argument][i], str):
                            value += '\"' + data[argument][i] + '\"'
                        elif isinstance(data[argument][i], (int, float, bool)):
                            value += str(data[argument][i])

                        if i != len(data[argument]) - 1:
                            value += ','
                elif data[argument] is None:
                    value = 'None'
                else:
                    raise Exception('Data type of the value is not yet supported')

                script = script.replace('##Automation--{0}--##'.format(argument), value)

        return script

    def run(self, data, return_script=False, add_final_script=True, select_columns=None, http_route=False):
        """Generates and Returns the final script / path of the final script
            based on the user inputs.

            Args:
                data                (dict)  --  dictionary consisting of the variables in
                the script as its keys, and their data is it's value

                return_script       (bool)  --  boolean flag specifying whether to return the
                contents of the final script as a string OR write the script to a file,
                and return the file path

                    default:    False

                add_final_script    (bool)  --  boolean flag to specify whether the footer part
                must be added to the script or not

                    **Only applicable for PowerShell scripts for Windows**

                    default:    True

                select_columns      (list)  --  list of columns to be further selected from the
                output of the **Invoke-Command** cmdlet

                    **Only applicable for PowerShell scripts for Windows**

                    default:    None

                http_route           (bool)  -- Set to True if the connection to machine has to via http

                        **Only applicable for PowerShell scripts for Windows**

                    default:    False


            Returns:
                str     -   string value consisting of either the script contents / full path of
                the script file

            Raises:
                Exception:
                    if an argument is missing in the **data** dict

                    if type of the value in the **data** dict is not supported

        """
        if self.extension == '.ps1':
            self.get_args()
            if not http_route:
                script = self.generate_script(add_final_script, select_columns)
            else:
                script = self.generate_script(add_final_script, select_columns, http_route)
        else:
            script = self.script

        script = self.substitute_arguments(script, data)

        if return_script is True:
            return script

        return self._write_temp_script(script)
