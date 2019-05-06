#include "Aircraft.h"
#include <cmath>

double Aircraft::get_velocity(){
  // TODO Car following model joins here
  double distance = 1000;

  if (command == STOP_COMMAND){
    cout << this -> id << "stop" << endl;
    acceleration = - velocity;
    return 0;
  }


  if (prev_aircraft == nullptr){
    acceleration = model.a_max;
    return velocity + acceleration;
  }


  if (prev_aircraft->current_edge_name()
      == this-> current_edge_name()){
    distance = prev_aircraft->pos.second - pos.second;
  }else{
    // what if there are more edges apart..
    distance = prev_aircraft->pos.second - pos.second +
      edge_path[pos.first].length;
  }


  if (distance < 150){
    // hard brake
    acceleration = - velocity;
    return 0;
  }

  if (distance > ideal_distance){
    // Not need to care about prev aircraft
    acceleration = model.a_max;
    return velocity + acceleration;
  }


  if (prev_aircraft -> acceleration < 0){
    acceleration = -model.a_brake;
    return velocity + acceleration;
  }

  // Accelerating 
  double v_other = prev_aircraft->velocity;
  double a_brake_other = prev_aircraft ->model.a_brake;



  double h = distance + (v_other * v_other / (2 * a_brake_other)) - 100;

  double T = 1/tick_per_time_unit;

  double a_eq = T * T;
  double b_eq = model.a_brake * T * T + 2 * velocity * T;
  double c_eq = velocity * velocity + 2 * model.a_brake * (velocity * T - h);

  acceleration =  min(model.a_max, (-b_eq + sqrt(b_eq * b_eq - 4 * a_eq * c_eq))/ (2 * a_eq));
  
  return velocity + acceleration;
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
