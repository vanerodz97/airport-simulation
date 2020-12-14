# Generate airport surface graph model for real west plan
# Can be used for both departure model and arrival model

import os
import json
import networkx as nx 
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt 
from surface import SurfaceFactory
from link import Link
from route import Route
from routing_expert import RoutingExpert


dir_path = os.path.dirname(os.path.realpath(__file__)) + "/"
AIRPORT_DATA_FOLDER = dir_path + "data/"
PLAN_OUTPUT_FOLDER = dir_path + "output/"

spots_to_intersections = {
    "S1": "I5",
    "S2": "I1",
    "S3": "I2",
    "S5": "I3",
    "S6": "I6",
    "S7": "I7",
    "S8": "I11",
    "S9": "I4",
    "S10": "I8",
    "S11": "I9"
}

arrival_runway_node_name = "10L/28R"
departure_runway_node_name = "1L/19R"

class GraphVisualization: 
   
    def __init__(self): 
        self.visual = [] 

    def addEdge(self, a, b, len): 
        temp = [a, b, len] 
        self.visual.append(temp) 
          
    def visualize(self, surface): 
        G = nx.Graph() 
        for edge in self.visual:
            print (edge)
            e = [edge[0], edge[1]]
            G.add_nodes_from(e)
            G.add_edge(edge[0], edge[1], len=edge[2])
        node_type = {}
        for node in G.nodes():
            if node in surface.gate_to_spot_mapping:
                node_type[node] = 'Gate'
            elif node in spots_to_intersections:
                node_type[node] = 'Spot'
            elif node[0] == 'I':
                node_type[node] = 'Intersection'
            else:
                node_type[node] = 'Runway'
        color_map = {'Gate':'#C7FFF9', 'Spot':'#FFC7CE', 'Runway':'#FFFF8A', 'Intersection':'#CCD1D1'}
        pos = nx.drawing.nx_agraph.graphviz_layout(G, prog='sfdp')
        nx.draw(G, pos, with_labels=True, node_size=700, node_color=[color_map[node_type[node]] for node in G])
        # nx.draw_networkx_edge_labels(G, pos, font_size=2)
        plt.tight_layout()
        plt.savefig("graph.png", dpi=1000)

def get_linknode_data(airport_data_folder, name):
    filename = airport_data_folder + "build/" + name + ".json"
    if not os.path.isfile(filename):
        raise Exception("Link data not found at %s" % filename)

    with open(filename) as f:
        links = json.loads(f.read())
    return links

def get_airport_metadata(airport_data_folder):
    filename = airport_data_folder + "build/airport-metadata.json"
    if not os.path.isfile(filename):
        raise Exception("Airport data not found at %s" % filename)

    with open(filename) as f:
        d = json.loads(f.read())
        name = d["name"]
        center = d["center"]

    return name, center

def get_surface_data(airport):
    airport_data_folder = AIRPORT_DATA_FOLDER + airport + "/"

    airport_name, airport_center = get_airport_metadata(airport_data_folder)
    pushback_ways = get_linknode_data(airport_data_folder, "pushback_ways")
    taxiways = get_linknode_data(airport_data_folder, "taxiways")
    runways = get_linknode_data(airport_data_folder, "runways")
    gates = get_linknode_data(airport_data_folder, "gates")
    spots = get_linknode_data(airport_data_folder, "spots")
    inters = get_linknode_data(airport_data_folder, "inters")

    return {
        "airport_name": airport_name,
        "airport_center": airport_center,
        "pushback_ways": pushback_ways,
        "taxiways": taxiways,
        "runways": runways,
        "gates": gates,
        "spots": spots,
        "inters": inters
    }

surface = SurfaceFactory.create(AIRPORT_DATA_FOLDER+"real-west-all-terminals/build/")
routing_expert = RoutingExpert(surface.links, surface.nodes, False)
G = GraphVisualization() 

def get_arrival_runway_node():
    for runway in surface.runways:
        if runway.name == arrival_runway_node_name:
            return runway.nodes[0]

def get_departure_runway_node():
    for runway in surface.runways:
        if runway.name == departure_runway_node_name:
            return runway.nodes[0]

def create_gates_to_spots_edge():
    gates = surface.gates
    gate_to_spot_mapping = surface.gate_to_spot_mapping
    for gate in gates:
        if gate.name in gate_to_spot_mapping:
            spot = gate_to_spot_mapping[gate.name]
            distance = gate.get_distance_to(spot)
            G.addEdge(gate.name, spot.name, round(distance, 2))

'''
    @param flight_type: Arrival or Departure
'''
def create_spots_to_taxiways_edge(flight_type):
    gate_to_spot_mapping = surface.gate_to_spot_mapping
    added_spot = set()
    for gate in surface.gates:
        if gate.name not in gate_to_spot_mapping:
            continue
        if flight_type == "Arrival":
            runway_node = get_arrival_runway_node()
            runway_name = arrival_runway_node_name
        else:
            runway_node = get_departure_runway_node()
            runway_name = departure_runway_node_name
        src, dst = gate, runway_node
        route = routing_expert.get_shortest_route(src, dst)
        links = route.get_links()
        spot = gate_to_spot_mapping[gate.name]
        gate_to_spot_distance = 0
        intersections = []
        intersection_distance = []
        dis = 0
        for link in links:
            gate_to_spot_distance += link.length
            if (link.contain_node(gate_to_spot_mapping[gate.name]) == True):
                break
        for link in links:
            dis += link.length
            if (link.nodes[-1].name[0] == 'I'):
                intersections.append(link.nodes[-1])
                intersection_distance.append(dis)
        # add gate to spot edge
        route_distance = route.distance
        G.addEdge(gate.name, spot.name, round(gate_to_spot_distance, 2))
        for idx, intersection in enumerate(intersections):
            # skip the first intersection (is a spot)
            if idx == 0:
                continue
            dist = intersection_distance[idx] - intersection_distance[idx-1]
            # add spot to intersection edge
            if idx == 1:
                G.addEdge(intersection.name, spot.name, round(dist, 2))
            # add intersection to intersection edge
            else:
                G.addEdge(intersection.name, intersections[idx-1].name, round(dist, 2))
        # add intersection to runway edge
        distance = route_distance - intersection_distance[-1]
        G.addEdge(runway_name, intersections[-1].name, round(distance, 2))

create_spots_to_taxiways_edge("Arrival")

G.visualize(surface)