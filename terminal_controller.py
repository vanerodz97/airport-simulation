from node import Node
import json

class TerminalController:
    def __init__(self):
        raw_flow_spots = ['{"intersection":"I9","lat":37.6207975,"lng":-122.3930747}',
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
        
        flow_spot_id_2_gates = {
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
        # self.flow_spot_ids = []
        self.arrival_2_gate = {}
        self.depature_2_gate = {}
        self.gate_2_flow_spot_id = {}
        self.flow_spot_id_2_access = {}


        # self.flow_spots = []
        self.flow_spot_id_2_spot = {}
        for raw_flow_spot in raw_flow_spots:
            json_dict = json.loads(raw_flow_spot)
            flow_spot_id = json_dict['intersection']
            flow_spot = Node(flow_spot_id, {'lat': json_dict['lat'], 'lng': json_dict['lng']})
            # self.flow_spot_ids.append(flow_spot_id)
            # self.flow_spots.append(flow_spot)
            self.flow_spot_id_2_spot[flow_spot_id] = flow_spot
            self.flow_spot_id_2_access[flow_spot_id] = 0
            gate_list = flow_spot_id_2_gates[flow_spot_id]
            for gate_name in gate_list:
                self.gate_2_flow_spot_id[gate_name] = flow_spot_id
        
        self.visited_arrivals = set()
    
    def add_arrival_gate(self, aircraft, gate_name):
        self.arrival_2_gate[aircraft] = gate_name
    
    def add_departure_gate(self, aircraft, gate_name):
        self.depature_2_gate[aircraft] = gate_name
        tgt_flow_spot_id = self.gate_2_flow_spot_id[gate_name]
        self.flow_spot_id_2_access[tgt_flow_spot_id] -= 1
        
    
    def remove_arrival(self, aircraft):
        gate_name = self.arrival_2_gate[aircraft]
        tgt_flow_spot_id = self.gate_2_flow_spot_id[gate_name]
        self.flow_spot_id_2_access[tgt_flow_spot_id] -= 1
        self.arrival_2_gate.pop(aircraft)
        self.visited_arrivals.remove(aircraft)
    
    # def remove_departure(self, aircraft):
    #     self.depature_2_gate.pop(aircraft)

    
    def get_arrival_access_during_path(self, aircraft):
        gate_name = self.arrival_2_gate[aircraft]
        tgt_flow_spot_id = self.gate_2_flow_spot_id[gate_name]
        tgt_flow_spot = self.flow_spot_id_2_spot[tgt_flow_spot_id]
        meet_tgt_flow_spot = False
        ahead_intersections, _ = aircraft.get_ahead_intersections_and_link()
        for ahead_intersection in ahead_intersections:
            if ahead_intersection.is_close_to(tgt_flow_spot):
                meet_tgt_flow_spot = True
                break
        
        if meet_tgt_flow_spot == False:
            return True
        
        if self.flow_spot_id_2_access[tgt_flow_spot_id] >= 0:
            if aircraft not in self.visited_arrivals:
                self.flow_spot_id_2_access[tgt_flow_spot_id] += 1
                self.visited_arrivals.add(aircraft)
            return True
        return False
    
    def update_flow_spot_access(self, aircraft, passed_intersections):
        is_departure = False
        gate_name = None
        if aircraft in self.depature_2_gate:
            is_departure = True
            gate_name = self.depature_2_gate[aircraft]
        # elif aircraft in self.arrival_2_gate:
        #     gate_name = self.arrival_2_gate[aircraft]
        else:
        #     # here is a special case
        #     # when a intersection is very near to the flow spot
        #     # the action is taken before the aircraft really reaches the 
        #     # flow spot, so we need to avoid duplicate update, which means,
        #     # we won't call this function when the aircraft reaches the flow
        #     # spot if this function has already been called.
            return
        tgt_flow_spot_id = self.gate_2_flow_spot_id[gate_name]
        tgt_flow_spot = self.flow_spot_id_2_spot[tgt_flow_spot_id]
        passed_tgt_flow_spot = False
        for passed_intersection in passed_intersections:
            if passed_intersection.is_close_to(tgt_flow_spot):
                passed_tgt_flow_spot = True
                break
        if passed_tgt_flow_spot:
            # only update for departure
            # the arrival will only update when it reaches the gate
            if is_departure == True:
                self.flow_spot_id_2_access[tgt_flow_spot_id] += 1
                self.depature_2_gate.pop(aircraft)
    
    def get_departure_access(self, gate_name):
        tgt_flow_spot_id = self.gate_2_flow_spot_id[gate_name]
        # if there any arrival, then cannot add departure
        if self.flow_spot_id_2_access[tgt_flow_spot_id] > 0:
            return False
        return True