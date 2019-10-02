from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
import time
import csv

url = 'https://www.flysfo.com/flight-info/flight-status'


def get_table_info(headers, name):
    csv_file = []
    try:
        while True:
            time.sleep(3)
            result = browser.find_element_by_id("flight_results")
            body = result.find_element_by_tag_name('tbody')
            body_rows = body.find_elements_by_tag_name('tr')
            for row in body_rows:
                data = row.find_elements_by_tag_name('td')
                file_row = {}
                for (datum, key) in zip(data, headers):
                    if key == 'details':
                        break
                    file_row[key] = datum.text
                csv_file.append(file_row)
            next = browser.find_element_by_id("flight_results_next")
            next.click()
    except:
        pass
    browser.close()

    with open(name, 'a') as f:
        f_csv = csv.DictWriter(f, headers)
        f_csv.writeheader()
        f_csv.writerows(csv_file)


if __name__ == "__main__":
    #  departure
    header = ['Airline', 'Departing to', 'Flight', 'Scheduled', 'Estimated', 'Remarks', 'Terminal', 'Gate', 'Details']
    browser = webdriver.Chrome(ChromeDriverManager().install())
    browser.get(url)
    browser.find_elements_by_name('codeshare')[0].click()
    get_table_info(header, 'all_terminal_departure.csv')
    #  arrival
    header = ['Airline', 'Arriving From', 'Flight', 'Scheduled', 'Estimated', 'Remarks', 'Terminal', 'Gate', 'Details']
    browser = webdriver.Chrome(ChromeDriverManager().install())
    browser.get(url)
    browser.find_elements_by_name('codeshare')[0].click()
    browser.find_element_by_id('r2').click()
    get_table_info(header, 'all_terminal_arrival.csv')
