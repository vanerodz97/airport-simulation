import pandas as pd
from datetime import datetime
import datetime as dt
import time

def datetimeToString(d):
    iso = str(d)
    iso2 = iso.split("1900-01-01 ")[1]
    iso3 = iso2.split(":00")[0]
    return iso3

if __name__ == "__main__":
    df = pd.read_csv("./all_terminal_arrival.csv")
    estimated_list = df["Estimated"].tolist()

    final_list = []
    timetup = time.gmtime()

    se = set()
    for e in estimated_list:
        if e.startswith("上午"):
            ss = e.strip("上午")
            e = ss + " am"
            flag = 1
        else:
            ss = e.strip("下午")
            e = ss + " pm"
            flag = 0

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

        final_list.append(iso)

    print(final_list)

    print(len(se))
    print(len(df.index))

    count = -1

    fr = open("./all_terminal_arrival.csv", "r")
    rw = open("./updated_all_terminal_arrival.csv", "w")
    for eachline in fr:
        print(eachline.strip())
        new_line = eachline.replace(estimated_list[count], final_list[count])
        count += 1
        rw.write(new_line)
