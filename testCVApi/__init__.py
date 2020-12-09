import logging
import azure.functions as func
from .processImage import processImage
from .predictCategory import predictCategory
import hmac
import hashlib
import base64
import requests
import time
import os
from datetime import datetime
from io import BytesIO

def getDate():
    date = datetime.utcnow()
    return date.strftime("%a, %d %b %Y %H:%M:%S GMT")

def generateAuth(storageaccount, stringtosign, key):
    encodedstring = bytes(stringtosign, 'utf-8')
    signature = hmac.new(key, msg=encodedstring, digestmod=hashlib.sha256).digest()
    signature = base64.b64encode(signature).decode()
    return "SharedKeyLite "+storageaccount+":"+signature

def getBlob(key, modelVer, storageaccount, modelname):
    url = "https://"+storageaccount+".blob.core.windows.net/"+modelname+"/"+modelVer
    date = getDate()
    stringtosign = "GET\n\n\n\nx-ms-date:"+date+"\nx-ms-version:2018-03-28\n/"+storageaccount+"/"+modelname+"/"+modelVer
    auth = generateAuth(storageaccount, stringtosign, key)
    header = {"Authorization": auth, "x-ms-date": date, "x-ms-version": "2018-03-28"}
    res = requests.get(url, headers=header)
    return BytesIO(res.content)

def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')
    key = base64.b64decode(os.environ.get('ModelStorageKey'))
    storageaccount = os.environ.get('ModelStorageAccount')
    telemetrytable = os.environ.get('TelemetryTable')
    try:
        modelVer = req.params.get('modelver')
        logging.info(f'{modelVer}')
    except ValueError:
        return func.HttpResponse(
            "Please specify a model version in the modelver query string. ie. ?modelver=2018-11-05",
            status_code=400
        )
    try:
        req_body = req.get_json()
    except ValueError:
            pass
    image = req_body.get('image')
    cachedModel = False
    if image:
        processedImage = processImage(image)
        img_dict = getBlob(key, modelVer, storageaccount, "imgdict")
        if os.path.isfile('./' + modelVer + '.h5'):
            logging.info('Cached model found')
            cachedModel = True
        if not cachedModel:
            imagemodel = getBlob(key, modelVer, storageaccount, "imagecat")
            with open(modelVer + '.h5', 'wb') as f:
                f.write(imagemodel.getvalue())
        prediction = predictCategory(processedImage, img_dict, modelVer)
        payload = {'category':prediction }
        return func.HttpResponse(f'{payload}')
    else:
        return func.HttpResponse(
             "Please pass a base64 encoded image in the request body",
             status_code=400
        )
