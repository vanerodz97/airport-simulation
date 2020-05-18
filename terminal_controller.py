from node import Node
import json

"""
TerminalController is used to control the aircraft movement in the terminal area,
which is between the terminal gate and the terminal spot. Definition of termianal gate:
the start location of a departure flight. Definition of termianl spot: a special intersection
that both departure flights and arrival flights need to cross through.

Constraint: The only edges of the airport graph that allow for bi-directional movement are those between
the gate and the spot nodes.

Our current strategy: If there is departure flight moving in the terminal area, then no arrival
flight should be allowed to enter the same terminal area until the terminal area is empty. 
Vice versa.
"""

class TerminalController:
    def __init__(self):
        # We hardcode the terminal spot Id and their location
        raw_terminal_spots = ['{"intersection":"I9","lat":37.6207975,"lng":-122.3930747}',
                          '{"intersection":"I4_0","lat":37.620453,"lng":-122.392242}',
                          '{"intersection":"I4_1","lat":37.620453,"lng":-122.392242}',
                          '{"intersection":"I11","lat":37.6225832,"lng":-122.3897306}',
                          '{"intersection":"I8","lat":37.6210348,"lng":-122.3853907}',
                          '{"intersection":"I7","lat":37.6207622,"lng":-122.3846701}',
                          '{"intersection":"I6","lat":37.6197099,"lng":-122.3821562}',
                          '{"intersection":"I3","lat":37.615431,"lng":-122.380449}',
                          '{"intersection":"I2","lat":37.613286,"lng":-122.3818837}',
                          '{"intersection":"I1","lat":37.6101585,"lng":-122.383978}',
                          '{"intersection":"I5","lat":37.6095765,"lng":-122.3843067}']
        
        # different terminal gates are controlled by different terminal spots
        # for example, if there is a departure aircraft moving from gate G101, but it
        # has not crossed the terminal spot I9, then no arrival aircraft whose destination
        # is gate {G101, or G101B, G101A, G99A ...} should be allowed to cross the terminal
        # spot I9. All arrival aircraft should wait until the area is empty.
        # Vice versa: if there is a arrival aircraft, whose destination is G101, crossed the
        # spot I9, but it has not reached its destination G101. Then no departure from 
        # ["G101", "G101B", "G101A", ...] should be able to be pushed to the pushback way.
        terminal_spot_id_2_gates = {
            'I9' : ["G101", "G101B", "G101A", "G99A", 'G99', 'G97', 'G95', 'G93', 'G91'],
            'I4_0' : ['G102', 'G100', 'G98', 'G96', 'G94', 'G92', 'G92A'],
            'I4_1' : ['90', '89', '87A', '87', '85', '83', '81', '72', '73A', '73', '74', '75'],
            'I11' : ['88', '86', '84A', '84B', '84C', '84D', '82', '80', '79'],
            'I8' : ['78', '77B', '77A', '76', '71A', '71B', '70', '69'],
            'I7' : ['65', '65A', '63', '61', '68'],
            'I6' : ['67', '66', '66A', '64', '64A', '62A', '62', '60A', '56A', '56B', '57', '58B', '59A', '59B', '59C'],
            'I3' : ['55', '54B', '54A', '53', '52', '51B', '51A', '50A', '50B', '41', '43', '45B', '45A', '47'],
            'I2' : ['40', '42', '44', '46', '48', 'B6', 'B7', 'B8'],
            'I1' : ['B9', 'B12', 'B13', 'B17', 'B18', 'A1', 'A3', 'A5'],
            'I5' : ['A7', 'A9', 'A11', 'A12', 'A10', 'A8', 'A6', 'A4', 'A2']
        }
        self.gate_2_terminal_spot_id = {}
        # key is terminal_spot_id, value is an interger stands for access
        # if key is I9, and value is 3, it means there is 3 arrival aircraft
        # in the terminal area (crossed the spot I9, but not reach the destination gate)
        # if key is I9, and value is -3, it means there is 3 departure aircrafts in this area.
        self.terminal_spot_id_2_access = {}
        # key is terminal spot id, value is terminal spot (data structure: Node)
        self.terminal_spot_id_2_spot = {}

        # initialize the values here
        for raw_terminal_spot in raw_terminal_spots:
            json_dict = json.loads(raw_terminal_spot)
            terminal_spot_id = json_dict['intersection']
            terminal_spot = Node(terminal_spot_id, {'lat': json_dict['lat'], 'lng': json_dict['lng']})
            self.terminal_spot_id_2_spot[terminal_spot_id] = terminal_spot
            self.terminal_spot_id_2_access[terminal_spot_id] = 0
            gate_list = terminal_spot_id_2_gates[terminal_spot_id]
            for gate_name in gate_list:
                self.gate_2_terminal_spot_id[gate_name] = terminal_spot_id

        # key is aircraft (arrival), value is the destination terminal gate.
        self.arrival_2_gate = {}
        # key is aircraft (departure), value is the start terminal gate
        self.depature_2_gate = {}
        
        # used for avoid redundant update
        # every time when an aircraft cross the terminal spots, we update
        # the values in self.terminal_spot_id_2_access
        # if a intersection node is close to (node.is_close_to) a terminal spot,
        # then we treat it as a terminal spot. However, since the airport graph 
        # is drawed manually, there might exits several intersection nodes close
        # to one terminal spot, therefore we need this set to avoid redundant update
        self.visited_arrivals = set()
        self.visited_departures = set()
    
    def add_arrival_gate(self, aircraft, gate_name):
        self.arrival_2_gate[aircraft] = gate_name
    
    # we need to call get_departure_access before call this.
    # because we cannot add departure aircraft to the similator if there is 
    # arrival aircrafts in its terminal area.
    def add_departure_gate(self, aircraft, gate_name):
        self.depature_2_gate[aircraft] = gate_name
        # once a departure aircraft is shown up at the terminal gate, 
        # we need to update the terminal_spot_id_2_access value
        tgt_terminal_spot_id = self.gate_2_terminal_spot_id[gate_name]
        self.terminal_spot_id_2_access[tgt_terminal_spot_id] -= 1

    # when arrival aircraft reaches its destination gate
    def remove_arrival(self, aircraft):
        gate_name = self.arrival_2_gate[aircraft]
        tgt_terminal_spot_id = self.gate_2_terminal_spot_id[gate_name]
        self.terminal_spot_id_2_access[tgt_terminal_spot_id] -= 1
        self.arrival_2_gate.pop(aircraft)
        self.visited_arrivals.remove(aircraft)
    
    def remove_departure(self, aircraft):
        self.depature_2_gate.pop(aircraft)
        self.visited_departures.remove(aircraft)

    
    def get_arrival_access_during_path(self, aircraft):
        gate_name = self.arrival_2_gate[aircraft]
        tgt_terminal_spot_id = self.gate_2_terminal_spot_id[gate_name]
        tgt_terminal_spot = self.terminal_spot_id_2_spot[tgt_terminal_spot_id]
        meet_tgt_terminal_spot = False
        ahead_intersections, _ = aircraft.get_ahead_intersections_and_link()
        for ahead_intersection in ahead_intersections:
            if ahead_intersection.is_close_to(tgt_terminal_spot):
                meet_tgt_terminal_spot = True
                break
        
        if meet_tgt_terminal_spot == False:
            return True
        
        if self.terminal_spot_id_2_access[tgt_terminal_spot_id] >= 0:
            if aircraft not in self.visited_arrivals:
                self.terminal_spot_id_2_access[tgt_terminal_spot_id] += 1
                self.visited_arrivals.add(aircraft)
            return True
        return False
    
    # update terminal_spot_id_2_access value when there is departure aircraft
    # crossed the terminal spot. (No update when arrival aircraft crossed the 
    # terminal spot. The arrival will only update when it reaches the destination gate)
    def update_terminal_spot_access(self, aircraft, passed_intersections):
        # only update for departure
        if aircraft in self.arrival_2_gate:
            return
        if aircraft in self.visited_departures:
            return
        gate_name = self.depature_2_gate[aircraft]

        tgt_terminal_spot_id = self.gate_2_terminal_spot_id[gate_name]
        tgt_terminal_spot = self.terminal_spot_id_2_spot[tgt_terminal_spot_id]
        # to determine whether the departure ciraft has passed its target
        # terminal spot or not
        passed_tgt_terminal_spot = False
        for passed_intersection in passed_intersections:
            if passed_intersection.is_close_to(tgt_terminal_spot):
                passed_tgt_terminal_spot = True
                break
        # if it passed the target terminal spot, update the values
        if passed_tgt_terminal_spot:
            self.visited_departures.add(aircraft)
            self.terminal_spot_id_2_access[tgt_terminal_spot_id] += 1
    
    def get_departure_access(self, gate_name):
        tgt_terminal_spot_id = self.gate_2_terminal_spot_id[gate_name]
        # if there any arrival, then cannot add departure
        if self.terminal_spot_id_2_access[tgt_terminal_spot_id] > 0:
            return False
        return True