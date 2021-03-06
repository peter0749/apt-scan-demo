from __future__ import unicode_literals
import os
import numpy as np
from django.db import models
import cv2
from .postprocess import find_corner_condidate 
from .unwrap import robust_unwarp
from PIL import Image
import tensorflow as tf
import keras
from keras.models import load_model

keras.backend.clear_session()
tfconfig = tf.ConfigProto()
tfconfig.gpu_options.allow_growth = True
tfsession = tf.Session(config=tfconfig)
keras.backend.set_session(tfsession)
model = load_model('./model.h5', custom_objects={'bce_dice_coef':keras.losses.binary_crossentropy, 'focal_loss': keras.losses.binary_crossentropy, 'mean_iou': keras.losses.binary_crossentropy})
# model.compile(loss='mse', optimizer='sgd')
graph = tf.get_default_graph()
input_h, input_w = model.input_shape[1:3]
output_h, output_w = model.output_shape[1:3]

class IMG(models.Model):
    img = models.ImageField()
    def __init__(self, *args, **kwargs):
        super(IMG, self).__init__(*args, **kwargs)
        self.original_filename = os.path.split(self.img.path)[-1]
        self.download_filename = os.path.splitext(self.original_filename)[0] + '_wrapped.jpg'
    
    def save(self):
        super(IMG, self).save() # if has same filename. change to different filename
        self.path = self.img.path
        t = os.path.splitext(self.img.path)
        self.wrap_path = t[0] + '_wrapped.jpg'
        self.url_path = self.img.url
        t = os.path.splitext(self.img.url)
        self.wrap_url_path = t[0] + '_wrapped.jpg'
        raw_image = Image.open(self.img)
        raw_image = raw_image.convert('RGB')
        raw_image = np.array(raw_image, dtype=np.uint8)
        img_r = np.clip(cv2.resize(raw_image, (input_w, input_h), interpolation=cv2.INTER_AREA).astype(np.float32)[np.newaxis,...] / 255.0, 0, 1)
        h, w = raw_image.shape[:2]
        with graph.as_default():
            label = model.predict(img_r, batch_size=1)[0]
        pts = find_corner_condidate((label>0.5).astype(np.uint8), 10) # format: (y, x)
        if len(pts)>0:
            pts[...,0] = np.clip(pts[...,0] * h / output_h, 0, h-1)
            pts[...,1] = np.clip(pts[...,1] * w / output_w, 0, w-1)
            raw_image = robust_unwarp(raw_image, pts)
        result = Image.fromarray(raw_image)
        result.save(self.wrap_path)