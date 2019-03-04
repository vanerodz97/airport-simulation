#pragma once

#include "Node.h"



enum vertex_type { GATE, SPOT, INTERSECTION, RUNWAY};




struct Vertex
{
	std::string name;
	position_t pos;
	vertex_type type;
};

struct Edge
{
	std::string name;
	float length;
};

typedef boost::adjacency_list<boost::vecS, boost::vecS, boost::bidirectionalS, Vertex, Edge> searchGraph_t;

class AirportGraph
{
public:
	searchGraph_t G;
	std::unordered_map<std::string, vertex_t> vNameToV;
	std::unordered_map<std::string, edge_t> eNameToE;
	vector<vertex_t> gates;
	vector<vertex_t> spots;
	vector<vertex_t> runways;
	vector<vertex_t> intersections;
	vector < vector<double >> heuristics; //shortest distances from runways to all other vertices
	bool loadGraph(const std::string& fileName);
	void computeHeuristics();

	void getGraphInfo();
	AirportGraph();
	~AirportGraph();
};

