"""Class file for the deterministic `Scheduler`."""
from link import HoldLink
from schedule import Schedule
from config import Config
from aircraft import State
from scheduler.abstract_scheduler import AbstractScheduler


class Scheduler(AbstractScheduler):
    """The deterministic scheduler scheduler implements the `Abstractscheduler`
    by offering `scheduler(simulation)`. The scheduler first generates a list
    of itinerary ignoring any conflict then it resolves the conflicts by
    cloning the simulation and ticking on the cloned simulation. Conflicts are
    resolved by adding delays on one of the aircrafts.
    """

    def schedule(self, simulation):

        self.logger.info("Scheduling start")
        itineraries = {}
        priority_list = {}

        # Assigns route per aircraft without any separation constraint
        for aircraft in simulation.airport.aircrafts:
            # NOTE: Itinerary objects are newly created the reference of these
            # object will be used in other objects; however, be ware that the
            # object will be shared instead of being cloned in the later
            # phases.
            itinerary = self.schedule_aircraft(aircraft, simulation)
            itineraries[aircraft] = itinerary
            priority_list[aircraft] = simulation.scenario.get_flight(aircraft).departure_time

        # Resolves conflicts
        schedule, priority = self.__resolve_conflicts(itineraries, simulation, priority_list)

        self.logger.info("Scheduling end")
        return schedule, priority

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
                Schedule(itineraries, 0, 0), priority_list)

            for i in range(tick_times):

                # Adds aircraft
                predict_simulation.pre_tick()

                # Check if all aircraft has an itinerary, if not, assign one
                self.__schedule_new_aircrafts(simulation, predict_simulation,
                                              itineraries, priority_list)

                # Gets conflict in current state
                conflict = self.__get_conflict_to_solve(
                    predict_simulation.airport.get_next_conflicts(predict_simulation.scenario),
                    unsolvable_conflicts
                )

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
                priority_list[aircraft] = simulation.scenario.get_flight(aircraft).departure_time

    def __resolve_conflict(self, itineraries, conflict, attempts,
                           max_attempt):

        self.logger.info("Try to solve %s", conflict)

        # Solves the first conflicts, then reruns everything again.
        aircraft = self.__get_aircraft_to_delay(conflict)
        if aircraft in itineraries:
            # NOTE: New aircraft that only appear in prediction are ignored
            aircraft.add_scheduler_delay()
            self.__mark_attempt(attempts, max_attempt, conflict, aircraft,
                                itineraries)
            self.logger.info("Added delay on %s", aircraft)

    def __mark_attempt(self, attempts, max_attempt, conflict, aircraft,
                       itineraries):

        attempts[conflict] = attempts.get(conflict, 0) + 1
        if attempts[conflict] >= max_attempt:
            self.logger.error("Found deadlock")

            self.logger.error("Aircraft %s itinerary: %s" % (
                conflict.aircrafts[0], conflict.aircrafts[0].itinerary.get_detailed_description()))
            self.logger.error("Aircraft %s itinerary: %s" % (
                conflict.aircrafts[1], conflict.aircrafts[1].itinerary.get_detailed_description()))

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

        if first.state == State.moving and second.state == State.hold:
            return first
        if first.state == State.hold and second.state == State.moving:
            return second
        if first.state == State.hold and second.state == State.hold:
            # This is the case generated by uncertainty in simulation and it's
            # unsolvable. However, if it's not generated by the uncertainty,
            # then this will be a bug needed to be fixed.
            self.logger.debug("Found conflict with two hold aircraft")
            raise ConflictException("Unsolvable conflict found")

        # TODO: if aircraft A is ahead of B, delay B
        # TODO: below is a simplified workaround
        overlapped_progress = self.__compare_itinerary_progress(first, second)

        return overlapped_progress if overlapped_progress else conflict.less_priority_aircraft

    def __compare_itinerary_progress(self, aircraft_a, aircraft_b):
        a_itinerary, b_itinerary = aircraft_a.itinerary, aircraft_b.itinerary
        a_target, b_target = a_itinerary.current_target, b_itinerary.current_target

        if type(a_target) is not HoldLink and a_target in b_itinerary.targets:
            a_target_index_in_b = b_itinerary.targets.index(a_target)
            self.logger.error("A %d %d %f %f" % (
                a_target_index_in_b, b_itinerary.current_target_index, a_itinerary.current_distance, b_itinerary.current_distance))
            if a_target_index_in_b > b_itinerary.current_target_index:
                return aircraft_b
            elif a_target_index_in_b < b_itinerary.current_target_index:
                return aircraft_a
            else:
                return aircraft_a if a_itinerary.current_distance < b_itinerary.current_distance else aircraft_b
        elif type(b_target) is not HoldLink and b_target in a_itinerary.targets:
            b_target_index_in_a = a_itinerary.targets.index(b_target)
            self.logger.error("B %d %d %f %f" % (
                b_target_index_in_a, a_itinerary.current_target_index, a_itinerary.current_distance, b_itinerary.current_distance))
            if b_target_index_in_a > a_itinerary.current_target_index:
                return aircraft_a
            elif b_target_index_in_a < a_itinerary.current_target_index:
                return aircraft_b
            else:
                return aircraft_a if a_itinerary.current_distance < b_itinerary.current_distance else aircraft_b
        else:
            self.logger.error("C")
            return None

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
