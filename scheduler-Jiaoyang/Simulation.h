#include "Schedule.h"

class Simulation
{

private:
  int simulation_time;
  unordered_map<int, vector<Aircraft*>> appear_schedule;
  unordered_set<Aircraft*> aircraft_on_graph;

  void update_fronter();

  // if an aircraft near to a check_point
  // controller may ant to send command in this scenario
  bool near_check_point(const Aircraft& a);

  unordered_map<string, queue<string>> checkpoint_pass_order;
  void update_schedule();
  void handle_conflict();

  void update_aircraft_edge_path();


public:
  int completed_count;
  int tick_per_time_unit;
  // need to be encapsulated
  AirportGraph airport;
  Schedule schedule;
  vector<Aircraft> departures;
	vector<Aircraft> arrivals;
  std::unordered_map<std::string, int> modelNameToModel;
	vector<AircraftModel> aircraftModels;

  void tick();

  void update_scheduler_params();

	// Parameters
	double wait_cost = 0.1;
	double wait_time = 10; // the time interval on waiting location
	double safety_time = 10;
  double safety_distance = 50;
  double safety_distance_check_point = 200;
	State gate_delay;
	State runway_delay;

  // Load files 
	bool loadGraph(const std::string& fileName);
	bool loadConfig(const std::string& fileName);
	bool loadAircraftModels(const std::string& fileName);
	bool loadInstance(const std::string& fileName);
	void generateInstance(const std::string& fileName, int num_of_agent, int interval_min, int interval_max);



  void init_simulation_setting();

	Simulation(){};
	~Simulation(){};

};
