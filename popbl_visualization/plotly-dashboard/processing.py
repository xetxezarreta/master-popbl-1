import numpy as np
import pandas as pd
import utils
from sklearn.model_selection import train_test_split
from sklearn import metrics
from sklearn.cluster import DBSCAN
from sklearn.preprocessing import StandardScaler


class Dashboard(object):
    def __init__(self):
        self.df = pd.read_csv('data/final.csv').head(1000)
        self.df_cluster = None
        self.model = None
        self.table_columns = ["a"]
        self.table_values = [1]

    def update_model(self, algorithm_name, ms, eps):
        print("Actualizando...")
        algorithm = utils.algorithms[algorithm_name](eps=eps, min_samples=ms)   
        self.model = algorithm.fit(self.df)
        self.df_cluster = self.df.copy()
        self.df_cluster['cluster'] = self.model.labels_

    def get_indicators(self):
        labels = self.model.labels_
        silhouette = metrics.silhouette_score(self.df, labels)
        clusters_ = len(set(labels)) - (1 if -1 in labels else 0)
        noise_ = list(labels).count(-1)
        return silhouette, clusters_, noise_

    def get_df_cluster(self):
        return self.df_cluster

    def get_variable_names(self):
        variables = []
        for col in self.df.columns:
            var = {
                'label': col,
                'value': col
            }
            variables.append(var)
        return variables

    def get_columns(self, column_names):
        columns = self.df[column_names]
        return columns

    def get_table_data(self):
        copy = self.df.copy()
        copy['cluster'] = self.model.labels_
        groupby = copy.groupby("cluster", as_index=False).mean()
        groupby = groupby.round(1)      

        columns = groupby.columns.values
        values = np.swapaxes(groupby,0,1).values       
     
        return columns, values

