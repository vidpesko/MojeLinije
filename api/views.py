import sys
sys.path.append("..")
from Planner.GraphImplementation.playing_with_algorithms_WORKING import d_algo, get_stop_name, get_stop_id
from Planner.GraphImplementation.neo4j_api import search_for_stations


from rest_framework.response import Response
from rest_framework.decorators import api_view

@api_view(['GET'])
def get_data(request):
    return Response({'lol': 10})

@api_view(['GET'])
def get_path(request):
    get = request.GET
    source_type = get['source_type']
    dest_type = get['dest_type']
    source = get['source']
    dest = get['destination']

    try:
        dep_time = int(get['dep_time'])
    except:
        print('dep-time is not int')
        dep_time = 100

    first_stop_name = ''
    second_stop_name = ''
    # If type is str, than convert that into station id
    if source_type == 'str':
        ids = get_stop_id(source)
        first_stop_name = source
        source = ids[0]
    if dest_type == 'str':
        ids = get_stop_id(dest)
        second_stop_name = dest
        dest = ids[0]

    stops = []
    source = int(source)
    dest = int(dest)

    routes = d_algo(source, dest, dep_time)
    for i in range(0, routes['stops_num']):
        stop = routes['route_stops'][i+1]
        stop_id = stop['stop_id']

        if i < (routes['stops_num'] - 1):
            connection = routes['route_connections'][f'{i+1}-{i+2}']
            stop_name = connection['station_a']
        else:
            stop_name = connection['station_b']

        stops.append({'stop_id': stop_id, 'transfer': stop['transfer'], 'stop_name': stop_name})

    # ? Making route_name
    connections_values = list(routes['route_connections'].values())
    if first_stop_name == '':
        first_stop_name = connections_values[0]['station_a']
    if second_stop_name == '':
        second_stop_name = connections_values[-1]['station_b']
    route_name = f'{first_stop_name} -> {second_stop_name}'

    output = {'routes': [
        {'name': route_name, 'stops': stops, 'transfers': routes['transfers'], 'departure_time': routes['start_time'], 'arrival_time': routes['arrival_time'], 'connections': routes['route_connections']},
    ]
    }
    return Response(output)


@api_view(['GET'])
def get_search_recommendations(request):
    get = request.GET
    query = get['query']
    how_many = get['num']

    results = search_for_stations(query, how_many)
    results = {'recommedations': results}

    return Response(results)
