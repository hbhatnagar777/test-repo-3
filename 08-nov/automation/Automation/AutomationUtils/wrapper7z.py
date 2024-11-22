# -*- coding: utf-8 -*-

# --------------------------------------------------------------------------
# Copyright Commvault Systems, Inc.
# See LICENSE.txt in the project root for
# license information.
# --------------------------------------------------------------------------

"""Main file for performing 7z file operations

construct_windows_command()  -- This function is used to create the windows command to extract zip file
construct_unix_command()     -- This function is used to create the unix command to extract zip/tar file
wrapper7z:

    extract()        -- This Function is used to extract the file present in the given path
"""

import os

from AutomationUtils.machine import Machine


def construct_windows_command(simpana_base_path, zipfilepath, dest_path):
    """
    This function constructs the command to extract files on a Windows machine.
    Args:
        simpana_base_path (str) -- The base installation path
        zipfilepath (str) -- The path of the zip file to extract
        dest_path (str) -- The destination path for extracted files
    """
    zip_executable = "\\Base\\cv7z.exe"
    simpana_base_path = simpana_base_path.replace(" ", "' '")
    zipfilepath = zipfilepath.replace(' ', "' '")
    dest_path = dest_path.replace(' ', "' '")
    cmd = simpana_base_path + zip_executable + " x " + zipfilepath + " -o"+ dest_path + " -y"
    return cmd


def construct_unix_command(zipfilepath):
    """
    This function constructs the command to extract files on a Unix-based machine.
    Args:
        zipfilepath (str): The path of the zip file to extract
    """
    dest_path = os.path.dirname(zipfilepath)
    return (
        f'cd {dest_path} && '
        'find . -type f \\( -name "*.7z" -o -name "*.tar" -o -name "*.zip" \\) '
        '-exec sh -c \'for file; do '
        'case "$file" in '
        '*.7z) 7z x -so "$file" | tar xf - --recursive-unlink -C "$(dirname "$file")" ;; '
        '*.tar) tar xf "$file" --recursive-unlink --strip-components=1 -C "$(dirname "$file")" ;; '
        '*.zip) unzip -p "$file" | tar xf - --recursive-unlink -C "$(dirname "$file")" ;; '
        'esac; done\' sh {} + && '
        'find . -type f -name "*.7z" -exec 7z x -o"$(dirname "{}")" "{}" \\; && '
        'tar xf *.tar'
    )


class Wrapper7Z(object):
    """Helper class to perform 7z file operations"""

    def __init__(self, commcell=None, client=None, log=None, zipfilepath=None):
        """Initializes wrapper7Z object and gets the commserv database object if not specified

            Args:
                client    (object)    --  client database object
                To unzip from controller machine dont pass client and commcell object
                then the local Machine object will be used for cv7z unzip
                default:    None

                commcell   (object)   --  client database object
                default:    None

                zipfilepath(string)   --  filepath to zip or unzip
        """
        self.log = log
        self.client = client
        self.commcell = commcell
        self.zipfilepath = zipfilepath

    def extract(self, dest=None):
        """
        This Function is used to extract the file present in the given path
        Return Value:
            @Success: Tuple, (Status=True/False, output=stdout/stderr)
            @Error: string, (output=stdout/stderr)
        """
        log = self.log
        base_path = os.path.dirname(self.zipfilepath)
        if not dest:
            dest = os.path.join(base_path, '*')
        try:
            if self.client:
                client_machine = Machine(self.client.client_name, self.commcell)
                simpana_base_path = self.client.install_directory
            else:
                client_machine = Machine()
                simpana_base_path = client_machine.get_registry_value('base', 'dGALAXYHOME')
            # Constructing the command based on the os type
            if "windows" in client_machine.os_info.lower():
                cmd = construct_windows_command(simpana_base_path, self.zipfilepath, dest)
            else:
                cmd = construct_unix_command(self.zipfilepath)

            log.info("Command used unzip %s" % cmd)
            output = client_machine.execute_command(cmd)
            if str(output.output).find("fail") >= 0 or output.exit_code != 0:
                log.error(
                    "Error while unzipping files, error %s" %
                    str(output))
                raise Exception(
                    "Error while unzipping files, error %s" %
                    str(output))
            else:
                log.info("Successfuly unzipped 7z Files on CS")
            return (True, output)
        except Exception as err:
            log.exception("Exception raised. Reason: %s" % (err))
            raise Exception(
                "Error while unzipping files, error %s" %
                str(output))
