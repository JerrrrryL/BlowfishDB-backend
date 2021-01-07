
import requests

API_ENDPOINT = "http://127.0.0.1:5000/"

def test_age():
    predicates = []
    for i in range(17, 91, 1):
        predicates.append(str(i) + "<=age and age <" + str((i + 1)))
    return predicates
predicates = test_age()
# data to be sent to api 
data = {
  "workload": predicates,
  "attrName": "age",
  "attrType": "Numerical",
  "thresholds": [1,2,3,4,5,6,7,8]
}
#[1,2,3,4,5,6,7,8,9,10]
  
# sending post request and saving response as response object 
r = requests.post(url = API_ENDPOINT, json = data) 

import json
with open('output.json','w') as fname:    
    json.dump(r.json(), fname, indent=4)
