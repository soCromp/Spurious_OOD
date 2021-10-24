#!/bin/bash
t=`date +"%Y-%m-%d_%H.%M.%S"`
echo $t
python train_bg.py --gpu-ids 1 --in-dataset waterbird --model resnet18 --epochs 30 --save-epoch 10  --data_label_correlation 0.9 --domain-num 4 --method erm --name $t --exp-name $t --lr 0.001 --weight-decay 0.001
python get_activations.py --gpu-ids 1 --in-dataset waterbird --model resnet18 --test_epochs 30 --data_label_correlation 0.9 --method erm --name $t --exp_name $t --root_dir datasets/ood_datasets 
python test_bg.py --gpu-ids 1 --in-dataset waterbird --model resnet18 --test_epochs 30 --data_label_correlation 0.9 --method erm --name $t --exp_name $t --root_dir datasets/ood_datasets -t 250
python present_results.py --in-dataset waterbird --name $t --exp-name $t --test_epochs 30
echo $t
