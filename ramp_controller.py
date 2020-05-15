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


