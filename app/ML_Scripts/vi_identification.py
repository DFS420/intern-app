import pandas as pd
import numpy as np
from os.path import join

from sklearn.cross_decomposition import PLSRegression
from sklearn.metrics import mean_squared_error
from sklearn.linear_model import LinearRegression
from sklearn.linear_model import ElasticNet
from sklearn.neighbors import KNeighborsRegressor
from sklearn.tree import DecisionTreeRegressor
from sklearn.ensemble import AdaBoostRegressor
from sklearn.ensemble import BaggingRegressor
from sklearn.ensemble import RandomForestRegressor
from sklearn.ensemble import ExtraTreesRegressor

from app.ML_Scripts import vi_settings

vi_settings.init()

class VariableImportanceRFE:
    """
    Bloc d'analyse de l'importance d'un ensemble de variables (inputs) pour prédire un résultat (output). La méthode
    d'analyse utilisée par ce bloc consiste à enlever et remettre séquentiellement les variables dans un ensemble de
    données (inputs) et d'évaluer l'impact du retrait de la variable sur la prédiction d'un résultat (output).

    Parameters
    ----------
    start : Datetime or numeric
        Date ou index du début de la période étudiée.
    end : Datetime or numeric
        Date ou index de la fin de la période étudiée.
    variables : array-like
        Les noms des variables à étudier.
    algo_list : array-like, default = ['lr','dtr']
        Liste des algorithmes à employer pour l'analyse. Les algorithmes disponibles sont les suivants:
        Linear Regression ('lr'), PLS Regression ('plsr'), ElasticNet ('enr'), K Neighbors Regressor ('knr'),
        DecisionTreeRegressor ('dtr'), AdaBoostRegressor ('abr'), BaggingRegressor ('br'), ExtraTreesRegressor ('etr')

    Attributes
    ----------
    variable_importance_array : ndarray
        Numpy array de dimension 0 égale au nombre d'algorithme analysés et de dimension 1 égale au nombre de variables.
        Cette table contient l'importance des variable pour différents algorithmes. Plus précisément, les valeurs
        indiquent l'écart entre l'erreur (RMSE) de la prédiction du modèle excluant la variable étudiée et la
        prédiction du modèle contenant cette variable. Par exemple, si la valeur est négative pour une variable donnée,
        cela indique que l'ajout de cette variable augmente l'erreur de la prédiction.

    """
    def __init__(self, start, end, variables, algo_list=['lr','dtr']):
        self.start = start
        self.end = end
        self.algo_list = algo_list
        self.variables = variables
        self.variable_importance_array = np.empty([len(algo_list), len(variables)])

        # ['lr','plsr','enr','knr','dtr','abr','br','etr']

    def recursive_feature_elimination(self, inputs, output, test_set_ratio = 0.5):
        """
        Méthode d'évaluation de l'importance de différentes variables sur l'erreur de prédiction. Cette méthode
        d'analyse consiste à enlever et remettre séquentiellement les variables dans un ensemble de données (inputs) et
        d'évaluer l'impact du retrait de la variable sur la prédiction d'un résultat (output).
        Parameters
        ----------
        inputs : ndarray
            Numpy array de contenant l'ensemble de données à analyser. De dimension 0 égale au nombre d'échantillons
            (lignes) et de dimension 1 égale au nombre de variables. Les variables doivent être classées dans le même
            ordre que le vecteur de variables propre à la Classe VariableImportanceRFE.
        output : ndarray
            Numpy array de contenant la variable cible. De dimension 0 égale au nombre d'échantillons (lignes) et de
            dimension 1 égale à 1 (une seule variable cible étudiée).
        test_set_ratio : float, default = 0.5
            Le ratio des échantillons à utiliser pour l'évaluation des prédictions. Doit se situer entre 0 et 1.
        """
        data = np.hstack((output, inputs))
        np.random.shuffle(data)

        test_set_size = int(data.shape[0]*test_set_ratio)

        train = data[test_set_size:, :]
        test = data[:test_set_size, :]

        train_X = train[:, 1:]
        train_y = train[:, 0]
        test_X = test[:, 1:]
        test_y = test[:, 0]

        rmse_all_inputs = np.empty([len(self.algo_list), 1])

        i_algo = 0

        for algo in self.algo_list:
            if algo == 'lr':
                model = LinearRegression()
            elif algo == 'plsr':
                model = PLSRegression(n_components=1)
            elif algo == 'enr':
                model = ElasticNet()
            elif algo == 'knr':
                model = KNeighborsRegressor()
            elif algo == 'dtr':
                model = DecisionTreeRegressor()
            elif algo == 'abr':
                model = AdaBoostRegressor()
            elif algo == 'br':
                model = BaggingRegressor()
            elif algo == 'rfr':
                model = RandomForestRegressor()
            elif algo == 'etr':
                model = ExtraTreesRegressor()
            else:
                rmse_all_inputs[i_algo, 1] = np.nan
                self.variable_importance_array[i_algo, i_var] = np.nan
                i_algo += 1
                continue

            model.fit(train_X, train_y)
            y_pred = model.predict(test_X)
            rmse_all_inputs[i_algo, 0] = mean_squared_error(test_y, y_pred)**0.5

            for i_var in range(len(self.variables)):
                train_X_elim = np.delete(train_X, obj = i_var, axis=1)
                test_X_elim = np.delete(test_X, obj = i_var, axis=1)
                model.fit(train_X_elim, train_y)
                y_pred = model.predict(test_X_elim)
                self.variable_importance_array[i_algo, i_var] = mean_squared_error(test_y, y_pred)**0.5

            i_algo += 1

        self.variable_importance_array = self.variable_importance_array - rmse_all_inputs

    def vi_to_csv(self, file_path):
        """
        Méthode pour mettre le variable_importance_array sous forme d'un fichier csv

        Parameters
        ----------
        file_path : string
            Chemin où le fichier csv sera enregistré.
        """
        variable_importance_df = pd.DataFrame(self.variable_importance_array, index = self.algo_list, columns = self.variables)
        variable_importance_df.to_csv(file_path)

    def vi_to_df(self):
        """
        Méthode pour mettre le variable_importance_array sous forme d'un DataFrame Pandas.

        Returns
        ----------
        variable_importance_df : Pandas DataFrame
            DataFrame contenant les données du variable_importance_array.
        """
        variable_importance_df = pd.DataFrame(self.variable_importance_array, index = self.algo_list, columns = self.variables)


def run_vi(input_path, output_path):
    df = pd.read_csv(input_path,header=0, index_col=0, encoding="utf-8", na_values=vi_settings.na_values)

    df.dropna(inplace=True)
    variables = df.columns.difference(['Pento'])

    start = 0
    end = 1
    output = df['Pento'].values
    output = output.reshape(output.shape[0], 1)
    inputs = df[df.columns.difference(['Pento'])].values

    vi = VariableImportanceRFE(start=start, end=end, variables=variables, algo_list=vi_settings.algo_list)

    vi.recursive_feature_elimination(inputs=inputs, output=output, test_set_ratio=0.5)
    output_file = join(output_path,'vi.csv')
    vi.vi_to_csv(file_path=output_file)

    return 'vi.csv'

if __name__ == "__main__":

    run_vi(r"C:\Users\loupl\Google Drive\Projets\2020\20-221, 3E, Outils d'analyse AC\03_Rapport\variable_importance_analysis\data.csv",
           r"C:\Users\loupl\Google Drive\Projets\2020\20-221, 3E, Outils d'analyse AC\03_Rapport\variable_importance_analysis")
