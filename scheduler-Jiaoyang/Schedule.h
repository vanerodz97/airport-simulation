#pragma once
#include "AirportGraph.h"
#include "Node.h"

struct Aircraft
{
	// Input
	std::string id;
	vertex_t start;
	vertex_t goal;
	double appear_time;
	int model;
	// Output
	vector<State> path;
	double pushback_time;
	double expected_runway_time;
	double cost;
	// Functions
	void clearPlan(){path.clear(); }
};

struct AircraftModel
{
	std::string name;
	double v_max;
	vector<double> v;
	vector<double> prob;
};

class Schedule
{
public:
	AirportGraph airport;
	vector<Aircraft> departures;
	vector<Aircraft> arrivals;
	std::unordered_map<std::string, int> modelNameToModel;
	vector<AircraftModel> aircraftModels;

	// Parameters
	double wait_cost = 0.1;
	double wait_time = 10; // the time interval on waiting location
	double safety_time = 10;
	State gate_delay;
	State runway_delay;

	// Performance analysis
	int expanded_nodes;
	int generated_nodes;

	// Load files
	bool loadGraph(const std::string& fileName);
	bool loadConfig(const std::string& fileName);
	bool loadAircraftModels(const std::string& fileName);
	bool loadInstance(const std::string& fileName);
	void generateInstance(const std::string& fileName, int num_of_agent, int interval_min, int interval_max);

	// Path planning
	void updatePath(Aircraft& a, Node* goal);
	double computeGValue(const State& curr, const State& move, const Aircraft& a);
	bool computeNextState(const State& curr, State& next, double length, const State& constraint, const Aircraft& a);
	bool AStarSearch(Aircraft& a, const std::vector<State>& constraints);

	// Priority
	bool compareLeaveTime(const Aircraft& a, const Aircraft& b) { return (a.appear_time + airport.heuristics[a.goal][a.start] < b.appear_time + airport.heuristics[b.goal][b.start]); }

	// Solver
	bool runFirstComeFirstServe();
	bool runFirstLeaveFirstServe();
	bool run(const std::string& solver);
	void clearPlans();
	Schedule();
	~Schedule();

	// Helper function
	void shiftTimeDistribution(Node* node);
	vector<int> shiftTimeDistribution(const vector<int>& vec, double time);
	void addTimeDistribution(const vector<int>& vec1, const vector<double>&  prob1,
		const vector<int>& vec2, const vector<double>&  prob2,
		vector<int>& vec3, vector<double>&  prob3);
};

