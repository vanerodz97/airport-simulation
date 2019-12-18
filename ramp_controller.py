from collections import deque
from flight import ArrivalFlight, DepartureFlight
from queue import PriorityQueue as PQ
from config import Config


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
        print(self.spot_queue.get(spot, None))
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



class InterSectionController:
    def __init__(self, ground):
        self.ground = ground
        self.method = Config.params["controller"]["intersection"]
        self.intersection = []
        for node, links in ground.surface.intersections_to_link_mapping.items():
            self.intersection.append(InterSection(node, links))

    def set_aircraft_at_intersection(self):
        """ Check whether there is conflict in the intersection"""
        aircraft_list = self.ground.aircrafts
        for aircraft in aircraft_list:
            for link in aircraft.link_this_tick:
                self.set_intersection(link, aircraft)

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
    def __get_conflict(spot, itineraries, method):
        """apply priority based on the distance to the intersection"""
        count_occupied = 0
        to_resolve = PQ()
        for q in spot.links.values():
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
            to_resolve.put((priority, q.queue))
        return to_resolve if to_resolve.qsize() > 1 else None

    def resolve_conflict(self, itineraries):
        flag = False
        """ Decide which aircraft to add the halt"""
        for spot in self.intersection:
            """ conflict will happen at the intersection"""
            to_resolve = self.__get_conflict(spot, itineraries, self.method)
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


