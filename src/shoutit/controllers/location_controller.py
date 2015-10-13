from django.core.exceptions import ValidationError
from django.db import IntegrityError
from elasticsearch import ElasticsearchException
import requests
from common.constants import DEFAULT_LOCATION
from shoutit.models import LocationIndex, GoogleLocation, PredefinedCity
from shoutit.utils import ip2location, error_logger


def from_ip(ip=None, use_location_index=False):
    try:
        if not ip:
            raise ValueError()
        result = ip2location.get_all(ip)
        if not (result and (result.latitude and result.longitude)):
            raise ValueError()
    except ValueError:
        return DEFAULT_LOCATION

    location = {
        'latitude': round(result.latitude, 6),
        'longitude': round(result.longitude, 6),
        'country': result.country_short if result.country_short != '-' else '',
        'postal_code': result.zipcode if result.zipcode != '-' else '',
        'state': result.region if result.region != '-' else '',
        'city': result.city if result.city != '-' else '',
        'address': ''
    }
    if use_location_index:
        location = from_location_index(result.latitude, result.longitude, ip_location=location)

    return location


def from_location_index(lat, lon, ip=None, ip_location=None):
    location = {}
    # 0 - if lat and lon are 0, use the ip to determine location
    if lat == 0 and lon == 0:
        location = from_ip(ip, use_location_index=True)

    # 1 - search for saved locations ordered by distance
    if not location:
        try:
            indexed_locations = LocationIndex.search().sort({
                "_geo_distance": {
                    "location": {
                        'lat': lat,
                        'lon': lon
                    }, 'unit': 'km', 'order': 'asc'
                }
            }).execute()[:1]
        except (ElasticsearchException, KeyError):
            error_logger.warn("Location Index searching failed", exc_info=True)
            if ip_location:
                location = ip_location
            elif ip:
                location = from_ip(ip)
            else:
                location = DEFAULT_LOCATION
        else:
            # 2 - check if there is results
            if indexed_locations:
                # 3 - check closest location, if closer than x km return its attributes
                closest_location = indexed_locations[0]
                if closest_location.meta['sort'][0] < 5.0:
                    location = closest_location.location_dict

    # 4 - else
    if not location:
        latlng = "%s,%s" % (lat, lon)
        location = from_google_geocode_response(latlng, ip, ip_location)

    # 5 - use original lat, lon if there were not 0 and we did not use DEFAULT_LOCATION
    if location != DEFAULT_LOCATION:
        if lat != 0.0:
            location['latitude'] = round(float(lat), 6)
        if lon != 0.0:
            location['longitude'] = round(float(lon), 6)
    return location


def from_google_geocode_response(latlng, ip=None, ip_location=None):
    params = {
        'latlng': latlng,
        'language': "en"
    }
    try:
        if latlng in ['0,0', '0.0,0.0', '0.0,0', '0,0.0']:
            raise ValueError("Ignoring 0,0 lat lng")
        geocode_response = requests.get("https://maps.googleapis.com/maps/api/geocode/json", params).json()
        if geocode_response.get('status') != 'OK':
            raise Exception("Make sure you have a valid latlng param")
        location = parse_google_geocode_response(geocode_response)
    except Exception:
        error_logger.warn("Google geocoding failed", exc_info=True)
        if ip_location:
            location = ip_location
        elif ip:
            location = from_ip(ip)
        else:
            location = DEFAULT_LOCATION
    return location


def parse_google_geocode_response(response):
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
        'state': administrative_area_level_1 or administrative_area_level_2 or postal_town or locality,
        'city': locality or postal_town or administrative_area_level_2 or administrative_area_level_1,
        'address': address
    }
    try:
        GoogleLocation.create(geocode_response=response, **location)
    except ValidationError:
        pass
    return location


def update_profile_location(profile, location, add_pc=True, notify=True):
    # determine whether the profile should send a notification about its location changes
    setattr(profile, 'notify', notify)
    update_object_location(profile, location)
    if profile.country and profile.city and add_pc:
        add_predefined_city(location)


def add_predefined_city(location):
    try:
        pc = PredefinedCity()
        update_object_location(pc, location)
    except (ValidationError, IntegrityError):
        pass


def update_object_location(obj, location, save=True):
    obj.latitude = location.get('latitude')
    obj.longitude = location.get('longitude')
    obj.country = location.get('country', '')
    obj.postal_code = location.get('postal_code', '')
    obj.state = location.get('state', '')
    obj.city = location.get('city', '')
    obj.address = location.get('address', '')
    if not save:
        return
    # if obj already exits, only save location attributes otherwise save everything
    if obj.created_at:
        obj.save(update_fields=['latitude', 'longitude', 'country', 'postal_code', 'state', 'city', 'address'])
    else:
        obj.save()
