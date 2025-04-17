# wearable_project_django

project for ELEG5757  
Team 7 Project 5 Group 1

## 1. How to install
this project used `pdm` to manage project.

#### pdm (if you installed conda, please turn to conda)
```shell
git clone https://github.com/leafliber/wearable_project_django
cd wearable_project_django
pip install --user pdm
pdm install
```
or
#### conda
```shell
conda create -n -yourenvname- python=3.9
conda activate -yourenvname-
pip install pdm
git clone https://github.com/leafliber/wearable_project_django
cd wearable_project_django
pip install -r requirements.txt
```

Then, replease the model files by [release](https://github.com/leafliber/wearable_project_django/releases) where you can download our models and demo.  
replace the models and demo documents:  
```
epoch_100.pth ->  
wearable_project_django/wearable_project/model/epoch_100.pth  
resnet50_batch256_fp16_imagenet_20210320-b3964210.pth ->  
wearable_project_django/wearable_project/model/config/resnet50_batch256_fp16_imagenet_20210320-b3964210.pth  
test.mp4 ->  
demo/test.mp4
```
(test demo could be your own video or backend stream or frontend stream)


## 2. How to use
You have to install before use.
run the server  
```shell
pdm run server
```
Visit your web [http://127.0.0.1:8000/stream](http://127.0.0.1:8000/stream)
