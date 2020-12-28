"""Class file for `Itinerary`."""
from link import HoldLink
from utils import str2sha1
from copy import deepcopy
from node import Node
from surface import *

class Itinerary:
    """Itinerary is a list of target nodes that an aircraft follows per tick.
    """

    def __init__(self, targets=None, unfinished_distance=0):
        # unfinished_distance == 0 means it's
        self.targets = [HoldLink()] if unfinished_distance == 0 else []
        self.targets += targets if targets else []  # links\
        self.backup = deepcopy(targets)
        self.unfinished_distance = unfinished_distance
        # distance: the distance travelled on the link
        # distance_left: the distance left for entire itinerary
        self.index, self.distance, self.distance_left = None, None, None
        self.reset()

        self.hash = str2sha1("#".join(str(self.targets)))
        self.uncertainty_delayed_index = []
        self.scheduler_delayed_index = []
        self.links_this_tick = []

    def tick(self, tick_distance):
        """Ticks this itinerary for moving to the next state."""
        if self.is_completed:
            return

        cur_index = self.index
        if type(self.targets[cur_index]) is not HoldLink:
            self.distance_left = max(0, self.distance_left - tick_distance)
        # Change current link if passing the last ones
        next_index, distance, _ = self.get_next_location(tick_distance)

        self.index = next_index
        self.distance = distance
        # return the link that it has passes
        return self.targets[cur_index:next_index]

    """
    Get the next location, update the link the aircraft finished as well
    @return index, distance, Node
    Return (None, None, None) if completed.
    """
    def get_next_location(self, tick_distance):
        # Return the last node in the itinerary if completed
        self.links_this_tick = []  # reset the link list at beginning

        completed_itinerary = self.length, 0, self.targets[-1].end

        if self.is_completed:
            return completed_itinerary

        index, distance = self.index, self.distance

        # Skip delays
        if type(self.targets[index]) is HoldLink:
            return self.index + 1, self.distance, self.current_precise_location

        # Find the link which the next location is on
        while tick_distance >= self.targets[index].length - distance:
            tick_distance -= self.targets[index].length - distance
            self.links_this_tick.append(self.targets[index])  # append the link the aircraft will go through
            index += 1
            distance = 0
            # Return the last node in the itinerary if completed

            while index < self.length and type(self.targets[index]) is HoldLink:
                index += 1

            if index >= self.length:
                return completed_itinerary
        # Update the distance on the link

        return index, distance + tick_distance, self.targets[index].get_middle_node(distance + tick_distance)

    def get_nth_target(self, n):
        """ Returns the nth link/target of the route/targets """
        if n >= self.length:
            return None
        return self.targets[n]
    
    # def get_ahead_intersections_and_link(self, ahead_distance):
    #     """get the intersections and future links with certain distance"""
    #     ahead_intersections = []
    #     ahead_links = []
    #     index, distance = self.index, self.distance
    #     while ahead_distance >= self.targets[index].length - distance:
    #         if type(self.targets[index]) is HoldLink:
    #             index += 1
    #             continue
    #         ahead_distance -= self.targets[index].length - distance
    #         ahead_intersections.append(self.targets[index].end)
    #         ahead_links.append(self.targets[index])
    #         index += 1
    #         distance = 0
    #         if index >= self.length:
    #             break
    #     return ahead_intersections, ahead_links

    def get_ahead_intersections_and_link(self, ahead_distance):
        """get the intersections and future links with certain distance"""
        ahead_intersections = []
        distances_to_intersections = []
        index, distance = self.index, self.distance
        relative_distance = -distance
        while ahead_distance >= self.targets[index].length - distance:
            if type(self.targets[index]) is HoldLink:
                index += 1
                continue
            ahead_distance -= self.targets[index].length - distance
            ahead_intersections.append(self.targets[index].end)
            relative_distance += self.targets[index].length
            distances_to_intersections.append(relative_distance)
            index += 1
            distance = 0
            if index >= self.length:
                break
        return ahead_intersections, distances_to_intersections
    

    def __add_delay(self):
        if self.is_completed:
            return None
        self.targets.insert(0, HoldLink())
        return self.targets[0]

    def add_uncertainty_delay(self, amount=1):
        """Adds `amount` of uncertainty delays at the head of this itinerary.
        """
        for _ in range(amount):
            self.__update_delayed_index(self.index)
            self.uncertainty_delayed_index.append(self.index)
            self.__add_delay()

    def add_scheduler_delay(self):
        """Adds a single scheduler delay at the head of this itinerary."""
        self.__update_delayed_index(self.index)
        self.scheduler_delayed_index.append(self.index)
        return self.__add_delay()

    def __update_delayed_index(self, new_index):
        for i in range(len(self.uncertainty_delayed_index)):
            if self.uncertainty_delayed_index[i] >= new_index:
                self.uncertainty_delayed_index[i] += 1
        for i in range(len(self.scheduler_delayed_index)):
            if self.scheduler_delayed_index[i] >= new_index:
                self.scheduler_delayed_index[i] += 1

    def reset(self):
        """Reset the index of this itinerary."""
        self.index = 0
        self.distance = self.unfinished_distance
        self.distance_left = -self.unfinished_distance  # distance till destination
        for link in self.targets:
            self.distance_left += link.length

    @property
    def length(self):
        """Returns the length of this itinerary."""
        return len(self.targets)

    @property
    def is_delayed_by_uncertainty(self):
        """Returns true if the next tick is delayed by the uncertainty."""
        if self.next_target is None or self.index <= 0:
            return False
        return self.index - 1 in self.uncertainty_delayed_index

    @property
    def is_delayed_by_uncertainty_now(self):
        """Returns true if the current tick is delayed by the uncertainty."""
        return self.index in self.uncertainty_delayed_index

    @property
    def is_delayed_by_scheduler(self):
        """Returns true if the next tick is delayed by the scheduler."""
        if self.next_target is None or self.index <= 0:
            return False
        return self.index - 1 in self.scheduler_delayed_index

    @property
    def is_delayed(self):
        """Returns true if the next tick is delayed."""
        return self.is_delayed_by_scheduler or self.is_delayed_by_uncertainty

    @property
    def current_target(self):
        """Returns the current target."""
        index = self.index
        while index < self.length and type(self.targets[index]) is HoldLink:
            index += 1

        if self.is_completed:
            return None

        return self.targets[index]

    @property
    def current_target_index(self):
        """Returns the current target."""
        index = self.index
        while index < self.length and type(self.targets[index]) is HoldLink:
            index += 1

        return index

    @property
    def current_distance(self):
        """Returns the current target."""
        if self.is_completed:
            return None

        return self.distance

    @property
    def current_coarse_location(self):
        """Returns the current location (the end node of current target/link)."""
        index = self.index
        while index < self.length and type(self.targets[index]) is HoldLink:
            index += 1

        if self.is_completed:
            return self.targets[-1].end
        return self.targets[index].end

    @property
    def current_precise_location(self):
        """Returns the current location (the precise node of current target/link)."""
        index = self.index
        while index < self.length and type(self.targets[index]) is HoldLink:
            index += 1

        if self.is_completed:
            return self.targets[-1].end

        return self.targets[index].get_middle_node(self.distance)

    @property
    def next_target(self):
        """Returns the next target."""
        if self.index >= self.length - 1:
            return None
        return self.targets[self.index + 1]

    @property
    def is_completed(self):
        """Returns true if this itinerary had been completed."""
        return self.index >= self.length

    @property
    def n_scheduler_delay(self):
        """Returns the number of delays added by the scheduler."""
        return len(self.scheduler_delayed_index)

    @property
    def n_uncertainty_delay(self):
        """Returns the number of delays added by the uncertainty."""
        return len(self.uncertainty_delayed_index)

    @property
    def n_future_uncertainty_delay(self):
        """Returns the number of delays added by the uncertainty from now on.
        """
        return len([i for i in self.uncertainty_delayed_index
                    if i >= self.index])

    @property
    def detailed_description(self):
        return "index=" + str(self.index) + \
               ", distance=" + str(self.distance) + \
               ", distance_left=" + str(self.distance_left) + \
               ", targets=" + "\n".join([link.detailed_description for link in self.targets])

    def __repr__(self):
        return "<Itinerary: %d target>" % len(self.targets)

    def __hash__(self):
        return self.hash

    def __eq__(self, other):
        return self.hash == other.hash

    def __ne__(self, other):
        return not self == other

    @property
    def distance_to_intersection(self):
        # get the distance to the next intersection (the end of current link)
        current_target = self.targets[self.index]
        print (current_target.detailed_description)
        if type(current_target) is HoldLink:
            return 0
        else:
            return current_target.length - self.distance
    
    @property
    def distance_to_intersection_point(self):
        # get the distance to the next intersection point in the map
        idx = -1
        distance = 0
        for i in range(self.index, len(self.targets)):
            # if type(self.targets[i]) is PushbackWay:
            #     continue
            target_nodes = self.targets[i].nodes
            if len(target_nodes) <= 0:
                continue
            target_node = target_nodes[0]
            if type(target_node) is not Node:
                continue
            distance += self.targets[i].length
            if target_node.name.startswith("I"):
                idx = i
                break
        if idx == -1:
            return 0
        elif type(self.targets[idx]) is HoldLink:
            return 0
        else:
            return distance