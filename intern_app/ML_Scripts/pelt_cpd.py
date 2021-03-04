# -*- coding: utf-8 -*-
from os.path import join
import ruptures as rpt
import pandas as pd
import numpy as np

def change_points(csv_path_in, path_out):
    """
    Permet d'identifier les points de changements dans des séries temporelle de données
    :param csv_path: Un fichier CSV pouvant contenir plusieurs séries de temps distinctes (plusieurs colonne).
     Le CSV intrant doit contenir une colonne de date-temps (sans doublons) et doit contenir uniquement des valeurs numériques.
    :type csv_path: str
    :param path_out: Chemin du répertoire où enregister les csv en sortie
    :param path_out: str
    :return: le chemin vers deux fichiers CSV. Le premier contient les statistiques (moyennes, limites inférieures et limites supérieures)
    des segments identifiés pour les différentes variables. Le second retourne les données initiales et les statistiques
    des segments sous la forme de séries de temps.
    :rtype: str
    """

    # Paramère de l'analyse
    model = "l2"  # Trois modèles sont disponibles : "l1", "l2", "rbf"
    path_in = csv_path_in  # Nom du fichier csv à analyser
    min_size = 2  # Longueur minimale du segment.
    jump = 5  # Sous-échantillon (un tous les points de saut).
    penalty_value = 100  # Valeur de pénalité. Plus grand que 0.
    control_limits = 0.5  # Largeur de la bande des limites de contrôle (pourcentage des valeurs incluses). Entre 0 et 1.

    # Calcul des limites inférieures et supérieurs (centile)
    ucl = 0.5 + control_limits / 2
    lcl = 0.5 - control_limits / 2

    # CSV vers DataFrame Pandas
    df_in = pd.read_csv(path_in, header=0, index_col=0)
    date_time = df_in.index

    # Initier l'index pour la boucle des variables
    j = 0

    # Initialisation de listes et tableaux
    stat = np.empty((0, 3))
    ts = np.empty((df_in.values.shape[0], df_in.values.shape[1] * 4))

    ts_columns = []

    stat_ti = []
    stat_tf = []
    stat_var = []

    # Boucle pour passer à travers les variables du DataFrame
    for col in df_in.columns:

        signal = df_in[col].values
        prev = 0

        # Fonction de Ruptures pour identifier les points de changement (retourne les index des points de changements)
        brpt = rpt.Pelt(model=model, jump=5, min_size=2).fit_predict(signal, penalty_value)

        stat_bloc = np.empty((len(brpt), 3))

        # Boucle pour passer à travers les segments identifiés et sortir les informations pertinentes des segments.
        for i in range(len(brpt)):
            stat_ti.append(np.amin(date_time[prev:brpt[i]]))
            stat_tf.append(np.amax(date_time[prev:brpt[i]]))
            stat_var.append(col)
            stat_bloc[i, 0] = np.mean(signal[prev:brpt[i]])
            stat_bloc[i, 1] = np.percentile(signal[prev:brpt[i]], ucl * 100)
            stat_bloc[i, 2] = np.percentile(signal[prev:brpt[i]], lcl * 100)

            ts[prev:brpt[i], 0 + 4 * j] = signal[prev:brpt[i]]
            ts[prev:brpt[i], 1 + 4 * j] = stat_bloc[i, 0]
            ts[prev:brpt[i], 2 + 4 * j] = stat_bloc[i, 1]
            ts[prev:brpt[i], 3 + 4 * j] = stat_bloc[i, 2]

            prev = brpt[i]

        stat = np.vstack((stat, stat_bloc))
        ts_columns += [col, col + '_mean', col + '_ucl', col + '_lcl']

        j += 1

    # Former les DataFrame contenant les statistiques et les séries de temps complémentés
    df_stat = pd.DataFrame(columns=['ti', 'tf', 'var', 'mean', 'ucl', 'lcl'])
    df_stat['ti'] = stat_ti
    df_stat['tf'] = stat_tf
    df_stat['var'] = stat_var
    df_stat['mean'] = stat[:, 0]
    df_stat['ucl'] = stat[:, 1]
    df_stat['lcl'] = stat[:, 2]

    df_ts = pd.DataFrame(ts, index=date_time, columns=ts_columns)

    # Convertir les deux DataFrames en fichiers CSV
    stat_path = join(path_out,'stat.csv')
    ts_path = join(path_out,'ts.csv')
    df_stat.to_csv(stat_path)
    df_ts.to_csv(ts_path)

    return stat_path, ts_path

if __name__ == "__main__":
    from tkinter.filedialog import askopenfilenames, asksaveasfilename
    from tkinter import Tk

    Tk().withdraw()
    file_path = askopenfilenames()[0]
    paths_out = change_points(file_path, r"../generated/ML")


