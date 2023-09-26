try:
    from .graph_building import Neo4jDatabase
except:
    from graph_building import Neo4jDatabase

import json
import os


# Setting up Neo4j database
def connect():
    driver = Neo4jDatabase(db='ijppcommon')
    driver.connect()
    return driver


driver = connect()


def get_stations(driver):
    result = driver.session.run(
        '''
        MATCH (n:STOP) RETURN n
        '''
    )
    return result.data()

def group_stations(stations: dict):
    grouped_stations = {}
    for station in stations:
        station = station['n']
        try:
            grouped_stations[station['name']].append(station)
        except:
            grouped_stations[station['name']] = [station, ]
    
    return grouped_stations

def search_for_stations(query, num):
    results = driver.session.run(
        f'''
        MATCH (n:STOP)
        WHERE n.name CONTAINS "{query}"
        RETURN n LIMIT {num}
        '''
    )

    return [n['n']['name'] for n in results.data()]


# d = connect()
# stations = get_stations(d)
# group_stations(stations)

# f = open('/'.join(os.getcwd().split('/')[:-2]) + '/static/map_assets/GeoJson/ijpp_stations_new.json')
# j = json.load(f)

# i = 0
# for feature in j['features']:
#     if feature['properties']['stop_name'] == 'Preba&#269;evo':
#         i += 1
#         print(feature)
#         print(i)