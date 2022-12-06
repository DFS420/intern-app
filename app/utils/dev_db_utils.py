# -*- coding: utf-8 -*-
import re


def prefill_prep(data):
    """
    Prepare the data to be read by the page 'search_project to prefill the fields
    :param data: a dictionary that contains the entry to prepare
    :type data: dict
    """
    if 'title' not in data.keys():
        raise ValueError("Title is missing form the data")
    try:
        prefill = data

        prefill[data['language']] = 'checked'
        prefill[data['currency']] = 'checked'

        for leader in data['leader']:
            prefill['leader'][leader] = 'selected'

        for expert in data['leader']:
            prefill['expert'][expert] = 'selected'

        for other in data['leader']:
            prefill['other'][other] = 'selected'

        prefill['custom_entry_keyword'] = [key for key in data['custom_entry'].keys()]
        prefill['custom_entry_value'] = [value for value in data['custom_entry'].values()]


        for k, v in data.items():
            if isinstance(v, list):
                prefill[k] = '; '.join(v)

        return prefill

    except KeyError as e:
        raise ValueError("{0} is missing from the data".format(e).split(':'))


def prep_data_for_db(web_input, type):
    """
    Take the inputs from the web page and prepare it to be save in the DB
    :param web_input: inputs from the user
    :type web_input: dict or request.form
    :return: prepared data
    :rtype: dict
    """

    data = dict(web_input)
    data["type"] = type
    data["tags"] = re.split(r"\W+\s*|\s+", web_input['project_tags'])
    data["country"] = re.split(r"\W+\s*|\s+", web_input['country'])
    data["location"] = re.split(r"\W+\s*|\s+", web_input['location'])
    data["leader"] = web_input.getlist('leader')
    data["expert"] = web_input.getlist('expert')
    data["other"] = web_input.getlist('other')
    data["associate"] = web_input.getlist('associate')
    data["type"] = 'project'
    data["body"] = data["project_body"]
    keys, values = re.split(r";", data['custom_entry_keyword']), re.split(r";", data['custom_entry_value'])
    data['custom_entry'] = dict(zip(keys, values))

    return data

