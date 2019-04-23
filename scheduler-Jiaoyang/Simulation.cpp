#include "Simulation.h"
#include "yaml-cpp/yaml.h"


bool Simulation::loadGraph(const std::string& fileName)
{
	return airport.loadGraph(fileName);
}

bool Simulation::loadConfig(const std::string& fileName)
{
	//std::cout << "******Load Configs " << fileName << "******" << std::endl;
	YAML::Node config = YAML::LoadFile(fileName);

	const auto& configs = config["config"];
	if (configs)
	{
		for (const auto& config : configs)
		{
			wait_cost = config["wait_cost"].as<double>();
			wait_time = config["wait_time"].as<double>();
			safety_time = config["safety_time"].as<double>();

      tick_per_time_unit = config["tick_per_time_unit"].as<int>();

      safety_distance = config["safety_distance"].as<double>();

			for (auto t : config["gate_delay_time"])
				gate_delay.time.push_back(t.as<double>());
			for (auto prob : config["gate_delay_prob"])
				gate_delay.prob.push_back(prob.as<double>());
			for (auto t : config["runway_delay_time"])
				runway_delay.time.push_back(t.as<double>());
			for (auto prob : config["runway_delay_prob"])
				runway_delay.prob.push_back(prob.as<double>());
			if (gate_delay.time.size() != gate_delay.prob.size() || runway_delay.time.size() != runway_delay.prob.size())
			{
				std::cerr << "Error prob distribution in config file ! " << std::endl;
				return false;
			}
		}
	}
	//std::cout << "wait_cost = " << wait_cost << " ; wait_time = " << wait_time << " ; safety_time = " << safety_time << std::endl;
	//std::cout << "******Configs loaded successfully******" << std::endl << std::endl;
	return true;
}

bool Simulation::loadAircraftModels(const std::string& fileName)
{
	//std::cout << "******Load Aircraft Models " << fileName << "******" << std::endl;
	YAML::Node config = YAML::LoadFile(fileName);

	const auto& models = config["models"];
	if (models) 
	{
		for (const auto& model : models)
		{
			AircraftModel a;
			a.name = model["name"].as<std::string>();
			a.v_max = model["v_max"].as<double>();
			for(auto v: model["velocity"])
				a.v.push_back(v.as<double>());
			for (auto prob : model["prob"])
				a.prob.push_back(prob.as<double>());
			if (a.v.size() != a.prob.size())
			{
				std::cerr << "Error prob distribution! " << a.name << std::endl;
				return false;
			}
			aircraftModels.push_back(a);
			modelNameToModel[a.name] = aircraftModels.size()-1;
		}
	}
	//std::cout << "#Models = " << aircraftModels.size() << std::endl;
	//std::cout << "******Aircraft Models loaded successfully******" << std::endl << std::endl;
	return true;
}

bool Simulation::loadInstance(const std::string& fileName)
{
  std::ifstream ifile(fileName);
  if(!ifile)
    return false;
  //std::cout << "******Load Instance " << fileName << "******" << std::endl;
  YAML::Node config = YAML::LoadFile(fileName);

  int flight_no = 0;

  const auto& aircrafts = config["departures"];
  if (aircrafts) {
    for (const auto& aircraft : aircrafts)
      {
        Aircraft a;
        std::string gate = aircraft["gate"].as<std::string>();
        auto iter = airport.vNameToV.find(gate);
        if (iter == airport.vNameToV.end())
          {
            std::cerr << "Error spot of aircraft! " << gate << std::endl;
            return false;
          }
        a.start = iter->second;
        std::string runway = aircraft["runway"].as<std::string>();
        iter = airport.vNameToV.find(runway);
        if (iter == airport.vNameToV.end())
          {
            std::cerr << "Error runway of aircraft! " << runway << std::endl;
            return false;
          }
        a.goal = iter->second;
        a.appear_time = aircraft["appear_time"].as<double>();
        auto iter2 = modelNameToModel.find(aircraft["model"].as<std::string>());
        a.model = aircraftModels[iter2->second];
        a.id = "departure_" + to_string(flight_no);
        flight_no ++;

        departures.push_back(a);
      }
	}
	return true;
}


void Simulation::update_aircraft_edge_path(){
  for (auto &a:schedule.departures){
    a.wait_cnt = 0;
    for(int i = 0; i < a.path.size() - 1; i ++){
      if (a.path[i].loc == a.path[i + 1].loc){
        a.wait_cnt ++;
        continue;
      }
      auto prev = a.path[i].loc;
      auto next = a.path[i + 1].loc;

      boost::graph_traits<searchGraph_t>::out_edge_iterator ei, ei_end;
      boost::tie(ei, ei_end) = out_edges(prev, airport.G);
      for( ; ei != ei_end; ++ei) {
        if(target(*ei, airport.G) == next) {
          a.edge_path.push_back(airport.G[*ei]);

          break;
        };
      };

    }
  }
  departures = schedule.departures;

}


void Simulation::init_simulation_setting(){
  update_aircraft_edge_path();
  appear_schedule.clear();
  aircraft_on_graph.clear();
  completed_count = 0;

  for (auto &a:departures){
    a.simulation_init();
    a.tick_per_time_unit = tick_per_time_unit;
  }
  simulation_time = 0;
  for (auto& a:departures){
    appear_schedule[a.actual_appear_time].push_back(&a);
  }


  update_schedule();
}

void Simulation::generateInstance(const std::string& fileName, int num_of_agents, int interval_min, int interval_max)
{
	//std::cout << "******Generate Instance " << fileName << "******" << std::endl;
	std::ofstream output;
	output.open(fileName, std::ofstream::app);

	output << "departures:" << std::endl;
	for(int i = 0; i < num_of_agents; i++)
	{
		Aircraft a;
		a.start = airport.gates[rand() % airport.gates.size()];
		a.goal = airport.runways[rand() % airport.runways.size()];
		if(i == 0)
			a.appear_time = 0;
		else
			a.appear_time = departures.back().appear_time + rand() % (interval_max - interval_min) + interval_min;
		a.model = aircraftModels[rand() % aircraftModels.size()];
		departures.push_back(a);

		// write file
		output << "    - " << "gate: " << airport.G[a.start].name << std::endl;
		output << "      " << "runway: " << airport.G[a.goal].name << std::endl;
		output << "      " << "appear_time: " << a.appear_time << std::endl;
		output << "      " << "model: " << a.model.name << std::endl;
	}
	output.close();
	//std::cout << "#Arrivals = " << arrivals.size() << " ; #Departures = " << departures.size() << std::endl;
	//std::cout << "******Instance generated successfully******" << std::endl << std::endl;

}

void Simulation::update_scheduler_params(){
  // pass arrivals

  // call after loading data and before scheduling

  this->schedule.wait_cost = this -> wait_cost;
  this->schedule.wait_time = this -> wait_time;
  this->schedule.safety_time = this -> safety_time;
  this->schedule.gate_delay = this -> gate_delay;


  // TODO hmmm this ain't cool?
  schedule.airport = airport;
  schedule.departures = departures;
  schedule.arrivals = arrivals;
  schedule.modelNameToModel = modelNameToModel;
  schedule.aircraftModels = aircraftModels;

}

bool Simulation::near_check_point(const Aircraft& a){
  return a.edge_path[a.pos.first].length - a.pos.second <= safety_distance_check_point;
}


void Simulation::update_fronter(){
  // n^2 iter
  for (auto ptr_0 : aircraft_on_graph){
    ptr_0 -> prev_aircraft = nullptr;
    for (auto ptr_1 : aircraft_on_graph){
      if (ptr_0 -> id == ptr_0->id){
        continue;
      }
      if (ptr_0 -> current_edge_name() != ptr_1 -> current_edge_name()){
        continue;
      }
      if (ptr_0->pos.second > ptr_1->pos.second){
        continue;
      }
      if (ptr_0->prev_aircraft != nullptr && ptr_0->prev_aircraft->pos.second < ptr_1->pos.second ){
        continue;
      }

      ptr_0->prev_aircraft = ptr_1;

    }
  }
}


void Simulation::update_schedule(){
  checkpoint_pass_order.clear();
  for (auto& a: departures){
    for (const auto &state: a.path){

      auto vertex_name = airport.G[state.loc].name;

      cout << vertex_name << "   " << a.id << endl;
      if (checkpoint_pass_order[vertex_name].size() > 0 && checkpoint_pass_order[vertex_name].back() == a.id){
        cout << "dup" << endl;
        continue;
      }
      checkpoint_pass_order[vertex_name].push(a.id);
    }

  }
}

void Simulation::tick(){
  // reschedule

  // add aircrafts
  // TODO before adding aircrafts, check will it cause conflict
  if (simulation_time % tick_per_time_unit == 0){
    if (appear_schedule[simulation_time/tick_per_time_unit].size() > 0){
      for (auto a_ptr:appear_schedule[simulation_time/tick_per_time_unit]){
        (*a_ptr).simulation_begin();
        aircraft_on_graph.insert(a_ptr);
      }
    }
  }

  // controller
  for (auto a:aircraft_on_graph){
    // if
    if (near_check_point(*a)){
      // if next checkpoint has a in front
      auto v_to = target(airport.eNameToE[a->edge_path[a->pos.first].name], airport.G);
      string v_name = airport.G[v_to].name;

      if (checkpoint_pass_order[v_name].front() == a->id){
        a->send_command(GO_COMMAND);
      }else{
        cout << a->id << " got delay at "<< v_name <<", waiting for " << checkpoint_pass_order[v_name].front() << endl;
        a->send_command(STOP_COMMAND);
      }
      }
  }

  // find fronter
  update_fronter();


  // tick aircraft
  for (auto a:aircraft_on_graph){
    (*a).move();
    for (auto passed : a->passed_check_point){
      cout << a->id << " passed " << passed << endl;
      // find coresponding node and pop.
      auto e_to = target(airport.eNameToE[passed], airport.G);
      cout << airport.G[e_to].name << endl;
      assert (checkpoint_pass_order[airport.G[e_to].name].front() == a->id);
      checkpoint_pass_order[airport.G[e_to].name].pop();


    }
  }

  // remove aircraft near to the runways
  for (auto it = aircraft_on_graph.begin(); it != aircraft_on_graph.end(); ) {
    if ((*it)->ready_for_runway){
      it = aircraft_on_graph.erase(it);
      completed_count += 1;
    }
    else {
      ++it;
    }
  }

  for (auto a_ptr:aircraft_on_graph){
    if (a_ptr -> prev_aircraft!= nullptr &&
        aircraft_on_graph.find(a_ptr -> prev_aircraft)!= aircraft_on_graph.end()){
      if (a_ptr->prev_aircraft->pos.second - a_ptr->pos.second < safety_distance){
        handle_conflict();


      }
    }
  }

  //

  for (auto a:aircraft_on_graph){
    cout << a->id << " - loc: "<< a->position_str() << endl;
    if (a->prev_aircraft != nullptr){
      cout << a->prev_aircraft->id << " in front of " << a->id << endl;
    }
  }
  cout << "completed: " << completed_count << endl;
  cout << "---" << endl;

  simulation_time ++;
}

void Simulation::handle_conflict(){
  cout << "conflict" << endl;
}

