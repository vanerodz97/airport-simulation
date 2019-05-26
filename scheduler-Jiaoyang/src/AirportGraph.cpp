#include "AirportGraph.h"
#include <fstream>
#include "yaml-cpp/yaml.h"
#include<boost/tokenizer.hpp>
#include <iostream>   // std::cout
#include <string>     // std::string, std::stod
#include <iomanip>      // std::setprecision
#include <cfloat>

position_t nodeAsPos(const YAML::Node& node)
{
	return std::make_pair(node[0].as<double>(), node[1].as<double>());
}

double getDistance(const position_t& a, const position_t& b)
{
	return sqrt((a.first - b.first)*(a.first - b.first) + (a.second - b.second)*(a.second - b.second));
}

bool AirportGraph::loadGraph(const std::string& fileName)
{
	//std::cout << "******Load Airport Graph " << fileName << "******" << std::endl;
	YAML::Node config = YAML::LoadFile(fileName);

	// add vertices
	const auto& vertices = config["vertices"];
	if (vertices) {
		for (const auto& node : vertices) {
			position_t pos = nodeAsPos(node["pos"]);
			std::string name = node["name"].as<std::string>();
			auto v = boost::add_vertex(G);
			G[v].name = name;
			G[v].pos = pos;
			vNameToV[name] = v;
			std::string type = node["type"].as<std::string>();
			if (type == "gate")
			{
				G[v].type = vertex_type::GATE;
				gates.push_back(v);
			}
			else if (type == "spot")
			{
				G[v].type = vertex_type::SPOT;
				spots.push_back(v);
			}
			else if (type == "intersection")
			{
				G[v].type = vertex_type::INTERSECTION;
				intersections.push_back(v);
			}
			else if (type == "runway")
			{
				G[v].type = vertex_type::RUNWAY;
				runways.push_back(v);
			}
			else
			{
				std::cerr << "Error vertex type! " << type << std::endl;
				return false;
			}
		}
	}

	// add edges
	const auto& edges = config["edges"];
	if (edges) {
		for (const auto& edge : edges) {
			std::string name = edge["name"].as<std::string>();
			std::string fromName = edge["from"].as<std::string>();
			auto fromIter = vNameToV.find(fromName);

			std::string toName = edge["to"].as<std::string>();
			auto toIter = vNameToV.find(toName);
			if (fromIter == vNameToV.end()
				|| toIter == vNameToV.end()
				|| fromIter->second == toIter->second) {
				std::cerr << "invalid edge! " << edge << std::endl;
				return false;
			}
			auto e = boost::add_edge(fromIter->second, toIter->second, G);
			G[e.first].name = name;
			G[e.first].length = edge["length"].as<double>();  //getDistance(G[fromIter->second].pos, G[toIter->second].pos);

			eNameToE[name] = e.first;
		}
	}
	//getGraphInfo();
	//std::cout << "******Graph Loaded Successfully******" << std::endl << std::endl;
	computeHeuristics();
	return true;
}


bool AirportGraph::GenerateAbstractGraph(const std::string& nodeFile, const std::string& linkFile,
	const std::string& spotFile, const std::string& runwayFile, const std::string& departFile,
	const std::string& outputFile)
{
	typedef boost::tokenizer<boost::char_separator<char> >
		tokenizer;
	boost::char_separator<char> sep("<:|,> ");

	// read the node file
	std::string line;
	std::ifstream myfile(nodeFile.c_str());
	if (!myfile.is_open())
	{
		std::cout << "The node file doesn't exist." << std::endl;
		return false;
	}
	getline(myfile, line);
	while (line != "")
	{

		tokenizer tok(line, sep);
		tokenizer::iterator beg = tok.begin();
		beg++; // skip "Node"
		std::string name = beg->c_str(); // read the name of the node
		position_t pos;
		beg++;
		pos.first = std::stod(beg->c_str()); // read the first coordinate of the position of the node
		beg++;
		pos.second = std::stod(beg->c_str()); // read the second coordinate of the position of the node
		auto iter = vPosToV.find(pos);
		auto iter2 = vNameToV.find(name);
		if (iter == vPosToV.end())
		{
			auto v = boost::add_vertex(G);
			G[v].name = name;
			vNameToV[name] = v;
			G[v].pos = pos;
			vPosToV[pos] = v;
			if (iter2 == vNameToV.end())
				vNameToV[name] = v;
		}
		else	if (iter2 == vNameToV.end())
			vNameToV[name] = iter->second;
		getline(myfile, line); // read the next line
	}
	myfile.close();

	// read the link file
	myfile.open(linkFile.c_str());
	if (!myfile.is_open())
	{
		std::cout << "The link file doesn't exist." << std::endl;
		return false;
	}
	getline(myfile, line);
	while (line != "")
	{
		tokenizer tok(line, sep);
		tokenizer::iterator beg = tok.begin();
		beg++; // skip "Link"
		beg++; // skip "Node"
		std::string fromName = beg->c_str(); // read the name of the "from" node
		auto fromIter = vNameToV.find(fromName);
		beg++;
		beg++; // skip its first coordinate
		beg++; // skip its second coordinate
		beg++; // skip "to"
		beg++; // skip "Node"
		std::string toName = beg->c_str(); // read the name of the "to" node
		auto toIter = vNameToV.find(toName);
		beg++;
		beg++; // skip its first coordinate
		beg++; // skip its second coordinate
		beg++; // skip "disance"
		double distance = std::stod(beg->c_str()); // read the length of the edge
		if (fromIter == vNameToV.end()
			|| toIter == vNameToV.end()
			|| (fromIter->second == toIter->second && abs(distance) > 0.001))
		{
			std::cerr << "invalid edge! " << line << std::endl;
			return false;
		}
		else if (fromIter->second != toIter->second)
		{
			std::string name = G[fromIter->second].name + "->" + G[toIter->second].name;
			auto iter = eNameToE.find(name);
			if (iter == eNameToE.end())
			{
				auto e = boost::add_edge(fromIter->second, toIter->second, G);
				G[e.first].length = distance;
				G[e.first].name = name;
				eNameToE[name] = e.first;
			}
		}
		getline(myfile, line); // read the next line
	}
	myfile.close();

	// read the depart routing table to correct some link directions
	//myfile.open(departFile.c_str());
	//if (!myfile.is_open())
	//{
	//	std::cout << "The depart file doesn't exist." << std::endl;
	//	return false;
	//}
	//getline(myfile, line);
	//while (line != "")
	//{
	//	if (line.at(0) == '[') // a new route
	//	{
	//		getline(myfile, line); // ignore the first line
	//		while (line != "")
	//		{
	//			tokenizer tok(line, sep);
	//			tokenizer::iterator beg = tok.begin();
	//			beg++; // skip "link"
	//			beg++; // skip "Node
	//			std::string fromName = beg->c_str(); // read the name of the "from" node
	//			auto fromIter = vNameToV.find(fromName);
	//			beg++;
	//			beg++; // skip its first coordinate
	//			beg++; // skip its second coordinate
	//			beg++; // skip "to"
	//			beg++; // skip "Node"
	//			std::string toName = beg->c_str(); // read the name of the "to" node
	//			auto toIter = vNameToV.find(toName);
	//			beg++;
	//			beg++; // skip its first coordinate
	//			beg++; // skip its second coordinate
	//			beg++; // skip "disance"
	//			double distance = std::stod(beg->c_str()); // read the length of the edge
	//			if (fromIter == vNameToV.end()
	//				|| toIter == vNameToV.end())
	//			{
	//				std::cerr << "invalid edge! " << line << std::endl;
	//				return false;
	//			}
	//			else if (fromIter->second == toIter->second)
	//			{
	//				getline(myfile, line); // read the next line
	//				continue;
	//			}
	//			std::string name = G[fromIter->second].name + "->" + G[toIter->second].name;
	//			auto iter = eNameToE.find(name);
	//			if (iter != eNameToE.end())
	//			{
	//				getline(myfile, line); // read the next line
	//				continue;
	//			}
	//			std::string nameForReverseEdge = G[toIter->second].name + "->" + G[fromIter->second].name;
	//			iter = eNameToE.find(nameForReverseEdge);
	//			if (iter != eNameToE.end())
	//			{
	//				boost::remove_edge(fromIter->second, toIter->second, G);
	//				eNameToE.erase(nameForReverseEdge);
	//			}
	//			auto e = boost::add_edge(fromIter->second, toIter->second, G);
	//			G[e.first].length = distance;
	//			G[e.first].name = name;
	//			eNameToE[name] = e.first;
	//			getline(myfile, line); // read the next line
	//		}
	//		getline(myfile, line); // read the next line
	//	}
	//}
	//myfile.close();

	//read the spot file
	myfile.open(spotFile.c_str());
	if (!myfile.is_open())
	{
		std::cout << "The spot file doesn't exist." << std::endl;
		return false;
	}
	getline(myfile, line);
	while (line != "")
	{
		tokenizer tok(line, sep);
		tokenizer::iterator beg = tok.begin();
		beg++; // skip "Node"
		std::string name = beg->c_str(); // read the name of the node
		auto iter = vNameToV.find(name);
		if (iter == vNameToV.end())
		{
			std::cerr << "non-existing spot node! " << line << std::endl;
			return false;
		}
		G[iter->second].type = vertex_type::SPOT;
		getline(myfile, line); // read the next line
	}
	myfile.close();

	//read the runway file
	myfile.open(runwayFile.c_str());
	if (!myfile.is_open())
	{
		std::cout << "The runway file doesn't exist." << std::endl;
		return false;
	}
	getline(myfile, line);
	while (line != "")
	{
		tokenizer tok(line, sep);
		tokenizer::iterator beg = tok.begin();
		beg++; // skip "Node"
		std::string name = beg->c_str(); // read the name of the node
		auto iter = vNameToV.find(name);
		if (iter == vNameToV.end())
		{
			std::cerr << "non-existing runway node! " << line << std::endl;
			return false;
		}
		G[iter->second].type = vertex_type::RUNWAY;
		getline(myfile, line); // read the next line
	}
	myfile.close();

	eliminateIntermidiateNodes(); // eliminate intermidiate nodes	
	//getGraphInfo();
	// printNodes(); 	//print all nodes
	// saveGraph(outputFile); // output for visualization
	computeHeuristics();
	return true;
}

void AirportGraph::printNodes()
{
	std::cout << "ALL NODES" << std::endl;
	boost::graph_traits<searchGraph_t>::vertex_iterator vi, vi_end;
	for (boost::tie(vi, vi_end) = boost::vertices(G); vi != vi_end; ++vi)
	{
		int in_degree = boost::in_degree(*vi, G);
		int out_degree = boost::out_degree(*vi, G);
		if (G[*vi].type == vertex_type::SPOT)
		{
			std::cout << "An spot node ";
		}
		else if (G[*vi].type == vertex_type::RUNWAY)
		{
			std::cout << "An runway node ";
		}
		else if (in_degree == 0 && out_degree == 0)
		{
			continue;
		}
		else if (out_degree == 0)
		{
			std::cout << "A fake runway node ";
		}
		else if (G[*vi].type == vertex_type::GATE)
		{
			std::cout << "A Gate node ";
		}
		else if (in_degree == 1 && out_degree == 1)
		{
			std::cout << "An intermidiate node ";
		}
		else if (in_degree > 1 || out_degree > 1)
		{
			std::cout << "An intersection node ";
		}
		std::cout << G[*vi].name <<
			std::setprecision(8) <<
			"(" << G[*vi].pos.first << "," << G[*vi].pos.second <<
			") with in-degree " << in_degree <<
			" and out-degree " << out_degree << std::endl;
	}
}

void AirportGraph::eliminateIntermidiateNodes()
{
	// classify nodes
	boost::graph_traits<searchGraph_t>::vertex_iterator vi, vi_end;
	for (boost::tie(vi, vi_end) = boost::vertices(G); vi != vi_end; ++vi)
	{
		int in_degree = boost::in_degree(*vi, G);
		int out_degree = boost::out_degree(*vi, G);
		if (G[*vi].type == vertex_type::SPOT || G[*vi].type == vertex_type::RUNWAY)
		{
			continue;
		}
		else if (in_degree == 1 && out_degree == 1) // an intermediate node
		{
			auto from = boost::in_edges(*vi, G).first;
			auto to = boost::out_edges(*vi, G).first;

			// combine the two edges to a new edge
			double distance = G[*from].length + G[*to].length;
			vertex_t vFrom = boost::source(*from, G);
			vertex_t vTo = boost::target(*to, G);
			auto e = boost::add_edge(vFrom, vTo, G);
			std::string name = G[vFrom].name + "->" + G[vTo].name;
			G[e.first].name = name;
			G[e.first].length = distance;
			for (auto p : G[*from].points)
				G[e.first].points.push_back(p);
			G[e.first].points.push_back(make_pair(G[*vi].pos, G[*from].length));
			for (auto p : G[*to].points)
				G[e.first].points.push_back(p);

			// delete the two edges
			boost::remove_edge(*from, G);
			boost::remove_edge(*to, G);

			//delete the node
			boost::remove_vertex(*vi, G);
			--vi;
			--vi_end;
		}
		else if (in_degree == 0 && out_degree == 0) // an isolated node
		{
			boost::remove_vertex(*vi, G);
			--vi;
			--vi_end;
		}
		else if (in_degree == 0)
		{
			G[*vi].type = vertex_type::GATE;
		}
		/*else if (out_degree == 0)
		{
		G[*vi].type = vertex_type::RUNWAY;
		runways.push_back(*vi);
		}*/
		else //if (in_degree > 1 || out_degree > 1)
		{
			G[*vi].type = vertex_type::INTERSECTION;
		}
	}

	//refine the vNameToV
	vNameToV.clear();
	vPosToV.clear();
	eNameToE.clear();
	for (boost::tie(vi, vi_end) = boost::vertices(G); vi != vi_end; ++vi)
	{
		vNameToV[G[*vi].name] = *vi;
		switch (G[*vi].type)
		{
		case vertex_type::RUNWAY:
			runways.push_back(*vi);
			break;
		case vertex_type::GATE:
			gates.push_back(*vi);
			break;
		case vertex_type::INTERSECTION:
			intersections.push_back(*vi);
			break;
		case vertex_type::SPOT:
			spots.push_back(*vi);
			break;
		default:
			break;
		}
	}
	auto es = edges(G);
	for (auto eit = es.first; eit != es.second; ++eit) {
		eNameToE[G[*eit].name] = *eit;
	}

}

void AirportGraph::saveGraph(const std::string& outputFile) // for visualization
{
	std::ofstream output;
	output.open(outputFile + "-gates.txt");
	// output gate nodes
	for (auto v : gates)
	{
		output << G[v].name << "," << std::setprecision(8) << G[v].pos.first << "," << G[v].pos.second << std::endl;
	}
	output.close();
	// output spot nodes
	output.open(outputFile + "-spots.txt");
	for (auto v : spots)
	{
		output << G[v].name << "," << G[v].pos.first << "," << G[v].pos.second << std::endl;
	}
	output.close();
	// output runway nodes
	output.open(outputFile + "-runways.txt");
	for (auto v : runways)
	{
		output << G[v].name << "," << G[v].pos.first << "," << G[v].pos.second << std::endl;
	}
	output.close();
	// output intersection nodes
	output.open(outputFile + "-intersections.txt");
	for (auto v : intersections)
	{
		output << G[v].name << "," << G[v].pos.first << "," << G[v].pos.second << std::endl;
	}
	output.close();
	// output intermidiate nodes
	output.open(outputFile + "-intermediates.txt");
	for (auto v : intermediates)
	{
		output << G[v].name << "," << G[v].pos.first << "," << G[v].pos.second << std::endl;
	}
	output.close();
	// output links
	output.open(outputFile + "-links.txt");
	boost::graph_traits<searchGraph_t>::edge_iterator ei, ei_end;
	for (boost::tie(ei, ei_end) = boost::edges(G); ei != ei_end; ++ei)
	{
		output << G[ei->m_source].name << "," << G[ei->m_source].pos.first << "," << G[ei->m_source].pos.second << "," <<
			G[ei->m_target].name << "," << G[ei->m_target].pos.first << "," << G[ei->m_target].pos.second << "," <<
			G[*ei].length << std::endl;
	}
	output.close();
}

void AirportGraph::computeHeuristics()
{
	// generate a heap that can save nodes (and a open_handle)
	boost::heap::fibonacci_heap< Node*, boost::heap::compare<Node::compare_node> > heap;
	boost::heap::fibonacci_heap< Node*, boost::heap::compare<Node::compare_node> >::handle_type open_handle;
	// generate hash_map (key is a node pointer, data is a node handler,
	//                    NodeHasher is the hash function to be used,
	//                    eqnode is used to break ties when hash values are equal)
	google::dense_hash_map<Node*, boost::heap::fibonacci_heap<Node*, boost::heap::compare<Node::compare_node> >::handle_type, Node::NodeHasher, Node::eqnode> nodes;
	nodes.set_empty_key(NULL);
	google::dense_hash_map<Node*, boost::heap::fibonacci_heap<Node*, boost::heap::compare<Node::compare_node> >::handle_type, Node::NodeHasher, Node::eqnode>::iterator it; // will be used for find()

	for (unsigned int i = 0; i < runways.size(); i++)
	{
		Node* root = new Node(runways[i], 0, 0, NULL);
		root->open_handle = heap.push(root);  // add root to heap
		nodes[root] = root->open_handle;       // add root to hash_table (nodes)
		while (!heap.empty()) {
			Node* curr = heap.top(); heap.pop();
			// cout << endl << "CURRENT node: " << curr << endl;
			auto neighbours = boost::in_edges(curr->state.loc, G);
			for (auto e : make_iterator_range(neighbours))
			{
				double next_g_val = curr->g_val + G[e].length;
				Node* next = new Node(e.m_source, next_g_val, 0, NULL);
				it = nodes.find(next);
				if (it == nodes.end()) {  // add the newly generated node to heap and hash table
					next->open_handle = heap.push(next);
					nodes[next] = next->open_handle;
				}
				else {  // update existing node's g_val if needed (only in the heap)
					delete(next);  // not needed anymore -- we already generated it before
					Node* existing_next = (*it).first;
					open_handle = (*it).second;
					if (existing_next->g_val > next_g_val) {
						existing_next->g_val = next_g_val;
						heap.update(open_handle);
					}
				}
			}
		}
		// iterate over all nodes and populate the num_of_collisionss
		heuristics[runways[i]].resize(boost::num_vertices(G), DBL_MAX);
		for (it = nodes.begin(); it != nodes.end(); it++) {
			Node* s = (*it).first;
			heuristics[runways[i]][s->state.loc] = s->g_val;
		}
		nodes.clear();
		heap.clear();
	}

}

position_t AirportGraph::getPosition(const edge_t e, double distance) // distance is the distance from current location to the start endpoint of the edge e.
{
	position_t from = G[e.m_source].pos;
	double remainingDistance = distance;

	list<pair<position_t, double>>::const_iterator pt = G[e].points.begin();
	while (pt != G[e].points.end() && remainingDistance > pt->second)
	{
		from = pt->first;
		remainingDistance -= pt->second;
		pt++;
	}

	position_t to;
	double ratio;
	if (pt == G[e].points.end())
	{
		to = G[e.m_target].pos;
		ratio = remainingDistance / (G[e].length - (distance - remainingDistance));
	}
	else
	{
		to = pt->first;
		ratio = remainingDistance / pt->second;
	}

	position_t rst;
	rst.first = (1 - ratio) * from.first + ratio * to.first;
	rst.second = (1 - ratio) * from.second + ratio * to.second;

	return rst;
}

void AirportGraph::getGraphInfo()
{
	std::cout << "|V| = " << num_vertices(G) << " ; |E| = " << num_edges(G) << std::endl;
	std::cout << "#Gates = " << gates.size()
		<< " ; #Spots = " << spots.size()
		<< " ; #Intersections = " << intersections.size()
		<< " ; #Runways = " << runways.size() << std::endl;
}

AirportGraph::AirportGraph()
{
}

AirportGraph::~AirportGraph()
{
}
