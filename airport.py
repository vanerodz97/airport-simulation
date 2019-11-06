"""`Airport` represents both the static and dynamic surface states of an
airport.
"""
import itertools
import logging
import os
from collections import deque

from aircraft import Aircraft
from config import Config
from conflict import Conflict
from controller import Controller
from surface import SurfaceFactory
from utils import get_seconds_after
from flight import ArrivalFlight


class Airport:
    """`Airport` contains the surface and all the aircraft currently moving or
    stopped in this airport.
    """

    def __init__(self, name, surface):

        # Setups the logger
        self.logger = logging.getLogger(__name__)

        # Runtime data
        self.aircrafts = []

        # Queues for departure flights at gates
        self.gate_queue = {}

        # departure control for the aircraft
        self.departure_queue = {}
        self.departure_info = []
        self.departure_tick_time = self.__get_interval()

        # Itinerary cache object for future flights
        self.itinerary_cache = {}

        # Static data
        self.name = name
        self.surface = surface

        # Number of flights sent to the sky. For performance evaluation use.
        self.takeoff_count = 0
        self.takeoff_ticks_count = 0

        self.priority = None
        # Ground controller
        self.controller = Controller(self)

    def apply_schedule(self, schedule):
        """Applies a schedule onto the active aircraft in the airport."""
        all_itineraries = {**self.itinerary_cache, **schedule.itineraries}

        # Clean up the cache (previous states)
        self.itinerary_cache = {}

        # Apply the itinerary onto the aircraft one by one
        for aircraft, itinerary in all_itineraries.items():
            if aircraft in self.aircrafts:
                aircraft.set_itinerary(itinerary)
            else:
                # If the aircraft is not found, we cache the itinerary for it
                self.logger.debug("%s hasn't found yet, we will cache its "
                                  "itinerary", aircraft)
                self.itinerary_cache[aircraft] = itinerary

    def apply_priority(self, priority):
        self.priority = priority

    def add_aircrafts(self, scenario, now, sim_time, scheduler):
        """Adds multiple aircraft according to the given scenario and current
        time stamp.
        """
        self.__add_aircrafts_from_queue()
        self.__add_aircrafts_from_scenario(scenario, now, sim_time, scheduler)

    def add_aircraft(self, aircraft):
        """Adds a new aircraft onto the airport and assigns it an itinerary if
        we have a cached itinerary for it.
        """
        self.aircrafts.append(aircraft)

        if aircraft in self.itinerary_cache:
            itinerary = self.itinerary_cache[aircraft]
            aircraft.set_itinerary(itinerary)
            self.logger.debug("Applied %s on %s from itinerary cache",
                              itinerary, aircraft)

    def __add_aircrafts_from_queue(self):

        for gate, queue in self.gate_queue.items():

            if self.is_occupied_at(gate) or not queue:
                continue

            # Put the first aircraft in queue into the airport
            aircraft = queue.popleft()
            aircraft.set_location(gate, Aircraft.LOCATION_LEVEL_COARSE)
            self.add_aircraft(aircraft)

    def __add_aircrafts_from_scenario(self, scenario, now, sim_time, scheduler):

        # NOTE: we will only focus on departures now
        next_tick_time = get_seconds_after(now, sim_time)

        # For all departure flights
        for flight in scenario.departures:
            # Only if the scheduled appear time is between now and next tick
            if not (now <= flight.appear_time < next_tick_time):
                continue

            gate, aircraft = flight.from_gate, flight.aircraft

            if self.is_occupied_at(gate):
                # Adds the flight to queue
                queue = self.gate_queue.get(gate, deque())
                queue.append(aircraft)
                self.gate_queue[gate] = queue
                self.logger.info("Adds %s into gate queue", flight)
            else:
                # Adds the flight to the airport
                if flight.runway is None:
                    runway_name = next(scheduler.departure_assigner)
                    runway = self.surface.get_link(runway_name)
                    flight.set_runway(runway)
                aircraft.set_location(gate, Aircraft.LOCATION_LEVEL_COARSE)
                self.add_aircraft(aircraft)
                self.logger.info("Adds %s into the airport", flight)

        # Deal with the arrival flights, assume that the runway is always not
        # occupied because this is an arrival flight

        for flight in scenario.arrivals:
            if not (now <= flight.appear_time < next_tick_time):
                continue
            if flight.runway is None:
                runway_name = next(scheduler.arrival_assigner)
                runway = self.surface.get_link(runway_name)
                flight.set_runway(runway)
            runway, aircraft = flight.runway.end, flight.aircraft
            aircraft.set_location(runway, Aircraft.LOCATION_LEVEL_COARSE)
            self.add_aircraft(aircraft)
            self.logger.info(
                "Adds {} arrival flight into the airport".format(flight))

    def __add_aircraft_to_departure_queue(self, aircraft,scenario):
        flight = scenario.get_flight(aircraft)
        if flight.runway not in self.departure_queue:
            self.departure_queue[flight.runway] = deque()
        self.departure_queue[flight.runway].append(aircraft)
        for i in range(1, self.departure_tick_time):
            self.departure_queue[flight.runway].append(None)

    @classmethod
    def __get_interval(cls):
        sim_time = Config.params["simulation"]["time_unit"]
        departure_interval = Config.params["simulation"]["departure_interval"]
        return int(departure_interval / sim_time)

    def remove_aircrafts(self, scenario):
        """Removes departure aircraft if they've moved to the runway.
        """
        to_remove_aircraft_departure = []
        to_remove_aircraft_arrival = []

        for aircraft in self.aircrafts:
            flight = scenario.get_flight(aircraft)
            if type(flight) == ArrivalFlight:
                # if it is the arrival aircraft, do not remove it.
                if aircraft.location.is_close_to(flight.to_gate):
                    to_remove_aircraft_arrival.append(aircraft)
                continue
            # Deletion shouldn't be done in the fly
            if aircraft.precise_location.is_close_to(flight.runway.start):
                to_remove_aircraft_departure.append(aircraft)

        for aircraft in to_remove_aircraft_departure:
            self.logger.info("Removes departure %s from the airport", aircraft)
            self.__add_aircraft_to_departure_queue(aircraft, scenario)
            self.departure_info.append(aircraft)
            self.aircrafts.remove(aircraft)

        for aircraft in to_remove_aircraft_arrival:
            self.logger.info("Removes arrive %s from the airport", aircraft)
            self.aircrafts.remove(aircraft)

    def remove_departure_aircrafts(self, aircrafts):
        for aircraft in aircrafts:
            self.departure_info.remove(aircraft)

    @property
    def conflicts(self):
        """Retrieve a list of conflicts observed in the current airport state.
        """
        return self.__get_conflicts()

    @property
    def next_conflicts(self):
        """Retrieve a list of conflicts will observed in the next airport
        state.
        """
        return self.__get_conflicts(is_next=True)

    def __get_conflicts(self, is_next=False):
        # Remove departed aircraft or
        __conflicts = []
        aircraft_pairs = list(itertools.combinations(self.aircrafts, 2))
        for pair in aircraft_pairs:
            if pair[0] == pair[1]:
                continue

            if is_next:
                loc1, loc2 = pair[0].get_next_location(Aircraft.LOCATION_LEVEL_PRECISE), \
                             pair[1].get_next_location(Aircraft.LOCATION_LEVEL_PRECISE)
            else:
                loc1, loc2 = pair[0].precise_location, pair[1].precise_location
            if not loc1 or not loc2 or not loc1.is_close_to(loc2):
                continue

            __conflicts.append(Conflict((loc1, loc2), pair))
        return __conflicts

    def is_occupied_at(self, node):
        """Check if an aircraft is occupied at the given node."""
        for aircraft in self.aircrafts:
            if aircraft.precise_location.is_close_to(node):
                return True
        return False

    def control_takeoff(self):
        """ Allow takeoff only at safe interval."""
        aircrafts = []
        for runway_queue in self.departure_queue.items():
            try:
                aircraft = runway_queue[1].popleft()
                if aircraft is None:
                    continue
                else:
                    aircrafts.append(aircraft)
                    aircraft.take_off = True
                    self.takeoff_ticks_count += aircraft.tick_count
                    self.takeoff_count += 1
                    self.logger.info("%s is ready to take off", aircraft)
            except IndexError:
                continue
        return aircrafts

    def tick(self, predict=False):
        # Ground Controller should observe all the activities on the ground.
        if predict is False:
            # self.controller.tick()
            pass

        # Ticks on all subjects under the airport to move them into the next state
        for aircraft in self.aircrafts:
            aircraft.tick()

    def print_stats(self):
        """Prints a summary of the current airport state.
        """
        self.surface.print_stats()

    def __getstate__(self):
        attrs = dict(self.__dict__)
        del attrs["logger"]
        return attrs

    def __setstate__(self, attrs):
        self.__dict__.update(attrs)

    def set_quiet(self, logger):
        """Puts the aircraft object to quiet mode where only important logs are
        printed.
        """
        self.logger = logger
        self.surface.set_quiet(logger)
        for aircraft in self.aircrafts:
            aircraft.set_quiet(logger)
        for queue in self.gate_queue.values():
            for airport in queue:
                airport.set_quiet(logger)

    @classmethod
    def create(cls, name):
        """Factory method used for generating an airport object using the given
        airport name.
        """

        dir_path = Config.DATA_ROOT_DIR_PATH % name

        # Checks if the folder exists
        if not os.path.exists(dir_path):
            raise Exception("Surface data is missing")

        surface = SurfaceFactory.create(dir_path)
        return Airport(name, surface)
