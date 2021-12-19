# %%
import time

from selenium import webdriver
from selenium.common import exceptions
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select


def get_elements(driver):
    elem_list = []
    email = driver.find_element(By.NAME, "email")
    name = driver.find_element(By.NAME, "name")
    password = driver.find_element(By.NAME, "password")
    re_password = driver.find_element(By.NAME, "password-repeat")
    submit = driver.find_element(By.TAG_NAME, "button")
    answer = Select(driver.find_element(By.NAME, "answer"))

    elem_list.append(email)
    elem_list.append(name)
    elem_list.append(password)
    elem_list.append(re_password)
    elem_list.append(answer)
    elem_list.append(submit)
    return elem_list


def send_vals(elem_list):
    elem_list[0].clear()
    elem_list[0].send_keys("eksploracja@eksploracja.kis.p.lodz.pl")

    elem_list[1].clear()
    elem_list[1].send_keys("eksploracja")

    elem_list[2].clear()
    elem_list[2].send_keys("tajnehaslo")

    elem_list[3].clear()
    elem_list[3].send_keys("tajnehaslo")

    elem_list[4].select_by_value("correct")

    elem_list[5].submit()


def main(address='http://127.0.0.1:5000/'):
    # %% Initial vals
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    driver = webdriver.Chrome('./files/chromedriver', options=options)
    driver.get(address)
    # %% expand webpage

    print(f"before click:{len(driver.find_elements(By.TAG_NAME, 'input'))}")

    try:
        elem_list = get_elements(driver)
    except exceptions.NoSuchElementException:
        driver.find_element(By.TAG_NAME, "input").click()

        print(f"after click:{len(driver.find_elements(By.TAG_NAME, 'input'))}")

        elem_list = get_elements(driver)
    # %% send data
    send_vals(elem_list)
    # %% return data
    time.sleep(1)
    print(f"return val:{driver.page_source}")

    # %% close driver
    driver.quit()


if __name__ == '__main__':
    main()
