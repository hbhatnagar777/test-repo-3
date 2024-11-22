"""Module for formatting the output of the executed command."""


class UnixOutput:
    """This class is used to store the output of the executed command."""

    def __init__(self, return_code, stdout, stderr):
        """Initialize the UnixOutput object with the provided parameters.

        Args:
            return_code (int): The return code of the executed command.
            stdout (str): The standard output of the executed command.
            stderr (str): The standard error of the executed command.
        """
        self._return_code = return_code
        self._stdout = stdout
        self._stderr = stderr

    @property
    def return_code(self):
        """Return the return code of the executed command.

        Returns:
            int: The return code of the executed command.
        """
        return self._return_code

    @property
    def stdout(self):
        """Return the standard output of the executed command.

        Returns:
            str: The standard output of the executed command.
        """
        return self._stdout

    @property
    def stderr(self):
        """Return the standard error of the executed command.

        Returns:
            str: The standard error of the executed command.
        """
        return self._stderr
