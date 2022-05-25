nvsm show health
nvsm dump health

sudo nvsm show gpus
sudo nvsm show drives
sudo nvsm show volumes

sudo docker run --rm --gpus all nvidia/cuda:11.6.0-base-ubuntu20.04 nvidia-smi