// AirportSurfaceOperation.cpp : Defines the entry point for the console application.
//
//boost
#include <boost/program_options.hpp>
#include <boost/tokenizer.hpp>
#include <boost/property_tree/ptree.hpp>
#include <boost/property_tree/json_parser.hpp>

#include "Simulation.h"
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
		("solver,s", po::value<std::string>()->required(), "solvers (FCFS, FLFS, ALL)")
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

  Simulation simulation;
	if(vm.count("graph"))
	{
		if(!simulation.loadGraph(vm["graph"].as<std::string>()))
			return 0;
	}
	else
	{
		simulation.airport.GenerateAbstractGraph(vm["node"].as<std::string>(), vm["link"].as<std::string>(),
			vm["spot"].as<std::string>(), vm["runway"].as<std::string>(), vm["depart"].as<std::string>(), vm["output"].as<std::string>());
	}
	if (!simulation.loadConfig(vm["config"].as<std::string>()))
		return 0;
	if(!simulation.loadAircraftModels(vm["model"].as<std::string>()))
		return 0;
	if (!simulation.loadInstance(vm["instance"].as<std::string>()))
	{
		simulation.generateInstance(vm["instance"].as<std::string>(), vm["agentNum"].as<int>(), vm["interval_min"].as<int>(), vm["interval_max"].as<int>());
	}


  simulation.update_scheduler_params();



	if (vm["solver"].as<std::string>() == "ALL")
	{
		time_t t = std::clock();
		simulation.schedule.run("FLFS");
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
		std::cout << "FLFS, " << runtime << ", " << wait_time << ", " << travel_time << ", " << cost << ", " << makespan << ", " <<
			simulation.schedule.expanded_nodes << ", " <<  simulation.schedule.generated_nodes << ", " << vm["instance"].as<std::string>() << std::endl;
		std::ofstream output;
		output.open(vm["output"].as<std::string>(), std::ofstream::app);
		output << "FLFS," << runtime << "," << wait_time << "," << travel_time << "," << cost << "," << makespan << "," <<
			simulation.schedule.expanded_nodes << "," << simulation.schedule.generated_nodes << "," << vm["instance"].as<std::string>() << std::endl;
		output.close();

		simulation.schedule.clearPlans();

		t = std::clock();
		simulation.schedule.run("FCFS");
		runtime = std::clock() - t;
		wait_time = 0;
		travel_time = 0;
		cost = 0;
		makespan = 0;
		for (auto a : simulation.departures)
		{
			wait_time += a.pushback_time - a.appear_time;
			travel_time += a.expected_runway_time - a.pushback_time;
			cost += a.cost;
			makespan = makespan > a.expected_runway_time ? makespan : a.expected_runway_time;
		}
		wait_time /= simulation.departures.size();
		travel_time /= simulation.departures.size();
		std::cout << "FCFS, " << runtime << ", " << wait_time << ", " << travel_time << ", " << cost << ", " << makespan << ", " <<
			simulation.schedule.expanded_nodes << ". " << simulation.schedule.generated_nodes << ", " << vm["instance"].as<std::string>() << std::endl;
		output.open(vm["output"].as<std::string>(), std::ofstream::app);
		output << "FCFS," << runtime << "," << wait_time << "," << travel_time << "," << cost << "," << makespan << "," <<
			simulation.schedule.expanded_nodes << "," << simulation.schedule.generated_nodes << "," << vm["instance"].as<std::string>() << std::endl;
		output.close();
	}
	else{
		simulation.schedule.run(vm["solver"].as<std::string>());
    simulation.init_simulation_setting();


    while (simulation.completed_count < simulation.departures.size()){
      simulation.tick();
    }

    for (auto a : simulation.departures){
      cout << a.id << "  runway:  " << a.actual_runway_time << "  expected: " << a.expected_runway_time << endl;
    }


  }


    return 0;
}

