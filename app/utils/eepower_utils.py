import pandas as pd
from math import sqrt
import re
from pathlib import Path

SCEN_PATERN = r".(lm|hv|30_cycle_report).(scen\D*)(\s*_*-*)(\d+\w{0,1})"


def simple_ed_report(rap_ed, bus_excluded=None):
    """
    Créer un dataframe pandas avec les données nécessaires issues d'EasyPower:

        Équipement | Scénario | Bus (V) | Type de défault | Disjoncteur en amont | Courant de court circuit (kA) |
     Courant d'arc (kA) | Temps de déclenchement (s) | Temps de l'arc (s) | Périmètre de sécurité (m) |
     Distance d'accès limité (m) | Distance de travail (m) | Niveau d'énergie (Cal/cm²)
    :param rap_af: rapport excel ou csv
    :type rap_af: str
    :param bus_excluded: liste des bus à ne pas inclure dans le tableau
    :type bus_excluded: list of str
    :return: un Dataframe Pandas contenant les informations nécessaire dans le tableau
    :rtype: pd.DataFrame
    """
    columns = {
        "Equipment\nName": "Équipement",
        "Worst Case Scenario": "Scénario",
        "Fault\nType": "Type de défault",
        "Bus Base\nkV": "Bus (V)",
        "Manufacturer": "Manufacturier",
        "Style": "Style",
        "Test\nStandard": "Standard de test",
        "1/2 Cycle\nRating\n(kA)": "Capacité pour 1/2 cycle (kA)",
        "1/2 Cycle\nDuty\n(kA)": "Utilisation pour 1/2 cycle (kA)",
        "1/2 Cycle\nDuty\n(%)": "Utilisation pour 1/2 cycle (%)",
        "Comments": "Commentaires"
    }

    rapport = pd.DataFrame(pd.read_excel(rap_ed, index_col=0))

    if bus_excluded is not None and bus_excluded != []:
        rapport = rapport[~rapport.index.str.contains('|'.join(bus_excluded))]

    rapport = rapport.rename(columns=columns)

    #on élimine les colonnes inutile
    column_to_keep = {v for k, v in columns.items()}
    column_existing = set(rapport.columns.to_list())
    column_to_drop = list(column_existing - column_to_keep)

    rapport = rapport.drop(column_to_drop, axis=1)
    rapport['Bus (V)'] = rapport['Bus (V)'] * 1000

    rapport = rapport.sort_index(ascending=True)

    return rapport


def simple_af_report(rap_af, bus_excluded=None):
    """
    Créer un dataframe pandas avec les données nécessaires issues d'EasyPower:

        Équipement | Scénario | Bus (V) | Type de défault | Disjoncteur en amont | Courant de court circuit (kA) |
     Courant d'arc (kA) | Temps de déclenchement (s) | Temps de l'arc (s) | Périmètre de sécurité (m) |
     Distance d'accès limité (m) | Distance de travail (m) | Niveau d'énergie (Cal/cm²)
    :param rap_af: rapport excel ou csv
    :type rap_af: str
    :param bus_excluded: liste des bus à ne pas inclure dans le tableau
    :type bus_excluded: list of str
    :return: un Dataframe Pandas contenant les informations nécessaire dans le tableau
    :rtype: pd.DataFrame
    """
    columns = {
        "Arc Fault Bus Name": "Équipement",
        "Worst Case Scenario": "Scénario",
        "Arc Fault Bus kV": "Bus (V)",
        "Fault Type": "Type de défault",
        "Upstream Trip Device Name": "Disjoncteur en amont",
        "Bus Bolted Fault (kA)": "Courant de court circuit (kA)",
        "Bus Arc Fault (kA)": "Courant d'arc (kA)",
        "Trip Time (sec)": "Temps de déclenchement (s)",
        "Arc Time (sec)": "Temps de l'arc (s)",
        "Limited Approach Boundary (m)": "Périmètre de sécurité (m)",
        "Restricted Approach Boundary (m)": "Distance d'accès limité (m)",
        "Working Distance (m)": "Distance de travail (m)",
        "Incident Energy\n(cal/cm2)": "Niveau d'énergie (Cal/cm²)"
    }
    file_path = Path(rap_af)
    typefile = file_path.suffix
    if typefile == '.csv':
        rapport = pd.DataFrame(pd.read_csv(rap_af, index_col=0))
    elif typefile == '.xlsx':
        rapport = pd.DataFrame(pd.read_excel(rap_af, index_col=0))

    if bus_excluded is not None and bus_excluded != []:
        rapport = rapport[~rapport.index.str.contains('|'.join(bus_excluded))]

    rapport.dropna()

    rapport = rapport.rename(columns=columns)

    #on élimine les colonnes inutile
    column_to_keep = {v for k, v in columns.items()}
    column_existing = set(rapport.columns.to_list())
    column_to_drop = list(column_existing - column_to_keep)

    rapport = rapport.drop(column_to_drop, axis=1)
    rapport['Bus (V)'] = rapport['Bus (V)'] * 1000

    rapport = rapport.sort_values(by='Bus (V)', ascending=False)

    return rapport.dropna()


def simple_cc_report(rap_30, rap_1, hv=None, typefile='csv', bus_excluded=None):
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
    #on conserve 'Bus kV' car il est changé par la suite pour 'Bus (V)'
    column_to_keep = {'Bus kV', 'Sym Amps', 'X/R Ratio', 'Asym Amps', 'I Peak', 'I Sym 30'}
    column_existing = set(rap.columns.to_list())
    column_to_drop = list(column_existing - column_to_keep)

    rap = rap.drop(column_to_drop, axis=1)
    rap = rap.rename(columns={'Bus kV': 'Bus (V)'})
    rap['Bus (V)'] = rap['Bus (V)'] * 1000

    rap = rap.sort_values(by='Bus (V)', ascending=False)

    peak = pd.DataFrame(rap['Asym Amps'] * sqrt(2)).round(1)
    rap.insert(4, 'I Peak', peak)

    if hv:
        hv_report = simple_cc_report(rap_30, hv, hv=None, typefile=typefile, bus_excluded=bus_excluded)
        rap = pd.concat([rap, hv_report])
        rap = rap.sort_values(by='Bus (V)', ascending=False)

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
    if m:
        return m.groups()[-1]
    else:
        return None

def scenario_finder(file_names):
    scen_list = []
    for name in file_names:
        num = scen_num_finder(name)
        if num:
            if num not in scen_list:
                scen_list.append(num)

    return scen_list

def pire_cas(reports, scenarios):
    pire_cas = pd.concat(reports, keys=scenarios, names=["Scénario", None])
    pire_cas = pire_cas.loc[pire_cas.groupby(level=1)['I Peak'].idxmax()]
    pire_cas = pire_cas.sort_values(by='Bus (V)', ascending=False)
    pire_cas = pire_cas.reset_index("Scénario")
    return pire_cas