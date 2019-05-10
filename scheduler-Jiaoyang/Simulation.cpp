#include "Simulation.h"
#include "yaml-cpp/yaml.h"
#include <random>

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
      safety_time = config["safety_time"].as<double>();

      strict_passing_order = (bool) (config["strict_passing_order"].as<int>());

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
			a.v_avg = model["v_avg"].as<double>();

			a.a_max = model["a_max"].as<double>();
			a.a_brake = model["a_brake"].as<double>();
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
  for (auto &a:departures){
    for(int i = 0; i < a.path.size() - 1; i ++){
      if (a.path[i].loc == a.path[i + 1].loc){
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

}

std::default_random_engine generator;

int sample_distribution(const vector<int>& time, const vector<double>& prob){
  discrete_distribution<double> distribution(prob.begin(), prob.end());
  int number = distribution(generator);
  return time[number];
}

int sample_distribution(State prob_state){
  return sample_distribution(prob_state.time, prob_state.prob);
}

void Simulation::init_simulation_setting(){
  update_aircraft_edge_path();
  appear_schedule.clear();
  aircraft_on_graph.clear();
  completed_count = 0;

  for (auto &a:departures){
    a.simulation_init();

    auto delay = sample_distribution(gate_delay);
    // cout << a.id  << " get delayed for " << delay << endl;
   a.actual_appear_time += delay;

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
  schedule.airport = &airport;
  schedule.departures = &departures;
  schedule.arrivals = &arrivals;
  schedule.modelNameToModel = &modelNameToModel;
  schedule.aircraftModels = &aircraftModels;

}

void Simulation::update_fronter(){

    // Iterate over an unordered_map using range based for loop
    for (auto & element : traffic){

      if (element.second.size() == 0){
        continue;
      }

      // element = (name_of_edge, deque<Aircraft*>)
      Aircraft* prev_ptr = nullptr;
      for (auto & aircraft_ptr : element.second){
        if (prev_ptr != nullptr){
          aircraft_ptr -> prev_aircraft = prev_ptr;
          aircraft_ptr -> distance_to_prev = prev_ptr->pos.second - aircraft_ptr -> pos.second;
        }

        prev_ptr = aircraft_ptr;
      }

      // prev_aircraft for front
      prev_ptr = nullptr;

      auto a_ptr = element.second.front();
      a_ptr -> prev_aircraft = prev_ptr;
      a_ptr -> distance_to_prev = 0;

      int i = a_ptr->pos.first;
      double base_dist = a_ptr->distance_to_next_point();

      while (i < a_ptr->edge_path.size() && base_dist < safety_distance + a_ptr -> brake_distance()){

        auto e_to = target(airport.eNameToE[a_ptr->edge_path[i].name], airport.G);
        double dist;

        boost::graph_traits<searchGraph_t>::out_edge_iterator ei, ei_end;
        boost::tie(ei, ei_end) = out_edges(e_to, airport.G);
        for( ; ei != ei_end; ++ei) {
          string edge_name = airport.G[*ei].name;

          if (traffic.find(edge_name) == traffic.end()){
            continue;
          }

          if (traffic[edge_name].size() == 0){
            continue;
          }

          if (prev_ptr == nullptr){
            prev_ptr = traffic[edge_name].back();
            dist = prev_ptr->pos.second;
          }else{
            auto prev_ptr_candidate = traffic[edge_name].back();
            if (prev_ptr_candidate->pos.second < dist){
              prev_ptr = prev_ptr_candidate;
              dist = prev_ptr->pos.second;
            }
          }
        }
        if (prev_ptr != nullptr){
          a_ptr -> prev_aircraft = prev_ptr;
          a_ptr -> distance_to_prev = dist + base_dist;
          break;
        }
        i += 1;
        base_dist += a_ptr->edge_path[i].length;

      }

      // auto e_to = target(airport.eNameToE[element.first], airport.G);


      // pair of node, distance
      // distance smaller than the lookup distance

      // Old method for looking up prev_aircraft
      // boost::graph_traits<searchGraph_t>::out_edge_iterator ei, ei_end;
      // boost::tie(ei, ei_end) = out_edges(e_to, airport.G);
      // for( ; ei != ei_end; ++ei) {
      //   string edge_name = airport.G[*ei].name;

      //   if (traffic[edge_name].size() == 0){
      //     continue;
      //   }

      //   if (prev_ptr == nullptr){
      //     prev_ptr = traffic[edge_name].back();
      //     dist = prev_ptr->pos.second;
      //   }else{
      //     auto prev_ptr_candidate = traffic[edge_name].back();
      //     if (prev_ptr_candidate->pos.second < dist){
      //       prev_ptr = prev_ptr_candidate;
      //       dist = prev_ptr->pos.second;
      //     }
      //   }
      // }
      // element.second.front()->prev_aircraft = prev_ptr;


      }

  // n^2 iter
  // for (auto ptr_0 : aircraft_on_graph){
  //   ptr_0 -> prev_aircraft = nullptr;
  //   for (auto ptr_1 : aircraft_on_graph){
  //     if (ptr_0 -> id == ptr_1->id){
  //       continue;
  //     }
  //     if (ptr_0 -> current_edge_name() != ptr_1 -> current_edge_name()){
  //       continue;
  //     }
  //     if (ptr_0->pos.second > ptr_1->pos.second){
  //       continue;
  //     }
  //     if (ptr_0->prev_aircraft != nullptr && ptr_0->prev_aircraft->pos.second < ptr_1->pos.second ){
  //       continue;
  //     }

  //     ptr_0->prev_aircraft = ptr_1;

  //   }
  // }
}

void Simulation::update_schedule(){
  /*
    Generate passing order of aircraft in each node.
   */
  checkpoint_pass_order.clear();
  if (strict_passing_order){
    for (auto& a: departures){
      for (const auto &state: a.path){

        auto vertex_name = airport.G[state.loc].name;

        if (checkpoint_pass_order[vertex_name].size() > 0 && checkpoint_pass_order[vertex_name].back() == a.id){
          cout << "dup" << endl;
          continue;
        }
        checkpoint_pass_order[vertex_name].push(a.id);
      }
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
        ready_to_start.push_back(a_ptr);
        //aircraft_on_graph.insert(a_ptr);
        //traffic[a_ptr -> current_edge_name()].push_back(a_ptr);
      }
    }
  }

  vector <Aircraft*> new_ready_to_start;
  for (auto a_ptr: ready_to_start){

    bool aircraft_in_front_flag = false;


    /* check if path before airplane is clear */
    string e_name = a_ptr->edge_path[0].name;

    if (traffic.find(e_name) != traffic.end() &&
        traffic[e_name].size() != 0 &&
        traffic[e_name].back()->pos.second < safety_distance){
      aircraft_in_front_flag = true;
    }



    string name = airport.G[a_ptr->path[0].loc].name;

    if (! strict_passing_order){

      if (checkpoint_pass_order.find(name) == checkpoint_pass_order.end() || checkpoint_pass_order[name].size() == 0){
        checkpoint_pass_order[name].push(a_ptr->id);
      }
    }

    if (! aircraft_in_front_flag && checkpoint_pass_order[name].front() == a_ptr->id){

      checkpoint_pass_order[name].pop();
      aircraft_on_graph.insert(a_ptr);
      traffic[a_ptr -> current_edge_name()].push_back(a_ptr);
    }else{
      new_ready_to_start.push_back(a_ptr);
    }

  }

  ready_to_start = new_ready_to_start;


  // controller
  for (auto a:aircraft_on_graph){
    // if
    bool deceleration_flag = false;
    string cross;

    vector<string> intersection_to_grab;

    for (auto e_str: a->intersection_in_sight(safety_distance + 100)){

      if (a->id == "departure_17"){
        cout << "boom" << endl;
      }

      auto v_to = target(airport.eNameToE[e_str], airport.G);

      auto name = airport.G[v_to].name;

      if (!strict_passing_order && ! deceleration_flag && checkpoint_pass_order[name].size() == 0){

        // TODO additional grabbing condition, that path must be empty

        if (e_str == a-> current_edge_name() && traffic[e_str].front()->id != a->id){

          cross = name;
          deceleration_flag = true;
          break;
        }

        if (e_str != a-> current_edge_name() && traffic[e_str].size()> 0){
          cross = name;
          deceleration_flag = true;
          break;
        }


        cout << a->id << " grab " << name << endl;

        intersection_to_grab.push_back(name);
        //checkpoint_pass_order[name].push(a->id);
      }



      if (checkpoint_pass_order[airport.G[v_to].name].size() != 0 && checkpoint_pass_order[airport.G[v_to].name].front() != a->id ){
        cross = airport.G[v_to].name;
        deceleration_flag = true;
        break;
      }
    }
    if (deceleration_flag){
      if (checkpoint_pass_order[cross].size() == 0){
        cout << a->id << " need to slow down due to intersection " << cross << " is still open for grabbing" << endl;
      }else{
        cout << a->id << " need to slow down due to intersection " << cross << " required " << checkpoint_pass_order[cross].front() << " to cross first" << endl;
      }
      a->send_command(STOP_COMMAND);
    }else{

      if (! strict_passing_order){
        for (auto v_name: intersection_to_grab){
          checkpoint_pass_order[v_name].push(a->id);
        }
      }

      a->send_command(GO_COMMAND);
    }

    // if (near_check_point(*a)){
    //   // if next checkpoint has a in front
    //   auto v_to = target(airport.eNameToE[a->edge_path[a->pos.first].name], airport.G);
    //   string v_name = airport.G[v_to].name;

    //   if (checkpoint_pass_order[v_name].front() == a->id){
    //     a->send_command(GO_COMMAND);
    //   }else{
    //     cout << a->id << " got delay at "<< v_name <<", waiting for " << checkpoint_pass_order[v_name].front() << endl;
    //     a->send_command(STOP_COMMAND);
    //   }
    // }
  }

  // find fronter
  update_fronter();


  bool passed_flag = false;

  // tick aircraft
  for (auto a:aircraft_on_graph){

    if (a-> ready_for_runway){
      continue;
    }

    a->move();
    for (auto passed : a->passed_check_point){
      passed_flag = true;
      cout << a->id << " passed " << passed << endl;
      // find coresponding node and pop.
      auto e_to = target(airport.eNameToE[passed], airport.G);
      cout << airport.G[e_to].name << endl;
      assert (checkpoint_pass_order[airport.G[e_to].name].front() == a->id);

      a-> time = (int) (simulation_time / tick_per_time_unit);

      checkpoint_pass_order[airport.G[e_to].name].pop();

      // TODO traffic and checkpoint_pass_order may merge
      if (traffic[passed].size() > 0 && traffic[passed].front()->id == a->id){
        traffic[passed].pop_front();
      }

    }

    auto current_edge_name = a->current_edge_name();
    if (!a->ready_for_runway && a->passed_check_point.size() > 0){
      a->location = source(airport.eNameToE[a->current_edge_name()], airport.G);
      a->next_location = target(airport.eNameToE[a->current_edge_name()], airport.G);

      traffic[current_edge_name].push_back(a);
    }
  }

  // remove aircraft near to the runways
  for (auto it = aircraft_on_graph.begin(); it != aircraft_on_graph.end(); ) {
    if ((*it)->ready_for_runway){
      if ((*it) -> actual_runway_time == 0){
        int runway_delay_time = sample_distribution(runway_delay);
        cout << "runway time of " << (*it)->id << " get delayed by " << runway_delay_time << endl;
        (*it) ->actual_runway_time = simulation_time/ tick_per_time_unit + runway_delay_time;
      }

      if (simulation_time / tick_per_time_unit == (*it)->actual_runway_time){
        cout <<(*it)->id << " departs " << endl;

        it = aircraft_on_graph.erase(it);
        completed_count += 1;
      }else{
        ++it;
      }

    }
    else {
      ++it;
    }
  }

  update_fronter();


  // check conflict
  for (auto a_ptr:aircraft_on_graph){
    if (a_ptr -> prev_aircraft!= nullptr &&
        aircraft_on_graph.find(a_ptr -> prev_aircraft)!= aircraft_on_graph.end()){
      if (a_ptr->pos.first == 0){
        continue;
      }
      if (a_ptr -> distance_to_prev < safety_distance){
        handle_conflict();
      }
    }
  }

  // print stat of simulation


  for (auto a:aircraft_on_graph){
    cout << a->id << " - loc: "<< a->position_str() << endl;
    cout << "v:  " << a->velocity << " acc: "<< a->acceleration << endl;
    if (a->prev_aircraft != nullptr){
      cout << a->prev_aircraft->id << " in front of " << a->id << " by " << a->distance_to_prev << endl;
    }
  }
  cout << "completed: " << completed_count << endl;
  cout << "---" << endl;

  simulation_time ++;
}

void Simulation::handle_conflict(){
  cout << "conflict" << endl;
}

