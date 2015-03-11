import os
import sys
import shutil
import json


def dict_to_folders(dictionary, relativepath):
    for k, i in dictionary.iteritems():
        print "Making dir: " + k
        os.makedirs("{0}/{1}".format(relativepath, k))
        if isinstance(i, dict):
            newrelativepath = "{0}/{1}".format(relativepath, k)
            dict_to_folders(i, newrelativepath)


def delete_folder(path):
    shutil.rmtree(path)


def delete_file(path):
    os.remove(path)


def move_folder(source, destination):
    shutil.move(source, destination)


def write_json_file(data, filepath):
    """
    Write JSON data to the data file.
    """
    JSONdata = json.dumps(data)
    datafile = open(filepath, "w")
    datafile.write(JSONdata)
    datafile.close()