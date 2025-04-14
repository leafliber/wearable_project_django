_base_ = [
    '../models/resnet50.py',#还是用的resnet50这个不变
    '../datasets/5757project.py',   # 数据配置
    '../schedules/imagenet_bs256.py',
    '../default_runtime.py',
    # './_randaug_policies.py',
]

# dataset settings

# lighting params, in order of BGR
EIGVAL = [0.0998764, 0.00488138,0.00068742]
EIGVEC = [[-0.6543126,-0.59734164,-0.46374345],
 [-0.73725312,0.36737927 , 0.56700115],
 [ 0.16832366, -0.71289231 , 0.68077287]]

train_pipeline = [
    dict(type='LoadImageFromFile'),
    dict(type='EfficientNetRandomCrop', scale=224, backend='pillow'),
    dict(type='RandomFlip', prob=0.5, direction='horizontal'),
    dict(type='PackInputs'),
]

test_pipeline = [
    dict(type='LoadImageFromFile'),
    dict(type='EfficientNetCenterCrop', crop_size=256, backend='pillow'),
    dict(type='PackInputs'),
]

# train_dataloader = dict(dataset=dict(pipeline=train_pipeline))
# val_dataloader = dict(dataset=dict(pipeline=test_pipeline))
# test_dataloader = dict(dataset=dict(pipeline=test_pipeline))

train_dataloader = dict(
    dataset=dict(pipeline=train_pipeline),
    persistent_workers=False
)
val_dataloader = dict(
    dataset=dict(pipeline=test_pipeline),
    persistent_workers=False
)
test_dataloader = dict(
    dataset=dict(pipeline=test_pipeline),
    persistent_workers=False
)
# schedule settings
optim_wrapper = dict(
    optimizer=dict(type='SGD', lr=0.08, momentum=0.9, weight_decay=1e-4),
    # optimizer = dict(type='AdamW',    lr=5e-2,    weight_decay=0.0005,    betas=(0.9, 0.999),    eps=1e-8),
    paramwise_cfg=dict(bias_decay_mult=0., norm_decay_mult=0.),
)

# optimizer = dict(    type='AdamW',    lr=5e-2,    weight_decay=0.0005,    betas=(0.9, 0.999),    eps=1e-8)

param_scheduler = [
    # warm up learning rate scheduler
    dict(
        type='LinearLR',
        start_factor=1e-6,
        by_epoch=True,
        begin=0,
        end=10,
        # update by iter
        convert_to_iter_based=True),
    # main learning rate scheduler
    dict(
        type='CosineAnnealingLR',
        T_max=40,
        by_epoch=True,
        begin=5,
        end=100,
    )
]

train_cfg = dict(by_epoch=True, max_epochs=100, val_interval=1)
# 验证配置（新增）
val_cfg = dict()
test_cfg = dict()
# val_cfg = dict(
#     data=dict(
#         samples_per_gpu=32,
#         workers_per_gpu=4
#     )
# )
# test_cfg = dict(
#     data=dict(
#         samples_per_gpu=32,
#         workers_per_gpu=4
#     )
# )
# NOTE: `auto_scale_lr` is for automatically scaling LR
# based on the actual training batch size.
# base_batch_size = (32 GPUs) x (64 samples per GPU)
# auto_scale_lr = dict(base_batch_size=2048)
