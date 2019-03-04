#include "stdafx.h"
#include "Node.h"


Node::Node()
{
}


Node::~Node()
{
}

std::ostream& operator<<(std::ostream& os, const Node& n) 
{
	os << "LOC=" << n.state.loc << " ; TIME=";
	for (unsigned int i = 0; i < n.state.time.size(); i++)
	{
		os << n.state.time[i] << "(" << n.state.prob[i] << "), ";
	}
	return os;
}