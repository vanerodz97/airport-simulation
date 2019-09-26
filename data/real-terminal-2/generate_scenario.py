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

spots = ["S2", "S3", "S4"]

spots_to_gates = {"S2": ["51A", "51B", "50A", "52", "50B"],
                  "S3": ["58A", "59A", "58B", "59B", "56A", "56B", "57"],
                  "S4": ["53", "54A", "54B", "55"]}

gates = ["50A", "55", "53", "52", "54A", "51A", "51B", "54B", "56B", "56A",
         "57", "59A", "58B", "58A", "59B", "50B"]


def get_departure_from_csv():
    departures = []
    df = pd.read_csv("./terminal2-departure.csv")
    size = len(df.index)
    airline_list = df["Airline"].tolist()
    name_list = df["Flight"].tolist()
    gate_list = df["Gate"].tolist()
    flight_list = df["Flight"].tolist()
    estimated_list = df["Estimated"].tolist()
    for i in range(1, size):
        new_flight = departure_flight_template.copy()
        if type(gate_list[i]) is not str and  math.isnan(gate_list[i]):
            new_flight["gate"] = random.choice(gates)
        # 45A 45B
        elif gate_list[i] not in gates:
            continue
        else:
            new_flight["gate"] = gate_list[i]
        new_flight["model"] = flight_list[i]
        new_flight["callsign"] = airline_list[i] + "-" + str(name_list[i])
        new_flight["time"] = new_flight["appear_time"] = set_time(
            estimated_list[i])
        for k, v in spots_to_gates.items():
            if new_flight["gate"] in v:
                new_flight["spot"] = k
                break
        departures.append(new_flight)
    return departures


def get_arrival_from_csv():
    arrivals = []
    df = pd.read_csv("./terminal2-arrival.csv")
    size = len(df.index)
    airline_list = df["Airline"].tolist()
    name_list = df["Flight"].tolist()
    gate_list = df["Gate"].tolist()
    flight_list = df["Flight"].tolist()
    estimated_list = df["Estimated"].tolist()
    for i in range(1, size):
        new_flight = arrival_flight_template.copy()
        if type(gate_list[i]) is not str and  math.isnan(gate_list[i]):
            new_flight["gate"] = random.choice(gates)
        # 45A 45B
        elif gate_list[i] not in gates:
            continue
        else:
            new_flight["gate"] = gate_list[i]
        new_flight["model"] = flight_list[i]
        new_flight["callsign"] = airline_list[i] + "-" + str(name_list[i])
        new_flight["time"] = new_flight["appear_time"] = set_time(
            estimated_list[i])
        for k, v in spots_to_gates.items():
            if new_flight["gate"] in v:
                new_flight["spot"] = k
                break
        arrivals.append(new_flight)
    return arrivals


def set_time(str_time):
    s = str_time.split(" ")
    hour = 0
    minute = 0
    if s[1] == 'AM':
        h_m = s[0].split(":")
        hour = int(h_m[0])
        minute = int(h_m[1])
    elif s[1] == 'PM':
        h_m = s[0].split(":")
        hour = int(h_m[0]) + 12
        minute = int(h_m[1])
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
    logger.debug("Generating gate spots data")
    gate_spots_filename = OUTPUT_FOLDER + "gates_spots.json"
    export_to_json(gate_spots_filename, spots_to_gates)
    logger.debug("Done")


if __name__ == "__main__":
    main()
