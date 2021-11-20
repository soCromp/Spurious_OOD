import sys
import numpy as np
import matplotlib.pyplot as plt

dataset = sys.argv[2]
name = sys.argv[1]
spood = ''
if dataset == 'waterbird':
    spood = 'placesbg'
if dataset == 'celebA':
    spood = 'celebA_ood'





# with open('./experiments/waterbird/2021-11-05_14.03.28a/energy_results/energy_score_at_epoch_30_top0.npy', 'rb') as f:
#     ida = -1* np.load(f)

# with open('./experiments/waterbird/2021-11-05_14.03.28a/energy_results/energy_score_placesbg_at_epoch_30_top0.npy', 'rb') as f:
#     spooda = -1* np.load(f)

# with open('./experiments/waterbird/2021-11-05_14.03.28a/energy_results/energy_score_SVHN_at_epoch_30_top0.npy', 'rb') as f:
#     nspooda = -1* np.load(f)

# with open('./experiments/waterbird/2021-11-02_12.19.08env0/energy_results/energy_score_at_epoch_30_top0.npy', 'rb') as f:
#     id0 = -1* np.load(f)

# with open('./experiments/waterbird/2021-11-02_12.19.08env0/energy_results/energy_score_placesbg_at_epoch_30_top0.npy', 'rb') as f:
#     spood0 = -1* np.load(f)

# with open('./experiments/waterbird/2021-11-02_12.19.08env0/energy_results/energy_score_SVHN_at_epoch_30_top0.npy', 'rb') as f:
#     nspood0 = -1* np.load(f)

# alpha = 0.5
# width = 0.5
# lo = min(ida.min(), spooda.min(), nspooda.min(), id0.min(), spood0.min(), nspood0.min())
# hi = 8 # max(ida.max(), spooda.max(), nspooda.max(), id200.max(), spood200.max(), nspood200.max())
# bins = np.arange(lo, hi, width)

# # plt.figure(figsize=(2,2))  #6.8 and 4.8 by default
# plt.rcParams['figure.figsize'] = [12, 4.8]
# fig, axs = plt.subplots(1, 2, sharey=True, )

# # axs[0].hist(x)
# axs[0].hist(ida, bins=bins, density=True, stacked=True, alpha=alpha, label='ID')
# axs[0].hist(nspooda, bins=bins, density=True, stacked=True, alpha=alpha, label='NSPOOD')
# axs[0].hist(spooda, bins=bins, density=True, stacked=True, alpha=alpha, label='SPOOD')


# axs[0].legend(loc="upper right", markerscale=5, fontsize=12)
# axs[0].set_title('top 0 all envs')


# axs[1].hist(id0, bins=bins, density=True, stacked=True, alpha=alpha, label='ID')
# axs[1].hist(nspood0, bins=bins, density=True, stacked=True, alpha=alpha, label='NSPOOD')
# axs[1].hist(spood0, bins=bins, density=True, stacked=True, alpha=alpha, label='SPOOD')

# axs[1].legend(loc="upper right", markerscale=5, fontsize=12)
# axs[1].set_title('top 512 env 0')

# plt.savefig('plot_energy.png')

def load(env, path):
    suffix = '_at_epoch_30_top0cm0b200t300_e0123_scoreenv'
    p = path + suffix + env + '.npy'
    print(p)
    with open(p, 'rb') as f:
        input = -1* np.load(f)
    return input

path = f'./experiments/{dataset}/{name}/energy_results/energy_score'
suffix = '_at_epoch_30_top0cm0b200t300_e'
envs = ['0', '3', '01', '23', '0123']
id = []
for e in envs:
    id.append( load(e, path) )

p = path + '_' + spood + suffix + '0123.npy'
print(p)
with open(p, 'rb') as f:
    spood = -1* np.load(f)
p = path + '_SVHN' + suffix + '0123.npy'
print(p)
with open(p, 'rb') as f:
    nspood = -1* np.load(f)

alpha = 0.5
width = 0.5
lo = 0
hi = 8 # max(ida.max(), spooda.max(), nspooda.max(), id200.max(), spood200.max(), nspood200.max())
bins = np.arange(lo, hi, width)

# plt.figure(figsize=(2,2))  #6.8 and 4.8 by default
plt.rcParams['figure.figsize'] = [12, 6.4]
fig, axs = plt.subplots(2, 3, sharey=True, )

# for i in range(len(envs)-1):
#     axs[i].hist(id[i], bins=bins, density=True, stacked=True, alpha=alpha, label='ID')
#     # axs[i].hist(nspood[i], bins=bins, density=True, stacked=True, alpha=alpha, label='NSPOOD')
#     # axs[i].hist(spood[i], bins=bins, density=True, stacked=True, alpha=alpha, label='SPOOD')
#     axs[i].set_title('Environment' + str(envs[i]))
#     axs[i].legend(loc="upper right", markerscale=5, fontsize=12)

axs[0][0].hist(id[0], bins=bins, density=True, stacked=True, alpha=alpha, label='ID')
axs[0][0].set_title('Environment ' + str(envs[0]))
axs[0][1].hist(id[1], bins=bins, density=True, stacked=True, alpha=alpha, label='ID')
axs[0][1].set_title('Environment ' + str(envs[1]))
axs[0][2].hist(id[2], bins=bins, density=True, stacked=True, alpha=alpha, label='ID')
axs[0][2].set_title('Environment ' + str(envs[2]))
axs[1][0].hist(id[3], bins=bins, density=True, stacked=True, alpha=alpha, label='ID')
axs[1][0].set_title('Environment ' + str(envs[3]))
axs[1][1].hist(id[4], bins=bins, density=True, stacked=True, alpha=alpha, label='ID')
axs[1][1].set_title('Environment ' + str(envs[4]))

axs[1][2].hist(spood, bins=bins, density=True, stacked=True, alpha=alpha, label='SPOOD', color='red')
axs[1][2].hist(nspood, bins=bins, density=True, stacked=True, alpha=alpha, label='NSPOOD', color='yellow')
axs[1][2].set_title('OOD')

axs[0][2].legend(loc="upper right", markerscale=5, fontsize=12)
axs[1][2].legend(loc="upper right", markerscale=5, fontsize=12)

plt.savefig(f'./experiments/{dataset}/{name}/plot_energy.png')
