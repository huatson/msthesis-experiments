# msthesis-experiments
Experiments for my masters thesis

Every experiment is a YAML file

```
dataset_path: datasets/cifar10.py
model_path: models/mlp.py
optimizer_path: optimizers/adamdef.py
train_path: train/train.py
```

* **dataset** contains
    * `inputs(eval_data, data_dir, batch_size)` and
    * `distorted_inputs(ata_dir=DATA_DIR, batch_size=128)` and
    * a dict `meta` which contains `n_classes`
* **model** contains `inference(images, dataset_meta)`
* **optimizer** contains `train(total_loss, global_step)`
* **train** contains `train(data, model, optimizer)`