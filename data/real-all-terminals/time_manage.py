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
    scheduled_list = df["Scheduled"].tolist()
    airline_list = df["Airline"].tolist()
    flight = df["Flight"].tolist()
    gate = df["Gate"].tolist()
    terminal = df["Terminal"].tolist()

    final_estimated_list = []
    final_scheduled_list = []
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

        appear_d = d - dt.timedelta(minutes=1)
        appear_s = datetimeToString(appear_d)

        final_estimated_list.append(iso)
        final_scheduled_list.append(appear_s)

    print(final_estimated_list)

    print(len(se))
    print(len(df.index))

    # count = -1
    # fr = open("./all_terminal_arrival.csv", "r")
    # rw = open("./updated_all_terminal_arrival.csv", "w")
    # for eachline in fr:
    #     print(eachline.strip())
    #     new_line = eachline.replace(estimated_list[count],
    #                                 final_estimated_list[count]).replace(
    #         scheduled_list[count], final_scheduled_list[count])
    #     count += 1
    #     rw.write(new_line)

    df = pd.DataFrame({'Scheduled': final_scheduled_list, 'Estimated':
        final_estimated_list, 'Airline': airline_list, 'Flight': flight,
                       'Gate': gate,'Terminal':terminal})
    df.to_csv('./updated_all_terminal_arrival.csv', encoding='gbk')
