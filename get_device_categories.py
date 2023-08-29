
import requests
import pandas as pd
import json

def get_device_categories(token, propertyCode=''):
 
    url = 'https://data.oceannetworks.ca/api/deviceCategories'
    parameters = {'method':'get',
                'token':token, 
                'propertyCode':propertyCode}
    
    response = requests.get(url,params=parameters)

    df =pd.DataFrame({})
    
    if (response.ok):
        deviceCategories = json.loads(str(response.content,'utf-8'))
        for deviceCategory in deviceCategories:
            df = pd.concat([df,pd.DataFrame(deviceCategory,index=[0])])
        return df
    else:
        if(response.status_code == 400):
            error = json.loads(str(response.content,'utf-8'))
            print(error) 
        else:
            print ('Error {} - {}'.format(response.status_code,response.reason))

            
