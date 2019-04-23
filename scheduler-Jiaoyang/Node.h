#pragma once
#include "stdafx.h"

using namespace std;

struct State
{
	vertex_t loc;
  edge_t* edge_from;
	vector<int> time;
	vector<double> prob;
	State():edge_from(nullptr){}
	State(int t, double p){time.push_back(t); prob.push_back(p);}
	void print(){ 
		std::cout << "loc = " << loc <<  " ; time = ";
		for (int i = 0; i < time.size(); i++)
		{
			std::cout << time[i] << " (" << prob[i] << "), ";
		}
		std::cout << std::endl;
	}
	double getExpectation()
	{
		double rst = 0;
		for (int i = 0; i < time.size(); i++)
		{
			rst += time[i] * prob[i];
		}
		return rst;
	}
	
};

class Node
{
public:
	State state;

	double g_val;
	double h_val;
	Node* parent;
	Node* move;
	int depth;
	bool in_openlist = false;

	///////////////////////////////////////////////////////////////////////////////
	// NOTE -- Normally, compare_node (lhs,rhs) suppose to return true if lhs<rhs.
	//         However, Heaps in STL and Boost are implemented as max-Heap.
	//         Hence, to achieve min-Head, we return true if lhs>rhs
	///////////////////////////////////////////////////////////////////////////////

	// the following is used to comapre nodes in the OPEN list
	struct compare_node {
		// returns true if n1 > n2 (note -- this gives us *min*-heap).
		bool operator()(const Node* n1, const Node* n2) const {
			if (n1->g_val + n1->h_val == n2->g_val + n2->h_val)
				return n1->g_val <= n2->g_val;  // break ties towards larger g_vals
			return n1->g_val + n1->h_val >= n2->g_val + n2->h_val;
		}
	};  // used by OPEN (heap) to compare nodes (top of the heap has min f-val, and then highest g-val)

	typedef boost::heap::fibonacci_heap< Node*, boost::heap::compare<Node::compare_node> >::handle_type open_handle_t;

	open_handle_t open_handle;

	// The following is used by googledensehash for checking whether two nodes are equal
	// we say that two nodes, s1 and s2, are equal if
	// both are non-NULL and agree on the id and timestep
	struct eqnode {
		bool operator()(const Node* s1, const Node* s2) const 
		{
			if(s1  == s2)
				return true;
			else if (s1 && s2 && s1->state.loc == s2->state.loc)
			{
				if (s1->state.time.size() != s2->state.time.size())
					return false;
				else if(s1->move != s2->move)
					return false;
				else if(s1->state.time.empty() && s2->state.time.empty())
					return true;
				else 
				{
					for (unsigned int i = 0; i < s1->state.time.size(); i++)
					{
						if(abs(s1->state.time[i] - s1->state.time[i]) > 0.001 || abs(s1->state.prob[i] - s1->state.prob[i]) > 0.001)
							return false;
					}
					return true;
				}
			}
			else
				return false;
		}
	};

	// The following is used by googledensehash for generating the hash value of a nodes
	struct NodeHasher {
		std::size_t operator()(const Node* n) const {
			return n->state.loc;
			// cout << "COMPUTE HASH: " << *n << " ; Hash=" << hash<int>()(n->id) << endl;
			// cout << "   Pointer Address: " << n << endl;
			//size_t loc_hash = std::hash<int>()(n->state.loc); 
			//size_t timestep_hash = std::hash<int>()(n->state.time[0]);
			//return loc_hash; //(loc_hash ^ (timestep_hash << 1));
		}
	};

	Node();
	Node(vertex_t loc, double g_value, double h_value, Node* parent, int depth = 0):
		g_val(g_value), h_val(h_value), parent(parent), depth(depth)
		{state.loc = loc; }
	~Node();

};

