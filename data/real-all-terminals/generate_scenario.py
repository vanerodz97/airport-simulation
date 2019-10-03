import sys
import random
import logging
import numpy
import csv
import pandas as pd
import numpy as np
import math

from utils import export_to_json, create_output_folder

OUTPUT_FOLDER = "./build/"

# Setups logger
logger = logging.getLogger(__name__)
logger_handler = logging.StreamHandler(sys.stdout)
logger_handler.setFormatter(logging.Formatter('%(asctime)s %(message)s'))
logger_handler.setLevel(logging.DEBUG)
logger.addHandler(logger_handler)
logger.setLevel(logging.DEBUG)

departure_flight_template = {
    "airport": "SJC",
    "runway": "10R/28L",
}

arrival_flight_template = {
    "airport": "SJC",
    "runway": "1R/19L",
}

# spots = ["S1", "S2", "S3", "S4", "S5", "S6", "S7", "S8"]
#
# spots_to_gates = {}
#
# # spots_to_gates = {"S2": ["51A", "51B", "50A", "52", "50B"],
# #                   "S3": ["58A", "59A", "58B", "59B", "56A", "56B", "57"]}

terminal_gates = [
    ['B18', 'B14', '43', 'B12', '41', '46', 'B9', '42', '40', '48', 'B6',
     'B17', 'B13', '47', '45B', 'B7', 'B8', '44'],
    ["50A", "55", "53", "52", "54A", "51A", "51B", "54B", "56B",
     "56A",
     "57", "59A", "58B", "58A", "59B", "50B", "45A", "59C"],
    ['87', '71A', '73', '81', '84C', '66', '72', '75', '78', '77B', '90', '83',
     '80', '77A', '84D', 'G97', '64', '85', '68', '62', '71B', '63', '88',
     '61', '69', '76', '82', '74', '67', '79', '73A', '87A', '65', '86', '70',
     '89', '84B', '60', '84A'],
    ['G98', 'G94', 'G101B', 'A3', 'G93', 'G92', 'G99A', 'A9',
     '75', 'A7', 'G102', 'A12', '53', 'A11', 'G97', 'A2', 'G95', 'G96', 'A4',
     'A8', 'A10', '68', 'G101A', 'G99', '67', 'G101', 'A5', 'G100', 'G91',
     'A6']]


def get_departure_from_csv():
    departures = []
    df = pd.read_csv("./all_terminal_departure.csv")
    size = len(df.index)
    airline_list = df["Airline"].tolist()
    terminal_list = df["Terminal"].tolist()
    gate_list = df["Gate"].tolist()
    flight_list = df["Flight"].tolist()
    estimated_list = df["Estimated"].tolist()
    for i in range(1, size):
        new_flight = departure_flight_template.copy()
        if terminal_list[i] == '1':
            new_flight["terminal"] = 1
        elif terminal_list[i] == '2':
            new_flight["terminal"] = 2
        elif terminal_list[i] == '3':
            new_flight["terminal"] = 3
        elif terminal_list[i] == 'Int\'l':
            new_flight["terminal"] = 4
        if type(gate_list[i]) is not str and math.isnan(gate_list[i]):
            new_flight["gate"] = random.choice(terminal_gates[int(new_flight[
                                                                      "terminal"]) - 1])
        elif gate_list[i] not in terminal_gates[int(new_flight[
                                                        "terminal"]) - 1]:
            continue
        else:
            new_flight["gate"] = gate_list[i]

        new_flight["model"] = flight_list[i]
        new_flight["callsign"] = airline_list[i] + "-" + str(flight_list[i])
        new_flight["time"] = new_flight["appear_time"] = set_time(
            estimated_list[i])
        # for k, v in spots_to_gates.items():
        #     if new_flight["gate"] in v:
        #         new_flight["spot"] = k
        #         break
        departures.append(new_flight)
    return departures


def get_arrival_from_csv():
    arrivals = []
    df = pd.read_csv("./all_terminal_arrival.csv")
    size = len(df.index)
    airline_list = df["Airline"].tolist()
    terminal_list = df["Terminal"].tolist()
    gate_list = df["Gate"].tolist()
    flight_list = df["Flight"].tolist()
    estimated_list = df["Estimated"].tolist()
    for i in range(1, size):
        new_flight = departure_flight_template.copy()
        if terminal_list[i] == '1':
            new_flight["terminal"] = 1
        elif terminal_list[i] == '2':
            new_flight["terminal"] = 2
        elif terminal_list[i] == '3':
            new_flight["terminal"] = 3
        elif terminal_list[i] == 'Int\'l':
            new_flight["terminal"] = 4
        if type(gate_list[i]) is not str and math.isnan(gate_list[i]):
            new_flight["gate"] = random.choice(terminal_gates[int(new_flight[
                                                                      "terminal"]) - 1])
        elif gate_list[i] not in terminal_gates[int(new_flight[
                                                        "terminal"]) - 1]:
            continue
        else:
            new_flight["gate"] = gate_list[i]

        new_flight["model"] = flight_list[i]
        new_flight["callsign"] = airline_list[i] + "-" + str(flight_list[i])
        new_flight["time"] = new_flight["appear_time"] = set_time(
            estimated_list[i])
        # for k, v in spots_to_gates.items():
        #     if new_flight["gate"] in v:
        #         new_flight["spot"] = k
        #         break
        arrivals.append(new_flight)
    return arrivals


def set_time(str_time):
    hour = 0
    minute = 0
    if str_time.startswith("上午"):
        ss = str_time.strip("上午")
        s = ss.split(':')
        hour = int(s[0])
        minute = int(s[1])
    elif str_time.startswith("下午"):
        ss = str_time.strip("下午")
        s = ss.split(':')
        hour = int(s[0]) + 12
        minute = int(s[1])
    return "%02d%02d" % (hour, minute)


def main():
    departures = get_departure_from_csv()
    arrivals = get_arrival_from_csv()
    print(len(departures))
    print(len(arrivals))
    scenario = {"arrivals": arrivals, "departures": departures}
    print(scenario)

    create_output_folder(OUTPUT_FOLDER)
    output_filename = OUTPUT_FOLDER + "scenario.json"
    export_to_json(output_filename, scenario)
    # logger.debug("Generating gate spots data")
    # gate_spots_filename = OUTPUT_FOLDER + "gates_spots.json"
    # export_to_json(gate_spots_filename, spots_to_gates)
    logger.debug("Done")


if __name__ == "__main__":
    main()
