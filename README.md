# wearable_project_django

this is a project for ELEG5757  
Team 7 Project 5 Group 1

## How to use
this project uses `pdm` to manage this project

#### pdm (not adapt with conda, if you installed conda, please skip it)
```shell
git clone https://github.com/leafliber/wearable_project_django
cd wearable_project_django
pip install --user pdm
pdm install
pdm run server
```

#### if you have conda
```shell
conda create -n -yourenvname- python=3.9
conda activate -yourenvname-
pip install pdm
git clone https://github.com/leafliber/wearable_project_django
cd wearable_project_django
pip install -r requirements.txt
pdm run server
```

Last, replease the model files by release where you can download our models.
replease the test.mp4 by your video. 
