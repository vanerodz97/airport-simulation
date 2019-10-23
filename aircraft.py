"""`Aircraft` and `State` represents an aircraft in the simulation and its
state.
"""
import enum
import logging
import random
from surface import *

from link import HoldLink
from config import Config
from controller import Controller


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
    IDEAL_DISTANCE = Config.params["aircraft_model"]["ideal_distance"]
    MIN_DISTANCE = Config.params["aircraft_model"]["min_distance"]
    MAX_SPEED = Config.params["aircraft_model"]["max_speed"]
    IDEAL_SPEED = Config.params["aircraft_model"]["ideal_speed"]

    def __init__(self, callsign, model, location, state):

        self.logger = logging.getLogger(__name__)

        self.callsign = callsign
        self.model = model

        # Aircraft's location as a vertex in on the node-link graph
        # If it's on the middle of a link, the coarse location will be the next node it will traverse.
        self.__coarse_location = location
        # aircraft's location as some point on a link
        self.__precise_location = None
        self.__state = state

        self.itinerary = None
        self.speed = Config.params["aircraft_model"]["init_speed"]
        self.pushback_speed = Config.params["aircraft_model"]["pushback_speed"]
        self.fronter_info = None
        self.speed_uncertainty = 0
        self.is_reroute_necessary = True
        self.take_off = False

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

        next_index, _, next_location = self.itinerary.get_next_location(self.tick_distance)

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

    """
    @:param fronter_info (target_speed, relative_distance)
    """
    def get_next_speed(self, fronter_info):
        if self.__state is State.pushback:
            return self.pushback_speed
        """ Calculate the speed based on following model."""
        # Drive at the ideal speed if no aircraft exists in the pilot's sight
        if fronter_info is None:
            return self.IDEAL_SPEED

        # calculate the new speed when it is following another aircraft
        fronter_speed = fronter_info[0]
        relative_distance = fronter_info[1]
        # Brake hard if less than MIN_DISTANCE
        if relative_distance <= self.MIN_DISTANCE:
            return self.brake_hard()

        # Adjust the speed
        if relative_distance > self.IDEAL_DISTANCE:
            # acceleration phase
            c, l, m = 1.1, 0.1, 0.2
        else:
            # deceleration phase
            c, l, m = -1.1, 1.2, 0.7

        acceleration = c * (self.speed ** m) \
                       * (abs(self.speed - fronter_speed) / (relative_distance ** l))
        """ Make sure the speed is always valid """
        new_speed = self.speed + acceleration
        if new_speed < 0:
            new_speed = 0
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
        new_speed = self.speed / 1.5
        #self.set_speed(new_speed)
        self.logger.info("%s with speed %f brakes hard", self, self.speed)
        return new_speed

    @property
    def tick_distance(self):
        """ Get the distance the aircraft passed in this tick"""
        return self.speed * 1  # 1 is the time of a tick

    def set_itinerary(self, itinerary):
        """Sets the itinerary of this aircraft."""
        self.itinerary = itinerary
        # self.logger.debug("%s: Roger, %s received.", self, itinerary)

        # for target in itinerary.targets:
        #     self.logger.debug(target)

    def add_speed_uncertainty(self, speed_bias):
        self.speed_uncertainty = speed_bias

    """ original """
    def add_uncertainty_delay(self):
        """Adds an uncertainty delay on this aircraft."""
        if not self.itinerary:
            # self.logger.debug("%s: No itinerary to add delay", self)
            return
        delay_added_at = self.itinerary.add_uncertainty_delay()
        # self.logger.debug("%s: Delay added at %s by uncertainty",
        #                   self, delay_added_at)

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

        if self.itinerary:
            self.__state = self.state
            new_speed = self.get_next_speed(self.fronter_info) + self.speed_uncertainty
            self.set_speed(new_speed)
            self.itinerary.tick(self.tick_distance)
            if self.itinerary.is_completed:
                self.logger.debug("%s: %s completed.", self, self.itinerary)
            last_target = self.itinerary.backup[-1]
            is_arrival_aircraft = type(last_target.end) is Gate
            if is_arrival_aircraft and type(self.itinerary.current_target.end) \
                    is Spot:
                self.is_reroute_necessary = False
            self.set_location(self.itinerary.current_coarse_location, Aircraft.LOCATION_LEVEL_COARSE)
            self.set_location(self.itinerary.current_precise_location, Aircraft.LOCATION_LEVEL_PRECISE)
        else:
            # self.logger.debug("%s: No itinerary request.", self)
            pass

        self.logger.info("%s at %s", self, self.__coarse_location)

    @property
    def state(self):
        """Returns the state of the current aircraft."""
        if self.itinerary is None or self.itinerary.is_completed:
            return State.stop
        if self.itinerary.next_target is None or \
                self.itinerary.current_target is None:
            return State.stop

        _, _, next_precise_location = self.itinerary.get_next_location(self.tick_distance)  # why is this needed ??
        if self.__state == State.stop:
            #  do not update state if holdlink is added at gate
            return State.stop if type(self.itinerary.current_target) is HoldLink else State.pushback
        if self.__state == State.pushback:
            if type(self.itinerary.current_target) is HoldLink:
                #  assume no hold link will be generated in the middle of pushback
                return State.hold
            elif type(self.itinerary.current_target) is Taxiway:
                return State.moving
            else:
                return State.pushback
        return State.hold if type(self.itinerary.current_target) is HoldLink else State.moving

    @property
    def is_delayed(self):
        """Returns True if the aircraft is currently be delayed."""
        return self.itinerary.is_delayed if self.itinerary else False

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
        return "<Aircraft: %s %s>" % (self.callsign, self.state)

    def __getstate__(self):
        attrs = dict(self.__dict__)
        del attrs["logger"]
        return attrs

    def __setstate__(self, attrs):
        self.__dict__.update(attrs)
