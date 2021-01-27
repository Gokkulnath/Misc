import json 
from models.resnet import Generator
from utils.misc import dict2clsattr

def read_config(config_path):
    with open(config_path,'r') as f:
        conf =json.load(f)
    return conf

train_config = read_config('temp.json')

model_config = {}

gan_conf = dict2clsattr(train_config,model_config)

Gen = Generator(gan_conf.z_dim, gan_conf.shared_dim, gan_conf.img_size, gan_conf.g_conv_dim, gan_conf.g_spectral_norm, gan_conf.attention,
                        gan_conf.attention_after_nth_gen_block, gan_conf.activation_fn, gan_conf.conditional_strategy, gan_conf.num_classes,
                        gan_conf.g_init, gan_conf.G_depth, mixed_precision=False)

print(Gen)




