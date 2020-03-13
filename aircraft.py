"""`Aircraft` and `State` represents an aircraft in the simulation and its
state.
"""
import enum
import logging
import random
from surface import *

from link import HoldLink
from config import Config
import re

AIRLINES_TO_CODE = {
    'Aer Lingus': "EI",
    'AeroMexico': "AM",
    'Air Canada': "AC",
    'Air China': "CA",
    'Air France': "AF",
    'Air India': "AI",
    'Air New Zealand': "NZ",
    'Alaska Airlines': "AS",
    'Alaska': "AS",
    'All Nippon Airways': "NH",
    'American Airlines': "AA",
    'American': "AA",
    'Asiana': "OZ",
    'Avianca': "AV",
    'British Airways': "BA",
    'Cathay Pacific': "CX",
    'China Airlines': "CI",
    'China': "CI",
    'China Eastern': "MU",
    'China Southern': "CZ",
    'Copa Airlines': "CM",
    'Copa': "CM",
    'Delta Air Lines': "DL",
    'EVA AIR': "BR",
    'Emirates': "EK",
    'Finnair': "AY",
    'French Bee': "BE",
    'Frontier Airlines': "F9",
    'Frontier': "F9",
    'Hawaiian Airlines': "HA",
    'Hawaiian': "HA",
    'Hong Kong Airlines': "HX",
    'Hong Kong': "HX",
    'Iberia Airlines': "IB",
    'Iberia': "IB",
    'Interjet': "4O",
    'Japan Airlines': "JL",
    'Japan': "JL",
    'JetBlue': "B6",
    'KLM Royal Dutch Airlines': "KL",
    'KLM Royal Dutch': "KL",
    'Korean Air': "KE",
    'Lufthansa': "LH",
    'Norwegian': "DY",
    'Philippine Airlines': "PR",
    'Philippine': "PR",
    'Qantas': "QF",
    'SWISS International Airlines': "LX",
    'SWISS International': "LX",
    'Scandinavian Airlines': "SK",
    'Scandinavian': "SK",
    'Singapore Airlines': "SQ",
    'Singapore': "SQ",
    'Southwest': "WN",
    'SunCountry': "SY",
    'Turkish Airlines': "TK",
    'Turkish': "TK",
    'United': "UA",
    'Virgin Atlantic': "VS",
    'WestJet': "WS"
}


class State(enum.Enum):
    """`State` is a enum object that represents a possible state of an aircraft.
    """
    unknown = 0
    stop = 1  # default for departure flights
    moving = 2  # on taxiway
    hold = 3
    flying = 4  # default for arrival flights
    pushback = 5  # new added, on pushback way


class Aircraft:
    """`Aircraft` represents an aircraft in the airport.
    """
    LOCATION_LEVEL_COARSE = 0
    LOCATION_LEVEL_PRECISE = 1

    def __init__(self, fullname, model, location, is_departure):

        self.logger = logging.getLogger(__name__)

        self.callsign = self.fullname2callsign(fullname)
        self.model = model

        # Aircraft's location as a vertex in on the node-link graph
        # If it's on the middle of a link, the coarse location will be the next node it will traverse.
        self.__coarse_location = location
        # aircraft's location as some point on a link
        self.__precise_location = None

        self.itinerary = None
        self.is_departure = is_departure
        self.speed = Config.params["aircraft_model"]["init_speed"]
        self.pushback_speed = Config.params["aircraft_model"]["pushback_speed"]
        self.IDEAL_DISTANCE = Config.params["aircraft_model"]["ideal_distance"]
        self.MIN_DISTANCE = Config.params["aircraft_model"]["min_distance"]
        self.MAX_SPEED = Config.params["aircraft_model"]["max_speed"]
        self.IDEAL_SPEED = Config.params["aircraft_model"]["ideal_speed"]
        self.fronter_info = None
        self.fronter_aircraft = None
        self.speed_uncertainty = 0
        self.is_reroute_necessary = True
        self.take_off = False

        self.tick_count = 0
        

    @staticmethod
    def fullname2callsign(fullname):
        flight_number = re.search('[0-9]+', fullname).group()
        airline = re.search("[a-zA-Z ]+", fullname).group()
        flight_number += fullname[-2:]

        if airline in AIRLINES_TO_CODE:
            return AIRLINES_TO_CODE[airline] + flight_number
        else:
            return 'N ' + flight_number

    def set_location(self, location, level=LOCATION_LEVEL_COARSE):
        """Sets the location of this aircraft to a given location."""
        if level == Aircraft.LOCATION_LEVEL_COARSE:
            self.__coarse_location = location
            self.__precise_location = location  # must reset precise location because the aircraft moved
            self.logger.info("%s coarse location changed to %s", self, location)
        elif level == Aircraft.LOCATION_LEVEL_PRECISE:
            self.__precise_location = location
            self.logger.info("%s precise location changed to %s", self, location)
        else:
            raise Exception("Unrecognized location level.")

    @property
    def location(self):
        """Same as coarse location. Keep the naming for compatibility. """
        return self.__coarse_location

    @property
    def precise_location(self):
        return self.__precise_location if self.__precise_location else self.__coarse_location

    def get_next_location(self, level=LOCATION_LEVEL_COARSE):
        """Gets the precise location of this aircraft in the next tick."""
        if not self.itinerary:
            return self.__coarse_location

        next_index, _, next_location = self.itinerary.get_next_location(self.next_tick_distance)

        if level == Aircraft.LOCATION_LEVEL_COARSE:
            if next_index < self.itinerary.length:
                next_target = self.itinerary.get_nth_target(next_index)
                return next_target.end
        elif level == Aircraft.LOCATION_LEVEL_PRECISE:
            return next_location
        else:
            raise Exception("Unrecognized location level.")

        return next_location

    """
    @:param fronter_info (target_speed, relative_distance)
    """

    def set_fronter_info(self, fronter_info):
        """ Set the information of the preceding aircraft. """
        self.fronter_info = fronter_info

    def set_fronter_aircraft(self, aircraft):
        self.fronter_aircraft = aircraft

    """
    @:param fronter_info (target_speed, relative_distance)
    """

    def get_next_speed(self, fronter_info, state):
        # if self.is_delayed:
        #     return 0
        if state is State.pushback:
            return self.pushback_speed
        """ Calculate the speed based on following model."""
        # Drive at the ideal speed if no aircraft exists in the pilot's sight
        if fronter_info is None:
            return self.IDEAL_SPEED

        # calculate the new speed when it is following another aircraft
        fronter_speed = fronter_info[0]
        relative_distance = fronter_info[1]

        if fronter_speed <= 0:
            return 0
            return self.brake_hard()

        # Brake hard if less than MIN_DISTANCE
        if relative_distance <= self.MIN_DISTANCE:
            return 0
            return self.brake_hard()

        # Adjust the speed
        acc_flag = False
        if relative_distance > self.IDEAL_DISTANCE:
            # acceleration phase
            c, l, m = 1.1, 0.1, 0.2
            acc_flag = True
        elif relative_distance < self.IDEAL_DISTANCE or fronter_speed < self.speed:
            # deceleration phase
            c, l, m = -2, 1.2, 0.7
        else:
            c, l, m = 0, 0, 0

        acceleration = c * (self.speed ** m) \
                       * (abs(self.speed - fronter_speed) / (relative_distance ** l))
        """ Make sure the speed is always valid """
        new_speed = self.speed + acceleration
        if new_speed < 0:
            new_speed = 0
        if acc_flag:
            new_speed = max(10, new_speed)
        # TODO: consider different speed limits for different type of roads
        if new_speed > self.MAX_SPEED:
            new_speed = self.MAX_SPEED
        return new_speed

    def set_speed(self, speed):
        """ Set the speed of the aircraft"""
        # Revise the value if the input speed is valid
        if speed < 0:
            self.speed = 0
            return
        if speed > self.MAX_SPEED:
            self.speed = self.MAX_SPEED
            return

        self.speed = speed

    def brake_hard(self):
        """ Brake hard to avoid potential crash"""
        # TODO: revise the model
        # new_speed = self.speed / 1.5
        # new_speed = self.speed / 3
        new_speed = 5
        # self.set_speed(new_speed)
        self.logger.info("%s with speed %f brakes hard", self, self.speed)
        return new_speed

    @property
    def tick_distance(self):
        """ Get the distance the aircraft passed in this tick"""
        return self.speed * 1  # 1 is the time of a tick

    @property
    def next_tick_distance(self):
        return self.get_next_speed(self.fronter_info, self.state) * 1

    def set_itinerary(self, itinerary):
        """Sets the itinerary of this aircraft."""
        self.itinerary = itinerary
        # self.logger.debug("%s: Roger, %s received.", self, itinerary)

        # for target in itinerary.targets:
        #     self.logger.debug(target)

    def add_speed_uncertainty(self, speed_bias):
        self.speed_uncertainty = speed_bias

    """ original """

    def add_scheduler_delay(self):
        """Adds a scheduler delay on this aircraft."""
        if not self.itinerary:
            # self.logger.debug("%s: No itinerary to add delay", self)
            return
        delay_added_at = self.itinerary.add_scheduler_delay()
        # self.logger.debug("%s: Delay added at %s by scheduler",
        #                   self, delay_added_at)

    def tick(self):
        """Ticks on this aircraft and its subobjects to move to the next state.
        """
        passed_links = None
        if self.itinerary:
            self.tick_count += 1
            new_speed = self.get_next_speed(self.fronter_info, self.state) + self.speed_uncertainty
            self.set_speed(new_speed)
            print("AIR %s: aircraft tick.", self)
            passed_links = self.itinerary.tick(self.tick_distance)
            if self.itinerary.is_completed:
                self.logger.debug("%s: %s completed.", self, self.itinerary)
            last_target = self.itinerary.backup[-1]
            is_arrival_aircraft = type(last_target.end) is Gate

            if is_arrival_aircraft and self.itinerary.current_target is not None \
                    and type(self.itinerary.current_target.end) is Spot:
                self.is_reroute_necessary = False
            self.set_location(self.itinerary.current_coarse_location, Aircraft.LOCATION_LEVEL_COARSE)
            self.set_location(self.itinerary.current_precise_location, Aircraft.LOCATION_LEVEL_PRECISE)
        else:
            # self.logger.debug("%s: No itinerary request.", self)
            print("AIR %s: No itinerary request.", self)
            pass

        self.logger.info("%s at %s", self, self.__coarse_location)
        return passed_links

    @property
    def state(self):
        """Identify whether the aircraft is on pushbackway or taxiway"""
        if self.itinerary is None or self.itinerary.is_completed:
            return State.stop
        if self.itinerary.next_target is None or \
                self.itinerary.current_target is None:
            return State.stop
        if self.is_departure is True:
            if type(self.itinerary.current_target.start) is Gate:
                #  do not update state if holdlink is added at gate
                return State.pushback
            elif type(self.itinerary.current_target) is PushbackWay:
                return State.pushback
        return State.moving

    @property
    def is_delayed(self):
        """Returns True if the aircraft is currently be delayed."""
        return self.itinerary.is_delayed if self.itinerary else False

    @property
    def is_predict_delayed(self):
        """Returns True if the aircraft is predicted to be delayed."""
        if self.itinerary:
            return True if type(self.itinerary.targets[0]) is HoldLink else False

        return False

    @property
    def link_this_tick(self):
        """Returns the link finished in this tick."""
        return self.itinerary.links_this_tick

    @property
    def current_target(self):
        """return the current exact link"""
        return self.itinerary.current_target
    
    def get_ahead_intersections_and_link(self):
        """get the intersections and future links with certain distance"""
        ahead_distance = 800.0
        return self.itinerary.get_ahead_intersections_and_link(ahead_distance)

    def set_quiet(self, logger):
        """Sets the aircraft into quiet mode where less logs are printed."""
        self.logger = logger

    def __hash__(self):
        return hash(self.callsign)

    def __eq__(self, other):
        return self.callsign == other.callsign

    def __ne__(self, other):
        return not self == other

    def __repr__(self):
        if self.fronter_info == None:
            fronter_speed = -999
            relative_dist = -999
        else:
            fronter_speed, relative_dist = self.fronter_info
        if self.fronter_aircraft is None:
            fronter_callsign = None
        else:
            fronter_callsign = self.fronter_aircraft.callsign
        return "<Aircraft: %s %s %.2f fronter: %s fronter_speed: %d relative_dist: %d>" % (self.callsign, self.state, self.speed, fronter_callsign, fronter_speed, relative_dist)

    def __getstate__(self):
        attrs = dict(self.__dict__)
        del attrs["logger"]
        return attrs

    def __setstate__(self, attrs):
        self.__dict__.update(attrs)
