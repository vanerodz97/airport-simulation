def ll2px(geo_pos, corners, px_size):

    lat_length = abs(corners[0]["lat"] - corners[2]["lat"]) # vertical
    lng_length = abs(corners[1]["lng"] - corners[0]["lng"]) # horizontal

    orin_top = abs(geo_pos["lat"] - corners[0]["lat"])
    orin_left = abs(geo_pos["lng"] - corners[0]["lng"])

    pix_top = int(px_size * (orin_top / lat_length))
    pix_left = int(px_size * (orin_left / lng_length))

    return px_bound(pix_left, px_size), px_bound(pix_top, px_size)

def px_bound(px, size):
    return max(min(px, size), 0)

def str2time(s):

    from datetime import time
    hours = int(s[0:2])
    mins = int(s[2:4])

    return time(hours, mins)

def is_valid_geo_pos(geo_pos):
    lat = geo_pos["lat"]
    lng = geo_pos["lng"]
    if lat < -90 or lat > 90:
        return False
    if lng < -180 or lng > 180:
        return False
    return True

def get_seconds_after(t, dt):
    """
    Since time calculation only works on datetime (not time), so we first
    combine self.time with today, then get the time() part
    """
    from datetime import date, datetime, timedelta
    from clock import ClockException
    holder = datetime.combine(date.today(), t)
    res = (holder + timedelta(seconds = dt)).time()
    if res < t: # overflow
        raise ClockException("Overflow in time")
    return res

def get_seconds_before(t, dt):
    from datetime import date, datetime, timedelta
    from clock import ClockException
    holder = datetime.combine(date.today(), t)
    res = (holder - timedelta(seconds = dt)).time()
    if res > t: # overflow
        raise ClockException("Overflow in time")
    return res

def str2sha1(s):
    import hashlib
    return int(hashlib.sha1(s.encode('utf-8')).hexdigest(), 16)

def interpolate_geo(start, end, ratio):
    """
    Interpolation method
    """
    s_geo = start.geo_pos
    e_geo = end.geo_pos
    lat = s_geo["lat"] + (e_geo["lat"] - s_geo["lat"]) * ratio
    lng = s_geo["lng"] + (e_geo["lng"] - s_geo["lng"]) * ratio
    return {"lat": lat, "lng": lng}

def get_seconds(t):
    return (t.hour * 60 + t.minute) * 60 + t.second

def get_time_delta(t1, t2):
    m1 = t1.hour * 60 * 60 + t1.minute * 60 + t1.second
    m2 = t2.hour * 60 * 60 + t2.minute * 60 + t2.second
    return m1 - m2
