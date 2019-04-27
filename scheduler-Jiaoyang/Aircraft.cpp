#include "Aircraft.h"
#include <cmath>

double Aircraft::get_velocity(){
  // TODO Car following model joins here
  double distance = 1000;

  if (command == STOP_COMMAND){
    cout << this -> id << "stop" << endl;
    return 0;
  }


  if (prev_aircraft == nullptr){
    return model.v_max;
  }


  if (prev_aircraft->current_edge_name()
      == this-> current_edge_name()){
    distance = prev_aircraft->pos.second - pos.second;
  }else{
    // what if there are more edges apart..
    distance = prev_aircraft->pos.second - pos.second +
      edge_path[pos.first].length;
  }




  double c, l, m;
  if(distance > ideal_distance){
    // c = 1.1, l = 0.1, m = 0.2;
    c = 10;
  }else{
    // c = -1.1, l = 1.2, m = 0.7;
    c = - 20;
  }

  double acc = c;

  return velocity + acc;
}

void Aircraft::move(){
  passed_check_point.clear();
  int edge_idx = pos.first;

  // velocity * timestep
  double v = get_velocity();
  if (v > model.v_max){
    v = model.v_max;
  }
  if (v < 0){
    v = 0;
  }
  velocity = v;

  double l = pos.second + velocity / (double)tick_per_time_unit;
  while (l > edge_path[edge_idx].length &&
         edge_idx + 1 < edge_path.size()){
    l = l - edge_path[edge_idx].length;
    passed_check_point.push_back(edge_path[edge_idx].name);
    edge_idx += 1;
  }
  if (l > edge_path[edge_idx].length){
    passed_check_point.push_back(edge_path[edge_idx].name);
    // arrive at runway
    ready_for_runway = true;
  }
  pos = {edge_idx, l};
  command = NO_COMMAND;
}

string Aircraft::position_str(){
  return edge_path[pos.first].name + string(" - ")
    + to_string(pos.second);
}

void Aircraft::simulation_init(){
  generate_actual_appear_time();
  ready_for_runway = false;
}

void Aircraft::simulation_begin(){
  ready_for_runway = false;
  pos = {0, 0};
}

void Aircraft::generate_actual_appear_time(){
  actual_appear_time = path[0].time[0]; // TODO add disturb
}

string Aircraft::current_edge_name(){
  return  edge_path[pos.first].name;
}


void Aircraft::send_command(int given_command){
  command = given_command;
}
