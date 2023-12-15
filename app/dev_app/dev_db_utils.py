# -*- coding: utf-8 -*-
import re
from copy import copy


def prefill_prep(data, _type):
    """
    Prepare the data to be read by the page 'search_project to prefill the fields
    :param data: a dictionary that contains the entry to prepare
    :type data: dict
    """

    try:
        prefill = copy(data)

        if 'name' not in data.keys():
            raise ValueError("Name is missing form the data")

        if _type == 'project':

            prefill[data['currency']] = 'checked'
            prefill['leader'] = {}
            for leader in data['leader']:
                prefill['leader'][leader] = 'selected'

            prefill['expert'] = {}
            for expert in data['expert']:
                prefill['expert'][expert] = 'selected'

            prefill['other'] = {}
            for other in data['other']:
                prefill['other'][other] = 'selected'

            prefill['xp_len'] = 0
            prefill['slan_len'] = 0
            prefill['degrees_len'] = 0

        if _type == 'person':

            prefill['xp_len'] = len([k for k in prefill['experiences'].keys()])
            prefill['slan_len'] = len([k for k in prefill['spoken_languages'].keys()])
            prefill['degrees_len'] = len([k for k in prefill['education'].keys()])


            prefill['associate_project'] = {}
            for associate_project in data['associate_project']:
                prefill['associate_project'][associate_project] = 'selected'

        prefill['custom_entry_keyword'] = '; '.join([key for key in prefill['custom_entry'].keys()])
        prefill['custom_entry_value'] = '; '.join([value for value in prefill['custom_entry'].values()])

        prefill[data['language']] = 'checked'

        for k, v in data.items():
            if isinstance(v, list):
                prefill[k] = '; '.join(v)
            elif isinstance(v, dict):
                for k2, v2 in v.items():
                    prefill[k2] = v2

        return prefill

    except KeyError as e:
        raise ValueError("{0} is missing from the data".format(e).split(':'))


def prep_data_for_db(web_input, _type):
    """
    Take the inputs from the web page and prepare it to be save in the DB
    :param web_input: inputs from the user
    :type web_input: dict or request.form
    :param _type: project or person
    :type _type: str
    :return: prepared data
    :rtype: dict
    """

    data = dict(web_input)
    if _type == 'project':

        data["locations"] = re.split(r";\s*", web_input['locations'])
        data["reference"] = re.split(r";\s*", web_input['reference'])
        data["expert"] = web_input.getlist('expert')
        data["other"] = web_input.getlist('other')
        data["associate"] = web_input.getlist('associate')
        data["persons"] = list(set([data["leader"]] + data["expert"] + data["other"] + data["associate"]))


    elif _type == 'person':
        data['associate_project'] = web_input.getlist('associate_project')
        data['experiences'] = {}
        data['spoken_languages'] = {}
        data['education'] = {}

        xp = {key: value for key, value in web_input.items() if key.startswith('xp')}
        klen = set([str(key.split('_')[-1]) for key in xp.keys()]) #récupération nombre de lignes d'Expérience
        for id in klen:
            kid = 'xp_{0}'.format(id)
            data['experiences'][kid] = {key: value for key, value in xp.items() if key.endswith(id)}

        slan = {key: value for key, value in web_input.items() if key.startswith('slan')}
        klen = set([str(key.split('_')[-1]) for key in slan.keys()]) #récupération nombre de lignes de langues
        for id in klen:
            kid = 'slan_{0}'.format(id)
            data['spoken_languages'][kid] = {key: value for key, value in slan.items() if key.endswith(id)}

        degree = {key: value for key, value in web_input.items() if key.startswith('degree')}
        klen = set([str(key.split('_')[-1]) for key in degree.keys()]) #récupération nombre de lignes de formation
        for id in klen:
            kid = 'degree_{0}'.format(id)
            data['education'][kid] = {key: value for key, value in degree.items() if key.endswith(id)}

    data["countries"] = re.split(r";\s*", web_input['countries'])
    data["type"] = _type
    data["tags"] = list(map(str.lower, re.split(r";\s*", web_input['{0}_tags'.format(_type)])))
    data["body"] = data["{0}_body".format(_type)]
    keys, values = re.split(r";\s*", data['custom_entry_keyword']), re.split(r";\s*", data['custom_entry_value'])
    data['custom_entry'] = dict(zip(keys, values))

    return data


def get_max_len(web_input, entry):
    """
    Give the length of new entry table such as 'xp', 'slan', 'degree'
    :param web_input: typically the request.from from the webpage
    :type web_input: dict
    :param entry: name of the entry table (ex: 'slan')
    :type entry: str
    :return: the current number of table lines
    :rtype: int
    """

    return max([int(k.split('_')[-1]) for k in web_input.keys() if k.startswith(entry)])

