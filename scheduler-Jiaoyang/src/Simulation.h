#include "Schedule.h"
#include <deque>

class Simulation
{

private:
  unordered_map<int, vector<Aircraft*>> appear_schedule;
  unordered_set<Aircraft*> aircraft_on_graph;

  void update_fronter();

  // if an aircraft near to a check_point
  // controller may ant to send command in this scenario
  bool near_check_point(const Aircraft& a);

  unordered_map<string, queue<string>> checkpoint_pass_order;
  void update_schedule();
  void handle_conflict(Aircraft*);

  void update_aircraft_edge_path();

  unordered_map<string, deque<Aircraft*> > traffic;

  vector<Aircraft*> ready_to_start;


public:

  int simulation_time;
  int schedule_time_window;

  bool strict_passing_order = false;



  string solver_name = "FLFS";
  void run_scheduler(){
    schedule.run(solver_name, simulation_time / tick_per_time_unit, schedule_time_window);
  }

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

  std::ofstream outfile;

	// Parameters
	double wait_cost = 0.1;
	double wait_time = 10; // the time interval on waiting location
	double safety_time;
  double safety_distance;
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
