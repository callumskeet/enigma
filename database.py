#!python3
import string
import os
import json


# credit to reddit user /u/tangerinelion
def read_json(folder, file_name, subdir=""):
    file_path = os.path.join("data", folder, subdir, file_name)
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def make_db(root, subdir):
    database = {}
    for path, folders, files in os.walk(root):
        if path == root:
            for folder in folders:
                database.setdefault(folder, {})
        for model in database.keys():
            database[model].setdefault(subdir, {})
            for file in files:
                if os.path.join(model, subdir) in path:
                    rotor = read_json(model, file, subdir)
                    database[model][subdir].update(rotor)
                elif model in path:
                    rotor = read_json(model, file)
                    database[model].update(rotor)
    return database
