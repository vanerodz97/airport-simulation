"""`Aircraft` and `State` represents an aircraft in the simulation and its
state.
"""
import enum
import logging


class State(enum.Enum):
    """`State` is a enum object that represents a possible state of an aircraft.
    """
    unknown = 0
    stop = 1  # default for departure flights
    moving = 2
    hold = 3
    flying = 4  # default for arrival flights


class Aircraft:
    """`Aircraft` represents an aircraft in the airport.
    """
    LOCATION_LEVEL_COARSE = 0
    LOCATION_LEVEL_PRECISE = 1

    def __init__(self, callsign, model, location, state):
        self.logger = logging.getLogger(__name__)

        self.callsign = callsign
        self.model = model

        # Aircraft's location as a vertex in on the node-link graph
        # If it's on the middle of a link, the coarse location will be the next node it will traverse.
        self.__coarse_location = location
        # aircraft's location as some point on a link
        self.__precise_location = None
        self.speed = 100.0
        self.__state = state

        self.itinerary = None

    def set_location(self, location, level=LOCATION_LEVEL_COARSE):
        """Sets the location of this aircraft to a given location."""
        if level == Aircraft.LOCATION_LEVEL_COARSE:
            self.__coarse_location = location
            self.__precise_location = None  # must reset precise location because the aircraft moved
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

    @property
    def next_location(self):
        """Gets the precise location of this aircraft in the next tick."""
        if self.itinerary:
            next_index, _, _ = self.itinerary.get_next_location(self.__get_tick_distance())
            if next_index is not None:
                return self.itinerary.get_nth_target(next_index).end
        return self.__coarse_location

    @property
    def next_precise_location(self):
        """Gets the precise location of this aircraft in the next tick."""
        if self.itinerary:
            _, _, next_location = self.itinerary.get_next_location(self.__get_tick_distance())
            if next_location is not None:
                return next_location
        return self.__coarse_location

    # TODO: discuss the interface
    def get_next_speed(self, proceed_aircraft_speed, distance):
        """ Calculate the speed based on following model."""
        # TODO: revise model
        acceleration = self.speed * (self.speed - proceed_aircraft_speed) / distance

        return self.speed + acceleration

    def set_speed(self, speed):
        """ Set the speed of the aircraft"""
        self.speed = speed

    def __get_tick_distance(self):
        """ Get the distance passed in this tick"""
        # TODO: implement
        return self.speed * 1  # 1 is the schedule window

    def set_itinerary(self, itinerary):
        """Sets the itinerary of this aircraft."""
        self.itinerary = itinerary
        self.logger.debug("%s: Roger, %s received.", self, itinerary)

        for target in itinerary.targets:
            self.logger.debug(target)

    def add_uncertainty_delay(self):
        """Adds an uncertainty delay on this aircraft."""
        if not self.itinerary:
            self.logger.debug("%s: No itinerary to add delay", self)
            return
        delay_added_at = self.itinerary.add_uncertainty_delay()
        self.logger.debug("%s: Delay added at %s by uncertainty",
                          self, delay_added_at)

    def add_scheduler_delay(self):
        """Adds a scheduler delay on this aircraft."""
        if not self.itinerary:
            self.logger.debug("%s: No itinerary to add delay", self)
            return
        delay_added_at = self.itinerary.add_scheduler_delay()
        self.logger.debug("%s: Delay added at %s by scheduler",
                          self, delay_added_at)

    def tick(self):
        """Ticks on this aircraft and its children to move to the next state.
        """
        if self.itinerary:
            tick_distance = self.__get_tick_distance()
            self.itinerary.tick(tick_distance)
            if self.itinerary.is_completed:
                self.logger.debug("%s: %s completed.", self, self.itinerary)
            else:
                self.set_location(self.itinerary.current_location, Aircraft.LOCATION_LEVEL_COARSE)
                self.set_location(self.itinerary.current_precise_location, Aircraft.LOCATION_LEVEL_PRECISE)
        else:
            self.logger.debug("%s: No itinerary request.", self)

        self.logger.info("%s at %s", self, self.__coarse_location)

    @property
    def state(self):
        """Returns the state of the current aircraft."""
        if self.itinerary is None or self.itinerary.is_completed:
            return State.stop
        if self.itinerary.next_target is None or \
                self.itinerary.current_target is None:
            return State.stop
        return State.hold if self.itinerary.current_target.is_close_to(
            self.itinerary.next_target) else State.moving

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
