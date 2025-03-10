import numpy as np
from utils import anom_utils
import os
import argparse
from collections import defaultdict


parser = argparse.ArgumentParser(description='Present OOD Detection metrics for Energy-score')
parser.add_argument('--name', '-n', default = 'erm_rebuttal', type=str,
                    help='name of experiment')
# parser.add_argument('--exp-name', default = 'erm_new_0.7', type=str, 
#                     help='help identify checkpoint')
parser.add_argument('--in-dataset', default='celebA', type=str, help='in-distribution dataset e.g. color_mnist')
parser.add_argument('--test_epochs', "-e", default = "15 20 25", type=str,
                    help='# epoch to test performance')
parser.add_argument('--top', '-t', default=0, type=int, help='number of top-contributing neurons used at test time')
parser.add_argument('--custom_mask', '-cm', default=0, type=int, help='whether a custom mask was used')
parser.add_argument('--custom_mask_bottom', '-cmb', default=200, type=int, help='whether a custom mask was used')
parser.add_argument('--custom_mask_top', '-cmt', default=300, type=int, help='whether a custom mask was used')
parser.add_argument('--environment', '-env', default='0123', type=str)
args = parser.parse_args()

def main():
    if args.in_dataset == "color_mnist" or args.in_dataset == "color_mnist_multi":
        out_datasets = ['partial_color_mnist_0&1', 'gaussian', 'dtd', 'iSUN', 'LSUN_resize']
    elif args.in_dataset == "waterbird":
        out_datasets = ['placesbg', 'SVHN', 'iSUN']
        # out_datasets = ['placesbg', 'SVHN', 'iSUN', 'LSUN_resize', ] #'dtd']
    elif args.in_dataset == "celebA":
        out_datasets = ['celebA_ood', 'SVHN', 'iSUN', 'LSUN_resize']
        
    fprs = dict()
    s = '' # will hold all info
    for test_epoch in args.test_epochs.split():
        all_results_ntom = []
        save_dir =  f"./experiments/{args.in_dataset}/{args.name}/energy_results" 
        with open(os.path.join(save_dir, f'energy_score_at_epoch_{test_epoch}_top{args.top}cm{args.custom_mask}b{args.custom_mask_bottom}t{args.custom_mask_top}_e{args.environment}_scoreenv0123.npy'), 'rb') as f:
            id_sum_energy = np.load(f)
        all_results = defaultdict(int)
        for out_dataset in out_datasets:
            with open(os.path.join(save_dir, f'energy_score_{out_dataset}_at_epoch_{test_epoch}_top{args.top}cm{args.custom_mask}b{args.custom_mask_bottom}t{args.custom_mask_top}_e{args.environment}.npy'), 'rb') as f:
                ood_sum_energy = np.load(f)
            p, auroc, aupr, fpr = anom_utils.get_and_print_results(-1 * id_sum_energy, -1 * ood_sum_energy, f"{out_dataset}", f" Energy Sum at epoch {test_epoch}")
            s = s + p
            results = cal_metric(known =  -1 * id_sum_energy, novel = -1* ood_sum_energy, method = "energy sum")
            all_results_ntom.append(results)
            all_results["AUROC"] += auroc
            all_results["AUPR"] += aupr
            all_results["FPR95"] += fpr
        s = s + "Avg FPR95: " + str(round(100 * all_results["FPR95"]/len(out_datasets),2)) + '\n'
        s = s + "Avg AUROC: " + str(round(all_results["AUROC"]/len(out_datasets),4)) + '\n'
        s = s + "Avg AUPR: " + str(round(all_results["AUPR"]/len(out_datasets),4)) + '\n'
        # print("HELLO")
        fprs[test_epoch] = 100 * all_results["FPR95"]/len(out_datasets)
        avg_results = compute_average_results(all_results_ntom)
        print_results(s, avg_results, args.in_dataset, "All", args.name, "energy sum", args.top, args.test_epochs, args.custom_mask, args.custom_mask_bottom, args.custom_mask_top, args.environment)

def print_results(s, results, in_dataset, out_dataset, name, method, top, epoch, custom_mask,b,t,env):
    mtypes = ['FPR', 'DTERR', 'AUROC', 'AUIN', 'AUOUT']
    s = s + 'in_distribution: ' + in_dataset + '\n'
    s = s + 'out_distribution: '+ out_dataset + '\n'
    s = s + 'Model Name: ' + name + '\n'
    s = s + '\n'

    s = s + ' OOD detection method: ' + method + '\n'
    for mtype in mtypes:
        s = s + ' {mtype:6s}'.format(mtype=mtype)
    s = s + '\n{val:6.2f}'.format(val=100.*results['FPR'])
    s = s + ' {val:6.2f}'.format(val=100.*results['DTERR'])
    s = s + ' {val:6.2f}'.format(val=100.*results['AUROC'])
    s = s + ' {val:6.2f}'.format(val=100.*results['AUIN'])
    s = s + ' {val:6.2f}'.format(val=100.*results['AUOUT'])
    s = s + '\n'
    print(s)
    file = os.path.join('experiments', in_dataset, name, 'result_epoch_{epoch}_top{top}cm{custom_mask}b{b}t{t}_e{env}.txt'.format(epoch=epoch, top=top, custom_mask=custom_mask,b=b,t=t, env=env))
    with open(file, 'w') as f:
        f.write(s)

def cal_metric(known, novel, method):
    tp, fp, fpr_at_tpr95 = get_curve(known, novel, method)
    results = dict()

    # FPR
    mtype = 'FPR'
    results[mtype] = fpr_at_tpr95

    # AUROC
    mtype = 'AUROC'
    tpr = np.concatenate([[1.], tp/tp[0], [0.]])
    fpr = np.concatenate([[1.], fp/fp[0], [0.]])
    results[mtype] = -np.trapz(1.-fpr, tpr)

    # DTERR
    mtype = 'DTERR'
    results[mtype] = ((tp[0] - tp + fp) / (tp[0] + fp[0])).min()

    # AUIN
    mtype = 'AUIN'
    denom = tp+fp
    denom[denom == 0.] = -1.
    pin_ind = np.concatenate([[True], denom > 0., [True]])
    pin = np.concatenate([[.5], tp/denom, [0.]])
    results[mtype] = -np.trapz(pin[pin_ind], tpr[pin_ind])

    # AUOUT
    mtype = 'AUOUT'
    denom = tp[0]-tp+fp[0]-fp
    denom[denom == 0.] = -1.
    pout_ind = np.concatenate([[True], denom > 0., [True]])
    pout = np.concatenate([[0.], (fp[0]-fp)/denom, [.5]])
    results[mtype] = np.trapz(pout[pout_ind], 1.-fpr[pout_ind])

    return results

def get_curve(known, novel, method):
    tp, fp = dict(), dict()
    fpr_at_tpr95 = dict()

    known.sort()
    novel.sort()

    end = np.max([np.max(known), np.max(novel)])
    start = np.min([np.min(known),np.min(novel)])

    all = np.concatenate((known, novel))
    all.sort()

    num_k = known.shape[0]
    num_n = novel.shape[0]

    if method == 'row':
        threshold = -0.5
    else:
        threshold = known[round(0.05 * num_k)]

    tp = -np.ones([num_k+num_n+1], dtype=int)
    fp = -np.ones([num_k+num_n+1], dtype=int)
    tp[0], fp[0] = num_k, num_n
    k, n = 0, 0
    for l in range(num_k+num_n):
        if k == num_k:
            tp[l+1:] = tp[l]
            fp[l+1:] = np.arange(fp[l]-1, -1, -1)
            break
        elif n == num_n:
            tp[l+1:] = np.arange(tp[l]-1, -1, -1)
            fp[l+1:] = fp[l]
            break
        else:
            if novel[n] < known[k]:
                n += 1
                tp[l+1] = tp[l]
                fp[l+1] = fp[l] - 1
            else:
                k += 1
                tp[l+1] = tp[l] - 1
                fp[l+1] = fp[l]

    j = num_k+num_n-1
    for l in range(num_k+num_n-1):
        if all[j] == all[j-1]:
            tp[j] = tp[j+1]
            fp[j] = fp[j+1]
        j -= 1

    fpr_at_tpr95 = np.sum(novel > threshold) / float(num_n)

    return tp, fp, fpr_at_tpr95

def compute_average_results(all_results):
    mtypes = ['FPR', 'DTERR', 'AUROC', 'AUIN', 'AUOUT']
    avg_results = dict()

    for mtype in mtypes:
        avg_results[mtype] = 0.0

    for results in all_results:
        for mtype in mtypes:
            avg_results[mtype] += results[mtype]

    # print("len of all results", float(len(all_results)))
    for mtype in mtypes:
        avg_results[mtype] /= float(len(all_results))

    return avg_results


if __name__ == '__main__':
    main()