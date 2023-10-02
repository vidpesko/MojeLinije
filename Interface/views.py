import sys
sys.path.append("..")
from Planner.GraphImplementation.playing_with_algorithms_WORKING import d_algo, get_stop_name
from MojeLinije.SECRET import GOOGLE_MAPS_API_KEY

from django.shortcuts import render

# Create your views here.
def map_view(request):
    GOOGLE_MAPS_API_KEY = 'AIzaSyBBQnBS3aCO69fywAGZ1RJJIKc65uj_FAM'

    get = request.GET
    search_by_url = False
    try:
        start, end = get['source'], get['dest']
        start_t, end_t = get['source_type'], get['dest_type']
        search_by_url = True
        # stops = []
        # nodes = d_algo(int(get['source']), int(get['destination']), 100)
        # for id, time, route in nodes:
        #     stops.append({'stop_id':id, 'stop_name': get_stop_name(id), 'arr_to_this_stop': time, 'arr_on_route': route})
    except KeyError:
        stops = False
        start = end = start_t = end_t = None
    return render(request, 'Interface/map_view.html', {'GOOGLE_MAPS_API_KEY': GOOGLE_MAPS_API_KEY, 'search_by_url': search_by_url, 'source': start, 'dest': end, 'source_type': start_t, 'dest_type': end_t })