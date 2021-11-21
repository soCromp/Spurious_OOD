import sys
import numpy as np
import matplotlib.pyplot as plt

allactivs = []
a = [] # index i is average activation for group i

dataset = sys.argv[1]
name = sys.argv[2]
spood = ''
if dataset == 'waterbird':
    spood = 'placesbg'
if dataset == 'celebA':
    spood = 'celebA_ood'

for i in range(4):
    with open(f'./experiments/{dataset}/{name}/activations/activations_id_at_epoch_30_e{i}.npy', 'rb') as f:
        allactivs.append(np.load(f))
    a.append(allactivs[-1].mean(axis=0))
    print(allactivs[-1].shape, a[-1].shape)

n = a[0].shape[0]

order = np.argsort(a[0])

plt.plot(range(n), a[0][order], 'o', ms=1.5, label='landbird, land', color='green')
plt.plot(range(n), a[1][order], 'o', ms=1.5, label='landbird, water', color='chartreuse')
plt.plot(range(n), a[2][order], 'o', ms=1.5, label='waterbird, land', color = 'plum')
plt.plot(range(n), a[3][order], 'o', ms=1.5, label='waterbird, water', color = 'blue')
plt.xlabel('unit')
plt.legend(loc="upper left", markerscale=5, fontsize=12)
plt.title(f'activation by group, resnet18 on {dataset} train\ngroup 0 (land)-sorted, exp ' + name)

plt.savefig(f'./experiments/{dataset}/{name}/groupactivs0.png') 
plt.clf()

order = np.argsort(a[3])

plt.plot(range(n), a[0][order], 'o', ms=1.5, label='landbird, land', color='green')
plt.plot(range(n), a[1][order], 'o', ms=1.5, label='landbird, water', color='chartreuse')
plt.plot(range(n), a[2][order], 'o', ms=1.5, label='waterbird, land', color = 'plum')
plt.plot(range(n), a[3][order], 'o', ms=1.5, label='waterbird, water', color = 'blue')
plt.xlabel('unit')
plt.legend(loc="upper left", markerscale=5, fontsize=12)
plt.title(f'activation by group, resnet18 on {dataset} train\ngroup 1 (water)-sorted, exp ' + name)

plt.savefig(f'./experiments/{dataset}/{name}/groupactivs1.png') 
plt.clf()

#ordering by contribution to all environments, each example weighted equally 
order = np.argsort(np.concatenate(allactivs).mean(axis=0))
print('tog', order.shape)

plt.plot(range(n), a[0][order], 'o', ms=1.5, label='landbird, land', color='green')
plt.plot(range(n), a[1][order], 'o', ms=1.5, label='landbird, water', color='chartreuse')
plt.plot(range(n), a[2][order], 'o', ms=1.5, label='waterbird, land', color = 'plum')
plt.plot(range(n), a[3][order], 'o', ms=1.5, label='waterbird, water', color = 'blue')
plt.xlabel('unit')
plt.legend(loc="upper left", markerscale=5, fontsize=12)
plt.title(f'activation by group, resnet18 on {dataset} train\nall group-sorted (example equal weight), exp ' + name)

plt.savefig(f'./experiments/{dataset}/{name}/groupactivsAll_perex.png') 
plt.clf()

#ordering by contribution to all environments, each group weighted equally
order = np.argsort( (a[0] + a[1] + a[2] + a[3]) / 4 )
print('tog', order.shape)

plt.plot(range(n), a[0][order], 'o', ms=1.5, label='landbird, land', color='green')
plt.plot(range(n), a[1][order], 'o', ms=1.5, label='landbird, water', color='chartreuse')
plt.plot(range(n), a[2][order], 'o', ms=1.5, label='waterbird, land', color = 'plum')
plt.plot(range(n), a[3][order], 'o', ms=1.5, label='waterbird, water', color = 'blue')
plt.xlabel('unit')
plt.legend(loc="upper left", markerscale=5, fontsize=12)
plt.title(f'activation by group, resnet18 on {dataset} train\nall group-sorted (group equal weight), exp ' + name)

plt.savefig(f'./experiments/{dataset}/{name}/groupactivsAll_pergr.png') 
plt.clf()
