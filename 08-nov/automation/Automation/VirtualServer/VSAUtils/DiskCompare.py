import io
import os
import sys
import subprocess
import win32file
import win32con
import winioctlcon
import ctypes
import struct
import hashlib
import threading
import wmi
import math
import time
from argparse import ArgumentParser
import string

c = wmi.WMI()
digs = string.digits + string.ascii_letters

# Global Shared Variables
totalSuccess = 0
totalFailures = 0
failedSectorList = []


def get_disk_list():
    """
    Returns a list the mountpaths of all the disks attached to the system
    """
    disklist = []

    for item in c.Win32_DiskDrive():
        disklist.append(item.DEVICEID)

    return disklist


def get_os_disk():
    """
    Returns a string which contains the mountpaths of disk in which OS is installed
    """
    cmdCommand = 'Get-Disk | Where { $_.BootFromDisk -eq $TRUE }  | foreach {$_.Number}'  # specify your cmd command
    p = subprocess.Popen(["powershell", cmdCommand], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE)
    output, err = p.communicate(b"input data that is passed to subprocess' stdin")
    rc = p.returncode
    os_index = int(output)

    for item in c.Win32_DiskDrive():
        if item.index == os_index:
            return item.DEVICEID


def get_compare_disk_list():
    """
    Returns a list the of all the mountpaths the disks attached to the system, except for that of the OS disk
    """
    disk_list = get_disk_list()
    os_disk = get_os_disk()
    compare_list = disk_list[:]
    compare_list.remove(os_disk)
    return compare_list


def get_compare_pairs(compare_list):
    """
    Returns a list of [str, str] disk mountpath pairs which are to be compared with each other
    """
    compare_pairs = []
    n_disks = int(len(compare_list) / 2)

    for i, disk in enumerate(compare_list):
        if i > n_disks - 1:
            break
        compare_pairs.append([compare_list[i], compare_list[i + n_disks]])

    return compare_pairs


def compare_logger(msg, type_):
    """
    Prints a message to the compare.log file

    Args:
            msg         (str):   Message to be printed to the log
            type_       (str):   Type of message

    Raise Exception:
            if invalid message type provided
    """
    type_list = {
        "info": "INFO",
        "error": "ERROR"
    }

    try:
        if type_ not in type_list:
            raise Exception("Invalid message type passed to compare_logger()")

        t = time.localtime()
        current_time = time.strftime("%d-%m-%Y %H:%M:%S", t)

        with open("C:\\CompareLogs\\compare.log", "a") as file_object:
            file_object.write(type_list[type_] + ": " + current_time + " " + str(msg) + "\n")

    except Exception as exp:
        compare_logger(exp, "error")


def getDiskHandlePair(sourceDiskPath, clonedDiskPath):
    """
    Creates a handle for reading the disks, and returns a list [sourceDiskPathHandle, clonedDiskPathHandle]

    Args:
            sourceDiskPath      (str):   Mountpath of source disk
            clonedDiskPath      (str):   Mountpath of cloned disk
    """
    desiredAccess = win32file.GENERIC_READ
    shareMode = win32file.FILE_SHARE_READ
    attributes = None
    CreationDisposition = win32file.OPEN_EXISTING
    flagAndAttributes = win32file.FILE_ATTRIBUTE_NORMAL
    hTemplateFile = None

    sourceDiskPathHandle = win32file.CreateFile(
        sourceDiskPath,
        desiredAccess,
        shareMode,
        attributes,
        CreationDisposition,
        flagAndAttributes,
        hTemplateFile
    )

    clonedDiskPathHandle = win32file.CreateFile(
        clonedDiskPath,
        desiredAccess,
        shareMode,
        attributes,
        CreationDisposition,
        flagAndAttributes,
        hTemplateFile
    )

    diskHandlePair = [sourceDiskPathHandle, clonedDiskPathHandle]

    return diskHandlePair


def getDiskHandlePairList(numThreads, sourceDiskPath, clonedDiskPath):
    """
    Returns a list of disk handle pairs [sourceDiskPathHandle, clonedDiskPathHandle]

    Args:
            numThreads          (int):  Number of threads
            sourceDiskPath      (str):  Mountpath of source disk
            clonedDiskPath      (str):  Mountpath of cloned disk
    """

    diskHandlePairList = []

    for i in range(numThreads):
        diskHandlePair = getDiskHandlePair(sourceDiskPath, clonedDiskPath)
        diskHandlePairList.append(diskHandlePair)

    return diskHandlePairList


def getDiskSectorInfo(diskMountPath):
    """
    Returns a list containing the disk sector informtion [bytesPerSector, totalSectors]

    Args:
            diskMountPath       (int):  Mountpath of a disk
    """

    bytesPerSector = None
    totalSectors = None

    for item in c.Win32_DiskDrive():
        if (diskMountPath == item.DEVICEID):
            bytesPerSector = int(item.BytesPerSector)
            totalSectors = int(item.TotalSectors)

    sectorInfo = [bytesPerSector, totalSectors]

    return sectorInfo


def calculateDiskHandleOffset(numThreads, bytesPerSector, totalSectors):
    """
    Returns a list of disk handle offsets

    Args:
            numThreads          (int):  Number of threads
            bytesPerSector      (int):  Bytes per sector of the disk
            totalSectors        (int):  Total number of sectors on the disk
    """
    diskHandleOffsetList = []
    sectorSlice = math.floor((totalSectors * bytesPerSector) / numThreads)
    for h in range(0, numThreads):
        offset = h * sectorSlice
        diskHandleOffsetList.append(offset)
    return diskHandleOffsetList


def setDiskHandlePairOffset(diskHandlePair, offset):
    """
    Returns a list of disk handle which have been adjusted by an offset

    Args:
            diskHandlePair      (list):  [str, str] disk handle pair
            offset              (int):  Offset to be added to the disk handles
    """
    if (offset == 0):
        return diskHandlePair

    sourceDiskPathHandle, clonedDiskPathHandle = diskHandlePair

    sourceDiskPathHandleOffset = win32file.SetFilePointer(
        sourceDiskPathHandle, offset, win32con.FILE_BEGIN)
    clonedDiskPathHandleOffset = win32file.SetFilePointer(
        clonedDiskPathHandle, offset, win32con.FILE_BEGIN)

    diskHandlePair = [sourceDiskPathHandle, clonedDiskPathHandle]

    return diskHandlePair


def getOffsetLimitList(diskHandleOffset, bytesPerSector, totalSectors):
    """
    Returns a list of offset limits, which is then used by a disk handle to stop reading.

    Args:
            diskHandleOffset    (int):  Disk handle offset
            bytesPerSector      (int):  Bytes per sector of the disk
            totalSectors        (int):  Total number of sectors on the disk
    """

    offsetLimitList = []

    for i in range(len(diskHandleOffset) - 1):
        offsetLimitList.append(diskHandleOffset[i + 1])
    offsetLimitList.append(bytesPerSector * totalSectors)

    return offsetLimitList


def getReaderThreads(diskHandlePairListWithOffset, diskHandleOffset, offsetLimitList, bytesPerSector, totalSectors,
                     multiplier):
    """
    Returns a list of threads which are later used for reading the disk.

    Args:
            diskHandlePairListWithOffset    (list): List of offset adjusted disk handles
            diskHandleOffset                (int): Disk handle offset
            offsetLimitList                 (list): List of offset read limits
            bytesPerSector                  (int): Bytes per sector of the disk
            totalSectors                    (int): Total number of sectors on the disk
            multiplier                      (int): Number of sectors to read at a time
    """
    readerThreads = []
    for pair, offset_start, offset_limit in zip(diskHandlePairListOffset, diskHandleOffset, offsetLimitList):
        t = threading.Thread(target=readerThread, args=(
            pair, offset_start, offset_limit, bytesPerSector, multiplier,))
        readerThreads.append(t)

    return readerThreads


def readerThread(diskHandlePair, offsetStart, offsetLimit, bytesPerSector, multiplier):
    """
    Creates a disk reader thread.

    Args:
            diskHandlePair                  (list): List with disk handle pair to be compared
            offsetStart                     (int): Beginning offset, where read will start
            offsetLimit                     (int): End offset, where read will stop
            bytesPerSector                  (int): Bytes per sector of the disk
            multiplier                      (int): Number of sectors to read at a time
    """

    sourceDiskPathHandle, clonedDiskPathHandle = diskHandlePair

    dataBufferS = None
    dataBufferC = None
    responseS = None
    responseC = None
    readNBytes = bytesPerSector * multiplier

    offsetPointer = offsetStart

    success = 0
    failureSectors = []

    # Shared Variables
    global totalSuccess
    global totalFailures
    global failedSectorList

    while (offsetPointer < offsetLimit):
        responseS, dataBufferS = win32file.ReadFile(
            sourceDiskPathHandle, readNBytes)
        responseC, dataBufferC = win32file.ReadFile(
            clonedDiskPathHandle, readNBytes)

        if (dataBufferS == dataBufferC):
            success += 1
        else:
            failure = offsetPointer
            failureSectors.append(failure)

        offsetPointer += readNBytes

    data_lock.acquire()
    totalSuccess += success
    totalFailures += len(failureSectors)
    failedSectorList.extend(failureSectors)
    data_lock.release()


def closeDiskHandlePairList(diskHandlePairList):
    """
    Closes all the opened disk handles

    Args:
        diskHandlePairList                  (list): List with of disk handle pairs
    """
    for pair in diskHandlePairList:
        for handle in pair:
            handle.Close()
    return


def initLogDir():
    """
    Creates the log directory
    """
    # Creating Log Folder
    log_dir = r'C:\CompareLogs'
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)


def powershell_output(output):
    """
    Prints output to a powershell instance
    """
    output_dict = {
        "success": "$true",
        "failure": "$false"
    }

    subprocess.call("powershell return " + output_dict[output])


def int2base(x, base):
    if x < 0:
        sign = -1
    elif x == 0:
        return digs[0]
    else:
        sign = 1

    x *= sign
    digits = []

    while x:
        digits.append(digs[int(x % base)])
        x = int(x / base)

    if sign < 0:
        digits.append('-')

    digits.reverse()

    res = ''.join(digits)

    return res.upper()


def reset_global_vars():
    # Shared Variables
    global totalSuccess
    global totalFailures
    global failedSectorList
    totalSuccess = 0
    totalFailures = 0
    failedSectorList = []


if __name__ == "__main__":

    parser = ArgumentParser()
    parser.add_argument("-m", "--multiplier", metavar="NUMSECTORS", help="Number of sectors to read at a time")
    parser.add_argument("-t", "--threads", metavar="NUMTHREADS", help="Number of threads to use")
    args = parser.parse_args()

    try:
        # Init
        if args.threads:
            numThreads = int(args.threads)
        else:
            numThreads = 4

        if args.multiplier:
            multiplier = int(args.multiplier)
        else:
            multiplier = 2048

        data_lock = threading.Lock()

        initLogDir()

        # Get disks to be compared
        compare_list = get_compare_disk_list()
        compare_list.sort()

        if len(compare_list) % 2 == 0 and len(compare_list) != 0:

            compare_pairs = get_compare_pairs(compare_list)
            res_list = []

            for sourceDisk, clonedDisk in compare_pairs:

                compare_logger("Initializing disk comparison.", "info")

                sourceDiskPath = sourceDisk
                clonedDiskPath = clonedDisk

                # Log disks to be compared
                compare_logger("Comparing %s against %s" % (sourceDiskPath, clonedDiskPath), "info")

                # Get Disks Handles
                compare_logger("Initializing disk handles for reading disks.", "info")
                diskHandlePairList = getDiskHandlePairList(
                    numThreads, sourceDiskPath, clonedDiskPath)

                # Get Disk Sector Info
                compare_logger("Reading disk sector information.", "info")
                bytesPerSector, totalSectors = getDiskSectorInfo(sourceDiskPath)
                compare_logger("BytesPerSector: %d, TotalSectors: %d" % (bytesPerSector, totalSectors), "info")

                # Calcute offset for each disk handle
                compare_logger("Calculating offset for each disk handle.", "info")
                diskHandleOffset = calculateDiskHandleOffset(
                    numThreads, bytesPerSector, totalSectors)

                # Adding calculated offset to each disk handle
                compare_logger("Appending offset to each disk handle.", "info")
                diskHandlePairListOffset = []

                for pair, offset in zip(diskHandlePairList, diskHandleOffset):
                    x = setDiskHandlePairOffset(pair, offset)
                    diskHandlePairListOffset.append(x)

                # Calculate offset limit for each disk handle
                compare_logger("Calculating offset limit for each disk handle.", "info")
                offsetLimitList = getOffsetLimitList(
                    diskHandleOffset, bytesPerSector, totalSectors)

                # Spawn threads for reading the disks
                compare_logger("Initializing disk reader threads.", "info")
                readerThreads = getReaderThreads(
                    diskHandlePairListOffset,
                    diskHandleOffset,
                    offsetLimitList,
                    bytesPerSector,
                    totalSectors,
                    multiplier)

                # Start the threads
                compare_logger("Reading disks using %d threads." % (numThreads), "info")
                for i in range(numThreads):
                    readerThreads[i].start()

                # Wait for all threads to complete reading the disks
                for i in range(numThreads):
                    readerThreads[i].join()
                compare_logger("Disk read complete.", "info")

                # Release all the disk handles
                closeDiskHandlePairList(diskHandlePairList)

                # Log results
                compare_logger("Total Mathches: %d" % (totalSuccess), "info")
                compare_logger("Total Mismatches: %d" % (totalFailures), "info")

                timestr = time.strftime("%d%m%Y-%H%M%S")
                mismatch_log = 'C:\\CompareLogs\\' + "compare_mismatch" + "_" + timestr + ".log"
                with open(mismatch_log, 'w') as f:
                    f.write("Comparing %s against %s\n" % (sourceDiskPath, clonedDiskPath))
                    failedSectorList.sort()
                    div = bytesPerSector * multiplier
                    extentList = [int2base(math.floor(f / div), 32) for f in failedSectorList]  # Dec to Base32
                    for item in extentList:
                        f.write("%s\n" % item)
                compare_logger("Mismatch Sector List written to %s" % mismatch_log, "info")
                res_list.append(True)

                reset_global_vars()

            if all(res_list):
                powershell_output("success")

        else:
            raise Exception("Invalid number of disks for comparison.")

    except Exception as exp:
        compare_logger(str(exp), "error")
        powershell_output("failure")