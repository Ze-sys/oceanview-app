import pandas as pd
from onc.onc import ONC

def get_device_locations(token, kwargs):
    onc = ONC(token) 
    deviceList = kwargs.get("devicelist")
    dateFrom = kwargs.get("dateFrom")
    dateTo = kwargs.get("dateTo")
    minLat = kwargs.get("minLat")
    minLon = kwargs.get("minLon")
    maxLat = kwargs.get("maxLat")
    maxLon = kwargs.get("maxLon")
    title = kwargs.get("title")

    count = 0
    locations = []
    # Loop through devices

    for device in deviceList:

        count += 1
        if device == 'RADCPTS':  # Use dataProductCode for ADCP (multiple frequencies)
            key = 'dataProductCode'
        else:
            key = 'deviceCategoryCode'

        # Identify and plot device locations
        for location in onc.getLocations(
                {key: device, 'dateFrom': dateFrom, 'dateTo': dateTo}):  # Main ONC function call
            if (location['lon'] != None) and (location['lat'] != None):

                if ((location['lon'] >= minLon) and (location['lon'] <= maxLon)) and (
                        (location['lat'] >= minLat) and (location['lat'] <= maxLat)):
                    locations.append(location)

    return pd.DataFrame(locations)
