"""Class file for the deterministic `Scheduler`."""
from itinerary import Itinerary
from link import HoldLink
from schedule import Schedule
from config import Config
from aircraft import State
from scheduler.abstract_scheduler import AbstractScheduler
from flight import ArrivalFlight, DepartureFlight
import time


class Scheduler(AbstractScheduler):
    """The deterministic scheduler scheduler implements the `AbstractScheduler`
    by offering `scheduler(simulation)`. The scheduler first generates a list
    of itinerary ignoring any conflict then it resolves the conflicts by
    cloning the simulation and ticking on the cloned simulation. Conflicts are
    resolved by adding delays on one of the aircraft.
    """

    def schedule(self, simulation):

        self.logger.info("Scheduling start")
        start = time.time()
        itineraries = {}
        priority_list = {}

        # Assigns route per aircraft without any separation constraint
        for aircraft in simulation.airport.aircrafts:
            # NOTE: Itinerary objects are newly created the reference of these
            # object will be used in other objects; however, be ware that the
            # object will be shared instead of being cloned in the later
            # phases.
            print("simulation.airport.aircrafts", aircraft)
            if aircraft.itinerary is not None:
                continue
            itinerary = self.schedule_aircraft(aircraft, simulation)
            itineraries[aircraft] = itinerary
            aircraft.set_itinerary(itinerary)

            cur_flight = simulation.scenario.get_flight(aircraft)
            calltime = cur_flight.departure_time if type(cur_flight) is \
                                                    DepartureFlight else \
                cur_flight.arrival_time
            priority_list[aircraft.callsign] = calltime

        # Resolves conflicts
        # schedule, priority = self.__resolve_conflicts(itineraries, simulation,
        #                                               priority_list)
        schedule, priority = Schedule(itineraries, 0, 0), priority_list
        # schedule, priority = self.__schedule(itineraries, simulation,priority_list)

        self.logger.info("Scheduling end")
        print(time.time() - start)
        return schedule, priority

    # def __schedule(self, itineraries, simulation, priority_list):
    #     self.__reset_itineraries(itineraries)
    #     predict_simulation = simulation.copy
    #     predict_simulation.airport.apply_schedule(Schedule(itineraries, 0, 0))
    #     tick_times = 5
    #     for i in range(tick_times):
    #         predict_simulation.pre_tick(self)
    #         self.__schedule_new_aircrafts(simulation, predict_simulation,
    #                                         itineraries, priority_list)
    #         predict_simulation.airport.apply_priority(priority_list)
    #         if i == tick_times - 1:
    #             # Done, conflicts are all handled, return the schedule
    #             self.__reset_itineraries(itineraries)
    #             return Schedule(itineraries, 0, 0), priority_list

    #         # After dealing with the conflicts in current state, tick to
    #         # next state
    #         predict_simulation.tick()
    #         predict_simulation.post_tick()

    def __resolve_conflicts(self, itineraries, simulation, priority_list):

        # Gets configuration parameters
        (tick_times, max_attempt) = self.__get_params()

        # Setups variables
        attempts = {}  # attempts[conflict] = count
        unsolvable_conflicts = set()

        while True:

            # Resets the itineraries (set their state to start node)
            self.__reset_itineraries(itineraries)

            # Creates simulation copy for prediction
            predict_simulation = simulation.copy
            predict_simulation.airport.apply_schedule(
                Schedule(itineraries, 0, 0))

            for i in range(tick_times):

                # Adds aircraft
                predict_simulation.pre_tick(self)

                # Check if all aircraft has an itinerary, if not, assign one
                self.__schedule_new_aircrafts(simulation, predict_simulation,
                                              itineraries, priority_list)
                predict_simulation.airport.apply_priority(priority_list)

                # Gets conflict in current state
                conflict = self.__get_conflict_to_solve(
                    predict_simulation.airport.next_conflicts,
                    unsolvable_conflicts
                )
                # if predict_simulation.airport.intersection_control.resolve_conflict(itineraries):
                #     break
                # if predict_simulation.airport.ramp_control.resolve_conflict(itineraries):
                #     break

                # If a conflict is found, tries to resolve it
                if conflict is not None:
                    try:
                        self.__resolve_conflict(itineraries, conflict, attempts,
                                                max_attempt)
                        # Okay, then re-run everything again
                        break
                    except ConflictException:
                        # The conflict isn't able to be solved, skip it in
                        # later runs
                        unsolvable_conflicts.add(conflict)
                        self.logger.warning("Gave up solving %s", conflict)
                        # Re-run everything again
                        break

                if i == tick_times - 1:
                    # Done, conflicts are all handled, return the schedule
                    self.__reset_itineraries(itineraries)
                    return Schedule(
                        itineraries,
                        self.__get_n_delay_added(attempts),
                        len(unsolvable_conflicts)
                    ), priority_list

                # After dealing with the conflicts in current state, tick to
                # next state
                predict_simulation.tick()
                predict_simulation.post_tick()

    def __schedule_new_aircrafts(self, simulation, predict_simulation,
                                 itineraries, priority_list):
        for aircraft in predict_simulation.airport.aircrafts:
            if not aircraft.itinerary:
                # Gets a new itinerary of this new aircraft
                itinerary = self.schedule_aircraft(aircraft, simulation)
                # Assigns this itinerary to this aircraft
                aircraft.set_itinerary(itinerary)
                # Store a copy of the itinerary
                itineraries[aircraft] = itinerary
            cur_flight = simulation.scenario.get_flight(aircraft)
            if type(cur_flight) is ArrivalFlight:
                call_time = cur_flight.arrival_time
            else:
                call_time = cur_flight.departure_time

            priority_list[aircraft.callsign] = call_time

    def __resolve_conflict(self, itineraries, conflict, attempts,
                           max_attempt):

        self.logger.info("Try to solve %s", conflict)

        # Solves the first conflicts, then reruns everything again.
        aircraft = self.__get_aircraft_to_delay(conflict)

        aircraft.add_scheduler_delay()
        itineraries[aircraft] = aircraft.itinerary
        self.__mark_attempt(attempts, max_attempt, conflict, aircraft,
                            itineraries)
        self.logger.info("Added delay on %s", aircraft)

    def __mark_attempt(self, attempts, max_attempt, conflict, aircraft,
                       itineraries):
        attempts[conflict] = attempts.get(conflict, 0) + 1
        if attempts[conflict] >= max_attempt:
            self.logger.error("Found deadlock")

            self.logger.error(conflict.detailed_description)

            import pdb
            pdb.set_trace()
            # Reverse the delay
            itineraries[aircraft].restore()
            # Forget the attempts
            del attempts[conflict]
            raise ConflictException("Too many attempts")

    @classmethod
    def __get_params(cls):

        rs_time = Config.params["simulation"]["reschedule_cycle"]
        sim_time = Config.params["simulation"]["time_unit"]
        tick_times = int(rs_time / sim_time) + 1
        max_attempt = \
            Config.params["scheduler"]["max_resolve_conflict_attempt"]

        return (tick_times, max_attempt)

    @classmethod
    def __get_conflict_to_solve(cls, conflicts, unsolvable_conflicts):
        for c in conflicts:
            if c not in unsolvable_conflicts:
                return c
        return None

    def __get_aircraft_to_delay(self, conflict):

        first, second = conflict.aircrafts

        if not first.is_predict_delayed and second.is_predict_delayed:
            return first
        if first.is_predict_delayed and not second.is_predict_delayed:
            return second
        if first.is_predict_delayed and second.is_predict_delayed:
            # This is the case generated by uncertainty in simulation and it's
            # unsolvable. However, if it's not generated by the uncertainty,
            # then this will be a bug needed to be fixed.
            self.logger.debug("Found conflict with two hold aircraft")
            raise ConflictException("Unsolvable conflict found")

        return second if first.itinerary.distance_left < second.itinerary.distance_left else first

    @classmethod
    def __get_n_delay_added(cls, attempts):
        return sum(attempts.values())

    @classmethod
    def __reset_itineraries(cls, itineraries):
        for _, itinerary in itineraries.items():
            itinerary.reset()


class ConflictException(Exception):
    """Extends `Exception` for the conflicts."""
    pass
