from __future__ import unicode_literals
import os
import numpy as np
from django.db import models
from skimage.transform import resize
from .postprocess import find_corner_condidate 
from .unwrap import robust_unwarp
from PIL import Image
import tensorflow as tf
import keras
from keras.models import load_model

class IMG(models.Model):
    img = models.ImageField(upload_to='upload')
    def __init__(self, *args, **kwargs):
        super(IMG, self).__init__(*args, **kwargs)
        keras.backend.clear_session()
        self.tfconfig = tf.ConfigProto()
        self.tfconfig.gpu_options.allow_growth = True
        self.tfsession = tf.Session(config=self.tfconfig)
        keras.backend.set_session(self.tfsession)
        self.model = load_model('./model.h5', custom_objects={'bce_dice_coef':keras.losses.binary_crossentropy, 'focal_loss': keras.losses.binary_crossentropy, 'mean_iou': keras.losses.binary_crossentropy})
        self.model.compile(loss='mse', optimizer='sgd')
        self.input_h, self.input_w = self.model.input_shape[1:3]
        self.output_h, self.output_w = self.model.output_shape[1:3]
        self.path = self.img.path
    
    def save(self):
        super(IMG, self).save()
        raw_image = Image.open(self.img)
        raw_image = raw_image.convert('RGB')
        raw_image = np.array(raw_image, dtype=np.uint8)
        img_r = resize(raw_image, (self.input_h, self.input_w), preserve_range=True).astype(np.float32)[np.newaxis,...] / 255.0
        h, w = raw_image.shape[:2]
        label = self.model.predict(img_r, batch_size=1)[0]
        pts = find_corner_condidate((label>0.5).astype(np.uint8), 13) # format: (y, x)
        if len(pts)>0:
            pts[...,0] = np.clip(pts[...,0] * h / self.output_h, 0, h-1)
            pts[...,1] = np.clip(pts[...,1] * w / self.output_w, 0, w-1)
            raw_image = robust_unwarp(raw_image, pts)
        result = Image.fromarray(raw_image)
        result.save(os.path.splitext(self.img.path)[0] + '.jpg')
        self.path = self.img.path