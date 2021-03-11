# -*- coding: utf-8 -*-
from .Mesures import get_elevation as get_alt, get_distance_with_altitude as get_dist, get_subcoord_dist as sub_dist
from .Mesures import AltitudeRetrievingError
from .Mesures import get_angle_between_two_lines as get_angle
from .Mesures import get_xy_ground_distance as xy_dist
from .Mesures import deg2grad, addToCoord
from .KMLutils import openKML, random_color_gen, gen_placemark_from_Line
from itertools import repeat
from fastkml import kml, Document, Folder, Placemark, styles
from shapely.geometry import Point, LineString, Polygon
import pandas as pd
from numpy import array, transpose
from . import settings
from copy import deepcopy
import random
import math
from colour import Color

resolution = 25 #résolution pour déterminer l'altitude en metres
ns = '{http://www.opengis.net/kml/2.2}'

class KMLHandler(kml.KML):
    def __init__(self,kml_file):
        """
        A handle to manage the KML file input and augmented output
        :param kml_file: a KML file path structured like : Documents => (Folders =>) Placemarks
        :property outputdf: a pandas DataFrame which contain all the data
        :property ouputkml: a kml with the divided sections (need to be generated with .generateOutput fisrt)
        :property camelia: a pandas DataFrame structured for Camelia software
        """
        super().__init__()
        self.offset = False
        self.inputKML = openKML(kml_file)

        self.Documents = self._set_documents()
        self.Folders = self._set_folders(self.Documents)
        if self.Folders != None:
            self.Placemarks = self._set_placemarks(self.Folders)
        else:
            self.Placemarks = self._set_placemarks(self.Documents)

        self._set_dataframe()

    def __repr__(self):
        return self.outputkml.to_string(prettyprint=True)

    def __str__(self):
        return self.outputkml.to_string(prettyprint=True)

    def generatePoles(self):
        self._set_sections()

    def generateOutput(self):
        self.outputkml = self._get_output_kml()

    def generateOffset(self, offset, max_dist):
        """
        Generate parallel lines every offset until max_dist is reach
        number of line on each side is max_dist // offset
        :param offset: offset from the previous line in meter
        :type offset: float or int
        :param max_dist: maximum distance from the base line
        :type max_dist: float or int
        :return: kml content
        :rtype: str
        """
        settings.space_by_type['offset'] = 1000000
        self._set_sections(offset, max_dist)
        self.offset = True


    def _get_outputdf(self):
        """
        Generata an output dataframe ready to enter in kml
        :return: dataframe with every available info
        :rtype: pandas.DataFrame
        """
        keys = self.info_df['Trace'].values.tolist()
        frame = deepcopy([line.df for line in self.info_df['Line'].values.tolist()])
        for i in range(len(frame)):
            df = frame[i]
            num = list(range(len(df)))
            angle_gr = list(map(deg2grad,df['Angle Horizontal'].values))
            df.insert(0,'Number', ['s' + '-'.join(x) + 'gr' for x in zip(map(str,num),map(str,map(int,angle_gr)))])
            df.insert(1, 'Name', keys[i])
        return pd.concat(frame, keys=keys, join='inner', ignore_index=True)

    def _get_cameliadf(self):
        return cameliaDF(self.outputdf)

    def _set_documents(self):
        return list(self.inputKML.features())

    def _set_folders(self, upstream_features):
        for feature in upstream_features:
            if isinstance(list(feature.features())[0], Folder):
                return list(feature.features())
            else:
                return None

    def _set_placemarks(self, upstream_features):
        for feature in upstream_features:
            if isinstance(list(feature.features())[0], Placemark):
                return list(feature.features())
            else:
                return None

    def _set_dataframe(self):
        pmname = []
        pmcoords = []
        pmdesc = []
        for pm in self.Placemarks:
            if pm.geometry.geom_type == 'LineString':
                pmname1 = pm.name
                pmcoords1 = self._flip_longlat(pm.geometry.coords)
                if pm.description == None:
                    pmdesc1 = 'normal'
                else:
                    pmdesc1 = pm.description
            pmname.append(pmname1)
            pmcoords.append(pmcoords1)
            pmdesc.append(pmdesc1)

        info = {'Trace':pmname, 'Coordinates':pmcoords, 'Type':pmdesc}
        info_df = pd.DataFrame(info)
        self.info_df = info_df


    def _set_sections(self, offset=None, offset_max_dist=None):
        if 'custom' in settings.space_by_type.keys():
            func = lambda trace: Line(trace['Coordinates'], typekey='custom')
        elif 'offset' in settings.space_by_type.keys():
            self.offset = True
            func = lambda trace: Line(trace['Coordinates'], typekey='offset',
                                      offset=offset, offset_max_dist=offset_max_dist)
        else:
            func = lambda trace: Line(trace['Coordinates'],typekey=trace['Type'])
        self.info_df['Line'] = self.info_df.apply(func, axis=1)

        try:
            self._add_offset_to_df()
        except IndexError as e:
            #print(traceback.format_exc())
            print(e)
            pass

        outputs_list = []
        for i in range(len(self.info_df)):
            current_line = self.info_df.Line[i]
            outputs_list.append(self._output_coord(current_line))
        self.info_df['Outputs'] = outputs_list

    def _get_output_kml(self):
        outputkml = kml.KML()
        for doc in self.Documents:
            id = doc.id
            name = doc.name
            desc = doc.description
            outdoc = kml.Document(ns, id, name, desc)
            outputkml.append(outdoc)

            if isinstance(list(doc.features())[0], Placemark):
                out_nsfolders = self._setPlacemark_for_KML(doc.features())
                for out_nsfolder in out_nsfolders:
                    outdoc.append(out_nsfolder)
            else:
                for folder in doc.features():
                    id = folder.id
                    name = folder.name
                    desc = folder.description
                    outfolder = kml.Folder(ns, id, name, desc)
                    out_nsfolders = self._setPlacemark_for_KML(folder.features())
                    for out_nsfolder in out_nsfolders:
                        outfolder.append(out_nsfolder)
                    outdoc.append(outfolder)

        return outputkml

    def _setPlacemark_for_KML(self,upstream_feature):
        output_df = self.outputdf
        out_nsfolders = []
        for placemark in upstream_feature:
            id = placemark.id
            name = placemark.name
            desc = placemark.description
            # creating nested folder
            out_nsfolder = kml.Folder(ns, id, name, desc)
            # creating placemarks (points and LineString)
            Lines = self.info_df[self.info_df['Trace'].str.contains(name)]['Outputs'].to_list()
            line_names = self.info_df[self.info_df['Trace'].str.contains(name)]['Trace'].to_list()
            outplacemarks = gen_placemark_from_Line(Lines,ns,line_names)
            for pm in outplacemarks:
                out_nsfolder.append(pm)

            out_points_folder = kml.Folder(ns, id, name='Poteaux')
            if not self.offset:
                for Line in Lines:
                    for point in Line:
                        id = str(Line.index(point))
                        point_name = output_df[output_df['Name'].str.contains(placemark.name)]['Number'].to_list()
                        name = point_name[Line.index(point)]
                        desc = 'Electric Pole'
                        outpoint = kml.Placemark(ns, id, name, desc)
                        outpoint.geometry = Point(point)
                        out_points_folder.append(outpoint)
                out_nsfolder.append(out_points_folder)
            out_nsfolders.append(out_nsfolder)
                
        return out_nsfolders
    
    def _flip_longlat(self, coordTuple):
        outList = []
        for coord in coordTuple:
            outList.append(tuple([coord[1],coord[0],coord[2]]))
        return tuple(outList)


    def _output_coord(self, Line):
        return Line.df[['long','lat','alt']].values.tolist()

    def _add_offset_to_df(self):
        for index, row in self.info_df.iterrows():
            offset_lines = row.Line.offset_lines
            for line in offset_lines:
                list_of_coords = offset_lines[line].to_list()
                info = {'Trace': '_'.join([row.Trace, line]), 'Coordinates': [list_of_coords],
                        'Type': 'offset', 'Line': Line(list_of_coords, typekey='offset',
                                                       offset=None, offset_max_dist=None)}
                info_os = pd.DataFrame(info)
                self.info_df = self.info_df.append(info_os,ignore_index=True)

    outputdf = property(_get_outputdf)
    camelia = property(_get_cameliadf)

class cameliaDF(pd.DataFrame):
    def __init__(self,line_df):
        columns = ['Ligne', 'Type', 'Nom', 'Hauteur (m)', 'Altitude (m)', 'Angle de piquetagegr', 'Orientation supportgr',
                   'Fonction', 'Branchements', 'Nature', 'Structure', 'Classe', 'Ecart entre unifilaires (m)',
                   'Nature du sol', 'Coef. ks', 'Surimplantation (m)', 'Armement', 'Orientation armementgr',
                   "Décalage d'accrochage (m)", 'Isolateur', 'Équipement', 'Longueur de portée(m)']
        empty_column = ['NaN'] * len(line_df)
        ligne = [n for n in line_df.Name.to_list()]
        type = empty_column
        nom = [n for n in line_df.Number.to_list()]
        hauteur = empty_column
        altitude = list(line_df.alt.values)
        piquetage = list(deg2grad(line_df['Angle Horizontal'].values))
        orientation = empty_column
        fonction = empty_column
        branchement = empty_column
        nature = empty_column
        structure = empty_column
        classe = empty_column
        ecart = empty_column
        nature_sol = empty_column
        ks = empty_column
        surimplantation = empty_column
        armement = empty_column
        orientation_armement = empty_column
        decalage = empty_column
        isolateur = empty_column
        equipement = empty_column
        portee = list(line_df.dist_from_prev.values)
        data = transpose(array([ligne, type, nom, hauteur, altitude, piquetage, orientation, fonction, branchement, nature, structure, classe,
                ecart, nature_sol, ks, surimplantation, armement, orientation_armement, decalage, isolateur, equipement,
                portee]))
        super().__init__(data, columns=columns)



class LineSection:
    def __init__(self, coord1, coord2, typekey='normal', offset=None, offset_max_dist=None):
        """
        Object that represent a section of LineString between two coordinates
        :param coord1: (lat, long)
        :type coord1: tuple or list
        :param coord2: tuple or list:(lat, long)
        :type coord2: tuple or list
        :param typekey: define the space between the poles e.g :'city', 'roads', 'hill', 'custom'
        :type typekey: str
        :param offset: if the value is not None, the LineSection will be duplicate with an offset
        :type offset: float
        :param offset_max_dist: maximum distance of the offset option, allow to know the number of LineSection copies
        :type offset_max_dist: float
        """
        self.start, self.stop, self.type = list(map(round,coord1, repeat(7))),\
                                           list(map(round,coord2, repeat(7))), typekey
        if offset != None:
            self.df = pd.DataFrame(self._get_alt_profile(pole='n'), columns=['lat', 'long', 'alt', 'descr'])
            self.addOffset(offset, offset_max_dist)
        else:
            self.df = pd.DataFrame(self._get_alt_profile(pole='y'), columns=['lat', 'long', 'alt', 'descr'])
            self._set_prev_azi_angles()

    def __get__(self, instance, owner):
        return self.df

    def __getitem__(self, item):
        if isinstance(item, slice):
            return self.df.iloc[item]
        else:
            return self.df[self.df.index == item]

    def _get_alt_profile(self, pole='n'):
        "Slice the section to get elevation every ${space} meter"
        dist_evaluated, *_ = get_dist(list(self.start), list(self.stop))
        listCoord = sub_dist(self.start, self.stop, settings.space_by_type[self.type], unit='m')
        alt = get_alt([coord[:-1] for coord in listCoord])
        for i in range(len(alt)):
            listCoord[i][-1] = alt[i]
            if listCoord[i][:-1] == self.start[:-1]:
                listCoord[i].append('Start Point')
            elif listCoord[i][:-1] == self.stop[:-1]:
                listCoord[i].append('Stop Point')
            else:
                if pole == 'y':
                    listCoord[i].append('Pole')
                else:
                    listCoord[i].append('Altitude Profile')
        return listCoord

    def _get_pole_points(self):
        return self.df[self.df.descr == 'pole']

    def _get_total_dist(self, list_of_coordAlt=None):
        tot_dist = 0
        if list_of_coordAlt == None:
            list_of_coordAlt = self._get_list_of_coord()

        for i in range(len(list_of_coordAlt)-1):
            tot_dist += get_dist(list_of_coordAlt[i], list_of_coordAlt[i+1])[0]
        return tot_dist

    def _get_list_of_coord(self):
        return self.df[['lat','long','alt']].values.tolist()

    def distance_from_origine(self, coord):
        """
        :return the distance from the first point
        """
        index = self.df.loc[(self.df['lat'] == coord[0]) & (self.df['long'] == coord[1])].index.values[0]
        listCoordAlt = self.df[self.df.index <= index][['lat','long','alt']].values.tolist()
        return self._get_total_dist(listCoordAlt)


    def closest_coords(self, coord):
        """:return closest coordinates index"""
        list_of_coord = self.df[['lat','long']].values.tolist()
        tree = spatial.KDTree(list_of_coord)
        _, index = tree.query([[coord]])

        return index[0][0]

    def insert_row(self, row_value, index):
        """
        Insert a new row at the determined index
        :param row_value: list of value to insert as: ['lat', 'long', 'alt', 'descr']
        :param index: index where the row will be inserted
        """
        row = pd.DataFrame(row_value, columns=['lat', 'long', 'alt', 'descr'])
        self.df = pd.concat([self.df.iloc[:index], row, self.df.iloc[index:]]).reset_index(drop=True)

    def _set_prev_azi_angles(self):
        angleList = [0]
        for index, row in self.df.iterrows():
            if index != 0:
                coord1 = self[index][['lat', 'long', 'alt']].values.tolist()[0]
                coord2 = self[index -1][['lat', 'long', 'alt']].values.tolist()[0]
                _, angle = get_dist(coord1, coord2)
                angleList.append(angle)
        self.df['Azimut Angle'] = angleList

    def dist_from_prev(self, index):
        if index == 0:
            return 0
        else:
            return (self[index]['dist_from_origin'].values - self[index-1]['dist_from_origin'].values)[0]

    def addOffset(self, offset, max_dist):
        nb_line = int(max_dist // offset)
        start_offset_r, start_offset_l = [], []
        stop_offset_r, stop_offset_l = [], []
        coord1, coord2 = list(self.start), list(self.stop)
        _, _, theta = xy_dist(coord1, coord2)
        phi = -math.pi/2 + theta
        dist = offset
        x_offsets = []
        y_offsets = []
        while dist <= max_dist:
            if (math.degrees(theta) > (-180) and math.degrees(theta)) < 0 or\
                    (math.degrees(theta) > (180) and math.degrees(theta) < 360):
                x_offsets.append(-dist * math.sin(phi))
                y_offsets.append(-dist * math.cos(phi))
            else:
                x_offsets.append(dist * math.sin(phi))
                y_offsets.append(dist * math.cos(phi))
            dist += offset
        for i in range(nb_line):
            start_offset_r.append(addToCoord(coord1, x_offsets[i], y_offsets[i]))
            start_offset_l.append(addToCoord(coord1, -x_offsets[i], -y_offsets[i]))
            stop_offset_r.append(addToCoord(coord2, x_offsets[i], y_offsets[i]))
            stop_offset_l.append(addToCoord(coord2, -x_offsets[i], -y_offsets[i]))
        for i in range(nb_line):
            self.df['offset_l_%im' % int((1+i)*offset)] = [start_offset_l[i], stop_offset_l[i]]
            self.df['offset_r_%im' % int((1+i)*offset)] = [start_offset_r[i], stop_offset_r[i]]

    def _get_offset_line(self):
        """
        Return a list of Line object representing the offset original Line
        :return: list of Line object
        :rtype: lisf of Line
        """
        columns = [col for col in self.df if col.startswith('offset_')]
        offset_lines = []
        if columns:
            return self.df[columns]
        else:
            print('No offsets available')
            raise IndexError

    list_of_coord = property(_get_list_of_coord)
    pole_points = property(_get_pole_points)
    total_dist = property(_get_total_dist)
    offset_lines = property(_get_offset_line)


class Line(LineSection):
    def __init__(self, list_of_coord, typekey='normal', offset=None, offset_max_dist=None):
        """
        Complete line composed of linesecions
        :param list_of_coord: [(lat1, long1), (lat2, long2), ...]
        :type coord1: list of lists or list of tuples
        :param typekey: define the space between the poles e.g :'city', 'roads', 'hill', 'custom'
        :type typekey: str
        :param offset: if the value is not None, the LineSection will be duplicate with an offset
        :type offset: float
        :param offset_max_dist: maximum distance of the offset option, allow to know the number of LineSection copies
        :type offset_max_dist: float
        """

        self.start, self.stop = list_of_coord[0], list_of_coord[-1]
        self.offset, self.offset_max_dist = offset, offset_max_dist
        if typekey in settings.space_by_type.keys():
            self.type = typekey
        else:
            self.type = 'normal'

        self.df = self._set_dataframe(list_of_coord)
        func = lambda row: self.distance_from_origine([row.lat, row.long, row.alt])
        self.df['dist_from_origin'] = self.df.progress_apply(func,axis=1)
        self.df['dist_from_prev'] = list(map(self.dist_from_prev, range(len(self.df))))
        self._set_prev_azi_angles()
        self._set_prev_hor_angles()

    def _set_dataframe(self, list_of_coord):
        ls_list = []
        for i in range(1, len(list_of_coord), 1):
            ls = LineSection(list_of_coord[i-1], list_of_coord[i],typekey=self.type,
                             offset=self.offset, offset_max_dist=self.offset_max_dist)
            if i == len(list_of_coord)-1: #si c'est le dernier de la liste, on ajout la dernière coordonnée
                ls_list.append(ls[:])
            else:
                ls_list.append(ls[:-1])
        return pd.concat(ls_list, ignore_index=True, sort=False)

    def _set_prev_hor_angles(self):
        angle_list = [0]
        for i in range(1, len(self.list_of_coord)-1, 1):
            angle_list.append(get_angle(self.list_of_coord[i-1], self.list_of_coord[i], self.list_of_coord[i+1]))
        angle_list.append(0)
        self.df['Angle Horizontal'] = angle_list