#!/bin/bash
name=`date +"%Y-%m-%d_%H.%M.%S"`
TS=(
    0
    400
    300
    256
    200
    150
    128
    100
    75
    64
    50
)

echo $name
echo "Train"
python train_bg.py --gpu-ids 1 --in-dataset waterbird --model resnet18 --epochs 30 --save-epoch 10  --data_label_correlation 0.9 --domain-num 4 --method erm --name $name  --lr 0.001 --weight-decay 0.001
echo "Get activations"
python get_activations.py --gpu-ids 1 --in-dataset waterbird --model resnet18 --test_epochs 30 --data_label_correlation 0.9 --method erm --name $name  --root_dir datasets/ood_datasets 

for t in "${TS[@]}"; do
    echo "TOP $t"
    echo "Test"
    python test_bg.py --gpu-ids 1 --in-dataset waterbird --model resnet18 --test_epochs 30 --data_label_correlation 0.9 --method erm --name $name  --root_dir datasets/ood_datasets -t $t
    echo "Present results"
    python present_results.py --in-dataset waterbird --name $name  --test_epochs 30 -t $t
done

echo $name
