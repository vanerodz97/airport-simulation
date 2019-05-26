import pandas as pd
import json
import datetime

# str(datetime.timedelta(seconds=666))


def aircraft_data(name, hold, reach_destination, lat, lng):
    return {"callsign": name,
            "state": "stop" if reach_destination else "moving",
            "is_delayed": hold,
            "location": {"lat": lat, "lng": lng},
            "itinerary": [], "itinerary_index": 1,
            "uncertainty_delayed_index": [], "scheduler_delayed_index": [],
    }



COL_NAMES = ["t", "id", "edge", "distance", "hold", "reach_destination", "lat", "lng"]

OUTPUT_FILE = "states.json"

f = open(OUTPUT_FILE, "w+")

data = pd.read_csv('schedule.txt', delimiter='\t', names=COL_NAMES)

json_data = {}

for _, row in data.iterrows():
    if row["t"] not in json_data:
        json_data[float(row["t"])] = []
    json_data[float(row["t"])].append((row["id"],
                                     bool(row["hold"]),
                                     bool(row["reach_destination"]),
                                     float(row["lat"]),
                                     float(row["lng"]),
    ))

json_data = sorted(json_data.items())


for t, data in json_data:

    row = {"time": str(datetime.timedelta(seconds=int(t))),
           "aircrafts": [aircraft_data(*a) for a in data]}
    f.write(json.dumps(row) + "\n")


# import pdb; pdb.set_trace()
