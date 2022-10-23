import bs4
import datetime

from environs import Env

env = Env()
env.read_env()

with open(env.str("HTML_ACTIVITIES_PATH"), "r") as f:  # HTML OF GARMIN CONNECT ACTIVITIES VIEW
    raw = f.read()

soup = bs4.BeautifulSoup(raw, "lxml")
items = soup.find_all('li', attrs={'class': 'list-item animated row-fluid'})

items_2 = []
for item in items:
    tmp_data = item.find('div', attrs={'class': 'pull-left activity-date date-col'})
    tmp_url = item.find('a', attrs={'class': 'inline-edit-target'})
    items_2.append([
        datetime.datetime.strptime(tmp_data.text.replace('\n', ' '), " %b %d %Y "),
        'https://connect.garmin.com' + tmp_url.get('href')
    ])

final_text = '\n'.join([f"{item[0].isoformat()};{item[1]}" for item in items_2])
print(final_text)
