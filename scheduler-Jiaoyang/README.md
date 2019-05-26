# Dependency

Threr external libiaries are needed:
 - boost: https://www.boost.org/
 - sparsemap: https://github.com/sparsehash/sparsehash
 - yamp-cpp: https://github.com/jbeder/yaml-cpp

# Scheduler

Allowed options:
  --help                                produce help message
  
  -g [ --graph ] arg                    input graph file
  
  -m [ --model ] arg                    input aircraft model file
  
  -i [ --instance ] arg                 input iternary file
  
  -c [ --config ] arg (=../config.yaml) input config file
  
  -o [ --output ] arg                   output schedule file
  
  -s [ --solver ] arg                   solvers (BASE, FCFS, FLFS, ALL)
  
  -k [ --agentNum ] arg (=0)            number of agents
  
  --interval_min arg (=0)               interval min
  
  --interval_max arg (=0)               interval max
  
  --node arg                            node model
  
  --link arg                            link model
  
  --spot arg                            spot model
  
  --runway arg                          runway model
  
# Visulization
Output of scheduler could be visulized with batch mode of airport simulation tool. Run translate_to_json.py to transfer output of shceduler to JSON format. Use states.json for batch mode visulizatio

Run exp_vis.py will automatically create and setup two sample visualizations. Once you run exp_vis.py, you could run visualization server and you will see base_sample and flfs_sample.
