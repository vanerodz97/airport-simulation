#!/usr/bin/env python3

from node import Node
from aircraft import Aircraft, State
from itinerary import Itinerary
from copy import deepcopy
from config import Config

import sys
import unittest
sys.path.append('..')


class TestSpeed(unittest.TestCase):

    Config.params["simulator"]["test_mode"] = True

    n1 = Node("N1", {"lat": 47.722000, "lng": -122.079057})
    
    def test_speed(self):
        # test init speed
        aircraft = Aircraft("F1", "M1", self.n1, State.unknown)
        self.assertEqual(aircraft.speed, 0)
        
        # test acceleration for pushback speed
        aircraft = Aircraft("F1", "M1", self.n1, State.pushback)
        new_speed = aircraft.get_next_speed(None, State.pushback)
        expected_speed = aircraft.IDEAL_ACC
        self.assertEqual(new_speed, expected_speed)

        # test deceleration for pushback speed
        aircraft = Aircraft("F1", "M1", self.n1, State.pushback)
        aircraft.set_speed(aircraft.pushback_speed + 10.0)
        new_speed = aircraft.get_next_speed(None, State.pushback)
        expected_speed = aircraft.pushback_speed
        self.assertEqual(new_speed, expected_speed)

        # test pushback speed
        aircraft = Aircraft("F1", "M1", self.n1, State.pushback)
        aircraft.set_speed(aircraft.IDEAL_ACC)
        new_speed = aircraft.get_next_speed(None, State.pushback)
        expected_speed = aircraft.pushback_speed
        self.assertEqual(new_speed, expected_speed)

        # test acceleration for ramp speed
        aircraft = Aircraft("F1", "M1", self.n1, State.ramp)
        aircraft.set_speed(aircraft.pushback_speed)
        new_speed = aircraft.get_next_speed(None, State.ramp)
        expected_speed = aircraft.pushback_speed + aircraft.IDEAL_ACC
        self.assertEqual(new_speed, expected_speed)

        # test deceleration for ramp speed
        aircraft = Aircraft("F1", "M1", self.n1, State.ramp)
        aircraft.set_speed(aircraft.ramp_speed + 10.0)
        new_speed = aircraft.get_next_speed(None, State.ramp)
        expected_speed = aircraft.ramp_speed
        self.assertEqual(new_speed, expected_speed)

        # test ramp speed
        aircraft = Aircraft("F1", "M1", self.n1, State.ramp)
        aircraft.set_speed(aircraft.ramp_speed - 10.0)
        new_speed = aircraft.get_next_speed(None, State.ramp)
        expected_speed = aircraft.ramp_speed
        self.assertEqual(new_speed, expected_speed)

        # test acceleration for active movement speed
        aircraft = Aircraft("F1", "M1", self.n1, State.taxi)
        aircraft.set_speed(aircraft.ramp_speed)
        new_speed = aircraft.get_next_speed(None, State.taxi)
        expected_speed = aircraft.ramp_speed + aircraft.IDEAL_ACC
        self.assertEqual(new_speed, expected_speed)

        # test deceleration for active movement speed
        aircraft = Aircraft("F1", "M1", self.n1, State.taxi)
        aircraft.set_speed(aircraft.IDEAL_SPEED + 10.0)
        new_speed = aircraft.get_next_speed(None, State.taxi)
        expected_speed = aircraft.IDEAL_SPEED
        self.assertEqual(new_speed, expected_speed)

        # test ramp speed
        aircraft = Aircraft("F1", "M1", self.n1, State.taxi)
        aircraft.set_speed(aircraft.IDEAL_SPEED - 10.0)
        new_speed = aircraft.get_next_speed(None, State.taxi)
        expected_speed = aircraft.IDEAL_SPEED
        self.assertEqual(new_speed, expected_speed)
