import requests
import base64
import json
import urllib.request as urllib

localUrl = 'http://localhost:7071/api/'
cloudUrl = ''
code = ""
image_url = 'https://uniqlo.scene7.com/is/image/UNIQLO/goods_67_400711?$pdp-medium$'

payload = {'location':'park', 'temperature':99, 'leaflets': 100, 'price':.5}
res = requests.post(cloudUrl + 'testApi?modelver=2018-11-05&code=' + code, json=payload)



def testMlApi(image_url, apiUrl):
    file = urllib.urlopen(image_url).read()
    base64_bytes = base64.encodestring(file)
    base64_string = base64_bytes.decode('utf-8')
    raw_data = {'image': base64_string}
    r = requests.post(apiUrl + 'testCVApi?modelver=2018-11-6&code=' + code, json=raw_data)
    return r.content.decode('utf-8')


testMlApi(image_url, cloudUrl)
