from cx_Freeze import setup, Executable
import os

base = None

path = os.path.join(os.path.dirname(__file__),"Extentcounttemp.py")
build_path = os.path.join(os.path.dirname(__file__),"build")

executables = [Executable(path, base=base)]

packages = ["encodings.idna"]
options = {
    'build_exe': {

        'packages': packages,
        'build_exe':build_path
    },

}

setup(
    name="extentcount",
    options=options,
    version="1",
    description='extentcount',
    executables=executables
)