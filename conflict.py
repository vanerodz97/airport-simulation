"""Class file for `Conflict`."""
from utils import str2sha1


class Conflict:
    """`Conflict` represents two aircrafts are too close to each other in an
    airport.
    """

    # The aircraft are always ranked by priority. Less comes first.
    def __init__(self, locations, aircrafts):

        self.locations = locations
        self.aircrafts = aircrafts

        callsigns = []
        for aircraft in aircrafts:
            callsigns.append(aircraft.callsign)
        callsigns.sort()

        self.hash = str2sha1("%s#%s" %
                             ("#".join(callsigns),
                              "#".join(str(self.locations))))

        self.less_priority_aircraft = aircrafts[0]

    def __hash__(self):
        return self.hash

    def __eq__(self, other):
        return self.hash == other.hash

    def __ne__(self, other):
        return not self == other

    def __repr__(self):
        return "<Conflict: %s %s>" % (self.locations, self.aircrafts)
