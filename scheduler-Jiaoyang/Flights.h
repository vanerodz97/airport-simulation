#include "AirportGraph.h"
#include "Aircraft.h"

using namespace std;

struct Flights{
  AirportGraph airport;
	vector<Aircraft> departures;
	vector<Aircraft> arrivals;
	std::unordered_map<std::string, int> modelNameToModel;
	vector<AircraftModel> aircraftModels;

  Flights(){};
  ~Flights(){};

};
