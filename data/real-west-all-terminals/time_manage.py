import pandas as pd
from datetime import datetime
import datetime as dt

OLDARRIVALPATH = "./all_terminal_arrival.csv"
NEWARRIVALPATH = "./updated_all_terminal_arrival.csv"

OLDDEPARTUREPATH = "./all_terminal_departure.csv"
NEWDEPARTUREPATH = "./updated_all_terminal_departure.csv"


def datetimeToString(d):
    iso = str(d)
    # deleting two 23:59 departure aircraft
    iso2 = iso.split("1900-01-01 ")[1]
    iso3 = iso2.split(":00")[0]
    return iso3


def main(OLDPATH, NEWPATH):
    df = pd.read_csv(OLDPATH)
    estimated_list = df["Estimated"].tolist()
    scheduled_list = df["Scheduled"].tolist()
    airline_list = df["Airline"].tolist()
    flight = df["Flight"].tolist()
    gate = df["Gate"].tolist()
    terminal = df["Terminal"].tolist()

    final_estimated_list = []
    final_scheduled_list = []

    se = set()
    for e in estimated_list:
        if e.startswith("上午"):
            ss = e.strip("上午")
            e = ss + " am"
        else:
            ss = e.strip("下午")
            e = ss + " pm"

        d = datetime.strptime(e, "%I:%M %p")
        iso = datetimeToString(d)

        if iso in se:
            d = d + dt.timedelta(minutes=2)
            iso = datetimeToString(d)
            while iso in se:
                d = d + dt.timedelta(minutes=2)
                iso = datetimeToString(d)
            se.add(iso)
        else:
            se.add(iso)

        appear_d = d - dt.timedelta(minutes=1)
        appear_s = datetimeToString(appear_d)

        final_estimated_list.append(iso)
        final_scheduled_list.append(appear_s)

    print(final_estimated_list)

    print(len(se))
    print(len(df.index))

    df = pd.DataFrame({'Scheduled': final_scheduled_list, 'Estimated':
        final_estimated_list, 'Airline': airline_list, 'Flight': flight,
                       'Gate': gate, 'Terminal': terminal})
    df.to_csv(NEWPATH, encoding='gbk')


if __name__ == "__main__":
    main(OLDARRIVALPATH, NEWARRIVALPATH)
    main(OLDDEPARTUREPATH,NEWDEPARTUREPATH)
