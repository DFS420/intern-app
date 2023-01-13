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

        if _type == 'person':

            prefill['xp_len'] = len([k for k in prefill['experiences'].keys() if k.isdigit()])

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
        data["countries"] = re.split(r"\W+\s*", web_input['countries'])
        data["locations"] = re.split(r"\W+\s*", web_input['locations'])
        data["reference"] = re.split(r"; *", web_input['reference'])

        data["expert"] = web_input.getlist('expert')
        data["other"] = web_input.getlist('other')
        data["associate"] = web_input.getlist('associate')
        data["persons"] = list(set([data["leader"]] + data["expert"] + data["other"] + data["associate"]))


    elif _type == 'person':
        data['associate_project'] = web_input.getlist('associate_project')
        data['experiences'] = {}
        xp = {key: value for key, value in web_input.items() if key.startswith('xp')}
        klen = set([str(key.split('_')[-1]) for key in xp.keys()]) #récupération nombre de lignes d'Expérience
        for id in klen:
            data['experiences'][id] = {key: value for key, value in xp.items() if key.endswith(id)}



    data["type"] = _type
    data["tags"] = list(map(str.lower, re.split(r"\W+\s*|\s+", web_input['{0}_tags'.format(_type)])))
    data["body"] = data["{0}_body".format(_type)]
    keys, values = re.split(r";", data['custom_entry_keyword']), re.split(r";", data['custom_entry_value'])
    data['custom_entry'] = dict(zip(keys, values))

    return data

