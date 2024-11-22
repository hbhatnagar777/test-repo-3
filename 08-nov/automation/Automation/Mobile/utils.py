"""
File operations related to edge app.
"""
import os.path
import hashlib


def get_apk_hash(file_path):
    """
    Generates hash value of apk file
    Args:
        file_path:(String)Any file name with path
    Returns: hash value of any specific file
    """
    data = open(file_path, "rb").read()
    hash_value = hashlib.md5(data).hexdigest()
    return hash_value


def read_hash_file(hash_text_path):
    """
    Reads specified hash file and returns the string
    Args:
        hash_text_path: (String) specify the hash file path with the file name
    Returns: (string) content of hash file
    """
    file_pointer = open(hash_text_path, "r")
    return file_pointer.readline()


def create_hash_file(hash_text_path, apk_hash_value):
    """
    Hash file will be written for specified apk file
    Args:
        hash_text_path: (string) text file path which contains hash value
        apk_hash_value: hash value of apk file
    """
    file_pointer = open(hash_text_path, "w")
    file_pointer.write(apk_hash_value)
    file_pointer.close()


def compare_hash(apk_file_path, hash_text_path):
    """
    Verifies hash string present in text file and hash of apk file.
    Args:
        apk_file_path:(String) apk file path
        hash_text_path:(String) hash file path
    Returns:True/False by comparing hash text file with hash of apk file
    """
    apk_hash_value = get_apk_hash(apk_file_path)
    # if hash text not found return false
    if os.path.exists(hash_text_path) is False:
        return False
    text_hash_value = read_hash_file(hash_text_path)
    if text_hash_value == apk_hash_value:
        return True
    return False


def is_apk_file_updated(local_apk_file_path):
    """
    Verifies if apk file has same hash as its present in hash text file
    Args:
        local_apk_file_path:(String) path of apk file
        hash_text_path:(String) path of text file which contains hash
    Returns:True if apk file is updated, return False if apk file not updated
    """
    hash_text_path = local_apk_file_path + r"_apk_hash.txt"
    if compare_hash(local_apk_file_path, hash_text_path) is False:
        apk_hash_value = get_apk_hash(local_apk_file_path)
        create_hash_file(hash_text_path, apk_hash_value)
        return True
    return False
