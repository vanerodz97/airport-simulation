import sys

from utils import ll2px

from PyQt5.QtCore import Qt, QPoint
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

REFRESH_RATE = 1 # fps
SIZE = 640

class Screen(QWidget):

    def __init__(self, airport):

        super().__init__()

        # Sets the window title
        self.setWindowTitle(airport.name)

        # Sets the window size
        self.setGeometry(0, 0, SIZE, SIZE)

        # Draws the background image
        self.draw_background(airport.image_filepath)

        # Saves the current airport state
        self.airport = airport

        # Shows
        self.show()

    def draw_background(self, image_filepath):

        # Sets the image object
        print(image_filepath)
        pixmap = QPixmap(image_filepath, "1")
        scaled_pixmap = pixmap.scaled(self.size(), Qt.KeepAspectRatio)

        # Draw
        palette = QPalette()
        palette.setBrush(10, QBrush(scaled_pixmap))
        self.setPalette(palette)

    def paintEvent(self, event):
        self.draw_gates()
        self.draw_spots()
        self.draw_runways()
        self.draw_taxiways()

    def draw_gates(self):
        for gate in self.airport.gates:
            self.draw_node(gate, Qt.darkGreen)

    def draw_spots(self):
        for spot in self.airport.spots:
            self.draw_node(spot, Qt.red)

    def draw_node(self, node, color):

        painter = QPainter()
        painter.begin(self)
        painter.setPen(color)
        px_pos = ll2px(node.geo_pos, self.airport.corners, SIZE)
        point = QPoint(px_pos[0], px_pos[1])
        painter.drawEllipse(point, 3, 3)
        painter.end()

    def draw_runways(self):
        for runway in self.airport.runways:
            self.draw_link(runway, Qt.blue)

    def draw_taxiways(self):
        for taxiway in self.airport.taxiways:
            self.draw_link(taxiway, Qt.black)

    def draw_link(self, link, color):

        # Setups painter
        painter = QPainter()
        painter.begin(self)
        painter.setPen(color)

        # Draws all nodes of the link
        previous_node = None
        for node in link.nodes:
            if previous_node:
                prev_geo_pos = ll2px(previous_node.geo_pos, self.airport.corners, SIZE)
                curr_geo_pos = ll2px(node.geo_pos, self.airport.corners, SIZE)
                painter.drawLine(prev_geo_pos[0], prev_geo_pos[1],
                                 curr_geo_pos[0], curr_geo_pos[1])
            previous_node = node

        # Closes the painter
        painter.end()


class Monitor:
    """ Monitor works as an observer which pull states from the simulation and
    draw them on the screen. Two types of states are used. Static states
    contain states that won't change during the whole simulation process; 
    runtime states indicates the states the changes within simulation.
    """

    def __init__(self, simulation):

        static_state = simulation.get_static_state()
        airport = static_state["airport"]

        # Initializes the screen
        self.simulation = simulation
        self.app = QApplication(sys.argv)

        # Starts screen and holds
        self.screen = Screen(airport)
        self.app.exec_()

    def close(self):
        self.screen.close()
