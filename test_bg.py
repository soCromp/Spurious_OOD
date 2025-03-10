import argparse
import os
import logging
from functools import partial

import numpy as np
import torch
import torchvision
import torch.nn.parallel
import torch.optim
import torch.utils.data
import torchvision.transforms as transforms
from torch.utils.data import DataLoader


from models.resnet import load_model
from datasets.color_mnist import get_biased_mnist_dataloader
from datasets.cub_dataset import WaterbirdDataset
from datasets.celebA_dataset import get_celebA_dataloader, celebAOodDataset
from utils import AverageMeter, accuracy
import utils.svhn_loader as svhn
from datasets.gaussian_dataset import GaussianDataset

parser = argparse.ArgumentParser(description='OOD Detection Evaluation based on Energy-score')
parser.add_argument('--name', default = 'erm_rebuttal', type=str, help='help identify checkpoint')
parser.add_argument('--exp_name', '-n', default = 'erm_new_0.7', type=str, help='name of experiment')
parser.add_argument('--in-dataset', default="celebA", type=str, help='name of the in-distribution dataset')
parser.add_argument('--root_dir', required = True, type=str, help='the root directory that contains the OOD test datasets')
parser.add_argument('--model-arch', default='resnet18', type=str, help='model architecture e.g. resnet18')
parser.add_argument('--method', default='erm', type=str, help='method used for model training')
parser.add_argument('--print-freq', '-p', default=10, type=int, help='print frequency (default: 10)') 
parser.add_argument('--domain-num', default=4, type=int,
                    help='the number of environments for model training')
parser.add_argument('-bs', '--batch-size', default= 64, type=int,
                    help='mini-batch size (default: 64) used for training id and ood')
parser.add_argument('--num-classes', default=2, type=int,
                    help='number of classes for model training')
parser.add_argument('--ood-batch-size', default= 64, type=int,
                    help='mini-batch size (default: 400) used for testing')
parser.add_argument('--data_label_correlation', default= 0.7, type=float,
                    help='data_label_correlation')
parser.add_argument('--test_epochs', "-e", default = "15 20 25", type=str,
                     help='# epoch to test performance')
parser.add_argument('--log_name',
                    help='Name of the Log File', type = str, default = "info_val.log")
parser.add_argument('--base-dir', default='output/ood_scores', type=str, help='result directory')
parser.add_argument('--gpu-ids', default='6', type=str,
                    help='id(s) for CUDA_VISIBLE_DEVICES')
parser.add_argument('--manualSeed', type=int, help='manual seed')
parser.add_argument('--multi-gpu', default=False, type=bool)
parser.add_argument('--local_rank', default=-1, type=int,
                        help='rank for the current node')
parser.add_argument('--top', '-t', default=0, type=int)
parser.add_argument('--custom_mask', '-cm', default=0, type=int, help='whether to use a specified custom mask. 0 means no, 1 means yes. Specity with cmb and cmt. If true, ignores top argument')
parser.add_argument('--custom_mask_bottom', '-cmb', default = 200, type=int, help='In custom mask, everything before this unit is ignored')
parser.add_argument('--custom_mask_top', '-cmt', default = 300, type=int, help='In custom mask, everything above this unit is ignored')
parser.add_argument('--environment', '-env', default='0123', type=str)

args = parser.parse_args()

state = {k: v for k, v in args._get_kwargs()}
directory = "checkpoints/{in_dataset}/{name}/".format(in_dataset=args.in_dataset, name=args.name)
if not os.path.exists(directory):
    os.makedirs(directory)
save_state_file = os.path.join(directory, 'test_args.txt')
fw = open(save_state_file, 'w')
print(state, file=fw)
fw.close()

os.environ['CUDA_VISIBLE_DEVICES'] = args.gpu_ids
if torch.cuda.is_available():
    torch.cuda.set_device(args.local_rank)
device = torch.device(f"cuda" if torch.cuda.is_available() else "cpu")


def get_ood_energy(args, model, val_loader, epoch, mask, log, method):
    def edit_activation(mask, mod, inp, out):
        return torch.mul(out, torch.tensor(mask, dtype=torch.float32).cuda())

    model.avgpool.register_forward_hook(partial(edit_activation, mask))

    in_energy = AverageMeter()
    model.eval()
    init = True
    log.debug("######## Start collecting energy score ########")
    with torch.no_grad():
        for i, (images, labels) in enumerate(val_loader):
            images = images.cuda()
            _, outputs = model(images)
            e_s = -torch.logsumexp(outputs, dim=1)
            e_s = e_s.data.cpu().numpy() 
            in_energy.update(e_s.mean(), len(labels))
            if init:
                sum_energy = e_s
                init = False
            else:
                sum_energy = np.concatenate((sum_energy, e_s))
            if i % args.print_freq == 0: 
                log.debug('Epoch: [{0}] Batch#[{1}/{2}]\t'
                    'Energy Sum {in_energy.val:.4f} ({in_energy.avg:.4f})'.format(
                        epoch, i, len(val_loader), in_energy=in_energy))
        return sum_energy

def get_id_energy(args, model, val_loader, epoch, mask, log, method):
    in_energy = AverageMeter()
    top1 = AverageMeter()
    acc_E = {0:AverageMeter(),
            1: AverageMeter(),
            2: AverageMeter(),
            3: AverageMeter() }
    env_E = {0:AverageMeter(),
            1: AverageMeter(),
            2: AverageMeter(),
            3: AverageMeter() }
    NUM_ENV = 4
    all_preds = torch.tensor([])
    all_targets = torch.tensor([])
    all_envs = torch.tensor([])
    energy = np.empty(0)
    energy_grey = np.empty(0)
    energy_nongrey = np.empty(0)


    def edit_activation(mask, mod, inp, out):
        return torch.mul(out, torch.tensor(mask, dtype=torch.float32).cuda())

    model.avgpool.register_forward_hook(partial(edit_activation, mask))

    model.eval()
    log.debug("######## Start collecting energy score ########")
    with torch.no_grad():
        for i, (images, labels, envs) in enumerate(val_loader):

            images = images.cuda() 
            labels = labels 

            _, outputs = model(images)

            all_envs = torch.cat((all_envs, envs),dim=0)
            all_targets = torch.cat((all_targets, labels),dim=0)
            all_preds = torch.cat((all_preds, outputs.argmax(dim=1).cpu()),dim=0)
            prec1 = accuracy(outputs.cpu().data, labels, topk=(1,))[0]
            top1.update(prec1, images.size(0))
            e_s = -torch.logsumexp(outputs, dim=1)
            e_s = e_s.data.cpu().numpy() 
            for j in range(NUM_ENV):
                numingroup = len(labels[envs == j])
                if numingroup == 0: continue
                env_E[j].update(e_s[envs == j].mean(), numingroup)
                correct = accuracy(outputs.cpu().data[envs == j], labels[envs == j], topk=(1,))[0]
                acc_E[j].update(correct, numingroup)
            in_energy.update(e_s.mean(), len(labels)) 
            energy = np.concatenate((energy, e_s))

            if i % args.print_freq == 0:
                if args.in_dataset == 'color_mnist': 
                    log.debug('Epoch: [{0}] Batch#[{1}/{2}]\t'
                    'ID Energy {in_energy.val:.4f} ({in_energy.avg:.4f})\t'
                    'red 0 {env_E[0].val:.4f} ({env_E[0].avg:.4f})\t'
                    'green 0 {env_E[1].val:.4f} ({env_E[1].avg:.4f})\t'
                    'red 1 {env_E[2].val:.4f} ({env_E[2].avg:.4f})\t'
                    'green 1 {env_E[3].val:.4f} ({env_E[3].avg:.4f})\t'.format(
                        epoch, i, len(val_loader), in_energy=in_energy, env_E = env_E))
                elif args.in_dataset == 'celebA': 
                    log.debug('Epoch: [{0}] Batch#[{1}/{2}]\t'
                    'ID Energy {in_energy.val:.4f} ({in_energy.avg:.4f})\t'
                    'nongrey hair F {env_E[0].val:.4f} ({env_E[0].avg:.4f})\t'
                    'nongrey hair M {env_E[1].val:.4f} ({env_E[1].avg:.4f})\t'
                    'gray hair F {env_E[2].val:.4f} ({env_E[2].avg:.4f})\t'
                    'gray hair M {env_E[3].val:.4f} ({env_E[3].avg:.4f})\t'.format(
                        epoch, i, len(val_loader), in_energy=in_energy, env_E = env_E))
        log.debug(' * Prec@1 {top1.avg:.3f}. Group 0: {e[0].avg}, 1: {e[1].avg}, 2: {e[2].avg}, 3: {e[3].avg}'.format(top1=top1, e=acc_E))

        return energy, energy_grey, energy_nongrey, all_envs, top1.avg, acc_E


def get_ood_loader(args, out_dataset, in_dataset = 'color_mnist'):
        # for mnist
        small_transform = transforms.Compose([
                transforms.Resize(32),
                 transforms.CenterCrop(32),
                transforms.ToTensor(),
                transforms.Normalize(mean=(0.5, 0.5, 0.5),
                             std=(0.5, 0.5, 0.5))])
        # for celebA
        scale = 256.0/224.0
        target_resolution = (224, 224)
        large_transform = transforms.Compose([
            transforms.Resize((int(target_resolution[0]*scale), int(target_resolution[1]*scale))),
            transforms.CenterCrop(target_resolution),
            transforms.ToTensor(),
            transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
        ])

        root_dir  = args.root_dir

        if in_dataset == 'color_mnist':   
            if out_dataset == 'gaussian':
                testsetout = GaussianDataset(dataset_size =10000, img_size = 32,
                    transform=transforms.Normalize(mean=(0.5, 0.5, 0.5),
                             std=(0.5, 0.5, 0.5)))
            else:
                testsetout = torchvision.datasets.ImageFolder(f"{root_dir}/{out_dataset}",
                                            transform=small_transform)
            subset = torch.utils.data.Subset(testsetout, np.random.choice(len(testsetout), 2000, replace=False))
            testloaderOut = torch.utils.data.DataLoader(subset, batch_size=args.ood_batch_size,
                                             shuffle=True, num_workers=4) 
        elif in_dataset == 'waterbird' or in_dataset == 'celebA':
            if out_dataset == "SVHN":
                testsetout = svhn.SVHN(f"{root_dir}/{out_dataset}", split='test',
                                    transform=large_transform, download=False)
            elif out_dataset == 'gaussian':
                testsetout = GaussianDataset(dataset_size =10000, img_size = 224,
                    transform=transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]))
            elif  out_dataset == 'celebA_ood':
                testsetout = celebAOodDataset()
            else:
                testsetout = torchvision.datasets.ImageFolder(f"{root_dir}/{out_dataset}",
                                            transform=large_transform)
            if out_dataset == 'celebA_ood':
                subset = torch.utils.data.Subset(testsetout, np.random.choice(len(testsetout), 2000, replace=True))
            else:
                subset = torch.utils.data.Subset(testsetout, np.random.choice(len(testsetout), 2000, replace=False))
            testloaderOut = torch.utils.data.DataLoader(subset, batch_size=args.ood_batch_size,
                                                shuffle=True, num_workers=4)           
        else: 
            testsetout = torchvision.datasets.ImageFolder("datasets/ood_datasets/{}".format(out_dataset),
                                        transform= small_transform)
            testloaderOut = torch.utils.data.DataLoader(testsetout, batch_size=args.ood_batch_size,
                                             shuffle=True, num_workers=4)
        return testloaderOut


def getactivations(args):
    shape = []
    if args.model_arch == 'resnet18': shape = [1,512,1,1]
    elif args.model_arch == 'resnet50': shape = [1,2048,1,1]

    if args.top == 0 and args.custom_mask == 0: return np.ones(shape)
    with open(f'experiments/{args.in_dataset}/{args.name}/activations/activations_id_at_epoch_{args.test_epochs}_e{args.environment}.npy', 'rb') as f:
        acs = np.load(f)
    
    a = acs.mean(axis=0) # average ID activation pattern
    order = np.argsort(a) # find which units are most "important"/contributing
    mask = np.zeros(a.shape) # form a mask to only include top units

    if args.custom_mask == 1:
        lowerbound = args.custom_mask_bottom
        upperbound = args.custom_mask_top
        units = order[lowerbound:upperbound]
        mask[units] = 1
        print(units[:3])
        
    if args.top>0:
        topinds = order[-args.top:]  # get just the top of these units
        mask[topinds] = 1

    mask = np.reshape(mask, shape) # to match with GAP layer output shape
    print(mask.sum(), 'used units')
    return mask


def main():

    log = logging.getLogger(__name__)
    formatter = logging.Formatter('%(asctime)s : %(message)s')
    fileHandler = logging.FileHandler(os.path.join(directory, args.log_name), mode='w')
    fileHandler.setFormatter(formatter)
    streamHandler = logging.StreamHandler()
    streamHandler.setFormatter(formatter)
    log.setLevel(logging.DEBUG)
    log.addHandler(fileHandler)
    log.addHandler(streamHandler) 


    if args.in_dataset == "color_mnist":
        val_loader = get_biased_mnist_dataloader(args, root = './datasets/MNIST', batch_size=args.batch_size,
                                            data_label_correlation= args.data_label_correlation,
                                            n_confusing_labels= args.num_classes - 1,
                                            train=False, partial=True, cmap = "1")
    elif args.in_dataset == "waterbird":
        val_dataset = WaterbirdDataset(data_correlation=args.data_label_correlation, split='test')
        val_loader = DataLoader(val_dataset, batch_size=args.batch_size, shuffle=True)
    elif args.in_dataset == "celebA":
        val_loader = get_celebA_dataloader(args, split='test')

    # create model
    if args.model_arch == 'resnet18':
        model = load_model()
    elif args.model_arch == 'resnet50':
        model = load_model(arch='resnet50')

    model = model.cuda()

    top = args.top # use this many of the last units
    mask = getactivations(args)

    test_epochs = args.test_epochs.split()
    if args.in_dataset == 'color_mnist':
        out_datasets = ['partial_color_mnist_0&1', 'gaussian', 'dtd', 'iSUN', 'LSUN_resize']
    elif args.in_dataset == 'waterbird':
        out_datasets = ['placesbg', 'SVHN', 'iSUN']
        # out_datasets = ['gaussian', 'placesbg', 'water', 'SVHN', 'iSUN', 'LSUN_resize']#, 'dtd']
    elif args.in_dataset == 'color_mnist_multi':
        out_datasets = ['partial_color_mnist_0&1']
    elif args.in_dataset == 'celebA':
        out_datasets = ['celebA_ood', 'SVHN', 'iSUN', 'LSUN_resize']

    cpts_directory = "./experiments/{in_dataset}/{name}/checkpoints".format(in_dataset=args.in_dataset, name=args.name, exp=args.exp_name)
    # cpts_directory = "/nobackup/sonic/checkpoints/waterbird_temp/gdro_r_0_9/".format(in_dataset=args.in_dataset, name=args.name, exp=args.exp_name)
    
    for test_epoch in test_epochs:
        cpts_dir = os.path.join(cpts_directory, "checkpoint_{epochs}.pth.tar".format(epochs=test_epoch))
        checkpoint = torch.load(cpts_dir)
        state_dict = checkpoint['state_dict_model']
        # state_dict = {k[6:]:v for k, v in state_dict.items()} #all key names are prefaced with "model." so remove that
        # print(state_dict.keys())
        if torch.cuda.device_count() == 1:
            new_state_dict = {}
            for k, v in state_dict.items():
                k = k.replace("module.", "")
                new_state_dict[k] = v
            state_dict = new_state_dict
        model.load_state_dict(state_dict)
        model.eval()
        model.cuda()
        save_dir =  f"./experiments/{args.in_dataset}/{args.name}/energy_results"
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
        acc_dir =  f"./experiments/{args.in_dataset}/{args.name}/acc"
        if not os.path.exists(acc_dir):
            os.makedirs(acc_dir)
        print("processing ID dataset")

        #********** normal procedure **********
        id_energy, _, _, envs, acc, acc_E  = get_id_energy(args, model, val_loader, test_epoch, mask, log, method=args.method)
        
        with open(os.path.join(acc_dir, f'id_test_acc_epoch_{test_epoch}_t{top}cm{args.custom_mask}b{args.custom_mask_bottom}t{args.custom_mask_top}_e{args.environment}.txt'), 'w') as f:
            f.write('Overall\t' + str(acc.item())+'\n\n')
            f.write('Env 0\t' + str(acc_E[0].avg.item())+'\n')
            f.write('Env 1\t' + str(acc_E[1].avg.item())+'\n')
            f.write('Env 2\t' + str(acc_E[2].avg.item())+'\n')
            f.write('Env 3\t' + str(acc_E[3].avg.item())+'\n\n')

        envcombos = ['0', '1', '2', '3', '01', '23', '0123']
        id_energyenv = []
        for i in range(4):
            id_energyenv.append(id_energy[envs==i])
            
        for c in envcombos:
            print([int(n) for n in c.split()])
            e = [id_energyenv[int(n)] for n in list(c)]
            eall = np.concatenate(e)
            with open(os.path.join(save_dir, f'energy_score_at_epoch_{test_epoch}_top{top}cm{args.custom_mask}b{args.custom_mask_bottom}t{args.custom_mask_top}_e{args.environment}_scoreenv{c}.npy'), 'wb') as f:
                np.save(f, eall)
        for out_dataset in out_datasets:
            print("processing OOD dataset ", out_dataset)
            testloaderOut = get_ood_loader(args, out_dataset, args.in_dataset)
            ood_energy = get_ood_energy(args, model, testloaderOut, test_epoch, mask, log, method=args.method)
            with open(os.path.join(save_dir, f'energy_score_{out_dataset}_at_epoch_{test_epoch}_top{top}cm{args.custom_mask}b{args.custom_mask_bottom}t{args.custom_mask_top}_e{args.environment}.npy'), 'wb') as f:
                np.save(f, ood_energy)

if __name__ == '__main__':
    main()

