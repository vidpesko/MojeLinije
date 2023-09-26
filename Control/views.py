from django.http import HttpResponse

import sys
sys.path.append("..")
from Planner.GraphImplementation.neo4j_api import get_stations, group_stations, connect

from django.shortcuts import render

import json
import os
import copy

# Create your views here.
def view_functions(request):
    return render


def calculate_midpoint(coordinates):
    total_lat = 0
    total_lon = 0
    num_coordinates = len(coordinates)

    for lon, lat in coordinates:
        total_lat += lat
        total_lon += lon

    avg_lat = total_lat / num_coordinates
    avg_lon = total_lon / num_coordinates

    return avg_lon, avg_lat


def update_geojson_ijppp_stations(request):
    f = open('static/map_assets/GeoJson/ijpp_stations_new.json', 'w')

    outer_t = {"type": "FeatureCollection", "features": []}

    single_stop_t = '''
    {
        "type": "Feature",
        "properties": {
            "station_type": "single_stop",
            "stop_name": "stop_namer",
            "stop_id": "stop_idr",
            "bus_train": "bus_trainr"
        },
        "geometry": {
            "coordinates": [
            stop_lon, stop_lat
            ],
            "type": "Point"
        }
    },
    '''
    single_stop_t = {
        'type': 'Feature',
        'properties': {
            'station_type': 'single_stop',
            "stop_name": "",
            "stop_ids": "",
            "bus_train": ""
        },
        "geometry": {
            "coordinates": [],
            "type": "Point"
        }
    }


    multiple_stop_t = '''
    {
        "type": "Feature",
        "properties": {
            "station_type": "multiple_stops",
            "stop_name": "stop_namer",
            "stop_ids": stop_idsr,
            "bus_train": "bus_trainr"
        },
        "geometry": {
            "coordinates": coordinatesr,
            "type": "LineString"
        }
    },
    '''

    multiple_stop_t = {
        'type': 'Feature',
        'properties': {
            'station_type': 'multiple_stops',
            "stop_name": "",
            "stop_ids": [],
            "bus_train": ""
        },
        "geometry": {
            "coordinates": [],
            "type": "LineString"
        }
    }

    SPECIAL_CHAR = [('š', '&#x161;'), ('č', '&#269;'), ('ž', '&#382;'), ('Š', '&#352;'), ('Ž', '&#381;'), ('Č', '&#268;'), ('"', '')]

    driver = connect()
    stations = group_stations(get_stations(driver))
    templated_stations = []
    for name, station in list(stations.items()):
        for org, nw in SPECIAL_CHAR:
            name = name.replace(org, nw)

        # Check if multiple stops
        if len(station) == 1:
            # Single stop
            station = station[0]

            template = copy.deepcopy(single_stop_t)

            template['properties']['stop_name'] = name
            template['properties']['stop_ids'] = station['stop_id']
            template['properties']['bus_train'] = station['bus_train']

            template['geometry']['coordinates'] = [station['stop_lat'], station['stop_lon']][::-1]

            templated_stations.append(template)

        else:
            # Multiple stops
            template = copy.deepcopy(multiple_stop_t)

            stop_ids = []
            coordinates = []

            for s in station:
                stop_ids.append(s['stop_id'])
                coordinates.append([s['stop_lat'], s['stop_lon']][::-1])

            # Get center of stations
            stations_midpoint = calculate_midpoint(coordinates)
            coordinates.append(stations_midpoint)

            template['properties']['stop_name'] = name
            template['properties']['stop_ids'] = stop_ids
            template['properties']['bus_train'] = station[0]['bus_train']

            template['geometry']['coordinates'] = coordinates
            templated_stations.append(template)

    outer_t['features'].extend(templated_stations)

    f.write(json.dumps(outer_t))
    f.close()

    return HttpResponse('hello')
