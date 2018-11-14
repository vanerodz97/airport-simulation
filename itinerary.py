"""Class file for `Itinerary`."""
from utils import str2sha1


class Itinerary:
    """Itinerary is a list of target nodes that an aircraft follows per tick.
    """

    def __init__(self, targets=None):

        if targets is None:
            targets = []

        self.targets = targets  # links
        self.index = 0  # index of current link
        self.distance = 0  # distance traversed on the current link

        self.hash = str2sha1("#".join(str(self.targets)))
        self.uncertainty_delayed_index = []
        self.scheduler_delayed_index = []

    def tick(self, tick_distance):
        """Ticks this itinerary for moving to the next state."""
        if self.is_completed:
            return
        # Change current link if passing the last ones
        index, distance, next_location = self.get_next_location(tick_distance)
        if not next_location:
            self.index = self.length
            self.distance = 0
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
        return self.targets[self.index:], self.distance

    """
    @return index, distance, Node
    Return (None, None, None) if completed.
    """

    def get_next_location(self, tick_distance):
        # Return the last node in the itinerary if completed
        completed_itinerary = None, None, None

        if self.is_completed:
            return completed_itinerary

        index = self.index

        # Advance on same same link
        if 0 < self.targets[index].length - self.distance < tick_distance:
            new_distance = self.distance + tick_distance
            return index, new_distance, self.targets[index].get_middle_node(new_distance)
        else:
            tick_distance -= self.targets[index].length - self.distance
            index += 1
            if index >= self.length:
                return completed_itinerary

        # Find the link which the next location is on
        while tick_distance >= self.targets[index].length:
            tick_distance -= self.targets[index].length
            index += 1
            # Return the last node in the itinerary if completed
            if index >= self.length:
                return completed_itinerary
        # Update the distance on the link

        return index, tick_distance, self.targets[index].get_middle_node(tick_distance)

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
    def current_distance(self):
        """Returns the current target."""
        if self.is_completed:
            return None
        return self.distance

    @property
    def current_coarse_location(self):
        """Returns the current location (the end node of current target/link)."""
        if self.is_completed:
            return self.targets[-1].end
        return self.targets[self.index].end

    @property
    def current_precise_location(self):
        """Returns the current location (the precise node of current target/link)."""
        if self.is_completed:
            return self.targets[-1].end
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
