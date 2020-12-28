from os import path
import sys

# get contents in format {<content>} {<content>} 
def lines_of(txt):
    ind = 0
    ret = []
    content = ""
    for i in range(len(txt)):
        c = txt[i]
        if c == '{':
            ind += 1
        elif c == '}':
            ind -= 1
            if ind == 0:
                ret.append(content.strip())
                content = ""
        if ind > 0 and not (c == '{' and ind == 1):
            content += c
    return ret

# get names and contents in format <name>: <content>， <name>: <content>
def content_of(txt):
    ind = 0
    colon = 0
    quote = 0
    contents = []
    names = []
    content = ""
    name = ""
    for i in range(len(txt)):
        c = txt[i]
        if c in ('{', '(', '['):
            ind += 1
        elif c in ('}', ')', ']'):
            ind -= 1
        elif c == ':' and quote == 0 and ind == 0:
            colon = (colon + 1) % 2
        elif c == '"':
            quote = (quote + 1) % 2
        if c == ',' and ind == 0 and quote == 0:
            colon = 0
            names.append(name.strip())
            name = ""
            contents.append(content.strip())
            content = ""
        elif colon == 0:
            name += c
        elif not (c == ':' and quote == 0 and ind == 0):
            content += c
    if c != ',':
        contents.append(content.strip())
        names.append(name.strip())
    return (names, contents)

# given tuple (names[], contents[]), get specific content according to name
def get_content_by_name(tuple, name):
    try:
        index = tuple[0].index(name)
        return tuple[1][index]
    except:
        return ""

# get plan name (ex. real-west-all-terminals)
if len(sys.argv) < 2:
    print("usage:   python csvdata.py <plan>")
    print("example: python csvdata.py real-west-all-terminals")
    exit()
dplan = sys.argv[1]
dpath = "output/" + dplan + "/"
if not path.exists(dpath + "states.json"):
    print(dpath + "states.json does not exist!")
    print("exiting...")
    exit()

in_file = open(dpath + "states.json", "r")
t = in_file.read()
in_file.close()
out_file = open(dpath + "states.csv", "w")
out_file.write("time,takeoff_count,total_ticks_on_surface,callsign,state,speed,is_delayed,itinerary_index,uncertainty_delayed_index,scheduler_delayed_index,takeoff,atgate_cnt\n")
by_time = lines_of(t)
count = 0
atgate_dict = {}
for i in by_time:
    count += 1
    by_time_contents = content_of(i)
    time = get_content_by_name(by_time_contents, '"time"')
    aircrafts = get_content_by_name(by_time_contents, '"aircrafts"')
    takeoff_count = get_content_by_name(by_time_contents, '"takeoff_count"')
    total_ticks_on_surface = get_content_by_name(by_time_contents, '"total_ticks_on_surface"')
    if aircrafts != "[]" and aircrafts != "":
        aircrafts = aircrafts[1:len(aircrafts)-1]
        aircrafts_lines = lines_of(aircrafts)
        for j in aircrafts_lines:
            aircrafts_contents = content_of(j)
            callsign = get_content_by_name(aircrafts_contents, '"callsign"')
            state = get_content_by_name(aircrafts_contents, '"state"')
            speed = get_content_by_name(aircrafts_contents, '"speed"')
            is_delayed = get_content_by_name(aircrafts_contents, '"is_delayed"')
            itinerary_index = get_content_by_name(aircrafts_contents, '"itinerary_index"')
            uncertainty_delayed_index = get_content_by_name(aircrafts_contents, '"uncertainty_delayed_index"')
            scheduler_delayed_index = get_content_by_name(aircrafts_contents, '"scheduler_delayed_index"')
            takeoff = get_content_by_name(aircrafts_contents, '"takeoff"')
            if not callsign in atgate_dict:
                atgate_dict[callsign] = 0
            if 'atGate' in state:
                atgate_dict[callsign] = atgate_dict[callsign] + 1
            out_file.write(time + ',' + takeoff_count + ',' + total_ticks_on_surface + ',' + callsign + ',' + state + ',' + speed + ',' + is_delayed + ',' + itinerary_index + ',' + uncertainty_delayed_index + ',' + scheduler_delayed_index + ',' + takeoff + ',' + str(atgate_dict[callsign]) + '\n')
out_file.close()
print("Done. Please check " + dpath + "states.csv")
