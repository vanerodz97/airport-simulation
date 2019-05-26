import os

input_dir = "./input-files/"
airport_simul_dir = "../"
airport_name = "sfo-all-terminals"
instance = input_dir + f"random_100.yaml"
config = input_dir + f"config.yaml"

algs = ["BASE", "FLFS"]

for alg in algs:

    output_dir = airport_simul_dir + f"output/{alg.lower()}_sample"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    with open(output_dir + "/airport.txt", "w") as f:
        f.write(airport_name)

    command = f"./airport --depart=./input-files/links.txt --output=./input-files/output --node=./input-files/nodes.txt --runway=./input-files/runway_nodes.txt --link=./input-files/links.txt --spot=./input-files/spot_nodes.txt -i {instance} -m ./input-files/aircraft-model.yaml -s {alg} -k 100 --interval_min=0 --interval_max=10 -c {config}"
    os.system(command)

    os.system("python ./translate_to_json.py")
    
    os.system(f"cp states.json {output_dir}/states.json")
