import json
import datetime
import subprocess
from pprint import pprint
from password import API_KEY
ZONE_ID = "3c3d16411c9bff6cf3100af4d25336f8"

def queryDate(startDate):
    endDate = startDate + datetime.timedelta(days=1)
    queryString = f'  \
            curl -X GET "https://api.cloudflare.com/client/v4/zones/{ZONE_ID}/dns_analytics/report?metrics=queryCount&since={startDate.strftime("%Y-%m-%d")}T00:00:00Z&until={endDate.strftime("%Y-%m-%d")}T00:00:00Z&limit=100000&time_delta=day" \
        -H "Content-Type:application/json" \
        -H "X-Auth-Key:{API_KEY}" \
        -H "X-Auth-Email:singaporezoo060@gmail.com" \
    '

    proc = subprocess.run(queryString, shell=True, capture_output=True)
    result = json.loads(proc.stdout)
    return result['result']['data'][0]['metrics'][0]

def getWeek():
    now = datetime.datetime.now()
    res = []
    for i in range(7):
        res.append(queryDate(now))
        now += datetime.timedelta(days=-1)
    return res[::-1]
