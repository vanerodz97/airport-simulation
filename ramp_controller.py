from surface import Spot
from collections import deque
from flight import ArrivalFlight, DepartureFlight
from queue import PriorityQueue as PQ


class InterSection:
    def __init__(self, node):
        self.node = node
        self.occupied = False
        self.aircrafts = PQ()


class RampController:
    def __init__(self, ground):
        self.ground = ground
        self.spot_queue = {}  # departure queue?
        self.intersection = []  # put all intersections, spot+intersection?

    def add_aircraft_to_spot_queue(self, aircraft, scenario):
        # todo: sort the priority by appear time? cell(tick)
        flight = scenario.get_flight(aircraft)
        if type(flight) == DepartureFlight:
            gate = flight.from_gate()
            # todo: get the spot from the gate name
            spot = gate.get_spots()
            if spot not in self.spot_queue:
                self.spot_queue[spot] = deque()
            else:
                self.spot_queue[spot].append(aircraft)

    def check_conflict_at_spot(self):
        aircraft_list = self.ground.aircrafts
        for aircraft in aircraft_list:
            for link in aircraft.link_this_tick:
                self.set_intersection(link, aircraft)

    def set_intersection(self, link, aircraft):
        for spot in self.intersection:
            if link.contains_node(spot):
                distance = spot.node.get_distance_to(aircraft.precise_location)
                spot.occupied = True
                spot.aircrafts.put((distance, aircraft))

    def resolve_conflict(self):
        for spot in self.intersection:
            if spot.occupied is True:
                # todo:
                # if aircraft in other conflict condition
                # lower the priority
                spot.aircrafts.get()  # pop the first one
                for item in spot.aircrafts:
                    aircraft = item[1]
                    # todo: figure out the usage of scheduler delay function
                    aircraft.itinerary.add_scheduler_delay()


class IntersectionController:
    def __init__(self):



