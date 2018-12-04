"""Class file for the deterministic `AbstractScheduler`."""
import logging

from copy import deepcopy
from itinerary import Itinerary
from flight import ArrivalFlight, DepartureFlight
from surface import Spot


def trimmed_route(route, start):
    """
    Delete some links form the route so that it routs from the current
    position to the gate.
    precondition: the flight is an arrival flight and it has passed Spot node.
    :param route:
    :return:
    """

    # get the link from spot to the gate
    links = route.links
    idx = 0
    for i in range(len(links)):
        if type(links[i].end) == Spot:
            idx = i
            break
    new_links = links[idx:]

    # check whether the start is in the gate-spot path
    start_idx = 0
    found = False
    for i in range(len(new_links)):
        link = new_links[i]
        if link.start.name == start.name:
            found = True
            start_idx = i

    if found:
        route.start = start
        # route.update_link(new_links[start_idx:])
        route.links = new_links[start_idx:]

class AbstractScheduler:
    """Parent class for different schedulers to extend."""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def schedule(self, simulation):
        """Schedule the aircraft within a simulation."""
        raise NotImplementedError("Schedule function should be overrided.")

    @classmethod
    def schedule_aircraft(cls, aircraft, simulation):
        """Schedule a single aircraft."""

        # Retrieves the route from the routing export
        flight = simulation.scenario.get_flight(aircraft)
        if type(flight) == ArrivalFlight:
            src, dst = aircraft.location, flight.to_gate
        else:
            src, dst = aircraft.location, flight.runway.start

        route = simulation.routing_expert.get_shortest_route(src, dst)

        if type(flight) is ArrivalFlight and aircraft.is_reroute_necessary is \
                False:
            trimmed_route(route, src)


        itinerary = Itinerary(deepcopy(route.nodes))

        # if type(
        #         flight) is DepartureFlight \
        #         or aircraft.is_reroute_necessary is True:
        #     route = simulation.routing_expert.get_shortest_route(src, dst)
        #     itinerary = Itinerary(deepcopy(route.nodes))
        # else:
        #     orig_itinerary = aircraft.itinerary
        #     aircraft.itinerary.backup = get_cutted_route_to_gate(orig_itinerary)
        #     aircraft.itinerary.index = 0
        #
        #     itinerary = aircraft.itinerary

        # Aggregates the uncertainty delay in previous itinerary if found
        if aircraft.itinerary:
            n_uncertainty_delay = aircraft.itinerary.n_future_uncertainty_delay
            itinerary.add_uncertainty_delay(n_uncertainty_delay)

        return itinerary

    def __getstate__(self):
        attrs = dict(self.__dict__)
        del attrs["logger"]
        return attrs

    def __setstate__(self, attrs):
        self.__dict__.update(attrs)
