def read_node_file(fileName):
    from pathlib import Path
    rst = []
    f = Path(fileName)
    if f.is_file() == False:
        print(fileName + " does not exist.")
        exit(-1)
    f = open(fileName, 'r')
    array = []
    for line in f.readlines():
        array.append(line[:-1].split(","))
        array[-1][1] = float(array[-1][1])
        array[-1][2] = float(array[-1][2])
    return array


def read_link_file(fileName):
    from pathlib import Path
    rst = []
    f = Path(fileName)
    if f.is_file() == False:
        print(fileName + " does not exist.")
        exit(-1)
    f = open(fileName, 'r')
    array = []
    for line in f.readlines():
        array.append(line[:-1].split(","))
        array[-1][1] = float(array[-1][1])
        array[-1][2] = float(array[-1][2])
        array[-1][4] = float(array[-1][4])
        array[-1][5] = float(array[-1][5])
        array[-1][6] = float(array[-1][6])
    return array


import matplotlib.pyplot as plt

links = read_link_file(".\output-links.txt")
for v in links:
    plt.plot([v[2],v[5]], [v[1],v[4]],'y-', markersize=3)
    #plt.plot(0.9*v[2]+ 0.1*v[5], 0.9*v[1] + 0.1*v[4], 'y.', markersize=5)

gates = read_node_file(".\output-gates.txt")
for v in gates:
    plt.plot(v[2], v[1],'g.')
    plt.text(v[2], v[1], v[0], fontsize=10)

spots = read_node_file(".\output-spots.txt")
for v in spots:
    plt.plot(v[2], v[1],'r.')
    plt.text(v[2], v[1], v[0], fontsize=10)

runways = read_node_file(".\output-runways.txt")
for v in runways:
    plt.plot(v[2], v[1],'.', color='k')
    plt.text(v[2], v[1], v[0], fontsize=10)

intersections = read_node_file(".\output-intersections.txt")
for v in intersections:
    plt.plot(v[2], v[1],'.', color='b')
    #plt.text(v[2], v[1], v[0], fontsize=10)

intermediates = read_node_file(".\output-intermediates.txt")
for v in intermediates:
    plt.plot(v[2], v[1],'y.', markersize=3)
    #plt.text(v[2], v[1], v[0], fontsize=10)

#plt.plot(-122.358089, v[1],'k.', markersize=8)
#plt.plot(v[2], v[1],'k.', markersize=8)
#plt.plot(v[2], v[1],'k.', markersize=8)
#plt.plot(v[2], v[1],'k.', markersize=8)

plt.show()