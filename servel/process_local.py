from multiprocessing import Pool
import os
from process_with_recovery import process
import json

with open('servel/local_config.json', 'r') as f:
    config = json.load(f)

OUT_FOLDER = config["OUT_FOLDER"]
INPUT_FOLDER = config["INPUT_FOLDER"]

file_list = config["file_list"]


def wrapper(tt):
    return process(*tt)


if __name__ == '__main__':
    data = [(os.path.join(INPUT_FOLDER, f), OUT_FOLDER) for f in file_list]

    with Pool(2) as p:
        p.map(wrapper, data, chunksize=1)
    # for d in data:
    #    wrapper(d)
