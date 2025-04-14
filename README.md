# wearable_project_django

this is a project for ELEG5757  
Team 7 Project 5 Group 1

## How to use
first you have to install `torch` under the [offical instruction](https://pytorch.org/get-started/locally/)  
PS: torch==2.6 is not work unless set torch  trust pt model with mmclassification.
  
then use `pdm` `conda` or `pip` to manage this project

#### pdm (not adapt with conda, if you installed conda, please skip it)
```shell
pip install --user pdm
pdm install
pdm run server
```

#### pip
```shell
pip install torch
pip install -r requirements.txt
```

#### conda
```shell
conda activate -yourenvname-
pip install -r requirements.txt
```