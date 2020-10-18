import requests
import bs4
import os
import pikepdf
from tqdm import trange

os.makedirs('raw')
os.makedirs('extractable')


def download_file(url):
    local_filename_raw = url.split('/')[-1]
    local_filename = os.path.join('raw', local_filename_raw)
    # NOTE the stream=True parameter below
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        with open(local_filename, 'wb') as f:
            for chunk in r.iter_content(chunk_size=8192):
                # If you have chunk encoded response uncomment if
                # and set chunk_size parameter to None.
                # if chunk:
                f.write(chunk)
    return local_filename, local_filename_raw


res = requests.get("https://www.servel.cl/padron-electoral-definitivo-territorio-nacional/")
soup = bs4.BeautifulSoup(res.content, "lxml")

panels = soup.find_all('div', attrs={'class': 'panel-body postclass'})
links = []
for p in panels:
    links.append(p.find('a').get('href'))

for i in trange(len(links)):
    link = links[i]
    new_file, filename = download_file(link)
    pdf = pikepdf.open(new_file)
    pdf.save(os.path.join('extractable', filename))
    print(filename)
