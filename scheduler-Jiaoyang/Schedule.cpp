#include "stdafx.h"
#include "Schedule.h"
#include <fstream>
#include "yaml-cpp/yaml.h"



void Schedule::shiftTimeDistribution(Node* node) {
	int size = node->state.time.size();
	for (int i = 0; i < size; i++) {
		node->state.time[i] += wait_time;
	}

}

vector<int> Schedule::shiftTimeDistribution(const vector<int>& vec, double time) {
	vector<int> ret;
	for (int i = 0; i < vec.size(); i++) {
		ret.push_back(vec[i] + time);
	}
	return ret;
}

void Schedule::addTimeDistribution(const vector<int>& vec1, const vector<double>&  prob1, 
	const vector<int>& vec2, const vector<double>&  prob2,
	vector<int>& vec3, vector<double>&  prob3)
{
	vec3.clear();
	prob3.clear();
	
	for (int i = 0; i < vec1.size(); i++) 
	{
		for (int j = 0; j < vec2.size(); j++)
		{
			if (i + j == 0 || vec1[i] + vec2[j] > vec3.back())
			{
				vec3.push_back(vec1[i] + vec2[j]);
				prob3.push_back(prob1[i] * prob2[j]);
				continue;
			}
			for (int k = 0; k < vec3.size(); k++)
			{
				if(vec1[i] + vec2[j] == vec3[k])
				{
					prob3[k] += prob1[i] * prob2[j];
					break;
				}
				else if (vec1[i] + vec2[j] < vec3[k])
				{
					vec3.insert(vec3.begin() + k, vec1[i] + vec2[j]);
					prob3.insert(prob3.begin() + k, prob1[i] * prob2[j]);
					break;
				}
			}
		}
	}
}

bool Schedule::loadGraph(const std::string& fileName)
{
	return airport.loadGraph(fileName);
}

bool Schedule::loadConfig(const std::string& fileName)
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

bool Schedule::loadAircraftModels(const std::string& fileName)
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

bool Schedule::loadInstance(const std::string& fileName)
{
	std::ifstream ifile(fileName);
	if(!ifile)
		return false;
	//std::cout << "******Load Instance " << fileName << "******" << std::endl;
	YAML::Node config = YAML::LoadFile(fileName);

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
			a.model = iter2->second;
			departures.push_back(a);
		}
	}
	//std::cout << "#Arrivals = " << arrivals.size() << " ; #Departures = " << departures.size() << std::endl;
	//std::cout << "******Instance loaded successfully******" << std::endl << std::endl;
	return true;
}

void Schedule::generateInstance(const std::string& fileName, int num_of_agents, int interval_min, int interval_max)
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
		a.model = rand() % aircraftModels.size();
		departures.push_back(a);

		// write file
		output << "    - " << "gate: " << airport.G[a.start].name << std::endl;
		output << "      " << "runway: " << airport.G[a.goal].name << std::endl;
		output << "      " << "appear_time: " << a.appear_time << std::endl;
		output << "      " << "model: " << aircraftModels[a.model].name << std::endl;
	}
	output.close();
	//std::cout << "#Arrivals = " << arrivals.size() << " ; #Departures = " << departures.size() << std::endl;
	//std::cout << "******Instance generated successfully******" << std::endl << std::endl;

}

void Schedule::updatePath(Aircraft& a, Node* goal) 
{
	a.path.resize(goal->depth + 1 - goal->move->depth);
	Node* curr = goal;
	a.pushback_time = goal->move->state.getExpectation();
	a.expected_runway_time = goal->state.getExpectation();
	a.cost = a.expected_runway_time - a.pushback_time + wait_cost * (a.pushback_time - a.appear_time);
	/*std::cerr << "---" << a.model << "---\n";
	std::cout << "Leave: ";
	curr->move->state.print();
	std::cerr <<"Arrival: ";
	curr->state.print();*/
	for (int t = goal->depth - goal->move->depth; t >=0; t--)
	{
		a.path[t] = curr->state;
		//curr->state.print();
		//std::cerr << curr->state.loc << " -> ";
		curr = curr->parent;
	}
	//std::cerr << std::endl;


}

double Schedule::computeGValue(const State& curr, const State& move, const Aircraft& a)
{
	double expected_wait = 0;
	for (unsigned int i = 0; i < move.time.size(); i++)
	{
		expected_wait += move.time[i] * move.prob[i];
	}
	expected_wait -= a.appear_time;

	double expected_traveltime = 0;
	for (unsigned int i = 0; i < curr.time.size(); i++)
	{
		expected_traveltime += curr.time[i] * curr.prob[i];
	}

	double move_time = 0.0;
	for (unsigned int i = 0; i < move.time.size(); i++)
	{
		move_time += move.time[i] * move.prob[i];
	}

	expected_traveltime -= move_time;
	return wait_cost * expected_wait + expected_traveltime;
}

bool Schedule::computeNextState(const State& curr, State& next, double length, const State& constraint, const Aircraft& a)
{
	vector<int> leave_time;
	vector<double> leave_prob;
	if (airport.G[curr.loc].type == GATE) // add gate_delay
	{
		addTimeDistribution(curr.time, curr.prob, gate_delay.time, gate_delay.prob, leave_time, leave_prob);
	}
	else
	{
		leave_time = curr.time;
		leave_prob = curr.prob;
	}
	if (constraint.time[0] < 0)
	{
		next.time = shiftTimeDistribution(leave_time, length / aircraftModels[a.model].v_max);
		next.prob = leave_prob;
		/*next.time.resize(curr.time.size());
		next.prob.resize(curr.prob.size());
		for (unsigned int i = 0; i < curr.time.size(); i++)
		{
			next.time[i] = curr.time[i] + length / aircraftModels[a.model].v_max;
			next.prob[i] = curr.prob[i];
		
		}*/
		
		return true;
	}


	// travel time with v_average
	double travel_time = length / aircraftModels[a.model].v_max;
	vector<int> newCurrTime = shiftTimeDistribution(leave_time, travel_time);
	vector<int> newConstraint = shiftTimeDistribution(constraint.time, safety_time);

	vector<int> vec1;
	vector<double> prob1;
	vector<int> vec2;
	vector<double> prob2;

	for (int i = 0; i < newCurrTime.size(); i++) {
		int t = newCurrTime[i];
		double P_Ti =  leave_prob[i];
		double P_Tc = 0.0; // calculate the probablity P(Ti' < t)
		for (int j = 0; j < newConstraint.size(); j++) {
			if(newConstraint[j] <= t) 
				P_Tc += constraint.prob[j];
		}
		vec1.push_back(t);
		prob1.push_back(P_Ti * P_Tc);
	}

	for (int i = 0; i < newConstraint.size(); i++) {
		int t = newConstraint[i];
		double P_Tc = constraint.prob[i];
		double P_Ti = 0.0;
		for (int j = 0; j < newCurrTime.size(); j++) {
			if(newCurrTime[j] < t)
				P_Ti += leave_prob[j];
		}
		vec2.push_back(t);
		prob2.push_back(P_Ti * P_Tc);
	}

	vector<int> nextTime;
	vector<double> nextProb;


	int j = 0;
	for (int i = 0; i < vec1.size(); i++) {
		if (prob1[i] < 0.001)
		{
			continue;
		}
		nextTime.push_back(vec1[i]);
		double temp_prob = prob1[i];
		if(j < vec2.size())
		{
			for (; j < vec2.size(); j++) {
				if (vec2[j] == vec1[i]) {
					temp_prob += prob2[j];
					j++;
					break;
				}
				else if(vec2[j] > vec1[i])
					break;
			}
		}
		nextProb.push_back(temp_prob);
	}

	for (; j < vec2.size(); j++) {
		if (prob2[j] < 0.001)
		{
			continue;
		}
		nextTime.push_back(vec2[j]);
		nextProb.push_back(prob2[j]);
	}


		

	next.time = nextTime;
	next.prob = nextProb;
	double sum = 0;
	for(int i = 0; i < next.prob.size(); i++)
		sum += next.prob[i];
	if (abs(sum - 1) > 0.001)
	{
		for (int i = 0; i < next.prob.size(); i++)
			next.prob[i] /= sum;
	}
	return true;

}



bool Schedule::AStarSearch(Aircraft& a, const std::vector<State>& constraints)
{
	typedef boost::heap::fibonacci_heap< Node*, boost::heap::compare<Node::compare_node> > heap_open_t;
	heap_open_t open_list;
	typedef google::dense_hash_map<Node*, Node*, Node::NodeHasher, Node::eqnode> hashtable_t;
	hashtable_t allNodes_table;
	// initialize allNodes_table (hash table)
	Node* empty_node = new Node();
	empty_node->state.loc = -1;
	Node* deleted_node = new Node();
	deleted_node->state.loc = -2;
	allNodes_table.set_empty_key(empty_node);
	allNodes_table.set_deleted_key(deleted_node);

	hashtable_t::iterator it;  // will be used for find()

	int num_expanded = 0;
	int num_generated = 0;	

	// generate start and add it to the OPEN list
	vector<double> h_table = airport.heuristics[a.goal]; //Heuristics table
	Node* start = new Node(a.start, 0, (int)(h_table[a.start]/aircraftModels[a.model].v_max), NULL);
	start->state.time.push_back(a.appear_time);
	start->state.prob.push_back(1);
	num_generated++;
	start->open_handle = open_list.push(start);
	start->in_openlist = true;
	allNodes_table[start] = start;
	start->move = start;

	while (!open_list.empty())
	{
		Node* curr = open_list.top(); open_list.pop();
		curr->in_openlist = false;
		num_expanded++;


		// Check if the popped node is a goal
		if (curr->state.loc == a.goal) {
			updatePath(a, curr);
			
			for (it = allNodes_table.begin(); it != allNodes_table.end(); it++) {
				delete ((*it).second);  // Node* s = (*it).first; delete (s);
			}
			expanded_nodes += num_expanded;
			generated_nodes += num_generated;
			return true;
		}

		// Wait at starts
		if (curr->state.loc == a.start)
		{
			Node* next = new Node();
			// Node* start = new Node(a.start, 0, h_table[a.start], NULL);
			next->parent = curr;
			next->state.time = shiftTimeDistribution(curr->state.time, wait_time);
			next->state.prob = curr->state.prob;
			next->state.loc = curr->state.loc; // remain at the same location as start
			next->g_val = curr->g_val + wait_time * wait_cost;
			next->h_val = curr->h_val; 
			next->depth = curr->depth + 1;
			next->move = next;			
			num_generated++;
			open_list.push(next);
		}
		// Move to neighbors
		auto neighbours = boost::out_edges(curr->state.loc, airport.G);
		for (auto e : boost::make_iterator_range(neighbours))
		{
			Node* next = new Node();
			next->parent = curr;
			next->state.loc = e.m_target;
			if (next->state.loc == a.start) {
				next->move = next;
			}
			else {
				next->move = next->parent->move;
			}

			if (!computeNextState(curr->state, next->state, airport.G[e].length, constraints[e.m_target], a))
			{
				return false;
			}
			next->depth = curr->depth + 1;
			next->g_val = computeGValue(next->state, next->move->state, a);
			next->h_val =(int)(h_table[next->state.loc] / aircraftModels[a.model].v_max);

			it = allNodes_table.find(next);
			if (it == allNodes_table.end()) 
			{
				next->open_handle = open_list.push(next);
				next->in_openlist = true;
				num_generated++;
				allNodes_table[next] = next;
			}
			else 
			{
				delete(next);
			}
		}  // end for loop that generates successors
	}  // end while loop
	// no path found
	std::cerr << "No path found! " << std::endl;
	for (it = allNodes_table.begin(); it != allNodes_table.end(); it++) {
		delete ((*it).second);
	}
	return false;
}

bool compareAppearTime(const Aircraft& a, const Aircraft& b) { return (a.appear_time < b.appear_time); }
bool Schedule::runFirstComeFirstServe()
{
	std::sort(departures.begin(), departures.end(), compareAppearTime);
	vector<State> constraints(boost::num_vertices(airport.G), State(-INT_MAX,1));
	for (int i = 0; i < departures.size(); i++)
	{
		if(!AStarSearch(departures[i], constraints))
			return false;
		// Update constarints
		for (auto s : departures[i].path)
			constraints[s.loc] = s;
	}
	return true;
}

bool compareRunwayTime(const Aircraft& a, const Aircraft& b) { return (a.expected_runway_time < b.expected_runway_time); }
bool Schedule::runFirstLeaveFirstServe()
{
	//std::sort(departures.begin() + 4, departures.end(), &Schedule::compareLeaveTime);
	vector<State> constraints(boost::num_vertices(airport.G), State(-INT_MAX, 1));
	for (int i = 0; i < departures.size(); i++)
	{
		if (!AStarSearch(departures[i], constraints))
			return false;
	}
	std::sort(departures.begin(), departures.end(), compareRunwayTime);
	for (int i = 0; i < departures.size(); i++)
	{
		if (!AStarSearch(departures[i], constraints))
			return false;
		// Update constarints
		for (auto s : departures[i].path)
			constraints[s.loc] = s;
	}
	return true;
}

bool Schedule::run(const std::string& solver)
{
	if (solver == "FCFS")
	{
		return runFirstComeFirstServe();
	}
	else if (solver == "FLFS")
	{
		return runFirstLeaveFirstServe();
	}
	else
	{
		return false;
	}
}

void Schedule::clearPlans()
{
	for(int i = 0; i < departures.size(); i++)
	{
		departures[i].clearPlan();
	}
	expanded_nodes = 0;
	generated_nodes = 0;
}

Schedule::Schedule()
{
	expanded_nodes = 0;
	generated_nodes = 0;
}


Schedule::~Schedule()
{
}
