#!/bin/bash
name=`date +"%Y-%m-%d_%H.%M.%S"`
data=$1
corr=$2
gpu=$3

ENV=(
    0123
    01
    23
)

echo $name
echo "Train"
python train_bg.py --gpu-ids $gpu --in-dataset $data --model resnet18 --epochs 30 --save-epoch 30 --data_label_correlation $corr --domain-num 4 --method erm --name $name  --lr 0.001 --weight-decay 0.001
# echo "Get activations"
# python get_activations.py --gpu-ids $gpu --in-dataset $data --model resnet18 --test_epochs 30 --data_label_correlation $corr --method erm --name $name  --root_dir datasets/ood_datasets 
# python get_activations.py --gpu-ids $gpu --in-dataset $data --model resnet18 --test_epochs 30 --data_label_correlation $corr --method erm --name $name  --root_dir datasets/ood_datasets --datasplit test

# python compare_activations.py $data $name 30
# python compare_group_activations.py $data $name

echo "Test all units"
python test_bg.py --gpu-ids $gpu --in-dataset $data --model resnet18 --test_epochs 30 --data_label_correlation $corr --method erm --name $name  --root_dir datasets/ood_datasets -cm 0
echo "Present results"
python present_results.py --in-dataset $data --name $name  --test_epochs 30 -cm 0

python plot_energy.py $name $data

# for e in "${ENV[@]}"; do
#     echo "Test 0-100, top 200"
#     python test_bg.py --gpu-ids $gpu --in-dataset $data --model resnet18 --test_epochs 30 --data_label_correlation $corr --method erm --name $name  --root_dir datasets/ood_datasets -env $e --top 200 -cm 1 -cmb 0 -cmt 100
#     echo "Present results"
#     python present_results.py --in-dataset $data --name $name  --test_epochs 30 -env $e --top 200  -cm 1 -cmb 0 -cmt 100

#     echo "Test 0-100, top 100"
#     python test_bg.py --gpu-ids $gpu --in-dataset $data --model resnet18 --test_epochs 30 --data_label_correlation $corr --method erm --name $name  --root_dir datasets/ood_datasets -env $e --top 100 -cm 1 -cmb 0 -cmt 100
#     echo "Present results"
#     python present_results.py --in-dataset $data --name $name  --test_epochs 30 -env $e --top 100  -cm 1 -cmb 0 -cmt 100

#     echo "Test 0-100, top 100"
#     python test_bg.py --gpu-ids $gpu --in-dataset $data --model resnet18 --test_epochs 30 --data_label_correlation $corr --method erm --name $name  --root_dir datasets/ood_datasets -env $e --top 100 -cm 1 -cmb 200 -cmt 300
#     echo "Present results"
#     python present_results.py --in-dataset $data --name $name  --test_epochs 30 -env $e --top 100  -cm 1 -cmb 200 -cmt 300
# done

python utils/notify.py
echo $name
