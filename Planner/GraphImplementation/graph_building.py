try:
    from .SECRET import NEO4J_AUTH, NEO4J_URI
    from .utils import Helper
except:
    from .SECRET import NEO4J_AUTH, NEO4J_URI
    from utils import Helper

from neo4j import GraphDatabase

import os
from tqdm import tqdm
import json


class GTFS:
    def __init__(self, folder) -> None:
        self.gtfs_folder = (folder + '/') if folder[-1] != '/' else folder
        self.open_files = {}

    def _open(self, file_name):
        self.open_files[file_name] = open(os.getcwd() + '/Planner/' + self.gtfs_folder + file_name)
        # self.open_files[file_name] = open(os.getcwd() + '/' + self.gtfs_folder + file_name)

    def get_all_lines(self, file_name, split=False):
        if file_name not in self.open_files:
            self._open(file_name)
            self.open_files[file_name + '_HEADER'] = self.open_files[file_name].readline().strip()

        if split:
            return [Helper.split_line(line.strip()) for line in self.open_files[file_name].readlines()]
        else:
            return [line.strip() for line in self.open_files[file_name].readlines()]

    def search_for_lines(self, lines, search, start=False, end=False):
        if (not end):
            search = str(search) + ','
        if (not start):
            search = ',' + search

        out = []
        for line in lines:
            if ((search in line) and (not start) and (not end)) or (line.startswith(search) and start) or (end and line.endswith(search)):
                out.append(line)
        return out

    def group_lines(self, lines, group_id_index, group_content_indexes):
        group = {}
        log = open(os.getcwd() + '/Planner/Cache/grouped_shapes2.json', 'w')
        for i, line in enumerate(tqdm(lines)):
            line = Helper.split_line(line)
            group_id = line[group_id_index]
            is_in_dict = group.get(group_id)
            
            if is_in_dict == None:
                start = True if group_id_index == 0 else False
                lines_with_group_id = self.search_for_lines(lines, group_id, start=start)
                lines_ = [Helper.split_line(l) for l in lines_with_group_id]
                lines_.sort(key=lambda x: int(x[-1]))
                lines__ = []
                for l in lines_:
                    lines__.append(f'{l[1]}-{l[2]}')
                group[group_id] = lines__
            
            # if i == 100000:
                # print('heelo')
                # json.dump(json.load(log).update(group), log)
            # group = {}

        json.dump(group, log)
        return group


class Neo4jDatabase:
    def __init__(self, db = 'ijppbus20230622') -> None:
        self.URI = NEO4J_URI
        self.AUTH = NEO4J_AUTH

        # self.use_database = 'neo4j'
        self.use_database = db
    
    def connect(self):
        with GraphDatabase.driver(self.URI, auth=self.AUTH) as driver:
            driver.verify_connectivity()
            self.driver = driver
            self.session = self.driver.session(database=self.use_database)
            print('Connected to:', self.use_database)
        return True

    def add_station(self, stop_id, stop_name, stop_lat, stop_lon):
        self.session.run('CREATE (station:BUS_STOP:STOP {name: $stop_name, stop_id: $stop_id, stop_lat: $stop_lat, stop_lon: $stop_lon})', stop_name=stop_name, stop_id=int(stop_id), stop_lat=float(stop_lat), stop_lon=float(stop_lon))


class GraphBuilding:
    def __init__(self, gtfs_folder, database) -> None:
        self.gtfs_folder = gtfs_folder
        self.gtfs = GTFS(self.gtfs_folder)

        self.EXCLUDE_AGENCY = 1161

        self.ROUTE_NAMES = {}


        self.database = Neo4jDatabase(db=database)
        self.database.connect()

    def add_stations(self, lines, add=True):
        stations = []
        if add:
            print('Adding stations:')
        for station in tqdm(lines):
            station_s = Helper.split_line(station)
            if add:
                self.database.add_station(*station_s)
            stations.append(Helper.line_2_dict(station, self.gtfs.open_files['stops.txt_HEADER']))
        return stations

    def shape_to_csv(self, shape_id, shape_lines):
        lines = self.gtfs.search_for_lines(shape_lines, shape_id, start=True)
        with open(str(shape_id) + '_shape.csv', 'w') as f:
            f.write('index, latitude, longitude\n')
            for i, line in enumerate(lines):
                lat, lon = Helper.split_line(line)[1:3]
                # f.write(f'{i}, {lat}, {lon}\n')
                print(f'{lat}, {lon}')


    def get_station_name(self, station_id, lines):
        return Helper.split_line(self.gtfs.search_for_lines(lines, str(station_id), start=True)[0])[1]
    
    def get_shape_id(self, trip_id):
        return Helper.split_line(self.gtfs.search_for_lines(self.trip_lines, str(trip_id))[0])[-1]

    def get_route_id(self, trip_id, lines):
        return Helper.split_line(self.gtfs.search_for_lines(lines, str(trip_id))[0])[0]
    
    def get_route_info(self, route_id, lines):
        return Helper.line_2_dict(self.gtfs.search_for_lines(lines, str(route_id), start=True)[0], self.gtfs.open_files['routes.txt_HEADER'])

    def get_dep_arr_time_for_neighbours(self, station_a_index, station_b_index, trip_id, stop_times_lines):
        trip_stops = [Helper.line_2_dict(stop, self.gtfs.open_files['stop_times.txt_HEADER']) for stop in self.gtfs.search_for_lines(stop_times_lines, trip_id, start=True)]
        trip_stops.sort(key=lambda x: int(x['stop_sequence']))
        # print(station_a_index, station_b_index, end=' ')
        a, b = trip_stops[station_a_index], trip_stops[station_b_index]
        return a['departure_time'], b['arrival_time']

    def get_all_times_between_two_neighbours_for_route(self, station_a_id, station_b_id, route_id, trips_for_route, stop_times_lines):
        times = []
        for trip_id in trips_for_route:
            stops_on_trip = self.get_stations_on_trip(trip_id, stop_times_lines, info=True)
            times.append(self.get_dep_arr_time_for_neighbours(station_a_id, station_b_id, trip_id, stop_times_lines))
        return times

    def get_trip_connections(self, trip_id, connections_dict, stop_times_lines):
        stations = self.get_stations_on_trip(trip_id, stop_times_lines, info=True)
        for i, station_a in enumerate(stations):
            if (i + 1) != len(stations):
                station_b = stations[i+1]
                dep = Helper.to_minutes_past(station_a['departure_time'])
                arr = Helper.to_minutes_past(station_b['arrival_time'])
                t = arr - dep
                con = (dep, arr, t, trip_id)
                try:
                    connections_dict[f'{station_a["stop_id"]}_{station_b["stop_id"]}'].append(con)
                except KeyError:
                    connections_dict[f'{station_a["stop_id"]}_{station_b["stop_id"]}'] = [con, ]

    def get_trips_for_day(self, day, cache_path='', load_cache='') -> dict:
        self.trip_lines = self.gtfs.get_all_lines('trips.txt')
        if load_cache != '':
            return open(load_cache).readlines()
        print('Getting trips for day:')
        schedule_lines = self.gtfs.get_all_lines('calendar.txt')
        exception_lines = self.gtfs.get_all_lines('calendar_dates.txt')
        datum = Helper.string_2_date(day)
        week_day = datum.strftime("%A").lower()

        # Output: {'route_id': ['trip_id', ...], 'route_id_2': ['', ...]}
        output = {}

        # 1. Getting all routes
        self.routes_lines = self.gtfs.get_all_lines('routes.txt')
        exclude_routes = [Helper.split_line(l)[0] for l in self.gtfs.search_for_lines(self.routes_lines, self.EXCLUDE_AGENCY)]
        for route in tqdm(self.routes_lines):
            # 2. Getting all trips for route
            route = Helper.line_2_dict(route, self.gtfs.open_files['routes.txt_HEADER'])
            if route['route_id'] not in exclude_routes:
                trips = self.gtfs.search_for_lines(self.trip_lines, route['route_id'], start=True)

                # print(f'Route with ID {route["route_id"]} has No. of trips: {len(trips)}')
                # print()
                for i, trip in enumerate(trips):
                    trip = Helper.line_2_dict(trip, self.gtfs.open_files['trips.txt_HEADER'])
                    does_work = False
                    # print(i+1)
                    # print(f'Trip with ID {trip["trip_id"]}')

                    # 3. Checking trip service days
                    service_id = trip['service_id']

                    # 3.a Checking in exceptions
                    exceptions_for_service = self.gtfs.search_for_lines(exception_lines, service_id, start=True)
                    found_exc = False

                    for exc in exceptions_for_service:
                        if Helper.split_line(exc)[1] == str(day):
                            # print(f'{exc=}')
                            if exc[-1] == '1':
                                does_work = True
                            found_exc = True
                            break
                    # # 3.b Checking in calendar
                    if not found_exc:
                        schedule = self.gtfs.search_for_lines(schedule_lines, service_id, start=True)[0]
                        schedule = Helper.line_2_dict(schedule, self.gtfs.open_files['calendar.txt_HEADER'])
                        does_work = True if schedule[week_day] == '1' else False
                        # print(f'Trip works on day {datum} ({week_day}): {works}')

                    if does_work:
                        try:
                            output[route['route_id']].append(trip['trip_id'])
                        except KeyError:
                            output[route['route_id']] = [trip['trip_id'], ]
        if cache_path != '':
            cache_file = open(cache_path, 'w')
            cache_file.writelines([out + '\n' for out in output])
            cache_file.close()

        return output

    def get_trips_through_station(self, station_id, available_trips, stop_times_lines):
        trips = self.gtfs.search_for_lines(stop_times_lines, str(station_id))
        return [Helper.line_2_dict(trip, self.gtfs.open_files['stop_times.txt_HEADER']) for trip in trips]

    def get_stations_on_trip(self, trip_id, stop_times_lines, info=False):
        stations = self.gtfs.search_for_lines(stop_times_lines, str(trip_id), start=True)
        stations = [Helper.line_2_dict(station, self.gtfs.open_files['stop_times.txt_HEADER']) for station in stations]
        stations.sort(key=lambda x: int(x['stop_sequence']))
        if info:
            return stations
        return [station['stop_id'] for station in stations]
    
    def get_route_name(self, route_id, stop_times_lines, stops_lines, trip_lines):
        name = self.ROUTE_NAMES.get(route_id)
        if name == None:
            trip_id = Helper.split_line(self.gtfs.search_for_lines(trip_lines, route_id, start=True)[0])[2]
            # print(trip_id)
            stops = self.get_stations_on_trip(trip_id, stop_times_lines)
            first_s = self.get_station_name(stops[0], stops_lines)
            last_s = self.get_station_name(stops[-1], stops_lines)
            name = f'{first_s}->{last_s}'

            self.ROUTE_NAMES[route_id] = name

        return name


    def get_neighbours(self, station_id, available_trips, times_lines, stop_lines):
        station_id = str(station_id)
        stop_times_lines = times_lines
        stops_lines = stop_lines

        neighbours = []

        # 1. Getting all lines through station
        trips_through_station = self.get_trips_through_station(station_id, available_trips, stop_times_lines)
        # 2. For trip that goes through station, get all stops on that trip
        for trip in trips_through_station:
            trip_id = trip['trip_id']
            stations_on_trip = self.get_stations_on_trip(trip_id, stop_times_lines)
            my_station_index = stations_on_trip.index(station_id)
            
            # Next on trip
            right_n = None
            # Prev on trip
            left_n = None
            if my_station_index == 0:
                right_n = stations_on_trip[1]
            elif my_station_index == (len(stations_on_trip) - 1):
                left_n = stations_on_trip[-1]
            else:
                left_n = stations_on_trip[my_station_index-1]
                right_n = stations_on_trip[my_station_index+1]

            if right_n is not None:
                next_neighbour = {'stop_time': Helper.to_minutes_past(trip['departure_time']), 'neighbour_id': right_n, 'trip_id': trip_id}
                neighbours.append(next_neighbour)
                if int(right_n) == 1165685:
                    print('TRIPSS', trip_id)
            # print(right_n)
            # print(f'Starting station: {self.get_station_name(stations_on_trip[0], stops_lines)}. Destination: {self.get_station_name(stations_on_trip[-1], stops_lines)}')
        
        return neighbours

    def get_trips_for_route(self, route_id, trip_lines):
        lines = [Helper.split_line(l)[2] for l in self.gtfs.search_for_lines(trip_lines, route_id, start=True)]
        return lines

    def get_shape_look_up_for_trip(self, station_a, station_b, trip_id):
        shape_id = int(self.get_shape_id(trip_id))
        lookup = f'{shape_id}_{station_a}_{station_b}'
        return lookup

    def build_bus(self, day):
        stop_times_lines = self.gtfs.get_all_lines('stop_times.txt')
        stop_lines = self.gtfs.get_all_lines('stops.txt')
        # id_look_up_file = open(os.getcwd() + '/Planner/Cache/identification_lookup.json')
        # id_look_up_file = json.loads(id_look_up_file.readlines()[0])
        self.add_stations(stop_lines, add=False)
        routes_for_day = self.get_trips_for_day(day)
        # trip_lines = self.gtfs.get_all_lines('trips.txt')
        # print(list(routes_for_day.keys())[1400:1500])
        # print(len(routes_for_day))
        # return
        for route, trips in tqdm(routes_for_day.items()):
            # ! Method:
            # ^ 1. Iterate through routes for day: for every route get all connections ('connections_from_a_to_b': [('dep_1', 'arr_1), (), ]). Than iterate through

            route_id = route
            route = self.get_route_info(route, self.routes_lines)
            route_name = self.get_route_name(route_id, stop_times_lines, stop_lines, self.trip_lines)

            # print(f'Working on route: {route["route_long_name"]}', trips)
            # print()

            # ? This dict contains all all times for every connection between stations
            connections = {}

            for trip_id in trips:
                self.get_trip_connections(trip_id, connections, stop_times_lines)

            for connection_name, times in connections.items():
                # times format: [(a_depart: min, b_arrive: min, travel_time: min), (), ...]
                t = times[0][2]

                # print(f'Current connection: {connection_name}')

                station_a, station_b = connection_name.split('_')

                # 1. Create inner nodes - route(R) and vehicle(V) node
                vehicle_id = route_id
                uni_node_name = f'{connection_name}_{route_id}'
                # print(f'Creating route and vehicle nodes: route_id {route_id}, uni_name {uni_node_name}')

                # ! TRYING SOMETHING
                # self.database.session.run('CREATE (:BUS_ROUTE {route_id: $route_id, node_name: $route_node_name, route_name: $route_name})', route_id=int(route_id), route_node_name=uni_node_name, route_name=route_name)
                # self.database.session.run('CREATE (:VEHICLE:VEHICLE_BUS {vehicle_id: $vehicle_id, node_name: $vehicle_node_name})', vehicle_id=int(vehicle_id), vehicle_node_name=uni_node_name)


                # 2. Match departing(S1), arriving(S2), route(R) and vehicle(V) nodes
                # 3. Connect: (S1) -> (R), (V) -> (S2)
                # print(f'Trying to match BUS_ROUTE: route_id {route_id}, uni_name {uni_node_name}, STOP_1: id {station_a}, STOP_2: id {station_b}')


                # self.database.session.run(
                #     '''
                #     MATCH (s1 {stop_id: $my_stop_id}), (s2 {stop_id: $stop_id}), (r:BUS_ROUTE {route_id: $route_id, node_name: $uni_name}), (v:VEHICLE_BUS {vehicle_id: $vehicle_id, node_name: $uni_name})
                #     CREATE (s1) -[:DISTANCE {distance: 1, travel_time: $travel_time}]-> (r)
                #     CREATE (v) -[:FEE {fee: 1}]-> (s2)
                #     ''',
                #     my_stop_id=int(station_a),
                #     stop_id=int(station_b),
                #     route_id=int(route_id),
                #     vehicle_id=int(vehicle_id),
                #     travel_time=t,
                #     uni_name=uni_node_name
                # )


                # 4. Enumerate trips and add time connections
                for time in times:
                    # Getting look up for coordinates
                    shape_lookup = self.get_shape_look_up_for_trip(station_a, station_b, time[3])

                    self.database.session.run(
                    '''
                    MATCH (r:BUS_ROUTE {route_id: $route_id, node_name: $uni_name}), (v:VEHICLE_BUS {vehicle_id: $vehicle_id, node_name: $uni_name})
                    CREATE (r) -[:TIME {departure_time: $departure_time, arrival_time: $arrival_time, travel_time: $travel_time, trip_id: $trip_id, shape_look_up: $shape_look_up}]-> (v)
                    ''',
                    route_id=int(route_id),
                    uni_name=uni_node_name,
                    vehicle_id=int(vehicle_id),
                    departure_time=time[0],
                    arrival_time=time[1],
                    travel_time=time[2],
                    trip_id=time[3],
                    shape_look_up=shape_lookup
                )


class BuildCommonGraph:
    def __init__(self):
        self.graph = Neo4jDatabase(db='ijppcommon')
        self.graph.connect()

        self.gtfs = GTFS('gtfs_copy/')

    def add_stations(self):
        stop_times_lines = self.gtfs.get_all_lines('stop_times.txt')
        trips_lines = self.gtfs.get_all_lines('trips.txt')
        route_lines = self.gtfs.get_all_lines('routes.txt')
        # agency_lines = self.gtfs.get_all_lines('trips.txt')
        for s in tqdm(self.gtfs.get_all_lines('stops.txt')):
            s = Helper.line_2_dict(s, self.gtfs.open_files['stops.txt_HEADER'])
            # print(self.gtfs.get_all_lines('stop_times.txt'))
            trip_id = Helper.split_line(self.gtfs.search_for_lines(stop_times_lines, s['stop_id'])[0])[0]
            route_id = Helper.split_line(self.gtfs.search_for_lines(trips_lines, trip_id)[0])[0]
            agency_id = Helper.split_line(self.gtfs.search_for_lines(route_lines, route_id, start=True)[0])[1]
            bus_train = 'train' if agency_id == '1161' else 'bus'

            # Add
            if bus_train == 'bus':
                self.graph.session.run('CREATE (station:BUS_STOP:STOP {name: $stop_name, stop_id: $stop_id, stop_lat: $stop_lat, stop_lon: $stop_lon, bus_train: $bus_train})', stop_name=s['stop_name'], stop_id=int(s['stop_id']), stop_lat=float(s['stop_lat']), stop_lon=float(s['stop_lon']), bus_train=bus_train)
            else:
                self.graph.session.run('CREATE (station:TRAIN_STOP:STOP {name: $stop_name, stop_id: $stop_id, stop_lat: $stop_lat, stop_lon: $stop_lon, bus_train: $bus_train})', stop_name=s['stop_name'], stop_id=int(s['stop_id']), stop_lat=float(s['stop_lat']), stop_lon=float(s['stop_lon']), bus_train=bus_train)



    def build(self):
        self.add_stations()


if __name__ == '__main__':
    # common_builder = BuildCommonGraph()
    # common_builder.add_stations()
    builder = GraphBuilding('gtfs_copy/', 'ijppbus20230620')
    builder.shape_to_csv(32620, builder.gtfs.get_all_lines('shapes.txt')[::5])
    # builder.build_bus('20230620')
    # print(builder.get_route_name(17731, builder.gtfs.get_all_lines('stop_times.txt'), builder.gtfs.get_all_lines('stops.txt'), builder.gtfs.get_all_lines('trips.txt')))