from collections import deque
from flight import ArrivalFlight, DepartureFlight
from queue import PriorityQueue as PQ
from config import Config
import copy
from node import Node
import json

import matplotlib.pyplot as plt

class InterSection:
    def __init__(self, node, links):
        self.node = node
        self.links = {}
        for link in links:
            self.links[link] = None

    def reset(self):
        for link in self.links:
            self.links[link] = None


class RampController:
    """ The class decide the priority of departure aircraft """
    def __init__(self, ground):
        self.ground = ground
        self.spot_queue = {}
        self.spot_gate_queue = {}
        self.spots = ground.surface.spots

    def add_aircraft_to_spot_queue(self, spot, gate, aircraft):
        """ Keep a spot queue for aircraft"""
        if spot not in self.spot_queue:
            self.spot_queue[spot] = deque()
            self.spot_gate_queue[spot] = deque()
        self.spot_queue[spot].append(aircraft)
        self.spot_gate_queue[spot].append(gate)

    def spot_occupied(self, spot):
        if not self.spot_queue.get(spot, None):
            return False
        return True

    def __resolve_conflict(self, spot, itineraries):
        if self.spot_queue.get(spot, None):
            for aircraft in self.spot_queue[spot]:
                aircraft.itinerary.add_scheduler_delay()
                itineraries[aircraft] = aircraft.itinerary
            return True
        return False

    def resolve_conflict(self, itineraries):
        # TODO: need to solve conflict between arrival and departure flights
        flag = False

        for spot in self.spots:
            occupied = self.__resolve_conflict(spot, itineraries)
            if occupied:
                flag = True
        return flag


class FlowSpotController:
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

            

class IntersectionController:
    def __init__(self, airport):
        # get all the unique nodes
        all_nodes = self._get_all_nodes(airport.surface.gates, airport.surface.links)
        unique_nodes = self._remove_overlapping_nodes(all_nodes)

        # all nodes here are the intersection
        self.intersection_list = unique_nodes

        # map intersection to links
        self.intersection_link_map = self._init_intersection_links_map(self.intersection_list, airport.surface.links)
        # self.intersection_available_link_map = {}
        self.intersection_lock_queue = {}
        self.intersections_status = {}
        for intersection in self.intersection_list:
            # available for pass
            self.intersections_status[intersection] = True
            # self.intersection_available_link_map[intersection] = None
        
        self.node_map = {}
        for node in all_nodes:
            for intersection in self.intersection_list:
                if intersection.is_close_to(node):
                    self.node_map[node] = intersection

        save_graph = False
        if save_graph:
            x = []
            y = []
            for node in self.intersection_list:
                x.append(node.geo_pos["lat"])
                y.append(node.geo_pos["lng"])
            plt.scatter(y, x, s=1)
            plt.savefig("./draw_new_intersection/" + "nodes_only.jpg", dpi=300)
            plt.clf()
            cnt = 0

            for node, links in self.intersection_link_map.items():
                plt.scatter([node.geo_pos["lng"]], [node.geo_pos["lat"]], s=5)
                for link in links:
                    link_x = []
                    link_y = []
                    pre, nxt = None, link.nodes[0]
                    for i in range(1, len(link.nodes)):
                        pre = nxt
                        nxt = link.nodes[i]
                        link_x.append(pre.geo_pos["lat"])
                        link_y.append(pre.geo_pos["lng"])
                        link_x.append(nxt.geo_pos["lat"])
                        link_y.append(nxt.geo_pos["lng"])
                    plt.scatter(y, x, s=1)
                    plt.plot(link_y, link_x, linewidth=1)
                plt.title(label=node.name)
                if len(links) > 2:
                    plt.savefig("./draw_new_intersection/" + node.name + "_" + str(cnt) + ".jpg", dpi=800)
                elif len(links) == 1:
                    plt.savefig("./draw_new_intersection/_onelink_" + node.name + "_" + str(cnt) + ".jpg", dpi=800)
                elif len(links) == 2:
                    plt.savefig("./draw_new_intersection/_twolink_" + node.name + "_" + str(cnt) + ".jpg", dpi=800)

                plt.clf()
                cnt += 1


    def lock_intersections(self, aircraft):
        ahead_intersections, distances_to_intersections = aircraft.get_ahead_intersections_and_link()
        # now the aircraft can pass, lock intersections

        tmp_set = set()
        for idx, ahead_intersection in enumerate(ahead_intersections):
            actual_intersection = self.node_map[ahead_intersection]
            if actual_intersection not in tmp_set:
                tmp_set.add(actual_intersection)
                self.intersections_status[actual_intersection] = False
                ahead_distance = distances_to_intersections[idx]
                if actual_intersection not in self.intersection_lock_queue:
                    self.intersection_lock_queue[actual_intersection] = []
                if len(self.intersection_lock_queue[actual_intersection]) == 0 or self.intersection_lock_queue[actual_intersection][-1][1] != aircraft:
                    self.intersection_lock_queue[actual_intersection].append((ahead_distance, aircraft))

    
    def is_lock_by(self, aircraft):
        ahead_intersections, _ = aircraft.get_ahead_intersections_and_link()
        if len(ahead_intersections) == 0:
            return True
        ahead_intersection = ahead_intersections[0]
        for _, ahead_intersection in enumerate(ahead_intersections):
            actual_intersection = self.node_map[ahead_intersection]
            sorted_queue = sorted(self.intersection_lock_queue[actual_intersection], key=lambda t : t[0])
            lock_by_aircraft = sorted_queue[0][1]
            if aircraft != lock_by_aircraft:
                # print("LOCK INFO: ", aircraft, " has no lock")
                # print("lock by", lock_by_aircraft)
                return False
        return True
    
    def remove_aircraft(self, aircraft):
        remove_list = []
        for intersection, aircraft_queue in self.intersection_lock_queue.items():
            for idx, tp in enumerate(aircraft_queue):
                _, cur_aircraft = tp
                if cur_aircraft == aircraft:
                    remove_list.append((intersection, idx))
        for intersection, aircraft_idx in remove_list:
            del self.intersection_lock_queue[intersection][aircraft_idx]
    
    def unlock_intersections(self, passed_intersections):
        for intersection in passed_intersections:
            actual_intersection = self.node_map[intersection]
            self.intersections_status[actual_intersection] = True
            self.intersection_lock_queue[actual_intersection] = []

    def unblock_intersections_lock_by_aircraft(self, aircraft):
        remove_intersections = []
        for actual_intersection, lock_queue in self.intersection_lock_queue.items():
            if len(lock_queue) == 0:
                continue
            sorted_queue = sorted(lock_queue, key=lambda t : t[0])
            lock_by_aircraft = sorted_queue[0][1]
            if aircraft == lock_by_aircraft:
                remove_intersections.append(actual_intersection)
        self.unlock_intersections(remove_intersections)

    
    """
    Get all the nodes from airport node link structure
    Note that some of the nodes might be overlapping, 
    which means they have different location but very near to each other
    """
    def _get_all_nodes(self, gates, links):
        # get all the nodes from the airport
        all_nodes = set()
        for node in gates:
            all_nodes.add(node)
        for link in links:
            all_nodes.add(link.start)
            all_nodes.add(link.end)
        return all_nodes
    
    """
    @ all_nodes: a set of all nodes
    @ return: a list of unique nodes
    treat the nodes that are very near to each other as the same node
    """
    def _remove_overlapping_nodes(self, all_nodes):
        all_nodes_list = list(all_nodes)
        length = len(all_nodes_list)
        idx_of_removed = set()
        for i in range(length):
            if i in idx_of_removed:
                continue
            for j in range(i+1, length):
                node_0, node_1 = all_nodes_list[i], all_nodes_list[j]
                if node_0.is_close_to(node_1):
                    idx_of_removed.add(j)
        unique_nodes = []
        for i in range(length):
            if i in idx_of_removed:
                continue
            unique_nodes.append(all_nodes_list[i])
        return unique_nodes
    
    """
    Map the intersection to links
    intersection_list: a list of intersection spot, which is a node structure
    """
    def _init_intersection_links_map(self, intersection_list, links):
        intersection_link_map = {}
        for intersection_spot in intersection_list:
            intersection_link_map[intersection_spot] = []
            for link in links:
                if intersection_spot.is_close_to(link.start) or intersection_spot.is_close_to(link.end):
                    intersection_link_map[intersection_spot].append(link)
        return intersection_link_map


class _InterSectionController:
    def __init__(self, ground):
        self.ground = ground
        self.method = Config.params["controller"]["intersection"]
        self.intersection = []
        draw_nodes = []
        for node, links in ground.surface.intersections_to_link_mapping.items():
            self.intersection.append(InterSection(node, links))
            draw_nodes.append(node)
        
        cnt = 0
        x = []
        y = []
        for node in draw_nodes:
            x.append(node.geo_pos["lat"])
            y.append(node.geo_pos["lng"])

        # for link in ground.surface.links:
        #     node = link.start
        #     x.append(node.geo_pos["lat"])
        #     y.append(node.geo_pos["lng"])
        #     node = link.end
        #     x.append(node.geo_pos["lat"])
        #     y.append(node.geo_pos["lng"])
        
        for node, links in ground.surface.intersections_to_link_mapping.items():
            plt.scatter(y, x, s=2)
            plt.scatter([node.geo_pos["lng"]], [node.geo_pos["lat"]], s=5)
            for link in links:
                link_x = []
                link_y = []
                pre, nxt = None, link.nodes[0]
                for i in range(1, len(link.nodes)):
                    pre = nxt
                    nxt = link.nodes[i]
                    link_x.append(pre.geo_pos["lat"])
                    link_y.append(pre.geo_pos["lng"])
                    link_x.append(nxt.geo_pos["lat"])
                    link_y.append(nxt.geo_pos["lng"])
                
                plt.plot(link_y, link_x, linewidth=1)
            
            plt.title(label=node.name)
            plt.savefig("./draw_intersection/" + node.name.replace("/", "-") + str(cnt) + ".jpg", dpi=300)
            plt.clf()
            cnt += 1

    def set_aircraft_at_intersection(self):
        """ Check whether there is conflict in the intersection"""
        aircraft_list = self.ground.aircrafts
        for aircraft in aircraft_list:
            for link in aircraft.link_this_tick:
                self.set_intersection(link, aircraft)
    
    def reset_all_intersections(self):
        for spot in self.intersection:
            spot.reset()

    def set_intersection(self, link, aircraft):
        """ Set the intersection as occupied and identify the aircraft in the conflict node"""
        for spot in self.intersection:
            node = spot.node
            if link in spot.links:
                distance = node.get_distance_to(aircraft.precise_location)
                if spot.links[link] is None:
                    spot.links[link] = PQ()
                spot.links[link].put((distance, aircraft, link))

    @staticmethod
    def __get_conflict(spot, method):
        """apply priority based on the distance to the intersection"""
        count_occupied = 0
        to_resolve = PQ()
        for q in spot.links.values():
            num_aircraft_each_link = []
            for item in spot.links.values():
                if item is None or item.qsize() == 0:
                    num_aircraft_each_link.append(0)
                else:
                    num_aircraft_each_link.append(item.qsize())

            if q is None or q.qsize() == 0:
                continue
            priority = None
            count_occupied += 1
            if method == "qsize":
                priority = -q.qsize()
            elif method == "distance":
                priority = q.queue[0][0]
            else:
                raise Exception("Unimplemented intersection control method")
            if len(q.queue) > 1:
                print("q.queue: ", q.queue)
            to_resolve.put((priority, q.queue))
        if count_occupied > 1:
            print("count_occupied > 1" + "!"*100 )
        return to_resolve if to_resolve.qsize() > 1 else None

    def resolve_conflict(self, itineraries):
        flag = False
        """ Decide which aircraft to add the halt"""
        for spot in self.intersection:
            """ conflict will happen at the intersection"""
            to_resolve = self.__get_conflict(spot, self.method)
            if to_resolve:
                print("resolve conflict")
                to_resolve.get()  # skip the first one
                while to_resolve.qsize() != 0:
                    queue = to_resolve.get()[1]
                    for _, aircraft, _ in queue:
                        aircraft.itinerary.add_scheduler_delay()
                        itineraries[aircraft] = aircraft.itinerary
                flag = True
            spot.reset()
            """how to choose the link to pass: longest queue, if same: shortest distance"""
        return flag

    def aircraft_to_stop(self):
        res = []
        for spot in self.intersection:
            """ conflict will happen at the intersection"""
            to_resolve = self.__get_conflict(spot, self.method)
            if to_resolve:
                print("resolve conflict")
                to_resolve.get()  # skip the first one
                while to_resolve.qsize() != 0:
                    queue = to_resolve.get()[1]
                    for _, aircraft, _ in queue:
                        res.append(aircraft)
        return res
    
    def pass_aircrafts(self, target_aircraft, passed_links):
        for link in passed_links:
            for spot in self.intersection:
                # if this link is connected to the intersectiopn
                if link in spot.links:
                    remove_aircrafts = []
                    aircrafts_on_link = spot.links[link].values
                    for item in aircrafts_on_link:
                        cur_aircraft = item[1]
                        if cur_aircraft == target_aircraft:
                            remove_aircrafts.append(item)
                    for item in remove_aircrafts:
                        spot.links[link].remove(item)


