import pandas as pd
from math import sqrt
import re

SCEN_PATERN = r".(scen\D*)(\s*_*-*)(\d+\w{0,1})"
#todo: add the possiblity to have csv and excel at the same time
def simple_report(rap_30, rap_1, hv=None, typefile='csv', bus_excluded=None):
    """
    Créer une dataframe pandas en groupant les information utile depuis les rapport 30 cycles et 1 cycle
    :param rap_30:
    :type rap_30:
    :param rap_1:
    :type rap_1:
    :param typefile:
    :type typefile:
    :return:
    :rtype:
    """
    bus_excluded = [str.upper(bus) for bus in bus_excluded]
    #ajouté pour être sûr de dropper les lignes voulues (easypower donne des noms en capitale)

    if typefile == 'csv':
        rapport_30cycles = pd.DataFrame(pd.read_csv(rap_30, skiprows=1, index_col=0))
        rapport_1cycle = pd.DataFrame(pd.read_csv(rap_1, skiprows=1, index_col=0))
    elif typefile == 'xlsx':
        rapport_30cycles = pd.DataFrame(pd.read_excel(rap_30, skiprows=7, index_col=0, engine='openpyxl'))
        rapport_1cycle = pd.DataFrame(pd.read_excel(rap_1, skiprows=7, index_col=0, engine='openpyxl'))

    if bus_excluded != None and bus_excluded != []:
        temp1 = rapport_1cycle[~rapport_1cycle.index.str.contains('|'.join(bus_excluded))]
        temp30 = rapport_30cycles[~rapport_30cycles.index.str.contains('|'.join(bus_excluded))]
    else:
        temp1 = rapport_1cycle
        temp30 = rapport_30cycles

    temp1.dropna()
    temp30.dropna()

    temp30 = temp30.rename(columns={'Sym Amps': 'I Sym 30'})
    rap = pd.concat([temp1, temp30['I Sym 30']], axis=1)

    #on élimine les colonnes inutile
    #on conserve 'Bus kV' car il est changé par la suie pour 'Bus V'
    column_to_keep = {'Bus kV', 'Sym Amps', 'X/R Ratio', 'Asym Amps', 'I Peak', 'I Sym 30'}
    column_existing = set(rap.columns.to_list())
    column_to_drop = list(column_existing - column_to_keep)

    rap = rap.drop(column_to_drop, axis=1)
    rap = rap.rename(columns={'Bus kV': 'Bus V'})
    rap['Bus V'] = rap['Bus V'] * 1000

    rap = rap.sort_values(by='Bus V', ascending=False)

    peak = pd.DataFrame(rap['Asym Amps'] * sqrt(2)).round(1)
    rap.insert(4, 'I Peak', peak)

    if hv:
        hv_report = simple_report(rap_30, hv, hv=None, typefile=typefile, bus_excluded=bus_excluded)
        rap = rap.dropna()
        rap = pd.concat([rap, hv_report])
        rap = rap.sort_values(by='Bus V', ascending=False)

    return rap.dropna()


def group_by_scenario(filepath_list, filename_list, scenario):
    """
    Make a list of tuple of the path of the file and the file name if it it's the same scenario that number provided
    :param filepath_list: list of the complete path of files to group
    :type filepath_list: list
    :param filename_list: list of the names of files to group
    :type filename_list: list
    :param scenario:
    :type scenario: int
    :return: list of pair (path, file name) for the scenario provided
    :rtype: list of tuple
    """
    grouped_files = []

    for file_tuple in tuple(zip(filepath_list, filename_list)):
        if scen_num_finder(file_tuple[1]) == scenario:
            grouped_files.append(file_tuple)

    return grouped_files

def scen_num_finder(file_name):
    m = re.search(SCEN_PATERN, file_name.lower())
    return m.groups()[-1]

def scenario_finder(file_names):
    scen_list = []
    for name in file_names:
        num = scen_num_finder(name)
        if num not in scen_list:
            scen_list.append(num)
    return scen_list

def pire_cas(reports, scenarios):
    pire_cas = pd.concat(reports, keys=scenarios, names=["Scénario", None])
    pire_cas = pire_cas.loc[pire_cas.groupby(level=1)['I Peak'].idxmax()]
    pire_cas = pire_cas.sort_values(by='Bus V', ascending=False)
    pire_cas = pire_cas.reset_index("Scénario")
    return pire_cas