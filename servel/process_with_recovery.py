import os

import pandas as pd
from pdfreader import SimplePDFViewer
from tqdm import tqdm
import json


def is_rut(string: str):
    import re
    return re.match(r".*\d\d\d\.\d\d\d-\w", string) is not None


column_names = ['NOMBRE',
                'C.IDENTIDAD',
                'SEXO',
                'DOMICILIO ELECTORAL',
                'CIRCUNSCRIPCIÓN',
                'MESA']


def process(path: str, output_folder):
    print(f"Starting {path}")

    fd = open(path, "rb")
    viewer = SimplePDFViewer(fd)
    n_pages = viewer.doc.root['Pages']['Count']

    pbar = tqdm(total=n_pages)
    lines = []
    cnt = 1

    _, filename_r = os.path.split(path)
    filename_c, _ = os.path.splitext(filename_r)

    output_path = os.path.join(output_folder, f"{filename_c}.csv")

    recovery_file = os.path.join(output_folder, f"{filename_c}.json")
    if os.path.exists(recovery_file):
        with open(recovery_file, 'r') as f:
            recovery = json.load(f)
        lines = recovery['lines']
        page = recovery['page']
        cnt = page + 1

        viewer.navigate(page + 1)
        pbar.update(page)

    while True:
        try:
            viewer.render()

            strings = viewer.canvas.strings
            bb = list(filter(lambda x: 'PADRÓN ELECTORAL' not in x, strings))
            current_line = []
            started = False

            for i in range(len(bb) - 1):
                if is_rut(bb[i + 1]):
                    if started:
                        lines.append(current_line)
                    current_line = [bb[i]]
                    started = True
                elif started:
                    current_line.append(bb[i])

            lines.append(current_line[:7])

            if cnt % 30 == 0:
                check_point = {
                    'lines': lines,
                    'page': cnt
                }
                with open(recovery_file, 'w') as f:
                    json.dump(check_point, f)
                viewer._pages = dict()

            pbar.update(1)
            cnt += 1
            viewer.next()
            viewer.canvas.inline_images == []

        except Exception as e:
            print(e)
            break
    pbar.close()

    data = []
    for line in lines:
        if len(line) == 6:
            data.append(line)
            continue
        new = line[:6]
        new[5] = line[5] + line[6]
        data.append(new)

    print(f"Converting to csv")
    df = pd.DataFrame(data=data, columns=column_names)
    df.to_csv(output_path, sep=';', index=False)
    print(f"Ending {path}")


def main():
    import sys

    args = sys.argv
    args = args[1:]

    input_file, output_folder, *_ = args
    process(input_file, output_folder)


if __name__ == '__main__':
    main()
