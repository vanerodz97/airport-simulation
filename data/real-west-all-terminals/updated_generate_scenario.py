import sys
import os
import random
import logging
import pandas as pd
import math

from utils import export_to_json, create_output_folder

dir_path = os.path.dirname(os.path.realpath(__file__))
REAL_DEPARTURE_PATH = dir_path + "/updated_all_terminal_departure.csv"
REAL_ARRIVAL_PATH = dir_path + "/updated_all_terminal_arrival.csv"
OUTPUT_FOLDER = dir_path + "/build/"

# Setups logger
logger = logging.getLogger(__name__)
logger_handler = logging.StreamHandler(sys.stdout)
logger_handler.setFormatter(logging.Formatter('%(asctime)s %(message)s'))
logger_handler.setLevel(logging.DEBUG)
logger.addHandler(logger_handler)
logger.setLevel(logging.DEBUG)

departure_flight_template = {
    "airport": "SFO",
    "runway": "1L/19R",
}

arrival_flight_template = {
    "airport": "SJC",
    "runway": "10R/28L",
}

spots = ["S1", "S2", "S3", "S5", "S6", "S7", "S8", "S9", "S11"]

# Gates are updated with the gate numbering being used from 2019 onward 
spots_to_gates = {
    "S1": ["A3", "A4", "A5", "A9", "A10", "A12", "A15"],
    "S2": ["A1", "A2", "A6", "A7", "A8", "A11", "A13", "A14", 
            "B1", "B2", "B4", "B5", "B10", "B11", "B15", "B16", "B19"
            "B20", "B26", "B27", "B25"],
    "S3": ["B6", "B7", "B8", "B18", "B17", "B13", "B12", "B9", 
            "C2", "C4", "C6", "C8", "C10"],
    "S5": ["C3", "C5", "C7", "C9", "C11", "D1", "D2", "D3", "D4",
           "D5", "D6", "D7", "D8", "D9"],
    "S6": ["D10", "D11", "D12", "D14", "D15", "D16", "D17", "D18", "E4",
            "E5", "E7", "E9", "E11"],
    "S7": ["E8", "E6", "E13", "E12", "E10", "E5"],
    "S8": ["F9", "F11", "F13", "F15", "F22", "F21"],
    "S9": ["G1", "G2", "G5", "G6", "G9", "G10", "F4", "F3", "F3A", "F2", "F1", 
            "F12", "F14", "F16", "F17", "F18", "F19", "F20"],
    "S11": ["G3", "G4", "G7", "G8", "G11", "G12", "G13", "G14"],
    "S10": ["E3", "E2", "E1", "F5", "F6", "F7", "F8", "F10"]
}

inters = ["I1", "I2", "I3", "I4", "I5", "I6", "I7", "I8", "I9", "I10",
          "I11","I12"]

# Some terminals may be missing, since there various gates that have the same location
# Was not tested on the 2021 Practicum, because the data set used was from 2018 and this 
# numbering is from 2019 onward. 
terminal_gates = [
    ['B18', 'C5', 'B12', 'C3', 'C8', 'B9', 'C4', 'C2', 'C10', 'B6',
     'B17', 'B13', 'C11', 'C9', 'B7', 'B8', 'C6', 'B1', 'B2', 'B4', 'B14',
     'B3', 'B10', 'B16', 'B20', 'B27', 'B25', 'B23', 'B22', 'B21', 'C1'],

    ["D1", "D9", "D6", "D5", "D7", "D3", "D4", "D8", "D11",
     "D10", "D12", "D16", "D15", "D17", "D2", "C7", "D18", 'D14', 'D2'],

    ['F17', 'E2', 'F3', 'F12', 'F15', 'E12', 'F4', 'F1', 'F10', 'F7', 'F20', 'F13',
     'F11', 'F6', 'G8', 'E11', 'F16', 'E8', 'E7', 'E1', 'E9', 'F21',
     'E5', 'E6', 'F5', 'F2', 'E10', 'F9', 'F3A', 'F18', 'E13', 'F22', 'E3',
     'F19', 'F14', 'E4'],

    ['G6', 'G2', 'G14', 'A3', 'G4', 'G1', 'G11', 'A9',
     'A7', 'G10', 'A12', 'G3', 'A11', 'G8', 'A2', 'G7', 'G5', 'A4',
     'A8', 'A10', 'G13', 'G12', '67', 'G101', 'A5', 'G9', 'G91',
     'A6']
]


# 58A, 60, B14(node inf)

def get_departure_from_csv():
    departures = []
    df = pd.read_csv(REAL_DEPARTURE_PATH)
    size = len(df.index)
    airline_list = df["Airline"].tolist()
    terminal_list = df["Terminal"].tolist()
    gate_list = df["Gate"].tolist()
    flight_list = df["Flight"].tolist()
    estimated_list = df["Estimated"].tolist()
    scheduled_list = df["Scheduled"].tolist()
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
        new_flight["callsign"] = airline_list[i].replace(" Airlines", "") + "-" \
                                 + str(
            flight_list[i]) + "-D"
        new_flight["time"] = set_new_time(
            estimated_list[i])
        new_flight["appear_time"] = set_new_time(
            scheduled_list[i])
        for k, v in spots_to_gates.items():
            if new_flight["gate"] in v:
                new_flight["spot"] = k
                break
        departures.append(new_flight)
    return departures


def get_arrival_from_csv():
    arrivals = []
    df = pd.read_csv(REAL_ARRIVAL_PATH)
    size = len(df.index)
    airline_list = df["Airline"].tolist()
    terminal_list = df["Terminal"].tolist()
    gate_list = df["Gate"].tolist()
    flight_list = df["Flight"].tolist()
    estimated_list = df["Estimated"].tolist()
    scheduled_list = df["Scheduled"].tolist()
    for i in range(1, size):
        new_flight = arrival_flight_template.copy()
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
        new_flight["callsign"] = airline_list[i].replace(" Airlines",
                                                         "") + "-" + str(
            flight_list[i]) + "-A"
        new_flight["time"] = set_new_time(
            estimated_list[i])
        new_flight["appear_time"] = set_new_time(
            scheduled_list[i])
        for k, v in spots_to_gates.items():
            if new_flight["gate"] in v:
                new_flight["spot"] = k
                break
        arrivals.append(new_flight)
    return arrivals


def set_new_time(new_time):
    if ":" not in new_time:
        minute = 0
        hour = int(new_time)
    else:
        s = new_time.split(":")
        hour = int(s[0])
        minute = int(s[1])
    return "%02d%02d" % (hour, minute)


def set_time(str_time):
    hour = 0
    minute = 0
    if str_time.startswith("上午"):
        ss = str_time.strip("上午")
        s = ss.split(':')
        if int(s[0]) == 12:
            hour = 0
        else:
            hour = int(s[0])
        minute = int(s[1])
    elif str_time.startswith("下午"):
        ss = str_time.strip("下午")
        s = ss.split(':')
        if int(s[0]) == 12:
            hour = 12
        else:
            hour = int(s[0]) + 12
        minute = int(s[1])
    if hour > 23 or hour < 0:
        print(hour)
        print(str_time)
    return "%02d%02d" % (hour, minute)


def main():
    departures = get_departure_from_csv()
    arrivals = get_arrival_from_csv()
    logger.debug("Number of departures" + str(len(departures)))
    logger.debug("Number of arrivals" + str(len(arrivals)))
    scenario = {"arrivals": arrivals, "departures": departures}
    # print(scenario)

    create_output_folder(OUTPUT_FOLDER)
    output_filename = OUTPUT_FOLDER + "scenario.json"
    export_to_json(output_filename, scenario)
    logger.debug("Generating gate spots data")
    gate_spots_filename = OUTPUT_FOLDER + "gates_spots.json"
    export_to_json(gate_spots_filename, spots_to_gates)
    logger.debug("Done")


if __name__ == "__main__":
    airport_data_folder = sys.argv[0] + "/"
    main()