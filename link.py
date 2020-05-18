"""Class file for `Link`."""
import random
from geopy.distance import vincenty

from config import Config
from id_generator import get_new_link_id
from node import get_middle_node
from utils import str2sha1
# from surface import *


class Link:
    """`Link` is one of the most important class in our link-node model which
    is represent a link composed by a list of nodes.
    """

    def __init__(self, name, nodes):

        if len(nodes) < 2:
            raise Exception("Less than two nodes were given")

        if name is None or not name:
            name = "l-id-" + str(get_new_link_id())

        self.name = name
        self.nodes = nodes
        self.segment_lengths = [nodes[i].get_distance_to(nodes[i + 1]) for i in range(len(nodes) - 1)]
        self.boundary = self.__calculate_boundary(nodes)
        self.hash = str2sha1("%s#%s" % (self.name, self.nodes))
        self.occupied = False

    @property
    def length(self):
        """Returns the physical length of this link in feet."""
        return sum(self.segment_lengths)

    def refresh(self):
        self.occupied = False

    @property
    def start(self):
        """Returns the start node of this link."""
        return self.nodes[0]

    @property
    def end(self):
        """Returns the end node of this link."""
        return self.nodes[len(self.nodes) - 1]

    @property
    def reverse(self):
        """Reverses the node orders, which means the start and end are switched.
        """
        return type(self)(self.name, self.nodes[::-1])

    def __calculate_boundary(self, nodes):
        """Returns the boundary nodes for the area the link formed """
        boundary = None
        for node in nodes:
            lat, lng = node.geo_pos["lat"], node.geo_pos["lng"]
            if not boundary:
                boundary = [lat, lat, lng, lng]
            else:
                boundary[0] = min(boundary[0], lat)
                boundary[1] = max(boundary[1], lat)
                boundary[2] = min(boundary[2], lng)
                boundary[3] = max(boundary[3], lng)

        threshold = Config.params["simulation"]["close_node_link_threshold"] / 3280.0  # convert to km

        dis_calculator = vincenty(kilometers=threshold)

        return [
            dis_calculator.destination((boundary[0], boundary[2]), 180).latitude,
            dis_calculator.destination((boundary[1], boundary[3]), 0).latitude,
            dis_calculator.destination((boundary[0], boundary[2]), 270).longitude,
            dis_calculator.destination((boundary[1], boundary[3]), 90).longitude,
        ]

    def __node_in_boundary(self, node):
        """Returns true if this node is inside the boundary"""
        return self.boundary[0] <= node.geo_pos["lat"] <= self.boundary[1] and \
               self.boundary[2] <= node.geo_pos["lng"] <= self.boundary[3]

    def contains_node(self, node):
        """Returns true if this link contains a given `node`."""
        if not self.__node_in_boundary(node) or self.start.is_close_to(node) or self.end.is_close_to(node):
            return False
        return self.contains_node_at(node) is not None

    def contain_node(self, node):
        if self.start.is_close_to(node) or self.end.is_close_to(node):
            return True
        return False

    def contains_node_at(self, node):
        """Returns the index of the given node in this link."""

        for i in range(len(self.nodes) - 1):
            src, dst = self.nodes[i], self.nodes[i + 1]
            if self.contains_node_on_segment(src, dst, node):
                return i

        return None

    @classmethod
    def contains_node_on_segment(cls, src, dst, node):
        """Returns true of a given node in contained by this link between `src`
        and `dst`.
        """

        threshold = Config.params["simulation"]["close_node_link_threshold"]
        return (src.get_distance_to(node) + dst.get_distance_to(node) -
                src.get_distance_to(dst)) < threshold

    def break_at(self, node):
        """Breaks this link into two links at a given `node`. An exception is
        raised if the node isn't be contained by this link.
        """

        if not self.contains_node(node):
            raise Exception("%s is not on %s" % (node, self))

        if self.start.is_close_to(node) or self.end.is_close_to(node):
            return [self]

        marker = self.contains_node_at(node)

        # First part
        nodes_first = []
        for i in range(marker + 1):
            nodes_first.append(self.nodes[i])
        nodes_first.append(node)

        # Second part
        nodes_second = [node]
        for i in range(marker + 1, len(self.nodes)):
            nodes_second.append(self.nodes[i])

        return (type(self)(self.name + "-b1", nodes_first),
                type(self)(self.name + "-b2", nodes_second))

    def get_middle_node(self, distance):
        """Get the Node with distance to the start of the link"""
        if distance > self.length or distance < 0:
            return None

        if distance == 0.0:
            return self.nodes[0]

        # Find the sub-link which the location (node) is on
        length = 0.0
        i = 0
        while length < distance:
            length += self.segment_lengths[i]
            i += 1
        # Get the geo position of the location
        # i must greater than 0 because distance cannot be less than 0
        src, dst = self.nodes[i - 1], self.nodes[i]

        link_length = self.segment_lengths[i - 1]
        if link_length == 0:
            return src

        # TODO: the route returned by RoutingExpert is in reverse order,
        # TODO: so I added 1 - x here. Should fix in the future.
        ratio = 1 - (length - distance) / link_length
        return get_middle_node(src, dst, ratio=ratio)

    @property
    def detailed_description(self):
        return "Nodes: " + " -> ".join([str(node) for node in self.nodes])

    def __hash__(self):
        return self.hash

    def __eq__(self, other):
        return self.hash == other.hash

    def __ne__(self, other):
        return not self == other

    def __repr__(self):
        return "<Link: " + self.name + ">"


class HoldLink:

    def __init__(self):
        self.name = "Hold Link"
        self.nodes = [None, None]
        self.segment_lengths = [0]
        self.boundary = [0, 0, 0, 0]
        self.hash = random.random()

    @property
    def detailed_description(self):
        return "<Hold>"

    @property
    def length(self):
        return 0
