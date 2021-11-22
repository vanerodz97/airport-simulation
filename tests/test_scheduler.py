#!/usr/bin/env python3
import logging
from clock import Clock
from copy import deepcopy
from datetime import time
from aircraft import Aircraft, State
from flight import DepartureFlight
from node import Node
from surface import RunwayNode, Spot
from config import Config
from simulation import get_scheduler
from conflict import Conflict
from link import Link

import sys
import unittest
sys.path.append('..')


class TestScheduler(unittest.TestCase):

    Config.params["simulator"]["test_mode"] = True
    Config.params["simulation"]["time_unit"] = 30

    #     (G1)a1
    #      |
    #      |
    #      |a4a5
    #     (S1)----------(RANWAY.start)
    #      |
    #      |
    #      |
    #     (G2)a2a3

    g1 = Node("G1", {"lat": 47.821849, "lng": -122.079057})
    g2 = Node("G2", {"lat": 47.822151, "lng": -122.079057})
    s1 = Spot("S1", {"lat": 47.822000, "lng": -122.079057})
    runway_start = RunwayNode({"lat": 47.822000, "lng": -122.078906})

    a1 = Aircraft("A1", None, g1, State.stop)
    a2 = Aircraft("A2", None, g2, State.stop)
    a3 = Aircraft("A3", None, g2, State.stop)

    a4 = Aircraft("A4", None, s1, State.stop)
    a5 = Aircraft("A5", None, s1, State.stop)

    class AirportMock():

        def __init__(self, simulation, aircraft1, aircraft2):
            self.aircrafts = [aircraft1, aircraft2]
            self.aircraft1 = aircraft1
            self.aircraft2 = aircraft2

        def apply_schedule(self, schedule):
            for aircraft, itinerary in schedule.itineraries.items():
                if aircraft == self.aircraft1:
                    self.aircraft1.set_itinerary(itinerary)
                else:
                    self.aircraft2.set_itinerary(itinerary)

        def apply_priority(self, priority):
            self.priority = priority

        def set_quiet(self, logger):
            self.aircraft1.logger = logger
            self.aircraft2.logger = logger

        def tick(self):
            self.aircraft1.tick()
            self.aircraft2.tick()

        @property
        def conflicts(self):
            if self.aircraft1.location == self.aircraft2.location:
                return [Conflict(None, [self.aircraft1, self.aircraft2])]
            return []

        @property
        def next_conflicts(self):
            loc1, loc2 = self.aircraft1.get_next_location(Aircraft.LOCATION_LEVEL_COARSE), \
                         self.aircraft2.get_next_location(Aircraft.LOCATION_LEVEL_COARSE)
            print("83", loc1, loc2)
            if not loc1 or not loc2 or not loc1.is_close_to(loc2):
                return []
            if loc1 == self.aircraft1.itinerary.targets[-1].nodes[-1] \
                and loc2 == self.aircraft2.itinerary.targets[-1].nodes[-1]:
                print("success")
                return []
            return [Conflict((loc1, loc2), [self.aircraft1, self.aircraft2])]

    class RunwayMock():

        def __init__(self, runway_start):
            self.runway_start = runway_start

        @property
        def start(self):
            return self.runway_start

    class ScenarioMock():

        def __init__(self, g1, g2, s1, runway_start):
            self.runway = TestScheduler.RunwayMock(runway_start)
            self.g1, self.g2, self.s1 = g1, g2, s1

        def get_flight(self, aircraft):
            if aircraft.callsign == "N 1A1":
                departureFlight = DepartureFlight(
                    "N 1A1", None, None, self.g1,
                    time(2, 36), time(2, 36)
                )
            elif aircraft.callsign == "N 2A2":
                departureFlight = DepartureFlight(
                    "N 2A2", None, None, self.g2,
                    time(2, 36, 30), time(2, 36, 30)
                )
            elif aircraft.callsign == "N 3A3":
                departureFlight = DepartureFlight(
                    "N 3A3", None, None, self.g2,
                    time(2, 36, 1), time(2, 36, 1)
                )
            elif aircraft.callsign == "N 4A4":
                departureFlight = DepartureFlight(
                    "N 4A4", None, None, self.g2,
                    time(2, 36, 1), time(2, 36, 1)
                )
            elif aircraft.callsign == "N 5A5":
                departureFlight = DepartureFlight(
                    "N 5A5", None, None, self.g2,
                    time(2, 36, 2), time(2, 36, 2)
                )
            else:
                departureFlight = DepartureFlight(
                    "wrong condition", None, None, self.g2,
                    time(2, 36, 2), time(2, 36, 2)
                )
            departureFlight.set_runway(self.runway)
            return departureFlight


    class RouteMock():

        def __init__(self, nodes):
            self.nodes = nodes
            self.links = []
            for i in range(1, len(nodes)):
                self.links.append(Link("test"+str(i), [nodes[i-1], nodes[i]]))

    class RoutingExpertMock():

        def __init__(self, g1, g2, s1, runway_start):
            self.g1, self.g2, self.s1 = g1, g2, s1
            self.runway_start = runway_start

        def get_shortest_route(self, src, dst):

            if src == self.g1 and dst == self.runway_start:
                return TestScheduler.RouteMock([self.g1, self.s1,
                                                self.runway_start])

            if src == self.g2 and dst == self.runway_start:
                return TestScheduler.RouteMock([self.g2, self.s1,
                                                self.runway_start])

            if src == self.s1 and dst == self.runway_start:
                return TestScheduler.RouteMock([self.s1, self.runway_start])

            else:
                raise Exception("Unsupported routing query")

    class SimulationMock():

        def __init__(self, a1, a2, g1, g2, s1, runway_start):
            self.airport = TestScheduler.AirportMock(self, a1, a2)
            self.scenario = TestScheduler.ScenarioMock(
                g1, g2, s1, runway_start)
            self.routing_expert = TestScheduler.RoutingExpertMock(
                g1, g2, s1, runway_start)
            self.clock = Clock()
            self.clock.now = time(2, 30)

        def set_quiet(self, logger):
            self.airport.set_quiet(logger)

        def remove_aircrafts(self):
            pass

        def pre_tick(self, scheduler):
            pass

        def tick(self):
            self.clock.tick()
            self.airport.tick()

        def post_tick(self):
            pass

        @property
        def now(self):
            return self.clock.now

        @property
        def copy(self):
            s = deepcopy(self)
            s.set_quiet(logging.getLogger("QUIET_MODE"))
            return s

    def test_naive_scheduler(self):
        Config.params["scheduler"]["name"] = "naive_scheduler"
        a1 = Aircraft("A1", None, self.g1, State.stop)
        a3 = Aircraft("A3", None, self.g2, State.stop)

        # Create mock objects, then schedule it
        simulation = self.SimulationMock(
            a1, a3, self.g1, self.g2, self.s1, self.runway_start)
        scheduler = get_scheduler()
        schedule, priority = scheduler.schedule(simulation)

        self.assertEqual(len(schedule.itineraries), 2)

        # a1 has an early departure time, so it goes first
        self.assertTrue(self.a1 in schedule.itineraries)
        self.assertTrue(self.a3 in schedule.itineraries)

        # Gets itineraries
        iti1 = schedule.itineraries[self.a1]
        iti2 = schedule.itineraries[self.a3]

        self.assertEqual(iti1.targets[1].nodes[0], self.g1)
        self.assertEqual(iti1.targets[1].nodes[1], self.s1)
        self.assertEqual(iti1.targets[2].nodes[0], self.s1)
        self.assertEqual(iti1.targets[2].nodes[1], self.runway_start)

        self.assertEqual(iti2.targets[1].nodes[0], self.g2)
        self.assertEqual(iti2.targets[1].nodes[1], self.s1)
        self.assertEqual(iti2.targets[2].nodes[0], self.s1)
        self.assertEqual(iti2.targets[2].nodes[1], self.runway_start)

    def test_deterministic_scheduler_with_one_conflict(self):

        Config.params["scheduler"]["name"] = "deterministic_scheduler"
        a1 = Aircraft("A1", None, self.g1, State.stop)
        a3 = Aircraft("A3", None, self.g2, State.stop)

        # Create mock objects, then schedule it
        simulation = self.SimulationMock(
            a1, a3, self.g1, self.g2, self.s1, self.runway_start)
        scheduler = get_scheduler()
        schedule, priority = scheduler.schedule(simulation)

        self.assertEqual(len(schedule.itineraries), 2)

        # a3 has an early departure time, so it goes first
        self.assertTrue(self.a1 in schedule.itineraries)
        self.assertTrue(self.a3 in schedule.itineraries)

        # Gets itineraries
        iti1 = schedule.itineraries[self.a1]
        iti2 = schedule.itineraries[self.a3]

        self.assertEqual(iti1.targets[1].nodes[0], self.g1)
        self.assertEqual(iti1.targets[1].nodes[1], self.s1)
        self.assertEqual(iti1.targets[2].nodes[0], self.s1)
        self.assertEqual(iti1.targets[2].nodes[1], self.runway_start)

        self.assertEqual(iti2.targets[2].nodes[0], self.g2)
        self.assertEqual(iti2.targets[2].nodes[1], self.s1)
        self.assertEqual(iti2.targets[3].nodes[0], self.s1)
        self.assertEqual(iti2.targets[3].nodes[1], self.runway_start)

    # def test_deterministic_scheduler_with_one_unsolvable_conflict(self):
    #
    #     # Sets two aircraft standing at the same node
    #     self.a4.set_location(self.s1, Aircraft.LOCATION_LEVEL_COARSE)
    #     self.a5.set_location(self.s1, Aircraft.LOCATION_LEVEL_COARSE)
    #
    #     # Create mock objects, then schedule it
    #     simulation = self.SimulationMock(
    #         self.a4, self.a5, self.g1, self.g2, self.s1, self.runway_start)
    #     scheduler = get_scheduler()
    #     schedule, priority = scheduler.schedule(simulation)
    #
    #     self.assertEqual(len(schedule.itineraries), 2)
    #
    #     # a3 has an early departure time, so it goes first
    #     self.assertTrue(self.a4 in schedule.itineraries)
    #     self.assertTrue(self.a5 in schedule.itineraries)
    #
    #     # Gets itineraries
    #     iti1 = schedule.itineraries[self.a4]
    #     iti2 = schedule.itineraries[self.a5]
    #
    #     self.assertEqual(schedule.n_unsolvable_conflicts, 0)
    #
    #     self.assertEqual(iti1.targets[0], self.s1)
    #     self.assertEqual(iti1.targets[1], self.runway_start)
    #
    #     self.assertEqual(iti2.targets[0], self.s1)
    #     self.assertEqual(iti2.targets[1], self.s1)
    #     self.assertEqual(iti2.targets[2], self.runway_start)
