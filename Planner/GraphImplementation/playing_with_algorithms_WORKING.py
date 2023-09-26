# This Python file uses the following encoding: utf-8

try:
    from graph_building import Neo4jDatabase, GTFS
    from data_structures_WORKING import PriorityQueue
    from utils import Helper
except:
    from .graph_building import Neo4jDatabase, GTFS
    from .data_structures_WORKING import PriorityQueue
    from .utils import Helper


import time
import sys
import os
import json

sys.setrecursionlimit(1000000000)


start_id = 1121307
start_time = 100

target_id = 1122692

f = open(os.getcwd() + '/Planner/Cache/grouped_shapes_final_really.json')
j = json.loads(f.readlines()[0])

# Setting up Neo4j database
driver = Neo4jDatabase(db='ijppbus20230620')
driver.connect()


def get_stop_name(stop_id):
    result = driver.session.run(
        """
        MATCH (s:STOP {stop_id: $stop_id})
        RETURN s.name AS name
        """,
        stop_id=stop_id
    )
    return result.single()['name']

def get_stop_id(stop_name):
    result = driver.session.run(
        """
        MATCH (s:STOP {name: $stop_name})
        RETURN s.stop_id AS id
        """,
        stop_name=stop_name
    )
    ids = [r.data()['id'] for r in list(result)]
    return ids


# * This function should return something like this [(stop_id_1, travel_time_to), ...]
# ! For now it returns for every neighbouring stop only one connection which is closest to min dep time
def get_neighbours(from_id, dep_time=0):
    # print('Getting n for from', from_id, 'at', dep_time)
    """
    Return an iterator that yields (name, weight) of all the neighboring stops. Travel time should be used as weight.
    """
    result = driver.session.run(
        """
        WITH $min_dep as minDepTime
        MATCH (s1 {stop_id: $from_id}) -[:DISTANCE]-> (x) -[t:TIME]-> (x2) -[:FEE]-> (s2)
        WHERE t.departure_time >= minDepTime
        RETURN s2.stop_id AS s2_id, s2.name AS s2_name, x.route_id AS route_id, t.departure_time AS depart_from_station_a, t.arrival_time AS arrive_to_station_b, t.travel_time AS travel_time, t.shape_look_up AS shape_lookup
        ORDER BY depart_from_station_a
        """,
        min_dep=dep_time,
        from_id=from_id
    )
    stop_ids = []
    output = []
    for r in result:
        if r['s2_id'] not in stop_ids:
            stop_ids.append(r['s2_id'])
            output.append((r['s2_id'], r['travel_time'], r['arrive_to_station_b'], r['depart_from_station_a'], r['route_id'], r['shape_lookup']))
    return output

# First problem: Get path from stop 1: name=Kokrica, stop_id=1121234, to stop 2: name=Kranj Gorenjska oblačila, stop_id=1121245

# Dijkstra Algorithm Implementation on Shortest Arrival Problem - start at some dep time and arrive as quick you can

def get_lookup_number(trip):
    result = driver.session.run(
        """
        MATCH (:BUS_ROUTE) -[n {trip_id: $trip_id}]-> (:VEHICLE)
        RETURN n.shape_look_up AS lookup
        """,
        trip_id=trip
    )
    return result.single()['lookup']

def get_coordinates_from_lookup(look_up, grouped_shapes_file):
    return grouped_shapes_file[look_up]

def get_coordinates_between_stations(look_up: str, grouped_shapes_file):
    if look_up == 'not':
        # print('not')
        return []
    shape_id, inner_lookup = look_up.split('_', maxsplit=1)
    inner_lookup = [int(i) for i in inner_lookup.split('_')]
    inner_lookup.sort()
    inner_lookup = str(inner_lookup[0]) + '_' + str(inner_lookup[1])

    # print('Lookup:', look_up, shape_id, inner_lookup)
    return grouped_shapes_file[shape_id][inner_lookup]

# TODO : return dep_t and arr_t


def prepare_output(nodes):
    # ? Process of getting no of transfers, dep_t, arr_t,...
    output = {
        'transfers': 0,
        'start_time': '00:00:00',
        'arrival_time': '00:00:00',
        'stops_num': 0,
        'route_stops': {
            # 1: {
            #     'stop_name': ''
            # },
            # 2: {
            #     'stop_name': ''
            # }
        },
        'route_connections': {
            # '1-2': {
            #     'departure_time': '00:00',
            #     'arrival_time': '00:00',
            #     'transfer': False,
            #     'coordinates': [],
            # },
        },
    }

    output['start_time'] = Helper.to_hh_mm(nodes[0][1], format=True)
    output['arrival_time'] = Helper.to_hh_mm(nodes[-1][1], format=True)
    transfers = 0
    l = len(nodes)
    output['stops_num'] = l

    # nodes values = stop_id, arrival_to_this_stop, on_which_route_does_arr_to_this_stop
    i = 0
    while i < (l-1):
        a_node = nodes[i]
        route_to_a = a_node[-2]
        a_node_id = a_node[0]
        a_node_name = get_stop_name(a_node_id)
        output['route_stops'][i+1] = {
            'stop_id': a_node_id,
        }

        b_node = nodes[i + 1]
        route_to_b = b_node[-2]
        b_node_id = b_node[0]
        b_node_name = get_stop_name(b_node_id)
        output['route_stops'][i+2] = {
            'stop_id': b_node_id,
            'transfer': False
        }

        # Check for transfer
        try:
            shape_lookup_from_b_to_c = b_node[-1]

            if i == 0:
                shape_lookup_from_a_to_b = a_node[-1]
                shape_lookup_from_b_to_c = shape_lookup_from_a_to_b

            coordinates = get_coordinates_between_stations(shape_lookup_from_b_to_c, j)

            use_every_nth_coord = 5

            first_cord = coordinates[0]
            last_cord = coordinates[-1]
            coordinates = coordinates[1:-1:use_every_nth_coord]
            coordinates = [first_cord, *coordinates, last_cord]
            # print(coordinates[0], coordinates[-1])
            # print()
            # print(len(coordinates))
            # coordinates = get_coordinates_from_lookup(b_node[-1], j)
        except Exception as e:
            # print(a_node, b_node)
            # print(e)
            coordinates = []
            pass
        if route_to_a == 0:
            output['route_stops'][i+1]['transfer'] = False
            # coordinates = get_coordinates_between_stations('', '', route_to_b)
        elif route_to_a != route_to_b:
            transfers += 1
            # Transfer happend on a station
            output['route_stops'][i+1]['transfer'] = True
        else:
            output['route_stops'][i+1]['transfer'] = False

        depart_from_a = b_node[2]
        arrive_to_b = b_node[1]

        output['route_connections'][f'{i+1}-{i+2}'] = {
            'station_a': a_node_name,
            'station_b': b_node_name,
            'departure_time': depart_from_a,
            'arrival_time': arrive_to_b,
            'route': route_to_b,
            'coordinates': coordinates,
        }
        i += 1
    
    output['transfers'] = transfers

    return output


def d_algo(start_n, end_n, time_at_start_n, visited=None, visited_ids=None, distances=None, cost_to_start_node=0, full_start_n=None, _start_n=None, _target_n=None, helper_queue=None):
    # ? About time_at_start_n: when looking for connections from start_n, departure time has to be later that time_at_start_n -> this is the arrival time at that station

    if start_n == end_n:
        # ! Backtracing
        # print('Started at:', start_id)
        # print('Ended at:', target_id)
        
        nodes = []
        end_dep_time = full_start_n[0]
        end_dep_from_a = 0
        final_route = full_start_n[3]
        prev_n = full_start_n[-2]
        final_prev_n = prev_n
        shape_lookup = full_start_n[-3]
        final_lookup = shape_lookup
        start = visited[0]
        # print(visited)
        # print(prev_n, start)
        # print(visited)

        # ! OPTIMISATION WELCOME
        while True:
            for node in visited:
                current_node = node[-1]
                if current_node == prev_n:
                    prev_dep_t = node[0]
                    prev_dep_from_a = node[-4]
                    route_id = node[3]
                    nodes.append((prev_n, prev_dep_t, prev_dep_from_a, route_id, shape_lookup))
                    shape_lookup = node[-3]
                    prev_n = node[-2]

                    if current_node == final_prev_n:
                        end_dep_from_a = prev_dep_t
                    break
            if prev_n == start[-1]:
                break
            # nodes.append(prev_n)
            # prev_n = distances[prev_n][1]
            # if prev_n == distances[prev_n][1]:
                # break

        # ! Data about start node
        start_n_dep_time = nodes[-1][2]
        start_n_shape_lookup = start[-3]
        # ? That zero t the end is for shape lookup from start node to first station
        nodes.append((_start_n, start_n_dep_time, start_n_dep_time, 'start_route', start_n_shape_lookup))
        # print(get_stop_name(start_id), '- start at this station:', Helper.to_hh_mm(start[0], format=True))
        # print('   O')
        # print('   |')
        # print('   v')
        # for id, dep_time, route_to_that_n in nodes[::-1]:
            # pass
            # print(id, get_stop_name(id), '- arrives to this station:', Helper.to_hh_mm(dep_time, format=True), 'on route', route_to_that_n)
            # print('   |')
            # print('   v')
        # print(get_stop_name(target_id), '- arrives to this station:', Helper.to_hh_mm(end_dep_time, format=True), 'on route', final_route)

        # ! Data about end node
        nodes.insert(0, (_target_n, end_dep_time, end_dep_from_a, final_route, 'not'))

        # print(cost_to_start_node)
        # print('Visited', len(visited), 'nodes')
        # print(nodes)

        return prepare_output(nodes[::-1])

    # ? First run
    if distances is None:
        distances = PriorityQueue()
        # Insert start node to queue with distance of 0
        distances.insert(start_n, 0, time_at_start_n, 0, start_n, 0, 'to_generate')
        # print(distances._queue)

        visited = []
        visited_ids = []
        # helper_queue = []
        _start_n = start_n
        _target_n = end_n

    # Cost to start_n
    current_cost = cost_to_start_node

    # All neighbors of current node
    # print(start_n)
    neighbours = get_neighbours(start_n, dep_time=time_at_start_n)
    # print(neighbours)
    # print('Neighbors are:', neighbours)
    # print()
    # print('Already visited:', [self.graph.nodes[x] for x in visited])
    for neighbour_id, cost_to, arrival_to_n, departure_from_start, route_id_to_that_n, shape_lookup in neighbours:
        # If node was not yet visited
        if neighbour_id not in visited_ids:
            # Check if node is already in priority queue
            # if it is, then check stored and calculated distances
            now_calculated_cost = current_cost + cost_to
            # print(departure_from_start)
            result = distances.change_priority_with_if(neighbour_id, arrival_to_n, departure_from_start, start_n, now_calculated_cost, route_id_to_that_n, shape_lookup, _start_n)

            # it it isn't, insert it into queue
            if result == -1:
                # print(neighbour_id)
                # print('Inserting', neighbour_id, 'to which it takes:', now_calculated_cost, 'and arrives at:', Helper.to_hh_mm(arrival_to_n, format=True), 'and departs from a at:', Helper.to_hh_mm(departure_from_start, format=True))
                distances.insert(neighbour_id, now_calculated_cost, arrival_to_n, departure_from_start, start_n, route_id_to_that_n, shape_lookup)
        # Else if node was already visited, I do not care about it
    # start_n is done. Remove from queue
    visited.append(distances.extract_lowest())
    visited_ids.append(start_n)

    # ? Choosing the next node to move on. Next node is first node in pq
    # ! ( arrival_to_node, index, cost_to_that_node, route_id, path_via, item/id )
    # Here, when you choose next node, also the start node lookup should be changed
    next_node = distances.get_lowest()
    time_at_start_n = next_node[0]
    next_node_id = next_node[-1]
    cost_to_next_node = next_node[2]

    try:
        if next_node[-2] == _start_n:
            # Changing starting node neighbour!
            lookup_to_n = next_node[-3]
            visited = distances.change_start_node_lookup(lookup_to_n, visited)
    except:
        pass

    # print('Next going to:', next_node_id, get_stop_name(next_node_id), cost_to_next_node)
    return d_algo(next_node_id, end_n, time_at_start_n, visited=visited, visited_ids=visited_ids, distances=distances, cost_to_start_node=cost_to_next_node, full_start_n=next_node , _start_n=_start_n, _target_n=_target_n)


if __name__ == '__main__':
    st = time.time()

    route = d_algo(start_id, target_id, 100)
    # print(route)
    # print(get_coordinates_between_stations('32620_1122697_1122692', j))

    # for key, s in route['route_connections'].items():
    #     if (key == '19-20'):
    #         # print(s['route'])
    #         print(s['coordinates'])
    #         for c in s['coordinates']:
    #             print(str(c['lat']) + ',', c['lng'])
    # print(Helper.haversine_formula((45.934593,14.655257), (46.41246,14.094548)))
    # print(get_neighbours(1129160))
    # d_algo(start_id, target_id)
    # print(dijkstra_algorithm(start_id, target_id))
    ft = time.time()
    print('Completed in:', ft - st)