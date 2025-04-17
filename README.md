# wearable_project_django

this is a project for ELEG5757  
Team 7 Project 5 Group 1

## How to use
first you have to install `torch` under the [offical instruction](https://pytorch.org/get-started/locally/)  
PS: torch==2.6 is not work unless set torch  trust pt model with mmclassification.
  
then use `pdm` `conda` or `pip` to manage this project

#### pdm (not adapt with conda, if you installed conda, please skip it)
```shell
git clone https://github.com/leafliber/wearable_project_django
cd wearable_project_django
pip install --user pdm
pdm install
pdm run server
```

#### pip
```shell
git clone https://github.com/leafliber/wearable_project_django
cd wearable_project_django
pip install torch
pip install -r requirements.txt
```

#### conda
```shell
git clone https://github.com/leafliber/wearable_project_django
cd wearable_project_django
conda activate -yourenvname-
pip install -r requirements.txt
```

Last, replease the model files by release where you can download our models.
replease the test.mp4 by your video. 
