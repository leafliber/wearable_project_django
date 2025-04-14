from mmpretrain import ImageClassificationInferencer
import os
import numpy as np
inferencer = ImageClassificationInferencer(
    model=r'./wearable_project/model/configs/resnet/5757project.py',
    pretrained=r'./wearable_project/model/epoch_100.pth'
)

folder_path=r'./wearable_project/model/demo/test'
for root, dirs, files in os.walk(folder_path):
    for file in files:
        if os.path.splitext(file)[1].lower()=='.png':
            
            full_path = os.path.join(root, file)
            image=full_path
            result= inferencer(np.array(image))[0]
            print(file)
            print(result['pred_class'])


