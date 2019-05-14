// AirportSurfaceOperation.cpp : Defines the entry point for the console application.
//
//boost
#include <boost/program_options.hpp>
#include <boost/tokenizer.hpp>
#include <boost/property_tree/ptree.hpp>
#include <boost/property_tree/json_parser.hpp>
#include <fstream>


#include "Simulation.h"
// #include "Simulation_baseline.h"
#include "Schedule.h"

int main(int argc, char** argv)
{
	namespace po = boost::program_options;
	// Declare the supported options.
	po::options_description desc("Allowed options");
	desc.add_options()
		("help", "produce help message")
		("graph,g", po::value<std::string>(), "input graph file")
		("model,m", po::value<std::string>()->required(), "input aircraft model file")
		("instance,i", po::value<std::string>()->required(), "input iternary file")
		("config,c", po::value<std::string>()->default_value("../config.yaml"), "input config file")
		("output,o", po::value<std::string>()->required(), "output schedule file")
		("solver,s", po::value<std::string>()->required(), "solvers (BASE, FCFS, FLFS, ALL)")
		("agentNum,k", po::value<int>()->default_value(0), "number of agents")
		("interval_min", po::value<int>()->default_value(0), "interval min")
		("interval_max", po::value<int>()->default_value(0), "interval max")
		("node", po::value<std::string>(), "node model")
		("link", po::value<std::string>(), "link model")
		("spot", po::value<std::string>(), "spot model")
		("runway", po::value<std::string>(), "runway model")
		("depart", po::value<std::string>(), "depart routing table")
		;

	po::variables_map vm;
	po::store(po::parse_command_line(argc, argv, desc), vm);

	if (vm.count("help")) {
		std::cout << desc << std::endl;
		return 1;
	}

	po::notify(vm);
	srand((int)time(0));

	// Simulation_baseline simulation;
	Simulation simulation;
	if (vm.count("graph"))
	{
		if (!simulation.loadGraph(vm["graph"].as<std::string>()))
			return 0;
	}
	else
	{
		simulation.airport.GenerateAbstractGraph(vm["node"].as<std::string>(), vm["link"].as<std::string>(),
			vm["spot"].as<std::string>(), vm["runway"].as<std::string>(), vm["depart"].as<std::string>(), vm["output"].as<std::string>());
	}
	if (!simulation.loadConfig(vm["config"].as<std::string>()))
		return 0;
	if (!simulation.loadAircraftModels(vm["model"].as<std::string>()))
		return 0;
	if (!simulation.loadInstance(vm["instance"].as<std::string>()))
	{
		simulation.generateInstance(vm["instance"].as<std::string>(), vm["agentNum"].as<int>(), vm["interval_min"].as<int>(), vm["interval_max"].as<int>());
	}


	simulation.update_scheduler_params();

	// This is just for my test. Han, you can move this part to your simulator
	// For all new aircraft, the location is its start location, and the time is its appear_time.
	// For all other aircraft, the location is its previous paseed location, and the time is the corresponding time that it passed the loctaion.
	for (int i = 0; i < simulation.departures.size(); i++)
	{
		simulation.departures[i].location = simulation.departures[i].start;
		simulation.departures[i].next_location = simulation.departures[i].start;
		simulation.departures[i].time = simulation.departures[i].appear_time;
	}

	if (vm["solver"].as<std::string>() == "ALL")
	{
		
		string solvers[] = {"BASE", "FCFS", "FLFS"};
		for (int i = 0; i < 3; i++)
		{
			time_t t = std::clock();
      cout << "ALL mode currently not available" << endl;
			// simulation.schedule.run(solvers[i]);
			double runtime = std::clock() - t;
			double wait_time = 0, travel_time = 0, cost = 0, makespan = 0;
			for (auto a : simulation.departures)
			{
				wait_time += a.pushback_time - a.appear_time;
				travel_time += a.expected_runway_time - a.pushback_time;
				cost += a.cost;
				makespan = makespan > a.expected_runway_time ? makespan : a.expected_runway_time;
			}
			wait_time /= simulation.departures.size();
			travel_time /= simulation.departures.size();
			std::cout << solvers[i] << ", " << runtime << ", " << wait_time << ", " << travel_time << ", " << cost << ", " << makespan << ", " <<
				simulation.schedule.expanded_nodes << ", " << simulation.schedule.generated_nodes << ", " << vm["instance"].as<std::string>() << std::endl;
			std::ofstream output;
			output.open(vm["output"].as<std::string>(), std::ofstream::app);
			output << solvers[i] << ", " << runtime << "," << wait_time << "," << travel_time << "," << cost << "," << makespan << "," <<
				simulation.schedule.expanded_nodes << "," << simulation.schedule.generated_nodes << "," << vm["instance"].as<std::string>() << std::endl;
			output.close();

			simulation.schedule.clearPlans();
		}
	}
	else {


		simulation.solver_name = vm["solver"].as<std::string>();
    // simulation.run_scheduler();
		simulation.init_simulation_setting();

		while (simulation.completed_count < simulation.departures.size()) {
			simulation.tick();
		}

    int total_wait_time = 0;
    int total_travel_time = 0;
    int total_zero_velocity_tick = 0;
    int total_stop_received = 0;

		for (auto a : simulation.departures) {
			cout << a.id << "  runway:  " << a.actual_runway_time << "  expected: " << a.expected_runway_time << endl;
      total_wait_time += a.actual_appear_time - a.appear_time;
      total_travel_time += a.actual_runway_time - a.actual_appear_time;
      total_zero_velocity_tick += a.zero_velocity_tick;
      total_stop_received += a.stop_received;
		}
    std::ofstream outfile;

    outfile.open("exp_res.txt", std::ios_base::app);
    outfile << vm["solver"].as<std::string>() << "\t" << vm["instance"].as<std::string>() << "\t"
            << vm["config"].as<std::string>() << "\t"
            << ((double)total_stop_received) / simulation.completed_count << "\t"
            <<  ((double)total_travel_time) / simulation.completed_count << "\t"
            <<  ((double)total_wait_time) / simulation.completed_count << "\t"
            << endl;
    cout << "avg stop received: " << ((double)total_stop_received) / simulation.completed_count << endl;
    cout << "wait time " << ((double)total_wait_time) / simulation.completed_count << endl;
    // cout << "avg zero velocity tick: " << ((double)total_zero_velocity_tick) / simulation.completed_count << endl;
    cout << "avg travel time: " << ((double)total_travel_time) / simulation.completed_count << endl;

	}


	return 0;
}

