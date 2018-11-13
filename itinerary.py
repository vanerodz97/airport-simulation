"""Class file for `Itinerary`."""
from utils import str2sha1


class Itinerary:
    """Itinerary is a list of target nodes that an aircraft follows per tick.
    """

    def __init__(self, targets=None):

        if targets is None:
            targets = []

        self.targets = targets  # links
        self.index = 0
        self.distance = 0

        self.hash = str2sha1("#".join(str(self.targets)))
        self.uncertainty_delayed_index = []
        self.scheduler_delayed_index = []

    def tick(self, tick_distance):
        """Ticks this itinerary for moving to the next state."""
        if self.is_completed:
            return
        # Change current link if passing the last ones
        index, distance, _ = self.get_next_location(tick_distance)
        if not _:
            return
        else:
            self.index = index
            self.distance = distance

    """
    @return the current target/link, current distance on the link
    Return (None, None) if completed.
    """
    def get_current_link_info(self):
        """ Get the the current target and the distance on it the aircraft has passed by"""
        if self.is_completed:
            return None, None
        return self.current_target, self.distance

    """
    @require: This method can only be invoked before the aircraft starts executing it.
    """
    def merge_with_prior_link(self, previous_link, previous_distance):
        """ Merge the new itinerary with the previous one by adding to the head the part
            of link that the aircraft has not passed by yet.
        """
        if previous_link is not None:
            self.targets.insert(0, previous_link)
            self.distance = previous_distance

    """
    @return index, distance, Node
    Return (None, None, None) if completed.
    """
    def get_next_location(self, tick_distance):
        if self.is_completed:
            return None, None, None

        distance = self.distance
        current_target = self.current_target
        index = self.index
        # Find the link which the next location is on
        rest_link_length = current_target.length - distance
        while tick_distance >= rest_link_length:
            tick_distance -= rest_link_length
            distance = 0
            index += 1
            if index >= self.length:
                return None, None, None
            rest_link_length = self.get_target_len(index)
        # Update the distance on the link
        distance += tick_distance

        return index, distance, self.targets[index].get_middle_node(distance)

    def get_target_len(self, n):
        """ Returns the length of the nth target. """
        if n >= self.length:
            return None
        return self.targets[n].length

    def get_nth_target(self, n):
        """ Returns the nth link/target of the route/targets """
        if n >= self.length:
            return None
        return self.targets[n]

    def __add_delay(self):
        if self.is_completed:
            return None
        self.targets.insert(self.index, self.targets[self.index])
        return self.targets[self.index]

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
        if self.is_completed:
            return None
        return self.targets[self.index]

    @property
    def current_location(self):
        """Returns the current location (the end node of current target/link)."""
        if self.is_completed:
            return None
        return self.targets[self.index].end

    @property
    def current_precise_location(self):
        """Returns the current location (the precise node of current target/link)."""
        if self.is_completed:
            return None
        return self.targets[self.index].get_middle_node(self.distance)

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

    def __repr__(self):
        return "<Itinerary: %d target>" % len(self.targets)

    def __hash__(self):
        return self.hash

    def __eq__(self, other):
        return self.hash == other.hash

    def __ne__(self, other):
        return not self == other
