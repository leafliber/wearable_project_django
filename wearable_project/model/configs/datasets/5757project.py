# dataset settings
dataset_type = 'CustomDataset'

train_pipeline = [
    dict(type='LoadImageFromFile'),
    dict(type='RandomResizedCrop', scale=224),
    dict(type='RandomFlip', prob=0.5, direction='horizontal'),
    dict(type='Normalize',
         mean=[0.23202182125643492, 0.18557084207703067, 0.14717898248173095],
         std=[0.2131485252658748, 0.1914308857884069, 0.15286306891699644],
         to_rgb=True),
    dict(type='PackInputs'),
]

test_pipeline = [
    dict(type='LoadImageFromFile'),
    dict(type='ResizeEdge', scale=256, edge='short'),
    dict(type='CenterCrop', crop_size=224),
    dict(type='Normalize',
         mean=[0.23202182125643492, 0.18557084207703067, 0.14717898248173095],
         std=[0.2131485252658748, 0.1914308857884069, 0.15286306891699644],
         to_rgb=True),
    dict(type='PackInputs'),
]

train_dataloader = dict(
    batch_size=256,
    num_workers=5,
    dataset=dict(
        type=dataset_type,
        data_root=r'C:\Users\t_shi\Desktop\5757projectdata\dataimage.part01\dataimage\train',
        with_label=True,
        pipeline=train_pipeline),
    sampler=dict(type='DefaultSampler', shuffle=True),
)

val_dataloader = dict(
    batch_size=32,
    num_workers=5,
    dataset=dict(
        type=dataset_type,
        data_root=r'C:\Users\t_shi\Desktop\5757projectdata\dataimage.part01\dataimage\val',
        with_label=True,
        pipeline=test_pipeline),
    sampler=dict(type='DefaultSampler', shuffle=True),

    persistent_workers=False
)
val_evaluator = dict(type='Accuracy', topk=(1, ))

# If you want standard test, please manually configure the test dataset
test_dataloader = val_dataloader
test_evaluator = val_evaluator
