try:
    from .utils import Helper
    from .graph_building import GTFS, GraphBuilding
except:
    from utils import Helper
    from graph_building import GTFS, GraphBuilding


import os
import json
from tqdm import tqdm


# Getting coordinates between two stations on trip:
# ? 1. Group trips that have same same coordinates: check all coordinates, watch out for same path but in reverse

gtfs = GTFS('/gtfs_copy')
# builder = GraphBuilding('/gtfs_copy', 'ijppbus20230621')
trips_lines = gtfs.get_all_lines('trips.txt')
shapes_lines = gtfs.get_all_lines('shapes.txt')
stop_lines = gtfs.get_all_lines('stops.txt')
stop_times_lines = gtfs.get_all_lines('stop_times.txt')


def get_shape_trips(shape_id, trip_lines):
    return [Helper.split_line(l)[2] for l in gtfs.search_for_lines(trip_lines, str(shape_id), end=True)]

def get_stations_on_trip(trip_id, stop_times_lines):
    stations = gtfs.search_for_lines(stop_times_lines, str(trip_id), start=True)
    # stations.sort(key=lambda x: int(x[-1]))
    # if info:
        # return stations
    return [Helper.split_line(station)[-2] for station in stations]

def join_stations(trip_ids, stop_times_lines):
    stations = set()
    for id in trip_ids:
        stations.update(get_stations_on_trip(id, stop_times_lines))
    # print(stations)
    return stations

def generate_grouped_shapes(shape_lines_):
    gtfs.group_lines(shape_lines_, 0, 1)

def check_for_same_shapes(shapes_lines_, trip_lines_):
    cache = open('Planner/Cache/grouped_shapes2.json')
    group = json.loads(cache.readlines() [0])

    compared_ids = {}
    for shape_id, content in group.items():
        # print(content)
        content = set(content)
        # trip_id = get_shape_trip(shape_id, trip_lines_)
        for shape_id_2, content_2 in group.items():
            if shape_id == shape_id_2:
                break
            if compared_ids.get(f'{shape_id_2}-{shape_id}') != None:
                break

            content_2 = set(content_2)
            if content_2 == content:
                print(shape_id, shape_id_2)
                compared_ids[f'{shape_id}-{shape_id_2}'] = True
            else:
                compared_ids[f'{shape_id}-{shape_id_2}'] = False

    print(compared_ids)


def get_closest_coordinate(station_id, station_pos, coordinates):
    closest = []
    for i, c in enumerate(coordinates):
        closest.append((Helper.haversine_formula(c, station_pos), i, station_id))
    closest.sort(key=lambda x: x[0])
    return closest[0]

def get_stations_on_shape(shape_id, stop_lines, trip_lines, stop_times_lines, shapes_cache='/Planner/Cache/grouped_shapes2.json', coordinates_=None):
    if coordinates_ is None:
        f = open(os.getcwd() + shapes_cache)
        coordinates_ = json.loads(f.readlines()[0])[str(shape_id)]
    coordinates = []
    updates = {str(shape_id): []}
    for c in coordinates_:
        c = c.split('-')
        c = [float(e) for e in c]
        coordinates.append(c)

    trip_ids = get_shape_trips(shape_id, trip_lines)
    # print(trip_ids)
    stations = join_stations(trip_ids, stop_times_lines)
    # print(stations)
    # print(get_stations_on_trip(87949, stop_times_lines))
    # stations_on_shape = builder.get_stations_on_trip(get_shape_trip(shape_id, trip_lines), stop_times_lines)
    to_update = []
    for station in stations:
        station_line = Helper.split_line(gtfs.search_for_lines(stop_lines, station, start=True)[0])
        station_pos = station_line[2:]
        station_pos = [float(c) for c in station_pos]
        station_coordinate = get_closest_coordinate(station, station_pos, coordinates)
        # print(station_coordinate)
        to_update.append(station_coordinate)
        # update = {'lat': station_coordinate[0], 'lng': station_coordinate[1], 'is_stop': False, 'stop_id': 0}

    for coordinate in coordinates:
        updates[str(shape_id)].append({'lat': coordinate[0], 'lng': coordinate[1], 'is_stop': False, 'stop_id': 0})

    for dist, index, station_id in to_update:
        updates[str(shape_id)][index]['is_stop'] = True
        updates[str(shape_id)][index]['stop_id'] = station_id

    return updates

def format_stations_on_shape(shape_id, coordinates):
    # coordinates = data[str(shape_id)]
    station_a = 0
    station_b = 0
    new_format = {}
    coords_between = []
    for coordinate in coordinates:
        coords_between.append(coordinate)
        if coordinate['is_stop'] and (station_a == 0):
            station_a = coordinate['stop_id']
        elif coordinate['is_stop'] and (station_b == 0):
            station_b = coordinate['stop_id']
            if int(station_a) < int(station_b):
                new_format[f'{station_a}_{station_b}'] = coords_between
            else:
                new_format[f'{station_b}_{station_a}'] = coords_between
            coords_between = [coordinate]
            station_a = station_b
            station_b = 0


    return {shape_id: new_format}

def generate_trip_ids_identification(trip_ids: list):
    id_dict = {}
    output = ''
    trip_ids.sort(key=lambda x: int(x))
    for id in trip_ids:
        output += str(id) + '_'
    for id in trip_ids:
        id_dict[id] = output
    return output, id_dict

def final_format_for_shape(shape_id, coordinates, trip_lines):
    final_format = {str(shape_id): {}}
    trip_ids = get_shape_trips(shape_id, trip_lines)
    identification, identification_dict = generate_trip_ids_identification(trip_ids)
    coordinates_updates = []
    updates_ = []
    for c in coordinates:
        updates_.append((c['lat'], c['lng']))
        if c['is_stop']:
            coordinates_updates.append(updates_)
            updates_ = []
        # coordinates_updates.append()

    final_format[identification] = coordinates_updates
    return final_format


f = open(os.getcwd() + '/Planner/Cache/grouped_shapes_updated.json')
f2 = open(os.getcwd() + '/Planner/Cache/grouped_shapes_final_really.json')
# s1_s2 = final_format['87949_'][2]
updates = {}
identification_dict = {}
for shape_id, coordinates in tqdm(json.loads(f.readlines()[0]).items()):
    update = format_stations_on_shape(shape_id, coordinates)
    # print(update['30028']['1120993_1120999'])
    print(update)
    break
    updates.update(update)
    # final_format, id_dict = final_format_for_shape(shape_id, coordinates, trips_lines)
    # updates.update(final_format)
    # identification_dict.update(id_dict)
exit()
w = open(os.getcwd() + '/Planner/Cache/grouped_shapes_final_really.json', 'w')
# w2 = open(os.getcwd() + '/Planner/Cache/identification_lookup.json', 'w')
json.dump(updates, w)
# json.dump(identification_dict, w2)

# ! Caching grouped shapes
f = open(os.getcwd() + '/Planner/Cache/grouped_shapes_final_really.json')
json_f = json.load(f)
# print(len([f'{x["lat"]}, {x["lng"]}' for x in json_f['32620_1122697_1122692']]))
for i, c in enumerate(json_f['32620']['1122692_1122697']):
    lat = c['lat']
    lng = c['lng']
    print(str(i) + ', ' + str(lat) + ',', lng)