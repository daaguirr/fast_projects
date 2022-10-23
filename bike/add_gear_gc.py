import dataclasses
import logging
import traceback
import json
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from environs import Env

env = Env()
env.read_env()

logFormatter = logging.Formatter("%(asctime)s [%(threadName)-12.12s] [%(levelname)-5.5s]  %(message)s")
rootLogger = logging.getLogger()
rootLogger.setLevel(logging.INFO)

consoleHandler = logging.StreamHandler()
consoleHandler.setFormatter(logFormatter)
consoleHandler.setLevel(logging.NOTSET)
rootLogger.addHandler(consoleHandler)

FILE_PATH = env.str("TXT_ACTIVITIES_URL_PATH")
GEAR_CONFIG_PATH = env.str("GEAR_CONFIG_PATH")
CYCLING_TYPE = env.str("CYCLING_TYPE")
GC_USERNAME = env.str("GC_USERNAME")
GC_PWD = env.str("GC_PWD")
DRIVER_PATH = env.str("DRIVER_PATH")
START_TIMESTAMP = env.str("START_TIMESTAMP", "")


@dataclasses.dataclass
class GearConfig:
    id: str
    name: str
    cycling_type: str
    added_timestamp: str

    def add_gear(self, driver: webdriver.Firefox, activity_timestamp: str):
        if activity_timestamp < self.added_timestamp:
            return

        li = driver.find_element(By.ID, f"edit-gear-{self.id}")
        if li.get_attribute('class') != "active":
            li.click()
            time.sleep(2)


def try_catch_driver(fn):
    def inner(*args, **kwargs):
        driver: webdriver = args[0]
        url: str = args[1]
        try:
            return fn(*args, **kwargs)
        except Exception as e:
            rootLogger.error(f"ERROR ON {url}\n{e}\n{driver.page_source}\n{traceback.format_exc()}")
            driver.close()

    return inner


with open(GEAR_CONFIG_PATH, "r") as f:
    GEAR_CONFIG = json.load(f)

with open(FILE_PATH, "r") as f:
    DATA_RAW = f.readlines()

GEAR_CONFIG = [GearConfig(**item) for item in GEAR_CONFIG if item["cycling_type"] == CYCLING_TYPE]


def add_gear(driver: webdriver.Firefox, timestamp: str):
    for gear in GEAR_CONFIG:
        gear.add_gear(driver, timestamp)


@try_catch_driver
def process_url(driver: webdriver.Firefox, url: str, timestamp: str):
    driver.get(url)
    time.sleep(6)
    driver.find_element(By.CLASS_NAME, 'toggle-add-gear').click()
    time.sleep(1)
    rootLogger.info("ON GEAR PAGE")
    add_gear(driver, timestamp)
    rootLogger.info(f"FINISHED : {url}")


@try_catch_driver
def login(driver: webdriver.Firefox, url: str = "https://connect.garmin.com/signin/"):
    driver.get(url)
    time.sleep(5)

    driver.switch_to.frame(driver.find_elements(By.TAG_NAME, 'iframe')[0])
    time.sleep(1)

    driver.find_element(By.ID, 'username').send_keys(GC_USERNAME)
    driver.find_element(By.ID, 'password').send_keys(GC_PWD)
    time.sleep(1)

    driver.find_element(By.ID, 'login-btn-signin').click()
    time.sleep(5)

    rootLogger.info("LOGIN SUCCESS")


def main():
    data = [d.split(';') for d in DATA_RAW]

    try:
        driver = webdriver.Firefox(executable_path=DRIVER_PATH)
        rootLogger.info("DRIVER STARTED")
    except Exception as e:
        rootLogger.error(f"ERROR ON \n{e}\nBROWSER INIT ERROR")
        return

    login(driver)
    start_time = time.time()

    for timestamp, url in data:
        if timestamp < START_TIMESTAMP:
            continue
        process_url(driver, url, timestamp)

    rootLogger.info('Time taken = {} seconds'.format(time.time() - start_time))


if __name__ == '__main__':
    main()
