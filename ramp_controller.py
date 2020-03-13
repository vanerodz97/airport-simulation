from collections import deque
from flight import ArrivalFlight, DepartureFlight
from queue import PriorityQueue as PQ
from config import Config
import copy

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

class IntersectionController:
    def __init__(self, airport):
        # get all the unique nodes
        all_nodes = self._get_all_nodes(airport.surface.gates, airport.surface.links)
        unique_nodes = self._remove_overlapping_nodes(all_nodes)

        # all nodes here are the intersection
        self.intersection_list = unique_nodes

        # map intersection to links
        self.intersection_link_map = self._init_intersection_links_map(self.intersection_list, airport.surface.links)
        self.intersection_available_link_map = {}
        self.intersection_lock_queue = {}
        self.intersections_status = {}
        for intersection in self.intersection_list:
            # available for pass
            self.intersections_status[intersection] = True
            self.intersection_available_link_map[intersection] = None
        
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

    # def lock_intersections(self, aircraft):
    #     pass_flag = True
    #     ahead_intersections, ahead_links = aircraft.get_ahead_intersections_and_link()
    #     for ahead_intersection in ahead_intersections:
    #         actual_intersection = self.node_map[ahead_intersection]
    #         # if self.intersections_status[actual_intersection] == False and self.intersection_available_link_map[actual_intersection] != aircraft.current_target:
    #         if self.intersections_status[actual_intersection] == False and self.intersection_available_link_map[actual_intersection] != aircraft:
    #             # intersection occupied,
    #             pass_flag = False
    #             return pass_flag
    #     # now the aircraft can pass, lock intersections
    #     pass_flag = True
    #     for idx, ahead_intersection in enumerate(ahead_intersections):
    #         actual_intersection = self.node_map[ahead_intersection]
    #         self.intersections_status[actual_intersection] = False
    #         # self.intersection_available_link_map[actual_intersection] = ahead_links[idx]
    #         self.intersection_available_link_map[actual_intersection] = aircraft
    #     return pass_flag

    def lock_intersections(self, aircraft):
        ahead_intersections, distances_to_intersections = aircraft.get_ahead_intersections_and_link()
        # now the aircraft can pass, lock intersections
        for idx, ahead_intersection in enumerate(ahead_intersections):
            actual_intersection = self.node_map[ahead_intersection]
            self.intersections_status[actual_intersection] = False
            ahead_distance = distances_to_intersections[idx]
            if actual_intersection not in self.intersection_lock_queue:
                self.intersection_lock_queue[actual_intersection] = []
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
                print("LOCK INFO: ", aircraft, " has no lock")
                print("lock by", lock_by_aircraft)
                return False
        return True

    
    def unlock_intersections(self, passed_intersections):
        for intersection in passed_intersections:
            actual_intersection = self.node_map[intersection]
            self.intersections_status[actual_intersection] = True
            self.intersection_available_link_map[actual_intersection] = None
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

            print("spot.links.keys()", len(spot.links.keys()))
            print("len spot.links.values()", len(spot.links.values()))
            num_aircraft_each_link = []
            for item in spot.links.values():
                if item is None or item.qsize() == 0:
                    num_aircraft_each_link.append(0)
                else:
                    num_aircraft_each_link.append(item.qsize())
            print(num_aircraft_each_link)

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


