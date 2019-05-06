#import "AirportGraph.h"

// aircrafts position is defined by two vertex and a double
typedef pair<int, double> position;

const int NO_COMMAND = 0;
const int GO_COMMAND = 1;
const int STOP_COMMAND = 2;

struct AircraftModel
{
	std::string name;
	double v_max;
  double a_brake = 20;
  double a_max = 10;

	vector<double> v;
	vector<double> prob;
};


struct Aircraft
{
private:
  void generate_actual_appear_time();
  int command;



public:

  double actual_runway_time;

	// Input
	std::string id;
	vertex_t start;
	vertex_t goal;


  int tick_per_time_unit = 50;


  Aircraft* prev_aircraft;

	double appear_time;
	AircraftModel model;
	// Output
	vector<State> path;
	double pushback_time;


  double ideal_distance=400;
	double expected_runway_time;
	double cost;
	// Functions
	void clearPlan(){path.clear(); }

  // simulation
  void simulation_init();

  // should be appear_time + wait_time + delay
  double actual_appear_time;

  void send_command(int command);

  bool ready_for_runway;
  position pos;
  double velocity=0;
  double acceleration = 0;
  double get_velocity();

  void simulation_begin();
  void move();

  string position_str();
  string current_edge_name();

  vector<string> passed_check_point;

  vector<Edge> edge_path;
};

