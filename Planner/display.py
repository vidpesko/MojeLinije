# Printing GTFS File contents in pretty way
import re
from datetime import date
import calendar


def split_line(line):
    return re.split(',(?=[^ ])', line)

def fprint(l: list, out=None):
    if out is None:
        out = '{: <5} '
        out = out * len(l)

    print(out.format(*l))

def line_2_dict(line, h_line):
    line = split_line(line.strip())
    h_line = split_line(h_line.strip())

    out_dict = {}
    for name, value in zip(h_line, line):
        out_dict[name] = value

    return out_dict

def get_lines(search, lines, start=False):
    search = str(search) + ','
    if not start:
        search = ',' + search

    out = []
    for line in lines:
        # print(search) 
        if ((search in line) and not start) or (line.startswith(search) and start):
            out.append(line.strip())
    return out


file_name = 'gtfs_copy/trips.txt'
file = open(file_name)
lines = file.readlines()

calendar_file = open('gtfs_copy/calendar.txt')
calendar_dates_file = open('gtfs_copy/calendar_dates.txt')
stop_times_file = open('gtfs_copy/stop_times.txt')
calendar_lines = calendar_file.readlines()
calendar_dates_lines = calendar_dates_file.readlines()
stop_times_lines = stop_times_file.readlines()

header_line = lines[0].strip()

print_format = '{: <10} {: <50} {: <40} {: <40}'

# fprint(header_line.split(','), out=print_format)

# for line in lines[:30]:
#     fprint(re.split(',(?=[^ ])', line))


# Printing shapes.txt
# for line in lines[1:]:
#     line = line.strip()
#     line = line_2_dict(line, header_line)

#     if line['shape_id'] == '30028':
#         print(line['shape_pt_lon'] + ',', line['shape_pt_lat'])
#     else:
#         # pri÷nt(line)
#         break


# Displaying all days for service id
service_id = 1630
schedule = get_lines(service_id, calendar_lines, start=True)[0]
schedule = line_2_dict(schedule, calendar_lines[0].strip())
exceptions = get_lines(service_id, calendar_dates_lines, start=True)
added_dates = []
removed_dates = []
if exceptions != []:
    for exc in exceptions:
        exc = line_2_dict(exc, calendar_dates_lines[0])
        datum = exc['date']
        exc_type = int(exc["exception_type"])
        d = date(int(datum[:4]), int(datum[4:6]), int(datum[6:]))
        added_dates.append(d) if exc_type == 1 else removed_dates.append(d)
        print(f'{d}, {d.strftime("%A")}; Exc value: {"Day added" if exc_type == 1 else "Day removed"}')

weekdays = list(map(lambda x: x.lower(), list(calendar.day_name)))
active_days = []
for index, day in enumerate(weekdays):
    active_days.append(int(schedule[day]))

print(active_days)
print(added_dates)
for month in range(1, 13):
    print(calendar.month_abbr[month])
    fprint(calendar.day_abbr)
    weeks = calendar.monthcalendar(2023, month)
    for week in weeks:
        for index, day in enumerate(week):
            day_date = date(2023, month, day) if day != 0 else 0
            if (active_days[index] != 1) or (day_date in removed_dates):
                week[index] = 'X'
            if day_date in added_dates:
                week[index] = day
        fprint(week)
    print()

# raise SystemExit(0)

# Getting all service days for route
route_id = 46478
trip_id = 89768

route_lines = get_lines(route_id, lines, start=True)
for line in route_lines:
    line = line_2_dict(line, header_line)

    # Servicee id for trip
    service_id = line['service_id']
    trip_id = line["trip_id"]

    print(f'TRIP with id: {trip_id} works on days with SERVICE_ID: {service_id}. ROUTE ID: {route_id}')
    # service = get_lines(service_id, calendar_lines, start=True)[0]
    # h_service = calendar_lines[0]
    # service = line_2_dict(service, h_service)
    # print('Usually it works on:')
    # print('Monday:', service['monday'])
    # print('Tue:', service['tuesday'])
    # print('Wed:', service['wednesday'])
    # print('thu:', service['thursday'])
    # print('fri:', service['friday'])
    # print('sat:', service['saturday'])
    # print('sun:', service['sunday'])

    # print('Expections:')
    # h_exc = calendar_dates_lines[0]
    # exceptions = get_lines(service_id, calendar_dates_lines, start=True)
    # # print(exceptions)
    # if exceptions != []:
    #     for exc in exceptions:
    #         exc = line_2_dict(exc, h_exc)
    #         datum = exc['date']
    #         d = date(int(datum[:4]), int(datum[4:6]), int(datum[6:]))
    #         print(f'{d}, {d.strftime("%A")}; Exc value: {"Day added" if exc["exception_type"] == 1 else "Day removed"}')

    print('At this days, this trip operates at this times:')
    h_stop = stop_times_lines[0]
    stop_times = get_lines(trip_id, stop_times_lines, start=True)
    stop_times = list(map(line_2_dict, stop_times, (h_stop,)*len(stop_times)))
    stop_times.sort(key=lambda x: int(x['stop_sequence']))
    for stop_time in stop_times:
        print(f'{stop_time["stop_sequence"]}: {stop_time["departure_time"]}, STOP ID: {stop_time["stop_id"]}')
    print()