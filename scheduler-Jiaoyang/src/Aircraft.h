#pragma once
#include "AirportGraph.h"

/*
aircrafts position is defined by an index on edge_path
and a double number represent by the distance already traversed.

*/
typedef pair<int, double> position;

const int NO_COMMAND = 0;
const int GO_COMMAND = 1;
const int STOP_COMMAND = 2;

struct AircraftModel
{
	std::string name;
	double v_max;
	double v_avg;
	double a_brake = 100;
	double a_max = 70;
	double safety_distance = 600;

	vector<double> v;
	vector<double> prob;
};


struct Aircraft
{
private:
	void init_expr_data();

	void generate_actual_appear_time();
	int prev_command = NO_COMMAND;


public:
	int command = NO_COMMAND;

	double brake_distance() { return 250; };

	// Input
	std::string id;
	vertex_t start;
	vertex_t goal;

	// to track the previous passed node and the corresponding time
	vertex_t location;
	double time = 0;
	vertex_t next_location;

	vector<string> intersection_in_sight(double);

	int tick_per_time_unit = 50;


	Aircraft* prev_aircraft;
	double distance_to_prev;

	double appear_time;
	AircraftModel model;
	// Output
	vector<State> path;
	double pushback_time;


	double ideal_distance = 2000;
	double expected_runway_time = 0;
	double cost;
	// Functions
	void clearPlan() { path.clear(); }

	// simulation
	void simulation_init();

	void send_command(int command);

  // TODO init
  bool ready_to_start = false;
  bool begin_moving = false;
	bool ready_for_runway = false;
	bool planned = false; // have being planned or not

	position pos;
	double velocity = 0;
	double acceleration = 0;
	double get_velocity();

	void simulation_begin();
	void move();

	// used for debuging
	string position_str();
	string current_edge_name();
	double distance_to_next_point();

	vector<string> passed_check_point;
  deque<string> mutex_held;


	vector<Edge> edge_path;

	/* experiment stat */
	//
  int stop_received;
	int zero_velocity_tick;
	int wait_tick;

	// should be appear_time + wait_time + delay
	double actual_appear_time;
	double actual_runway_time;
};
