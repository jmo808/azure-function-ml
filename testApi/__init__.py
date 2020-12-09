import logging
import azure.functions as func
import pickle, os
import joblib
from io import BytesIO
from sklearn import linear_model
import hmac
import hashlib
import base64
import requests
import time
from datetime import datetime

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

def prepPayload(payload, loc_dict):
    loc_dict = joblib.load(loc_dict)
    payload['location'] = payload['location'].capitalize()
    payload['location'] = next(key for key, value in loc_dict.items() if value == payload['location'])
    return payload

def salesForecast(payload, lemonmodel, orangemodel):
    lemon_model = joblib.load(lemonmodel)
    orange_model = joblib.load(orangemodel)
    lemonForecast = lemon_model.predict([[payload['location'], 
        payload['temperature'], payload['leaflets'], payload['price']]])
    orangeForecast = orange_model.predict([[payload['location'], 
        payload['temperature'], payload['leaflets'], payload['price']]])
    return {'lemonforecast': int(round(lemonForecast.item(0), 0)), 
        'orangeforecast': int(round(orangeForecast.item(0), 0))}

def saveTelemetry(modelVer, payload, forecast, key, storageaccount, telemetrytable):
    payload['PartitionKey'] = modelVer
    payload['ModelName'] = 'lemonadeStandModel'
    rowkey = func.Context.invocation_id
    logging.info(f'{rowkey}')
    payload['RowKey'] = str(rowkey)
    payload.update(forecast)
    url = "https://"+storageaccount+".table.core.windows.net/"+telemetrytable
    date = getDate()
    stringtosign = date+"\n/"+storageaccount+"/"+telemetrytable
    auth = generateAuth(storageaccount, stringtosign, key)
    headers = {"Authorization": auth, "Date": date, \
        "Content-Type": "application/json", "x-ms-version": "2018-03-28", "DataServiceVersion":"3.0;NetFx"}
    res = requests.post(url, json=payload, headers=headers)
    return res.content

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
    lemonmodel = getBlob(key, modelVer, storageaccount, "lemonmodel")
    orangemodel = getBlob(key, modelVer, storageaccount, "orangemodel")
    loc_dict = getBlob(key, modelVer, storageaccount, "locdict")
    payload = prepPayload(req_body, loc_dict)
    forecast = salesForecast(payload, lemonmodel, orangemodel)
    saveTelemetry(modelVer, payload, forecast, key, storageaccount, telemetrytable)
    location = req_body.get('location')

    if location:
        return func.HttpResponse(f'{forecast}')
    else:
        return func.HttpResponse(
             "Please pass data in the request body",
             status_code=400
        )
