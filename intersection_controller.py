from config import Config
import copy

import matplotlib.pyplot as plt

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