from surface import Spot
from collections import deque
from flight import ArrivalFlight, DepartureFlight
from queue import PriorityQueue as PQ


class InterSection:
    def __init__(self, node):
        self.node = node
        self.aircrafts = None


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
        for node in ground.surface.intersections:
            self.intersection.append(InterSection(node))

    def check_conflict_at_intersection(self):
        """ Check whether there is conflict in the intersection"""
        aircraft_list = self.ground.aircrafts
        for aircraft in aircraft_list:
            for link in aircraft.link_this_tick:
                self.set_intersection(link, aircraft)

    def set_intersection(self, link, aircraft):
        """ Set the intersection as occupied and identify the aircraft in the conflict node"""
        for inter in self.intersection:
            node = inter.node
            if link.contains_node(node):
                distance = node.get_distance_to(aircraft.precise_location)
                if inter.aircrafts is None:
                    inter.aircrafts = PQ()
                inter.aircrafts.put((distance, aircraft))

    def resolve_conflict(self, itineraries):
        """ Decide which aircraft to add the halt"""
        for spot in self.intersection:
            chosen = False
            while spot.aircrafts and spot.aircrafts.qsize() != 0:
                aircraft = spot.aircrafts.get()[1]
                if chosen:
                    aircraft.itinerary.add_scheduler_delay()
                    itineraries[aircraft] = aircraft.itinerary
                    # print("%s is hold at intersection %s", aircraft, spot)
                chosen = True




