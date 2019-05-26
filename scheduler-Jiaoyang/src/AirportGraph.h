#pragma once
#include "Node.h"


enum vertex_type { GATE, SPOT, INTERSECTION, RUNWAY, INTERMEDIATE };




struct Vertex
{
	std::string name;
	position_t pos;
	vertex_type type;
};

struct Edge
{
	std::string name;
	double length;
	list<pair<position_t, double>> points; // <pos of the point, distance to the previous point> 
};

typedef boost::adjacency_list<boost::vecS, boost::vecS, boost::bidirectionalS, Vertex, Edge> searchGraph_t;

class AirportGraph
{
public:
	searchGraph_t G;
	std::unordered_map<std::string, vertex_t> vNameToV;
	std::unordered_map<position_t, vertex_t, pair_hash> vPosToV;
	std::unordered_map<std::string, edge_t> eNameToE;
	vector<vertex_t> gates;
	vector<vertex_t> spots;
	vector<vertex_t> runways;
	vector<vertex_t> intersections;
	vector<vertex_t> intermediates;
	std::unordered_map<vertex_t, vector<double >> heuristics; //shortest distances from runways to all other vertices
	bool loadGraph(const std::string& fileName);
	bool GenerateAbstractGraph(const std::string& nodeFile, const std::string& linkFile,
		const std::string& spotFile, const std::string& runwayFile, const std::string& departFile,
		const std::string& graphFile);

	void computeHeuristics();

	void getGraphInfo();
	void printNodes();
	void saveGraph(const std::string& outputFile); // for visualization

	position_t getPosition(const edge_t e, double distance);

	AirportGraph();
	~AirportGraph();

private:
	void eliminateIntermidiateNodes();
};

