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

# allactivsc = []
# c = [] # index i is average activation for group i

# for i in ['01','23']:
#     with open(f'./experiments/waterbird/{exp}/activations/activations_id_at_epoch_30_e{i}.npy', 'rb') as f:
#         allactivsc.append(np.load(f))
#     c.append(allactivsc[-1].mean(axis=0))
#     print(allactivsc[-1].shape, c[-1].shape)

# n = a[0].shape[0]

# order = np.argsort(c[0])

# plt.plot(range(n), c[0][order], 'o', ms=1.5, label='landbird')
# plt.plot(range(n), c[1][order], 'o', ms=1.5, label='waterbird')
# plt.xlabel('unit')
# plt.legend(loc="upper left", markerscale=5, fontsize=12)
# plt.title('activation by class, resnet18 on waterbird 0.9, land-sorted')

# plt.savefig(f'plot0class_bad.png') 
# plt.clf()

# order = np.argsort(c[1])

# plt.plot(range(n), c[0][order], 'o', ms=1.5, label='landbird')
# plt.plot(range(n), c[1][order], 'o', ms=1.5, label='waterbird')

# plt.xlabel('unit')
# plt.legend(loc="upper left", markerscale=5, fontsize=12)
# plt.title('activation by class, resnet18 on waterbird 0.9, water-sorted')

# plt.savefig(f'plot1class_bad.png') 
