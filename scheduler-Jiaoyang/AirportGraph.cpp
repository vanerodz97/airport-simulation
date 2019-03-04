#include "stdafx.h"
#include "AirportGraph.h"
#include <fstream>
#include "yaml-cpp/yaml.h"

position_t nodeAsPos(const YAML::Node& node)
{
	return std::make_pair(node[0].as<float>(), node[1].as<float>());
}

float getDistance(const position_t& a, const position_t& b)
{
	return sqrt((a.first-b.first)*(a.first - b.first) + (a.second-b.second)*(a.second - b.second));
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
		for (const auto& node : edges) {
			std::string name = node["name"].as<std::string>();
			std::string fromName = node["from"].as<std::string>();
			auto fromIter = vNameToV.find(fromName);

			std::string toName = node["to"].as<std::string>();
			auto toIter = vNameToV.find(toName);
			if (fromIter == vNameToV.end()
				|| toIter == vNameToV.end()
				|| fromIter->second == toIter->second) {
				std::cerr << "invalid edge! " << node << std::endl;
				return false;
			}
			auto e = boost::add_edge(fromIter->second, toIter->second, G);
			G[e.first].name = name;
			G[e.first].length = node["length"].as<float>();  //getDistance(G[fromIter->second].pos, G[toIter->second].pos);

			eNameToE[name] = e.first;
		}
	}
	//getGraphInfo();
	//std::cout << "******Graph Loaded Successfully******" << std::endl << std::endl;
	computeHeuristics();
	return true;
}

void AirportGraph::computeHeuristics()
{
	heuristics.resize(boost::num_vertices(G));
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
