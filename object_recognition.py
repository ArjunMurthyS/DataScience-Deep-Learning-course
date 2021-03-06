# -*- coding: utf-8 -*-
"""Object-Recognition.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1r5Yz3oSV5fnzaJd-3H_mWx1zPwiYofir
"""

#%reload_ext autoreload
#%autoreload 2
# %matplotlib inline

!pip install --no-cache-dir -I pillow==4.1.1

import PIL.Image

from fastai.imports import *

from fastai.transforms import *
from fastai.conv_learner import *
from fastai.model import *
from fastai.dataset import *
from fastai.sgdr import *
from fastai.plots import *

PATH = "data/dogscats/"
sz=224

torch.cuda.is_available()

!ls $PATH

torch.backends.cudnn.enabled

os.listdir(PATH)

os.listdir(f'{PATH}valid')

files=os.listdir(f'{PATH}valid/cats')[:5]
files

img=plt.imread(f'{PATH}valid/cats/{files[0]}')
plt.imshow(img)

img.shape

img[:4,:4]

"""#Training the first model using pretrained model"""

arch=resnet34
data = ImageClassifierData.from_paths(PATH, tfms=tfms_from_model(arch, sz))
learn = ConvLearner.pretrained(arch, data, precompute=True)
learn.fit(0.01, 2)

data.val_y

data.classes

#prediction
log_pred=learn.predict()
log_pred.shape

log_pred[:10]

pred=np.argmax(log_pred,axis=1)
pred_d=np.exp(log_pred[:,1])

def random_mask(mask):
  return np.random.choice(np.where(mask)[0],4,replace=False)

def rand_correct(is_corr):
  return random_mask((pred==data.val_y)==is_corr)

def plot_val_with_title(idxs, title):
    imgs = np.stack([data.val_ds[x][0] for x in idxs])
    title_probs = [probs[x] for x in idxs]
    print(title)
    return plots(data.val_ds.denorm(imgs), rows=1, titles=title_probs)

def plots(ims, figsize=(12,6), rows=1, titles=None):
    f = plt.figure(figsize=figsize)
    for i in range(len(ims)):
        sp = f.add_subplot(rows, len(ims)//rows, i+1)
        sp.axis('Off')
        if titles is not None: sp.set_title(titles[i], fontsize=16)
        plt.imshow(ims[i])

def load_img_id(ds, idx): return np.array(Image.open(PATH+ds.fnames[idx]))

def register_extension(id, extension): Image.EXTENSION[extension.lower()] = id.upper()
Image.register_extension = register_extension
def register_extensions(id, extensions): 
  for extension in extensions: register_extension(id, extension)
Image.register_extensions = register_extensions

def plot_val_with_title(idxs, title):
    imgs = [load_img_id(data.val_ds,x) for x in idxs]
    title_probs = [pred_d[x] for x in idxs]
    print(title)
    return plots(imgs, rows=1, titles=title_probs, figsize=(16,8))

plot_val_with_title(rand_correct(True), "Correctly classified")

plot_val_with_title(rand_correct(False), "Incorrectly classified")

def most_by_mask(mask, mult):
    idxs = np.where(mask)[0]
    return idxs[np.argsort(mult * pred_d[idxs])[:4]]

def most_correct(y, is_correct):
    mult = -1 if (y==1)==is_correct else 1
    return most_by_mask(((pred == data.val_y)==is_correct) & (data.val_y == y), mult)

plot_val_with_title(most_correct(0, True), "Most correct cats")

plot_val_with_title(most_correct(1, True), "Most correct dogs")

plot_val_with_title(most_correct(0, False), "Most incorrect cats")

plot_val_with_title(most_correct(1, False), "Most incorrect dogs")

most_uncertain = np.argsort(np.abs(pred_d -0.5))[:4]
plot_val_with_title(most_uncertain, "Most uncertain predictions")

learn = ConvLearner.pretrained(arch, data, precompute=True)

lrf=learn.lr_find()                    #finds the learning rate

learn.sched.plot_lr()

learn.sched.plot()

#using transform time augmentation
tfms = tfms_from_model(resnet34, sz, aug_tfms=transforms_side_on, max_zoom=1.1)

def get_augs():
    data = ImageClassifierData.from_paths(PATH, bs=2, tfms=tfms, num_workers=1)
    x,_ = next(iter(data.aug_dl))
    return data.trn_ds.denorm(x)[1]

ims = np.stack([get_augs() for i in range(6)])

plots(ims, rows=2)

data = ImageClassifierData.from_paths(PATH, tfms=tfms)
learn = ConvLearner.pretrained(arch, data, precompute=True)

learn.fit(1e-2, 2)

learn.precompute=False

learn.fit(1e-2, 3, cycle_len=1)

learn.sched.plot_lr()

#save the last layer
learn.save('224_lastlayer')

#load the saved last layer
learn.load('224_lastlayer')

#unfreeze remaining layers
learn.unfreeze()

lr=np.array([1e-4,1e-3,1e-2])

learn.fit(lr, 3, cycle_len=1, cycle_mult=2)

learn.sched.plot_lr()

learn.save('224_all')

learn.load('224_all')

log_preds,y = learn.TTA()
probs = np.mean(np.exp(log_preds),0)

accuracy_np(probs, y)

preds = np.argmax(probs, axis=1)
probs = probs[:,1]

from sklearn.metrics import confusion_matrix
cm = confusion_matrix(y, preds)

plot_confusion_matrix(cm, data.classes)

plot_val_with_title(most_correct(0, False), "Most incorrect cats")

plot_val_with_title(most_correct(1, False), "Most incorrect dogs")