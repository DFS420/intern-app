from .eepower_utils import simple_report, group_by_scenario, pire_cas
from pandas import ExcelWriter
from pathlib import Path
from re import search

XL_FILE_NAME = 'eep-output.xlsx'
TEX_FILE_NAME = "tab_cc.tex"

def report(data, target_repert):
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
    :param target_repert: the path to the target path
    :type target_repert: str
    :return: a path to the directory and the name of generated file
    :rtype: tuple of path
    """
    reports = []
    hv = None
    xl_output_path = Path(target_repert).joinpath(XL_FILE_NAME)
    tex_output_path = Path(target_repert).joinpath(TEX_FILE_NAME)

    writer = ExcelWriter(xl_output_path)
    scenarios = data["SCENARIOS"]

    for scenario in scenarios:
        group = group_by_scenario(data["FILE_PATHS"], data["FILE_NAMES"], scenario)
        file30, file1, _type = None, None, None
        for path, name in group:
            if '30_Cycle_Report' in name or '30 Cycle' in name:
                file30 = path
            elif 'LV' in name or 'LM' in name:
                file1 = path
            elif 'HV' in name:
                hv = path
            if '.csv' in path:
                _type = 'csv'
            elif '.xls' in path:
                _type = 'xlsx'

        if not _type:
            raise FileNotFoundError("Les fichiers doivent être au format csv ou xlsx")
        elif not file1 or not file30:
            raise FileNotFoundError("Il faut au moins un fichier 30s et un fichier instantané")

        tmp_report = simple_report(file30, file1, hv=hv, typefile=_type, bus_excluded=data["BUS_EXCLUS"])
        reports.append(tmp_report)

    pire_cas_rap = pire_cas(reports, scenarios)

    try:
        pire_cas_rap.to_excel(writer, sheet_name='Pire Cas')
        latex_table_filepath = df_to_tabularay(pire_cas_rap, tex_output_path)

        for scenario in scenarios:
            i = scenarios.index(scenario)
            reports[i].to_excel(writer, sheet_name=('Scénario {0}'.format(scenario)))
        writer.save()
        #on retourne le repertoire et le fichier séparément
        return xl_output_path, latex_table_filepath

    except PermissionError:
        raise PermissionError("Le fichier choisis est déjà ouvert ou vous n'avez pas la permission de l'écrire")
    except ValueError:
        raise ValueError


def df_to_tabularay(df, filepath):
    """
    Gives a tabularray table instead of the normal to_latex()
    :param df: DataFrame
    :return:
    """

    match = search(r"(?<=\\midrule\n)(.+\n)+(?=\\bottomrule)", df.to_latex())
    isolated_table = match.group()
    header = r"""
    \begin{longtblr}[caption = {Analyse de court-circuit}]%
                    {colspec={*{7}{ X X X X X X X}},
                     rowhead = {1},
                     rows = {font=\small},
                     row{odd} = {white}, row{even} = {blue9},
                     column{1} = {3.5cm}
                     }
    \toprule \SetRow{bg=abszero,fg=white}
     %\SetCol{width=5cm}
    \textbf{Équipement}
		&\textbf{Scénario} 
		    & \textbf{Bus (V)} 
		        & \textbf{Sym Amps (A)} 
                        & \textbf{X/R Ratio}
                            & \textbf{Asym Amps(A)}
                                    & \textbf{I Crête(A)}
                                        & \textbf{I Sym 30 (A)}\\
    """
    foot = r"\end{longtblr}"

    table = header + isolated_table + foot

    with open(filepath, 'w') as file:
        file.write(table)

    return filepath


