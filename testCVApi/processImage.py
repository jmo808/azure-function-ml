import numpy as np
from PIL import Image, ImageOps
import base64
import io

def resizeImage(img):
    desired_size = 128
    old_size = img.size
    ratio = float(desired_size)/max(old_size)
    new_size = tuple([int(x*ratio) for x in old_size])
    img = img.resize(new_size, Image.ANTIALIAS)
    new_im = Image.new("RGB", (desired_size, desired_size))
    new_im.paste(img, ((desired_size-new_size[0])//2,(desired_size-new_size[1])//2))
    return new_im

def normalize(arr):
    """
    Linear normalization
    http://en.wikipedia.org/wiki/Normalization_%28image_processing%29
    """
    arr = arr.astype('float')
    # Do not touch the alpha channel
    for i in range(3):
        minval = arr[...,i].min()
        maxval = arr[...,i].max()
        if minval != maxval:
            arr[...,i] -= minval
            arr[...,i] *= (255.0/(maxval-minval))
    return arr

def processImage(img):
    test_img = base64.b64decode(img)
    test_img = io.BytesIO(test_img)
    test_img = Image.open(test_img).convert('RGB')
    img_arr = np.array(test_img)
    new_img = Image.fromarray(normalize(img_arr).astype('uint8'),'RGB')
    new_arr = np.array(resizeImage(new_img)).astype('float32')/255.0
    new_arr = np.expand_dims(new_arr, axis=0)
    return new_arr