"""
Ground Controller oversees the aircraft movement on the ground. It continuously observes the world and sends
commands to pilots when there is a notable situation.
"""
import collections

from config import Config


class Controller:
    def __init__(self, ground):
        self.ground = ground

        self.PILOT_VISION = Config.params["aircraft_model"]["pilot_vision"]
        self.CLOSE_NODE_THRESHOLD = Config.params["simulation"]["close_node_threshold"]

    def tick(self):
        self.__observe()
        self.__resolve_conflicts()

    def __observe(self):
        aircraft_list = self.ground.aircrafts

        self.aircraft_location_lookup = collections.defaultdict(list)  # {link: (aircraft, distance_on_link)}
        self.aircraft_ahead_lookup = {}  # {aircraft: (target_speed, relative_distance)}

        self.conflicts = []

        """
        Observe the invertedAircraftLocations = {link: (aircraft, distance_on_link)} set.
        Observe the closestAircraft = {aircraft: (target_speed, relative_distance)} dict.
        Observe potential conflicts.
        """
        for aircraft in aircraft_list:
            if aircraft.itinerary.is_completed:
                continue
            link, distance = aircraft.itinerary.current_target, aircraft.itinerary.current_distance
            self.aircraft_location_lookup[link].append((aircraft, distance))

        # Sort the {link: (aircraft, distance_on_link)} by distance_on_link.
        for _, aircraft_pair in self.aircraft_location_lookup.items():
            aircraft_pair.sort(key=lambda pair: pair[1])

        for aircraft in aircraft_list:
            if aircraft.itinerary.is_completed:
                continue
            try:
                target_speed, relative_distance, fronter_aircraft = self.__find_aircraft_ahead(aircraft)
                self.aircraft_ahead_lookup[aircraft] = (target_speed, relative_distance)
                # TODO: discuss with zy & what if none
                aircraft.set_fronter_info((target_speed, relative_distance))
                aircraft.set_fronter_aircraft(fronter_aircraft)
            except NoCloseAircraftFoundError:
                # TODO: discuss with zy & what if none
                aircraft.set_fronter_info(None)
                # TODO: currently just assume the front is moving
                # aircraft.set_fronter_info((200, 100))
                pass

    def __find_aircraft_ahead(self, aircraft):
        link_index, link_distance = aircraft.itinerary.current_target_index, aircraft.itinerary.current_distance

        relative_distance = -link_distance
        for index in range(link_index, aircraft.itinerary.length):
            link = aircraft.itinerary.targets[index]

            aircraft_on_same_link = self.aircraft_location_lookup.get(link, [])
            for item in aircraft_on_same_link:
                item_aircraft, item_distance = item
                # Skip if the item is behind the aircraft
                if index == link_index and item_distance <= link_distance:
                    continue

                # Found an aircraft ahead!
                relative_distance += item_distance

                if relative_distance < self.CLOSE_NODE_THRESHOLD:
                    self.conflicts.append((aircraft, item_aircraft))

                if relative_distance > self.PILOT_VISION:
                    # Too far that the pilot can't see the aircraft
                    raise NoCloseAircraftFoundError
                else:
                    return item_aircraft.speed, relative_distance, item_aircraft

            relative_distance += link.length

        raise NoCloseAircraftFoundError

    def __resolve_conflicts(self):
        """
        If two aircraft on two links would enter the same link using their current speed, we see a potential conflict.
        Send command to one of the pilots to wait there.
        Will call Aircraft.Pilot.Slowdown() or something alike.
        """
        priority_list = self.ground.priority

        # TODO: UNIMPLEMENTED
        for aircraft_1, aircraft_2 in self.conflicts:
            aircraft_2.set_fronter_info((-1, -1))

    def get_closest_aircraft_ahead(self, aircraft):
        return self.aircraft_ahead_lookup.get(aircraft, None)


class NoCloseAircraftFoundError(Exception):
    pass
