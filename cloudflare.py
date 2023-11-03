ZONE_ID = "3c3d16411c9bff6cf3100af4d25336f8"
from password import API_KEY

"""Cloudflare API code - example"""
# https://github.com/cloudflare/python-cloudflare

import os
import sys
import time
import datetime
import pytz

ZONE_ID = "3c3d16411c9bff6cf3100af4d25336f8"
sys.path.insert(0, os.path.abspath('..'))
import CloudFlare

def now_iso8601_time(h_delta):
    """Cloudflare API code - example"""

    t = time.time() - (h_delta * 3600)
    r = datetime.datetime.fromtimestamp(int(t), tz=pytz.timezone("UTC")).strftime('%Y-%m-%dT%H:%M:%SZ')
    return r

def main():
    """Cloudflare API code - example"""

    cf = CloudFlare.CloudFlare()

    # A minimal call with debug enabled
    cf = CloudFlare.CloudFlare(debug=True)

    # An authenticated call using an API Key
    cf = CloudFlare.CloudFlare(email='singaporezoo060@gmail.com', token=API_KEY)

    # grab the zone identifier
    params = {}
    try:
        zones = cf.zones.get(params=params)
    except CloudFlare.exceptions.CloudFlareAPIError as e:
        return None
        exit('/zones.get %d %s - api call failed' % (e, e))
    except Exception as e:
        return None
        exit('/zones - %s - api call failed' % (e))

    date_before = now_iso8601_time(0) # now
    date_after = now_iso8601_time(8 * 24) # 7 days worth

    query="""
      query {
        viewer {
            zones(filter: {zoneTag: "%s"} ) {
            httpRequests1dGroups(limit:40, filter:{date_lt: "%s", date_gt: "%s"}) {
              sum { countryMap { bytes, requests, clientCountryName } }
              dimensions { date }
            }
          }
        }
      }
    """ % (ZONE_ID, date_before[0:10], date_after[0:10]) # only use yyyy-mm-dd part for httpRequests1dGroups
    # query - always a post
    try:
        r = cf.graphql.post(data={'query':query})
    except CloudFlare.exceptions.CloudFlareAPIError as e:
        return None
        exit('/zones.get %d %s - api call failed' % (e, e))
    except Exception as e:
        return None
        exit('/zones - %s - api call failed' % (e))

    ## only one zone, so use zero'th element!
    zone_info = r['data']['viewer']['zones'][0]

    httpRequests1dGroups = zone_info['httpRequests1dGroups']
    result = {}

    for h in sorted(httpRequests1dGroups, key=lambda v: v['dimensions']['date']):
        tot = 0
        result_date = h['dimensions']['date']
        result_info = h['sum']['countryMap']
        for element in sorted(result_info, key=lambda v: -v['bytes']):
            tot += element['requests']
            #print("    %7d %7d %2s" % (element['bytes'], element['requests'], element['clientCountryName']))
        result[result_date] = tot
    return result

if __name__ == '__main__':
    print(main())
    exit(0)
