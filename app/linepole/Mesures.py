# -*- coding: utf-8 -*-
import math
import subprocess
from itertools import repeat
from geopy import distance
from shapely.geometry import LineString, MultiPoint

r_earth = 6371.009


class AltitudeRetrievingError(Exception):
    def __init__(self, err, list):
        self.err = err
        self.list = list
        self.message = ("Error while getting elevation :", err, '\n arguments : {0}'.format(list))

def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]

def get_elevation(coordList):
    coordList = [list(i) for i in coordList]
    coordList_sliced = chunks(coordList, 100)
    elevation = []
    for coords_chunk in coordList_sliced:
        proc = subprocess.Popen(["curl", "-d", str(coords_chunk), "-XPOST", "-H", "Content-Type: application/json", \
                                 "https://elevation.racemap.com/api"], stdout=subprocess.PIPE, shell=True)
        (elevation_sliced, err) = proc.communicate()

        if err != None or b'Too Many Requests' in elevation_sliced:
            try:
                elevation += get_elevation(coords_chunk)
            except:
                print("Too many requests :", err, elevation_sliced)
                raise AltitudeRetrievingError(err, 'Too many requests')
        elif elevation_sliced == b'' or b'<' in elevation_sliced or b'>' in elevation_sliced:
            print("Error while getting elevation :", err, elevation)
            raise AltitudeRetrievingError(err, elevation_sliced)
        else:
            elevation += eval(elevation_sliced)

    return list(map(round,elevation, repeat(2)))

def addToCoord(coord, dx, dy, unit='m'):
    if unit == 'm':
        dx /= 1000
        dy /= 1000
        latitude, longitude, alt = coord
        new_latitude = latitude + (dy / r_earth) * (180 / math.pi)
        new_longitude = longitude + (dx / r_earth) * (180 / math.pi) / math.cos(latitude * math.pi / 180)
    return [round(new_latitude, 6), round(new_longitude,6), alt]

def get_distance_with_altitude(coordAlt1, coordAlt2, unit='m'):
    """
    Give the distance relative to altitude between two coordinates
    the altitude must be provided in the same unit as the one supplied (default : m)
    :param coord1: tuple:(float:latitude, float:longitude, float:altitude)
    :param coord2: tuple:(float:latitude, float:longitude, float:altitude)
    :param unit: string:name of the returned unit i.e : "km", "miles", "m"
    :return: (distance, angle) in the selected unit and degrees
    """
    lat1, long1, alt1 = coordAlt1
    lat2, long2, alt2 = coordAlt2
    if alt1 == 0 or alt2 == 0:
        return distance.geodesic(coordAlt1[:-1], coordAlt2[:-1]).m, 0
    x_dist = eval('distance.geodesic((lat1,long1),(lat2, long2)).{0}'.format(unit))
    y_dist = abs(alt2 - alt1)
    hypothenus = math.sqrt(x_dist**2 + y_dist**2)
    angle = math.degrees(math.atan(y_dist / x_dist))
    return round(hypothenus, 3), round(angle, 3)


def get_xy_ground_distance(coord1, coord2, unit='m'):
    y_dist = distance.geodesic(coord1[:-1], (coord2[0],coord1[1])).m
    if coord2[0] < coord1[0]:
        y_dist *= -1
    x_dist = distance.geodesic(coord1[:-1], (coord1[0], coord2[1])).m
    if coord2[1] < coord1[1]:
        x_dist *= -1
    if x_dist < 0 or y_dist < 0:
        angle = math.atan2(y_dist, x_dist)
    elif x_dist == 0:
        return x_dist, y_dist, 0.0001
    else:
        angle = math.atan(y_dist / x_dist)

    return round(x_dist, 3), round(y_dist, 3), round(angle,3)

def get_subcoord_dist(coord1, coord2, space, unit='m'):
    """
    Give coordinates between two coordinates separated by the given distance
    :param coord1: float: first coord
    :param coord2: float: second coord
    :param space: distance in given unit (default meter)
    :param unit: string:name of the returned unit i.e : "km", "miles", "m"
    :return: a list of coordinates
    """
    dist_tot = distance.geodesic(coord1, coord2).m
    x_dist, y_dist, angle = get_xy_ground_distance(coord1,coord2, unit=unit)

    number = math.ceil(abs(dist_tot / space))

    if number <= 1:
        return [list(coord1), list(coord2)]

    line = LineString([coord1[:-1], coord2[:-1]])
    splitter = MultiPoint([line.interpolate((i / number), normalized=True) for i in range(1, number)])
    wkt = splitter.wkt.replace('MULTIPOINT','').replace('(','').replace(')','').split(',')
    coordlist_str = [point.replace(' ','',1).split(' ') for point in wkt]
    # ici on coupe à 7 décimales les coordonnées
    coordlist = [list(map(round,list(map(float, coord_str)), repeat(7))) for coord_str in coordlist_str]
    [coord.append(0.0) for coord in coordlist]

    coordlist.insert(0, list(coord1))
    coordlist.append(list(coord2))

    return coordlist


def get_angle_between_two_lines(coord1, coord2, coord3):
    _, _, angle1 = get_xy_ground_distance(coord1, coord2)
    _, _, angle2 = get_xy_ground_distance(coord2, coord3)
    return round(math.degrees(angle2) - math.degrees(angle1), 3)

def grad2deg(angle_in_grad):
    """
    Convert angle in grad in degree
    :param angle_in_grad: float
    :return: float angle in degree
    """
    return angle_in_grad*0.9


def deg2grad(angle_in_degrees):
    """
    Convert angle in degrees in grad
    :param angle_in_degrees: float
    :return: float angle in grad
    """
    return angle_in_degrees/0.9

def grad2rad(angle_in_grad):
    """
    Convert angle in grad in radians
    :param angle_in_grad: float
    :return: float angle in radians
    """
    return math.radians(grad2deg(angle_in_grad))

def rad2grad(angle_in_rad):
    """
    Convert angle in radians in grad
    :param angle_in_rad: float
    :return: float angle in radians
    """
    return deg2grad(math.degrees(angle_in_rad))

# if __name__ == "__main__":
#     #get_elevation(11.430555, -12.682673)
#     listTest = [[11.466135, -12.616524, 0],[11.489022, -12.538672, 0]]
#     start = [11.466135, -12.616524, 0]
#     print(coordinates_solver(50,start, listTest[1:]))
#     print(get_distance_with_altitude((11.447561, -12.672399, 1008),(11.446225,-12.672896,1052),unit='m'))
#     a = get_elevation([[11.447561, -12.672399],[11.446225,-12.672896]])
#     print(get_subcoord_dist((11.447561, -12.672399),(11.446225,-12.672896),5))