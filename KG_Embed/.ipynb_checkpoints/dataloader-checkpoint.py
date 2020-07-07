import pickle
import time
import pandas as pd
import numpy as np

#device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

class AmazonDataset:


    def __init__(self, data_dir, model_name='DistMulti'):
        self.data_dir = data_dir
        if not self.data_dir.endswith('/'):
            self.data_dir += '/'

        self.model_name = model_name
        self.load_triplet()
        self.load_user_items_dict()

        # TransEの時だけ使う辞書
        if model_name == 'TransE' or model_name == 'SparseTransE':
            self.relation_aggregate(self.nega_triplet_df)


    def load_triplet(self):
        self.user_item_test_df = pd.read_csv(self.data_dir + 'user_item_test.csv')
        self.triplet_df = pd.read_csv(self.data_dir + 'triplet.csv')
        self.nega_triplet_df = pd.read_csv(self.data_dir + 'nega_triplet.csv')

        self.user_list = []
        self.item_list = []
        self.brand_list = []
        self.entity_list = []
        with open(self.data_dir + 'user_list.txt', 'r') as f:
            for l in f:
                self.user_list.append(l.replace('\n', ''))

        with open(self.data_dir + 'item_list.txt', 'r') as f:
            for l in f:
                self.item_list.append(l.replace('\n', ''))
                
        with open(self.data_dir + 'brand_list.txt', 'r') as f:
            for l in f:
                self.brand_list.append(l.replace('\n', ''))
                
        with open(self.data_dir + 'entity_list.txt', 'r') as f:
            for l in f:
                self.entity_list.append(l.replace('\n', ''))

        self.y_train = np.loadtxt(self.data_dir + 'y_train.txt')
                
                
    def load_user_items_dict(self):
        self.user_items_test_dict = pickle.load(open(self.data_dir + 'user_items_test_dict.pickle', 'rb'))
       
    # relation -> [h, e, r]_1, [h, e, r]_2, [h, e, r]_3, ...
    def relation_aggregate(self, df):
        relation_entity_dict = {}
        relation_num = len(set(df['relation']))

        for i in range(relation_num):
            relation_df = df[df['relation'] == i]
            relation_entity_dict[i] = relation_df.values

        self.relation_entity_dict = relation_entity_dict

    def get_batch(self, batch_size=2):

        if self.model_name == 'DistMulti':
            train_num = len(self.triplet_df) + len(self.nega_triplet_df)
            batch_idx = np.random.permutation(train_num)[:batch_size]
            # posi_tripletとnega_tripletを連結
            batch = pd.concat([self.triplet_df, self.nega_triplet_df]).values[batch_idx]
            batch_y_train = self.y_train[batch_idx]
        
            return batch, batch_y_train

        elif self.model_name == 'TransE' or self.model_name == 'SparseTransE':
            batch_idx = np.random.permutation(len(self.triplet_df))[:batch_size]
            posi_batch = self.triplet_df.values[batch_idx]
            nega_batch = self.get_nega_batch(posi_batch[:, 2])

            return posi_batch, nega_batch
    
    def get_nega_batch(self, relations):
        nega_batch = []
        for rel in relations:
            nega_triplet = self.relation_entity_dict[rel]
        
            # ここ直す
            if len(nega_triplet) == 0:
                head = np.random.randint(len(self.entity_list))
                tail = np.random.randint(len(self.entity_list))
                nega_batch.append([head, tail, rel])
                continue
        
            nega_tri = nega_triplet[np.random.randint(len(nega_triplet))]
            nega_batch.append(nega_tri)
    
        return np.array(nega_batch)
            