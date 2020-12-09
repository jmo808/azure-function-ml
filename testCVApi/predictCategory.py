from keras.models import Sequential
from keras.layers import Conv2D, MaxPooling2D
from keras.layers import Activation, Dropout, Flatten, Dense
from keras.utils.np_utils import to_categorical
from keras.models import load_model
import joblib
import os

def predictCategory(processedImage, img_dict, modelVer):
    model = load_model(modelVer + '.h5')
    img_dict = joblib.load(img_dict)
    prediction = model.predict_classes(processedImage)[0]
    return img_dict[prediction]
