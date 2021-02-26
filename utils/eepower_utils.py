import pandas as pd
from math import sqrt

def simple_report(rap_30, rap_1, typefile='csv', bus_excluded=None):
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
    #ajouté pour être sur de dropper les lignes voulues (easypower donne des noms en capitale)

    if typefile == 'csv':
        rapport_30cycles = pd.DataFrame(pd.read_csv(rap_30, skiprows=1, index_col=0))
        rapport_1cycle = pd.DataFrame(pd.read_csv(rap_1, skiprows=1, index_col=0))
    elif typefile == 'xlsx':
        rapport_30cycles = pd.DataFrame(pd.read_excel(rap_30, skiprows=5, index_col=0, engine='openpyxl'))
        rapport_1cycle = pd.DataFrame(pd.read_excel(rap_1, skiprows=5, index_col=0, engine='openpyxl'))

    if bus_excluded != None and bus_excluded != []:
        temp1 = rapport_1cycle[~rapport_1cycle.index.str.contains('|'.join(bus_excluded))]
        temp30 = rapport_30cycles[~rapport_30cycles.index.str.contains('|'.join(bus_excluded))]
    else:
        temp1 = rapport_1cycle
        temp30 = rapport_30cycles

    temp1.dropna()
    temp30.dropna()

    temp30 = temp30.rename(columns={'Sym Amps': 'I Sym 30'})
    rap = pd.concat([temp1,temp30['I Sym 30']], axis=1)

    rap = rap.drop(['Mult Factor', 'Equip Type', 'Duty Amps'], axis=1)
    rap = rap.rename(columns={'Bus kV': 'Bus V'})
    rap['Bus V'] = rap['Bus V'] * 1000

    rap = rap.sort_values(by='Bus V', ascending=False)

    peak = pd.DataFrame(rap['Asym Amps'] * sqrt(2)).round(1)
    rap.insert(4, 'I Peak', peak)

    return rap.dropna()

def group_by_scenario(filepathTuple, fileNameTuple, scenario):
    groupedFiles =[]

    for t in tuple(zip(filepathTuple, fileNameTuple)):
        if t[1].endswith('scen{0}'.format(scenario)):
            groupedFiles.append(t)

    return groupedFiles

def pire_cas(reports, scenarios):
    pire_cas = pd.concat(reports, keys=scenarios, names=["Scénario", None])
    pire_cas = pire_cas.loc[pire_cas.groupby(level=1)['I Peak'].idxmax()]
    pire_cas = pire_cas.sort_values(by='Bus V', ascending=False)
    pire_cas = pire_cas.reset_index("Scénario")
    return pire_cas