import sys
import numpy as np
import matplotlib.pyplot as plt

dataset = sys.argv[1]
name = sys.argv[2]

spood = ''
if dataset == 'waterbird':
    spood = 'placesbg'
if dataset == 'celebA':
    spood = 'celebA_ood'


