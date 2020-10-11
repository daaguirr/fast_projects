# import pikepdf

# pdf = pikepdf.open('/Users/tdc/Downloads/A05301.pdf')
# pdf.save('extractable.pdf')

import pandas as pd
from pdfreader import SimplePDFViewer
import pprint


def is_rut(string: str):
    import re
    return re.match(r".*\.\d\d\d\.\d\d\d-\w", string) is not None


fd = open('extractable.pdf', "rb")
lines = []

viewer = SimplePDFViewer(fd)

cnt = 0
while True:
    try:
        viewer.render()
        strings = viewer.canvas.strings
        bb = list(filter(lambda x: 'PADRÓN ELECTORAL' not in x, strings))
        current_line = []
        for i in range(len(bb) - 1):
            if is_rut(bb[i + 1]):
                lines.append(current_line)
                current_line = [bb[i]]
            else:
                current_line.append(bb[i])

        lines.append(current_line[:7])
        cnt += 1
        if cnt == 2:
            break
        viewer.next()
    except StopIteration:
        break

pprint.pprint(lines)
