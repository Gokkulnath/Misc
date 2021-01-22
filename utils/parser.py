import json 


def read_config(config_path):
    with open(config_path,'r') as f:
        conf =json.load(f)
    return conf


print(read_config('temp.json'))