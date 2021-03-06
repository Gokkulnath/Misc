# System Imports
from __future__ import print_function
import argparse
import os
import math
from math import log10

# Vis
import matplotlib.pyplot as plt
plt.switch_backend('agg')

# Torch
import torch
import torchvision
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader
import torch.backends.cudnn as cudnn
import torchvision.transforms as transforms
import numpy as np

# Custom 
#from models import ResnetGenerator, weights_init
# from material.models.generators import ResnetGenerator, weights_init

# Custom Code for Generator
import json 
from models.resnet import Generator
from utils.misc import dict2clsattr

# Dataset Setup
from data import CustomDataset,ImageFolder

def read_config(config_path):
    with open(config_path,'r') as f:
        conf =json.load(f)
    return conf

# def weights_init(m, act_type='relu'):
#     classname = m.__class__.__name__
#     if classname.find('Conv') != -1:
#         if act_type == 'selu':
#             n = float(m.in_channels * m.kernel_size[0] * m.kernel_size[1])
#             m.weight.data.normal_(0.0, 1.0 / math.sqrt(n))
#         else:
#             m.weight.data.normal_(0.0, 0.02)        
#         if hasattr(m.bias, 'data'):
#             m.bias.data.fill_(0)
#     elif classname.find('BatchNorm2d') != -1:
#         m.weight.data.normal_(1.0, 0.02)
#         m.bias.data.fill_(0)

train_config = read_config('temp.json')
model_config = {}

gan_conf = dict2clsattr(train_config,model_config)




# Training settings
parser = argparse.ArgumentParser(description='generative adversarial perturbations')
parser.add_argument('--imagenetTrain', type=str, default='/train', help='ImageNet train root')
parser.add_argument('--imagenetVal', type=str, default='/valid', help='ImageNet val root')
parser.add_argument('--batchSize', type=int, default=30, help='training batch size')
parser.add_argument('--testBatchSize', type=int, default=16, help='testing batch size')
parser.add_argument('--nEpochs', type=int, default=10, help='number of epochs to train for')
parser.add_argument('--ngf', type=int, default=64, help='generator filters in first conv layer')
parser.add_argument('--optimizer', type=str, default='adam', help='optimizer: "adam" or "sgd"')
parser.add_argument('--lr', type=float, default=0.0002, help='Learning Rate. Default=0.002')
parser.add_argument('--beta1', type=float, default=0.5, help='beta1 for adam. default=0.5')
parser.add_argument('--threads', type=int, default=4, help='number of threads for data loader to use')
parser.add_argument('--seed', type=int, default=123, help='random seed to use. Default=123')
parser.add_argument('--MaxIter', type=int, default=50, help='Iterations in each Epoch')
parser.add_argument('--MaxIterTest', type=int, default=160, help='Iterations in each Epoch')
parser.add_argument('--mag_in', type=float, default=10.0, help='l_inf magnitude of perturbation')
parser.add_argument('--expname', type=str, default='tempname', help='experiment name, output folder')
parser.add_argument('--checkpoint', type=str, default='', help='path to starting checkpoint')
parser.add_argument('--foolmodel', type=str, default='incv3', help='model to fool: "incv3", "vgg16", or "vgg19"')
parser.add_argument('--mode', type=str, default='train', help='mode: "train" or "test"')
parser.add_argument('--perturbation_type', type=str, help='"universal" or "imdep" (image dependent)')
parser.add_argument('--target', type=int, default=-1, help='target class: -1 if untargeted, 0..999 if targeted')
parser.add_argument('--gpu_ids', help='gpu ids: e.g. 0 or 0,1 or 1,2.', type=str, default='0')
parser.add_argument('--path_to_U_noise', type=str, default='', help='path to U_input_noise.txt (only needed for universal)')
parser.add_argument('--explicit_U', type=str, default='', help='Path to a universal perturbation to use')
opt = parser.parse_args()

print(opt)

#if not torch.cuda.is_available():
#    raise Exception("No GPU found.")

# train loss history
train_loss_history = []
test_loss_history = []
test_acc_history = []
test_fooling_history = []
best_fooling = 0
itr_accum = 0

# make directories
if not os.path.exists(opt.expname):
    os.mkdir(opt.expname)

if opt.perturbation_type == 'universal':
    if not os.path.exists(opt.expname + '/U_out'):
        os.mkdir(opt.expname + '/U_out')

torch.autograd.set_detect_anomaly(True) # For Debugging ?
# Setting Seed for reprodicility 
cudnn.benchmark = True
torch.cuda.manual_seed(opt.seed)

MaxIter = opt.MaxIter
MaxIterTest = opt.MaxIterTest
gpulist = [int(i) for i in opt.gpu_ids.split(',')]
n_gpu = len(gpulist)
print('Running with n_gpu: ', n_gpu)

# define normalization means and stddevs
model_dimension = 299 if opt.foolmodel == 'incv3' else 256
center_crop = 299 if opt.foolmodel == 'incv3' else 224 # cropped Image Dimensions

mean_arr = [0.485, 0.456, 0.406]
stddev_arr = [0.229, 0.224, 0.225]
normalize = transforms.Normalize(mean=mean_arr,
                                 std=stddev_arr)

data_transform = transforms.Compose([
    transforms.Resize(model_dimension),
    transforms.CenterCrop(center_crop),
    transforms.ToTensor(),
    normalize,
])

print('===> Loading datasets')

if opt.mode == 'train':
    # train_set = torchvision.datasets.ImageFolder(root = opt.imagenetTrain, transform = data_transform)
    train_set =  ImageFolder(root='ILSVRC/train',transform=data_transform) # ChangedHere
    training_data_loader = DataLoader(dataset=train_set, num_workers=opt.threads, batch_size=opt.batchSize, shuffle=True)

# test_set = torchvision.datasets.ImageFolder(root = opt.imagenetVal, transform = data_transform)
test_set = CustomDataset(subset='valid',root_dir='ILSVRC',transform=data_transform) #ChangedHere
testing_data_loader = DataLoader(dataset=test_set, num_workers=opt.threads, batch_size=opt.testBatchSize, shuffle=True)

print("Dataset Validation Done")
if opt.foolmodel == 'incv3':
    pretrained_clf = torchvision.models.inception_v3(pretrained=True)
elif opt.foolmodel == 'vgg16':
    pretrained_clf = torchvision.models.vgg16(pretrained=True)
elif opt.foolmodel == 'vgg19':
    pretrained_clf = torchvision.models.vgg19(pretrained=True)

# device = torch.device((gpulist[0])) # Might need to Fix for Multi GPU training
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

pretrained_clf = pretrained_clf.to(device)

pretrained_clf.eval()
# pretrained_clf.volatile = True  # TODO : Why use Volatile ? Save Backprop Gradients ?
# Volatile Deprecated

# magnitude
mag_in = 10 # opt.mag_in # Linf Magnitude for perturbations aka Max allowed Perturbation in a pixel

print('===> Building model')

if not opt.explicit_U:
    # will use model paralellism if more than one gpu specified
    netG = Generator(gan_conf.z_dim, gan_conf.shared_dim, gan_conf.img_size, gan_conf.g_conv_dim, gan_conf.g_spectral_norm, gan_conf.attention,
                        gan_conf.attention_after_nth_gen_block, gan_conf.activation_fn, gan_conf.conditional_strategy, gan_conf.num_classes,
                        gan_conf.g_init, gan_conf.G_depth, mixed_precision=False)
    print("Generator Arch: ")
    print(netG)
    print("<","="*8,">")
    # resume from checkpoint if specified
    if opt.checkpoint:
        if os.path.isfile(opt.checkpoint):
            print("=> loading checkpoint '{}'".format(opt.checkpoint))
            netG.load_state_dict(torch.load(opt.checkpoint, map_location=lambda storage, loc: storage))
            print("=> loaded checkpoint '{}'".format(opt.checkpoint))
        else:
            print("=> no checkpoint found at '{}'".format(opt.checkpoint))
            # netG.apply(weights_init)
    # else:
    #     netG.apply(weights_init)

    # setup optimizer
    if opt.optimizer == 'adam':
        optimizerG = optim.Adam(netG.parameters(), lr=opt.lr, betas=(opt.beta1, 0.999))
    elif opt.optimizer == 'sgd':
        optimizerG = optim.SGD(netG.parameters(), lr=opt.lr, momentum=0.9)

    criterion_pre = nn.CrossEntropyLoss().to(device)
    
    # fixed noise for universal perturbation
    if opt.perturbation_type == 'universal':
        # noise_data = np.random.uniform(0, 255, center_crop * center_crop * 3) # 1d Array
        noise_data = np.random.uniform(0, 255, 128) # 1d Array
        if opt.checkpoint:
            if opt.path_to_U_noise:
                noise_data = np.loadtxt(opt.path_to_U_noise)
                np.savetxt(opt.expname + '/U_input_noise.txt', noise_data)
            else:
                noise_data = np.loadtxt(opt.expname + '/U_input_noise.txt')
        else:
            np.savetxt(opt.expname + '/U_input_noise.txt', noise_data)
        # im_noise = np.reshape(noise_data, (3, center_crop, center_crop)) # Reshape to C X H X W  array
        noise_data = noise_data[np.newaxis, :]
        noise_data_tr = np.tile(noise_data, (opt.batchSize, 1))
        noise_tr = torch.from_numpy(noise_data_tr).type(torch.FloatTensor).to(device)

        noise_data_te = np.tile(noise_data, (opt.testBatchSize, 1))
        noise_te = torch.from_numpy(noise_data_te).type(torch.FloatTensor).to(device)

def train(epoch):
    netG.train()
    global itr_accum
    global optimizerG

    for itr, (image, _) in enumerate(training_data_loader, 1):
        if itr > MaxIter:
            break

        if opt.target == -1:
            # least likely class in nontargeted case
            pretrained_label_float = pretrained_clf(image.to(device))
            _, target_label = torch.min(pretrained_label_float, 1)
        else:
            # targeted case
            target_label = torch.LongTensor(image.size(0))
            target_label.fill_(opt.target)
            target_label = target_label.to(device)

        itr_accum += 1
        if opt.optimizer == 'sgd':
            lr_mult = (itr_accum // 1000) + 1
            optimizerG = optim.SGD(netG.parameters(), lr=opt.lr/lr_mult, momentum=0.9)

        image = image.to(device)

        ## generate per image perturbation from fixed noise
        if opt.perturbation_type == 'universal':
            delta_im = netG(noise_tr,target_label)
        else:
            delta_im = netG(image)

        delta_im = normalize_and_scale(delta_im, 'train')
        print(delta_im.shape)
        import pdb 
        pdb.set_trace()
        netG.zero_grad()

        recons = torch.add(image.to(device), delta_im.to(device))

        # do clamping per channel
        for cii in range(3):
            recons[:,cii,:,:] = recons[:,cii,:,:].clone().clamp(image[:,cii,:,:].min(), image[:,cii,:,:].max())

        output_pretrained = pretrained_clf(recons.to(device))

        # attempt to get closer to least likely class, or target
        loss = torch.log(criterion_pre(output_pretrained, target_label))

        loss.backward()
        optimizerG.step()

        train_loss_history.append(loss.item())
        print("===> Epoch[{}]({}/{}) loss: {:.4f}".format(epoch, itr, len(training_data_loader), loss.item()))


def test():
    if not opt.explicit_U:
        netG.eval()
    correct_recon = 0
    correct_orig = 0
    fooled = 0
    total = 0

    if opt.perturbation_type == 'universal':
        if opt.explicit_U:
            U_loaded = torch.load(opt.explicit_U)
            U_loaded = U_loaded.expand(opt.testBatchSize, U_loaded.size(1), U_loaded.size(2), U_loaded.size(3))
            delta_im = normalize_and_scale(U_loaded, 'test')
        else:
            delta_im = netG(noise_te)
            delta_im = normalize_and_scale(delta_im, 'test')

    for itr, (image, class_label) in enumerate(testing_data_loader):
        if itr > MaxIterTest:
            break

        image = image.to(device)

        if opt.perturbation_type == 'imdep':
            delta_im = netG(image)
            delta_im = normalize_and_scale(delta_im, 'test')

        recons = torch.add(image.to(device), delta_im[0:image.size(0)].to(device))

        # do clamping per channel
        for cii in range(3):
            recons[:,cii,:,:] = recons[:,cii,:,:].clone().clamp(image[:,cii,:,:].min(), image[:,cii,:,:].max())

        outputs_recon = pretrained_clf(recons.to(device))
        outputs_orig = pretrained_clf(image.to(device))
        _, predicted_recon = torch.max(outputs_recon, 1)
        _, predicted_orig = torch.max(outputs_orig, 1)
        total += image.size(0)
        correct_recon += (predicted_recon == class_label.to(device)).sum()
        correct_orig += (predicted_orig == class_label.to(device)).sum()

        if opt.target == -1:
            fooled += (predicted_recon != predicted_orig).sum()
        else:
            fooled += (predicted_recon == opt.target).sum()

        if itr % 50 == 1:
            print('Images evaluated:', (itr*opt.testBatchSize))
            # undo normalize image color channels
            delta_im_temp = torch.zeros(delta_im.size())
            for c2 in range(3):
                recons[:,c2,:,:] = (recons[:,c2,:,:] * stddev_arr[c2]) + mean_arr[c2]
                image[:,c2,:,:] = (image[:,c2,:,:] * stddev_arr[c2]) + mean_arr[c2]
                delta_im_temp[:,c2,:,:] = (delta_im[:,c2,:,:] * stddev_arr[c2]) + mean_arr[c2]
            if not os.path.exists(opt.expname):
                os.mkdir(opt.expname)

            post_l_inf = (recons - image[0:recons.size(0)]).abs().max() * 255.0
            print("Specified l_inf:", mag_in, "| maximum l_inf of generated perturbations: %.2f" % (post_l_inf.item()))

            torchvision.utils.save_image(recons, opt.expname+'/reconstructed_{}.png'.format(itr))
            torchvision.utils.save_image(image, opt.expname+'/original_{}.png'.format(itr))
            torchvision.utils.save_image(delta_im_temp, opt.expname+'/delta_im_{}.png'.format(itr))
            print('Saved images.')

    test_acc_history.append((100.0 * correct_recon / total))
    test_fooling_history.append((100.0 * fooled / total))
    print('Accuracy of the pretrained network on reconstructed images: %.2f%%' % (100.0 * float(correct_recon) / float(total)))
    print('Accuracy of the pretrained network on original images: %.2f%%' % (100.0 * float(correct_orig) / float(total)))
    if opt.target == -1:
        print('Fooling ratio: %.2f%%' % (100.0 * float(fooled) / float(total)))
    else:
        print('Top-1 Target Accuracy: %.2f%%' % (100.0 * float(fooled) / float(total)))

def normalize_and_scale(delta_im, mode='train'):
    if opt.foolmodel == 'incv3':
        delta_im = nn.ConstantPad2d((0,-1,-1,0),0)(delta_im) # crop slightly to match inception

    delta_im = delta_im + 1 # now 0..2
    delta_im = delta_im * 0.5 # now 0..1

    # normalize image color channels
    for c in range(3):
        delta_im[:,c,:,:] = (delta_im[:,c,:,:].clone() - mean_arr[c]) / stddev_arr[c]

    # threshold each channel of each image in deltaIm according to inf norm
    # do on a per image basis as the inf norm of each image could be different
    bs = opt.batchSize if (mode == 'train') else opt.testBatchSize
    for i in range(bs):
        # do per channel l_inf normalization
        for ci in range(3):
            l_inf_channel = delta_im[i,ci,:,:].detach().abs().max()
            mag_in_scaled_c = mag_in/(255.0*stddev_arr[ci])
            gpu_id = gpulist[1] if n_gpu > 1 else gpulist[0]
            delta_im[i,ci,:,:] = delta_im[i,ci,:,:].clone() * np.minimum(1.0, mag_in_scaled_c / l_inf_channel.cpu().numpy())

    return delta_im


def checkpoint_dict(epoch):
    netG.eval()
    global best_fooling
    if not os.path.exists(opt.expname):
        os.mkdir(opt.expname)

    task_label = "foolrat" if opt.target == -1 else "top1target"

    net_g_model_out_path = opt.expname + "/netG_model_epoch_{}_".format(epoch) + task_label + "_{}.pth".format(test_fooling_history[epoch-1])
    if opt.perturbation_type == 'universal':
        u_out_path = opt.expname + "/U_out/U_epoch_{}_".format(epoch) + task_label + "_{}.pth".format(test_fooling_history[epoch-1])
    if test_fooling_history[epoch-1] > best_fooling:
        best_fooling = test_fooling_history[epoch-1]
        torch.save(netG.state_dict(), net_g_model_out_path)
        if opt.perturbation_type == 'universal':
            torch.save(netG(noise_te[0:1]), u_out_path)
        print("Checkpoint saved to {}".format(net_g_model_out_path))
    else:
        print("No improvement:", test_fooling_history[epoch-1], "Best:", best_fooling)


def print_history():
    # plot history for training loss
    if opt.mode == 'train':
        plt.plot(train_loss_history)
        plt.title('Model Training Loss')
        plt.ylabel('Loss')
        plt.xlabel('Iteration')
        plt.legend(['Training Loss'], loc='upper right')
        plt.savefig(opt.expname+'/reconstructed_loss_'+opt.mode+'.png')
        plt.clf()

    # plot history for classification testing accuracy and fooling ratio
    plt.plot(test_acc_history)
    plt.title('Model Testing Accuracy')
    plt.ylabel('Accuracy')
    plt.xlabel('Epoch')
    plt.legend(['Testing Classification Accuracy'], loc='upper right')
    plt.savefig(opt.expname+'/reconstructed_acc_'+opt.mode+'.png')
    plt.clf()

    plt.plot(test_fooling_history)
    plt.title('Model Testing Fooling Ratio')
    plt.ylabel('Fooling Ratio')
    plt.xlabel('Epoch')
    plt.legend(['Testing Fooling Ratio'], loc='upper right')
    plt.savefig(opt.expname+'/reconstructed_foolrat_'+opt.mode+'.png')
    print("Saved plots.")

if opt.mode == 'train':
    for epoch in range(1, opt.nEpochs + 1):
        train(epoch)
        print('Testing....')
        test()
        checkpoint_dict(epoch)
    print_history()
elif opt.mode == 'test':
    print('Testing...')
    test()
    print_history()
