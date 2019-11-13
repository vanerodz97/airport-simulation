from surface import Spot
from collections import deque
from flight import ArrivalFlight, DepartureFlight
from queue import PriorityQueue as PQ


class InterSection:
    def __init__(self, node, links):
        self.node = node
        self.links = {}
        for link in links:
            self.links[link] = None


class RampController:
    """ The class decide the priority of departure aircraft """
    def __init__(self, ground):
        self.ground = ground
        self.spot_queue = {}  # departure queue?
        self.intersection = []  # put all intersections, spot+intersection?

    def add_aircraft_to_spot_queue(self, aircraft, scenario):
        """ Keep a priority queue for """
        # todo: sort the priority by appear time? cell(tick)
        flight = scenario.get_flight(aircraft)
        if type(flight) == DepartureFlight:
            gate = flight.from_gate()
            spot = gate.get_spots()
            if spot not in self.spot_queue:
                self.spot_queue[spot] = deque()
            self.spot_queue[spot].append(aircraft)


class InterSectionController:
    def __init__(self, ground):
        self.ground = ground
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

    def __check_conflict(self, spot, itineraries):
        count_occupied = 0
        for q in spot.links.values():
            if q is None or q.qsize() == 0:
                continue
            count_occupied += 1
            # if count_occupied > 1:
            #     while q.qsize() != 0:
            #         aircraft = q.get()[1]
            #         aircraft.itinerary.add_scheduler_delay()
            #         itineraries[aircraft] = aircraft.itinerary
        return True if count_occupied > 1 else False

    def resolve_conflict(self, itineraries):
        """ Decide which aircraft to add the halt"""
        for spot in self.intersection:
            """ conflict will happen at the intersection"""
            occupied = self.__check_conflict(spot, itineraries)
            if occupied:
                print("conflict")
            """how to choose the link to pass: longest queue, if same: shortest distance"""



class IntersectionController:
    def __init__(self):



