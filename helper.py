from datetime import timedelta

def get(dict, key, default=None):
    if key in dict: return dict[key]
    else: return default

def getfreeSpeed(w):
    if w.tags.get('maxspeed'): return float(w.tags.get('maxspeed'))/3.6
    if w.tags.get("railway") == "rail": return 27.77777777777778
    if w.tags.get("railway") == "light_rail": return 16.666666666666668
    if w.tags.get("railway") == "tram": return 13.88888888888889
    if w.tags.get("railway") == "subway": return 22.22222222222222
    if w.tags.get("highway") == "motorway": return 33.333333333333336
    if w.tags.get("highway") == "motorway_link": return 22.22222222222222
    if w.tags.get("highway") == "trunk": return 22.22222222222222
    if w.tags.get("highway") == "trunk_link": return 13.88888888888889
    if w.tags.get("highway") == "primary": return 22.22222222222222
    if w.tags.get("highway") == "primary_link": return 16.666666666666668
    if w.tags.get("highway") == "secondary": return 16.666666666666668
    if w.tags.get("highway") == "secondary_link": return 16.666666666666668
    if w.tags.get("highway") == "tertiary": return 12.5
    if w.tags.get("highway") == "tertiary_link": return 12.5
    if w.tags.get("highway") == "minor": return 12.5
    if w.tags.get("highway") == "unclassified": return 12.5
    if w.tags.get("highway") == "residential": return 8.333333333333334
    if w.tags.get("highway") == "service": return 4.166666666666667
    return 4.166666666666667

def getNLanes(w):
    if w.tags.get('lanes'): return float(w.tags.get('lanes'))
    if w.tags.get("highway") == "motorway": return 2.0
    return 1.0

def getCapacity(w):
    if w.tags.get("highway") == "motorway": return 2000.0
    if w.tags.get("highway") == "motorway_link": return 1500.0
    if w.tags.get("highway") == "trunk": return 2000.0
    if w.tags.get("highway") == "trunk_link": return 1500.0
    if w.tags.get("highway") == "primary": return 1500.0
    if w.tags.get("highway") == "primary_link": return 1500.0
    if w.tags.get("highway") == "secondary": return 1000.0
    if w.tags.get("highway") == "secondary_link": return 1000.0
    if w.tags.get("highway") == "tertiary": return 600.0
    if w.tags.get("highway") == "tertiary_link": return 600.0
    if w.tags.get("highway") == "minor": return 600.0
    if w.tags.get("highway") == "unclassified": return 600.0
    if w.tags.get("highway") == "residential": return 600.0
    if w.tags.get("highway") == "service": return 300.0
    if w.tags.get("highway") == "living_street": return 300.0
    else: return 999999

def forward(w):
    if w.tags.get("oneway") == '-1' or w.tags.get("access") == 'no':
        return False
    return True

def backwards(w):
    if w.tags.get("oneway") == 'no' or w.tags.get("oneway") == '-1':
        return True
    return False

def createElement(__xmlRoot__, __name__, __value__=None, __parent__=None, **kwargs):
    element = __xmlRoot__.createElement(__name__)
    for att, attVal in kwargs.items():
        element.setAttribute(att.replace("__",""), str(attVal))
    if __value__:
        element.appendChild(__xmlRoot__.createTextNode(__value__))
    if __parent__:
        __parent__.appendChild(element)
    
    return element

def parse_time(time_str):
    hours, minutes, seconds = map(int, time_str.split(':'))
    
    total_seconds = hours * 3600 + minutes * 60 + seconds

    return timedelta(seconds=total_seconds)

def fix_time(time_str):
    hours, minutes, seconds = map(int, time_str.split(':'))

    return f"{str(hours%24).zfill(2)}:{str(minutes).zfill(2)}:{str(seconds).zfill(2)}"