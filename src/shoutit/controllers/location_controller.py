import requests
from common.constants import DEFAULT_LOCATION
from shoutit.models import LocationIndex, GoogleLocation
from shoutit.utils import ip2location, error_logger


def location_from_ip(ip, use_google_geocode=False):
    result = ip2location.get_all(ip)
    if use_google_geocode:
        return get_google_geocode_response('%s,%s' % (result.latitude or 0, result.longitude or 0))
    location = {
        'latitude': round(result.latitude or 0, 6),
        'longitude': round(result.longitude or 0, 6),
        'country': result.country_short if result.country_short != '-' else '',
        'postal_code': result.zipcode if result.zipcode != '-' else '',
        'state': result.region if result.region != '-' else '',
        'city': result.city if result.city != '-' else '',
        'address': ''
    }
    return location


def location_from_latlng(lat, lon, ip=None):
    # 1 - search for saved locations ordered by distance
    indexed_locations = LocationIndex.search().sort({
        "_geo_distance": {
            "location": {
                'lat': lat,
                'lon': lon
            }, 'unit': 'km', 'order': 'asc'
        }
    }).execute()[:1]

    # 2 - check if there is results
    if indexed_locations:
        # 3 - check closest location, if closer than x km return its attributes
        closest_location = indexed_locations[0]
        if closest_location.meta['sort'][0] < 5.0:
            return closest_location.location_dict

    # 4 - else
    latlng = "%s,%s" % (lat, lon)
    return get_google_geocode_response(latlng, ip)


def get_google_geocode_response(latlng, ip=None):
    params = {
        'latlng': latlng,
        'language': "en"
    }
    response = None
    try:
        response = requests.get("https://maps.googleapis.com/maps/api/geocode/json", params).json()
        if response.get('status') != 'OK':
            raise Exception("Make sure you have a valid latlng param")
        return location_from_google_geocode_response(response)
    except Exception as e:
        error_logger.warn("Google geocoding failed", extra={'detail': str(e), 'latlng': latlng, 'ip': ip, 'geocode_response': response})
        try:
            return location_from_ip(ip)
        except Exception as e2:
            error_logger.warn("IP geocoding failed", extra={'detail': str(e2), 'latlng': latlng, 'ip': ip})
            return DEFAULT_LOCATION


def location_from_google_geocode_response(response):
    locality = ''
    postal_town = ''
    administrative_area_level_2 = ''
    administrative_area_level_1 = ''
    country = ''
    postal_code = ''

    results = response['results']
    first_result = results[0]
    address = first_result['formatted_address']
    for result in results:
        for component in result['address_components']:
            if 'locality' in component['types']:
                locality = component['long_name']

            elif 'postal_town' in component['types']:
                postal_town = component['long_name']

            elif 'administrative_area_level_2' in component['types']:
                administrative_area_level_2 = component['long_name']

            elif 'administrative_area_level_1' in component['types']:
                administrative_area_level_1 = component['long_name']

            elif 'country' in component['types']:
                country = component['short_name']

            elif 'postal_code' in component['types']:
                postal_code = component['long_name']

    location = {
        'latitude': round(float(first_result['geometry']['location']['lat']), 6),
        'longitude': round(float(first_result['geometry']['location']['lng']), 6),
        'country': country,
        'postal_code': postal_code,
        'state': administrative_area_level_1,
        'city': locality or postal_town or administrative_area_level_2 or administrative_area_level_1,
        'address': address
    }
    GoogleLocation.create(geocode_response=response, **location)
    return location
