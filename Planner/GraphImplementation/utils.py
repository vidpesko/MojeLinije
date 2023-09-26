from re import split
import math
import datetime


class Helper:
    @staticmethod
    def fprint(l: list, out=None):
        if out is None:
            out = '{: <5} '
            out = out * len(l)
        print(out.format(*l))

    @staticmethod
    def split_line(line):
        return split(',(?=[^ ])', line)

    @staticmethod
    def line_2_dict(line, h_line):
        line = Helper.split_line(line.strip())
        h_line = Helper.split_line(h_line.strip())
        out_dict = {}
        for name, value in zip(h_line, line):
            out_dict[name] = value
        return out_dict

    @staticmethod
    def string_2_date(datum):
        return datetime.date(int(datum[:4]), int(datum[4:6]), int(datum[6:]))

    @staticmethod
    def to_minutes_past(time):
        # time = hh:mm:ss -> (hh*60) + mm + (ss/60)
        h, m, s = [int(x) for x in time.split(':')]
        return (h * 60) + m + (s / 60)

    @staticmethod
    def to_hh_mm(time: int, format=False):
        m = time % 60
        h = (time - m) / 60
        hf = int(h)
        mf = int(m)
        if h < 10:
            hf = f'0{int(h)}'
        if m < 10:
            mf = f'0{int(m)}'
        if format:
            return f'{hf}:{mf}'
        return h, m
    
    @staticmethod
    def haversine_formula(first_cord: set, second_cord: set):
        # a = sin²(φB - φA/2) + cos φA * cos φB * sin²(λB - λA/2)
        # c = 2 * atan2( √a, √(1−a) )
        # d = R ⋅ c
        EARTH_RADIUS = 6371000

        lat1, lon1 = first_cord
        lat2, lon2 = second_cord

        phi_1 = math.radians(lat1)
        phi_2 = math.radians(lat2)

        delta_phi = math.radians(lat2 - lat1)
        delta_lambda = math.radians(lon2 - lon1)

        a = math.sin(delta_phi / 2.0) ** 2 + math.cos(phi_1) * math.cos(phi_2) * math.sin(delta_lambda / 2.0) ** 2
    
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        meters = EARTH_RADIUS * c  # output distance in meters
        km = meters / 1000.0  # output distance in kilometers

        return meters
        # return round(km, 3)
        # km = round(km, 3)