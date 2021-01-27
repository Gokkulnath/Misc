python GAP_clf.py \
--expname test_incv3_universal_targeted_linf10_cpu \
--batchSize 30 --testBatchSize 16 --mag_in 10 --foolmodel vgg16 --mode train \
--perturbation_type universal --target 806  --nEpochs 10


#CUDA_VISIBLE_DEVICES=0 python GAP_clf.py \
#--expname test_incv3_universal_targeted_linf10_gpu \
#--batchSize 30 --testBatchSize 16 --mag_in 10 --foolmodel incv3 --mode train \
#--perturbation_type universal --target 805 --gpu_ids 0 --nEpochs 10