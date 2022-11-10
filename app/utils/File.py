import pandas as pd
import os
import zipfile
from glob import glob
from pathlib import Path

def get_uploads_files(dir_name=r'.\uploads'):
    if os.path.exists(dir_name) and os.path.isdir(dir_name):
        if not os.listdir(dir_name):
            print("Directory ", dir_name, " is empty")
            return []
        else:
            print("Directory ", dir_name, " is not empty")
            return os.listdir(dir_name)

    else:
        print("Directory ", dir_name, " doesn't exist")
        return []


def purge_file(dir_name=r'.\uploads'):
    if get_uploads_files(dir_name) != []:
        for file in get_uploads_files(dir_name):
            os.remove(os.path.join(dir_name, file))


def validate_file_epow(file):
    col30 = {'Bus kV', 'Sym Amps'}
    col1 = {"Bus kV", "Sym Amps", "X/R Ratio", "Mult Factor", "Asym Amps", "Equip Type", "Duty Amps"}
    try:
        df = pd.DataFrame(pd.read_csv(file, skiprows=1, index_col=0))
    except:
        try:
            df = pd.DataFrame(pd.read_excel(file, skiprows=7, index_col=0, engine='openpyxl'))
        except openpyxl.utils.exceptions.InvalidFileException as notXL:
            return -1

    if col1.issubset(df.columns.to_list()) or col30.issubset(df.columns.to_list()):
        return 0
    else:
        return -1

def dirname(full_path):
    return os.path.dirname(full_path)

def full_paths(upload_dir):
    return glob(os.path.join(upload_dir, "*"))

def create_dir_if_dont_exist(dir_name):
    Path(dir_name).mkdir(parents=True, exist_ok=True)
    return Path(dir_name)


def zip_files(list_of_files, zip_file_name=''):
    """
    Generate a zip file from a list of files in the location of the first file of the list
    :param list_of_files:
    :type list_of_files:
    :param zip_file_name:
    :type zip_file_name:
    :return:
    :rtype:
    """

    if zip_file_name == '':
        file_name = os.path.dirname(list_of_files[0])

    #the current working directory is changed to the directory of the first file in the list
    # return to the previous directory after saving
    previous_dir = os.getcwd()
    os.chdir(os.path.dirname(os.path.abspath(list_of_files[0])))

    with zipfile.ZipFile(zip_file_name + '.zip',
                         "w",
                         zipfile.ZIP_DEFLATED,
                         allowZip64=True) as zf:
        for name in list_of_files:
            zf.write(os.path.split(name)[-1])

    os.chdir(previous_dir)
    return os.path.abspath(zf.filename)


def decode_str_filename(str_filename):
    try:
        test_str = eval(str_filename)
        if len(test_str[0]) > 1:
            return test_str, 'list'
        else:
            return str_filename, 'str'
    except NameError or IndexError:
        return str_filename, 'str'


def add_to_list_file(filename, *items):
    with open(filename, 'a') as file:
        for item in items:
            file.write(item)
            file.write('\n')
    file.close()


def get_items_from_file(filename):
    if os.path.exists(filename):
        with open(filename, 'r') as file:
            lines = [line.rstrip('\n') for line in file]
        file.close()

        return lines

    else:
        return []


def get_items_from_json(filename):
    if os.path.exists(filename):
        with open('data.json') as json_file:
            data = json.load(json_file)

        return data

