from .eepower_utils import simple_report, group_by_scenario, pire_cas
from pandas import ExcelWriter
from os.path import join

FILE_NAME = 'eep-output.xlsx'

def report(data,target):
    """
    Generate a xlsx report for easy power
    :param data: a dictionary that contains all information for the processs
    :type data: dict
    :param data["BUS_EXCLUS"]: list of string patern to exclude form the analysis
    :type data["BUS_EXCLUS"]: list of str
    :param data["FILE_PATHS"]: list of path to the files
    :type data["FILE_PATHS"]: list of str
    :param data["FILE_NAME"]: list of name of the files
    :type data["FILE_NAME"]: list of str
    :param data["NB_SCEN"]: number of scenario
    :type data["NB_SCEN"]: list of str
    :param target: the path to the target path
    :type target: str
    :return: a path to the directory and the name of generated file
    :rtype: tuple of path
    """
    reports = []
    output_path = join(target, FILE_NAME)
    writer = ExcelWriter(output_path)
    scenarios = data["SCENARIOS"]
    for scenario in scenarios:
        group = group_by_scenario(data["FILE_PATHS"], data["FILE_NAMES"], scenario)
        for path, name in group:
            if '30_Cycle_Report' in name or '30 Cycle'in name:
                file30 = path
            elif 'LV' in name or 'LM' in name:
                file1 = path
            if '.csv' in path:
                _type = 'csv'
            elif '.xls' in path:
                _type = 'xlsx'

        if not '_type' in locals() or not 'file1' in locals() or not 'file30' in locals():
            raise FileNotFoundError("Il faut au moins un fichiers 30s et un fichier instanné")

        reports.append(simple_report(file30, file1, typefile=_type, bus_excluded=data["BUS_EXCLUS"]))

    pire_cas_rap = pire_cas(reports, scenarios)

    try:
        pire_cas_rap.to_excel(writer, sheet_name='Pire Cas')
        for scenario in scenarios:
            i = scenarios.index(scenario)
            reports[(i - 1)].to_excel(writer, sheet_name=('Scénario {0}'.format(scenario)))
        writer.save()
        #on retourne le repertoire et le fichier séparément
        return target, FILE_NAME

    except PermissionError:
        raise PermissionError("Le fichier choisis est déjà ouvert ou vous n'avez pas la permission de l'écrire")
    except ValueError:
        raise ValueError
