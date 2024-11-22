import argparse
import logging
import os
import shutil
import stat
import subprocess
import traceback
from pathlib import Path
from sys import exit, executable, platform

# Parse args
parser = argparse.ArgumentParser()
parser.add_argument("--username", help="CVS Username for Login", default="gbuilder")
parser.add_argument("--skip-cvs-login", help="Use this arg if you've already setup CVSROOT and logged in",
                    action="store_true")
parser.add_argument("--skip-cvs-checkout", help="Use this arg to skip CompiledBins checkout from CVS",
                    action="store_true")
parser.add_argument("--git-cred-manager",
                    help="Use this arg if you have setup credentials using Git Credential Manager (local creds)",
                    action="store_true")
args = parser.parse_args()

# Common
home = Path(__file__).parent.resolve()
PYTHON_PATH = executable


def remove_readonly(func, path, excinfo):
    os.chmod(path, stat.S_IWRITE)
    func(path)


def run_command_locally(commands_list):
    try:
        return subprocess.Popen(commands_list)
    except FileNotFoundError:
        logger.error(f"Please verify if {commands_list[0]} is on path.", exc_info=True)
        traceback.print_exc()
        print(f"Please verify if {commands_list[0]} is on path.")
        exit(1)


logging.basicConfig(filename='setup.log',
                    level=logging.DEBUG,
                    filemode='a',
                    format='%(asctime)s: %(levelname)s: %(name)s: %(message)s')
logger = logging.getLogger("setup")

# # Delete CompiledBins if exists
# folder = Path(home) / 'Automation' / 'CompiledBins'
# if folder.exists():
#     logger.info("Deleting existing CompiledBins")
#     shutil.rmtree(folder, onerror=remove_readonly)

# # Checkout CompiledBins
# if not args.skip_cvs_checkout:
#     logger.info(f"Attempting checkout as user: {args.username}")
#     if not args.skip_cvs_login:
#         print(f"Login as CVS user: {args.username}")
#         process = run_command_locally(["cvs", "-d", f":pserver:{args.username}@cvs.commvault.com:/repos", "login"])
#         if process.wait():
#             logger.error("CVS Login failed")
#             exit(-1)
#     process = run_command_locally(
#         ["cvs", "-d", f":pserver:{args.username}@cvs.commvault.com:/repos", "checkout", "-d", folder,
#          "vaultcx/Source/tools/Automation/CompiledBins/"])
#     if process.wait():
#         logger.error("CVS Checkout failed")
#         exit(-1)

# Uninstall and reinstall cvpysdk
logger.info("Attempting to uninstall existing cvpysdk")
process = subprocess.Popen([PYTHON_PATH, "-m", "pip", "uninstall", "cvpysdk", "-y"])
process.wait()
logger.info("Attempting to install cvpysdk from source")
process = subprocess.Popen([PYTHON_PATH, "-m", "pip", "install", "."], cwd=Path(home) / 'cvpysdk')
# fallback to setup.py for commvault installed Python error
if process.wait():
    logger.error("cvpysdk install failed with pyproject.toml. Please avoid using Commvault installed Python for Automation. Fallback to setup.py")
    process = subprocess.Popen([PYTHON_PATH, "setup.py", "install"], cwd=Path(home) / 'cvpysdk')

# Install automation requirements
REQUIREMENTS_FILE = "requirements.txt"
OS_REQUIREMENTS_FILE = "requirements_win.txt" if "win" in platform.lower() else "requirements_lin.txt"
logger.info("Attempting to install common Automation requirements")
process = subprocess.Popen([PYTHON_PATH, "-m", "pip", "install", "-r", REQUIREMENTS_FILE],
                           cwd=Path(home) / 'Automation' / 'cvautomationmask' / 'packages')
process.wait()
logger.info("Attempting to install OS specific Automation requirements")
process = subprocess.Popen([PYTHON_PATH, "-m", "pip", "install", "-r", OS_REQUIREMENTS_FILE],
                           cwd=Path(home) / 'Automation' / 'cvautomationmask' / 'packages')
process.wait()

# Merge config file
logger.info("Attempting to merge config file")
process = subprocess.Popen([PYTHON_PATH, "config_generator.py"], cwd=Path(home) / 'Automation' / 'CoreUtils')
process.wait()

# # Localization folder
# logger.info("Attempting to clone localization")
# if (Path(home) / 'Automation' / 'Web' / 'AdminConsole' / 'web').exists():
#     shutil.rmtree(Path(home) / 'Automation' / 'Web' / 'AdminConsole' / 'web', onerror=remove_readonly)
# process = subprocess.Popen(["git", "clone", "--filter=blob:none", "--no-checkout", "--depth", "1", "--sparse",
#                             "https://git.commvault.com/eng/ui/web.git" if args.git_cred_manager else "git@git.commvault.com:eng/ui/web.git"],
#                            cwd=Path(home) / 'Automation' / 'Web' / 'AdminConsole')
# if process.wait():
#     logger.error("Web checkout failed. Please ensure you have permission for this project")
#     exit(-1)
# process = subprocess.Popen(["git", "sparse-checkout", "add", "AdminConsole/resources/localization"],
#                            cwd=Path(home) / 'Automation' / 'Web' / 'AdminConsole' / 'web')
# process.wait()
# process = subprocess.Popen(["git", "checkout"], cwd=Path(home) / 'Automation' / 'Web' / 'AdminConsole' / 'web')
# process.wait()

# localization_path = Path(
#     home) / 'Automation' / 'Web' / 'AdminConsole' / 'web' / 'AdminConsole' / 'resources' / 'localization'
# if localization_path.exists():
#     logger.info("Attempting to copy localization and delete repo after")
#     if (Path(home) / 'Automation' / 'Web' / 'AdminConsole' / 'Localization').exists():
#         shutil.rmtree(Path(home) / 'Automation' / 'Web' / 'AdminConsole' / 'Localization', onerror=remove_readonly)
#     shutil.copytree(localization_path, Path(home) / 'Automation' / 'Web' / 'AdminConsole' / 'Localization')
#     shutil.rmtree(Path(home) / 'Automation' / 'Web' / 'AdminConsole' / 'web', onerror=remove_readonly)
# else:
#     logger.error("Can't find the checkout folder")
