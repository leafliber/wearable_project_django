# model settings
model = dict(
    type='ImageClassifier',
    backbone=dict(
        type='ResNet',
        depth=50,
        num_stages=4,
        out_indices=(3, ),
        style='pytorch',
        frozen_stages=2,
        init_cfg=dict(
            type='Pretrained',
            checkpoint=r'C:\Users\t_shi\Desktop\5757projectdata\mmpretrain-dev\mmpretrain-dev\configs\_base_\resnet50_batch256_fp16_imagenet_20210320-b3964210.pth',
            prefix='backbone',
        )),
    neck=dict(type='GlobalAveragePooling'),
    head=dict(
        type='LinearClsHead',
        num_classes=6,
        in_channels=2048,
        loss=dict(type='CrossEntropyLoss', loss_weight=1.0),
        topk=(1,),
    ))


