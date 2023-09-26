from graph_building import Neo4jDatabase
from data_structures import PriorityQueue
from utils import Helper


import time
import sys

sys.setrecursionlimit(1000000000)


start_id = 1121307
start_cord = (46.249573,14.352859)

target_id = 1121194
end_cord = (46.27409,14.364189)


# Setting up Neo4j database
driver = Neo4jDatabase()
driver.connect()


def get_all_stops():
    result = driver.session.run(
        """
        MATCH (s:STOP)
        RETURN s.id AS stop_id
        """,
    )
    return list(result)

def get_stop_name(stop_id):
    result = driver.session.run(
        """
        MATCH (s:STOP {stop_id: $stop_id})
        RETURN s.name AS name
        """,
        stop_id=stop_id
    )
    return result.single()['name']

def get_stop_cord(stop_id):
    result = driver.session.run(
        """
        MATCH (s:STOP {stop_id: $stop_id})
        RETURN s.latitude AS lat, s.longitude AS lon
        """,
        stop_id=stop_id
    )
    r = result.single()
    return r['lat'], r['lon']

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
        RETURN s2.stop_id AS s2_id, s2.name AS s2_name, s2.latitude AS s2_lat, s2.longitude AS s2_lon, x.route_id AS route_id, t.departure_time AS depart_from_station_a, t.arrival_time AS arrive_to_station_b, t.travel_time AS travel_time
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
            output.append((r['s2_id'], r['travel_time'], r['arrive_to_station_b'], (r['s2_lat'], r['s2_lon'])))
    return output

# A Star Algorithm Implementation on Shortest Arrival Problem - start at some dep time and arrive as quick you can

def a_star_algo(start_n, end_n, time_at_start_n, visited=None, visited_ids=None, current_cord=None, distances=None, cost_to_start_node=0, full_start_n=None):
    # ? About time_at_start_n: when looking for connections from start_n, departure time has to be later that time_at_start_n -> this is the arrival time at that station

    if start_n == end_n:
        print('Les go')

        # ! Backtracing
        # print('Started at:', start_id)
        # print('Ended at:', target_id)
        
        nodes = []
        end_dep_time = full_start_n[2]
        prev_dep_t, prev_n = full_start_n[2:4]
        start = visited[0]
        # print(prev_n, start)
        # print(visited)
        while True:
            for node in visited:
                # print('here2')
                if node[-1] == prev_n:
                    prev_dep_t = node[2]
                    nodes.append((prev_n, prev_dep_t))
                    prev_n = node[3]
                    break
            if prev_n == start[-1]:
                break

            # nodes.append(prev_n)
            # prev_n = distances[prev_n][1]
            # if prev_n == distances[prev_n][1]:
                # break

        print(get_stop_name(start_id), '- start at this station:', Helper.to_hh_mm(start[2], format=True))
        print('   O')
        print('   |')
        print('   v')
        for id, dep_time in nodes[::-1]:
            print(get_stop_name(id), '- arrives to this station:', Helper.to_hh_mm(dep_time, format=True), '- waiting time:')
            print('   |')
            print('   v')
        print(get_stop_name(target_id), '- arrives to this station:', Helper.to_hh_mm(end_dep_time, format=True))

        print(cost_to_start_node)
        return 'Hurray'

    # ? First run
    if distances is None:
        distances = PriorityQueue()
        # Insert start node to queue with distance of 0
        dist_to_end = Helper.haversine_formula(start_cord, end_cord)
        distances.insert(start_n, dist_to_end, time_at_start_n, start_n)

        visited = []
        visited_ids = []
        current_cord = start_cord

    # Cost to start_n
    current_cost = cost_to_start_node

    # All neighbors of current node
    # print(start_n)
    neighbours = get_neighbours(start_n, dep_time=time_at_start_n)
    # print(neighbours)
    # print('Neighbors are:', neighbours)
    # print()
    # print('Already visited:', [self.graph.nodes[x] for x in visited])
    for neighbour_id, cost_to, arrival_to_n, cordinates in neighbours:
        # cost_to = neighbour['travel_time']
        # neighbour_id = neighbour['s2_id']

        # If node was not yet visited
        if neighbour_id not in visited_ids:
            # Check if node is already in priority queue
            # if it is, then check stored and calculated distances
            dist_to_end = Helper.haversine_formula(cordinates, current_cord)
            now_calculated_cost = current_cost + cost_to + dist_to_end
            result = distances.change_priority_with_if(neighbour_id, now_calculated_cost, path_via)
            # it it isn't, insert it into queue
            if result == -1:
                # print('Inserting', neighbour_id, 'to which it takes:', now_calculated_cost, 'and arrives at:', Helper.to_hh_mm(arrival_to_n, format=True))
                distances.insert(neighbour_id, now_calculated_cost, arrival_to_n, start_n)
        # Else if node was already visited, I do not care about it
    # print()
    # start_n is done. Remove from queue
    visited.append(distances.extract_lowest())
    visited_ids.append(start_n)

    # ? Choosing the next node to move on. Next node is first node in pq
    # ! ( priority, index, dep_time, path_via, item/id )
    # print('Choosing next node from:', [n[::-3] for n in distances._queue])
    # print(time_at_start_n)
    next_node = distances.get_lowest()
    cost_to_next_node = next_node[0]
    next_node_id = next_node[-1]
    next_node_cord = get_stop_cord(next_node_id)
    time_at_start_n = next_node[2]

    # print('Next going to:', next_node_id, get_stop_name(next_node_id), cost_to_next_node)
    # print()

    # input()
    a_star_algo(next_node_id, end_n, time_at_start_n, visited=visited, visited_ids=visited_ids, current_cord=next_node_cord, distances=distances, cost_to_start_node=cost_to_next_node, full_start_n=next_node)


st = time.time()
a_star_algo(start_id, target_id, 0.0)
# print(get_neighbours(1129160))
# d_algo(start_id, target_id)
# print(dijkstra_algorithm(start_id, target_id))
ft = time.time()
print('Completed in:', ft - st)