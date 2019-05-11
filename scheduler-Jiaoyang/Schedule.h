#pragma once
#include "Node.h"
#include "stdafx.h"
#include "Aircraft.h"
#include "AirportGraph.h"

class Schedule
{
public:
	AirportGraph* airport;
	vector<Aircraft>* departures;
	vector<Aircraft>* arrivals;
	std::unordered_map<std::string, int>* modelNameToModel;
	vector<AircraftModel>* aircraftModels;

	// Performance analysis
	int expanded_nodes;
	int generated_nodes;

	// scheduling params
	double wait_cost = 0.1;
	double wait_time = 10; // the time interval on waiting location
	double safety_time = 10;
	State gate_delay;
	State runway_delay;



	// Path planning
	void updatePath(Aircraft& a, Node* goal);
	double computeGValue(const State& curr, const State& move, const Aircraft& a);
	bool computeNextState(const State& curr, State& next, double length, const State& constraint, const Aircraft& a);
	bool AStarSearch(Aircraft& a, const std::vector<State>& constraints);

	// Priority
	bool compareLeaveTime(const Aircraft& a, const Aircraft& b) { return (a.appear_time + airport->heuristics[a.goal][a.start] < b.appear_time + airport->heuristics[b.goal][b.start]); }

	// Solver
	bool runBase();
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

