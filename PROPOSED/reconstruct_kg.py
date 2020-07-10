import networkx as nx
from networkx.exception import NetworkXError

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import scipy.sparse
import pickle

import torch

from dataloader import AmazonDataset
import models
from models import DistMulti, TransE
from training import TrainIterater
from evaluate import Evaluater

import optuna
import time 

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

import warnings
warnings.filterwarnings('ignore')


# dataload
model_name = 'TransE'
dataset = AmazonDataset('./data', model_name='TransE')
edges = [[r[0], r[1]] for r in dataset.triplet_df.values]


# load network
G = nx.DiGraph()
G.add_nodes_from([i for i in range(len(dataset.entity_list))])
G.add_edges_from(edges)


def reconstruct_kg(model):
    with torch.no_grad():
        batch_size = int(len(dataset.item_list) / 2)
        item_index = [self.dataset.entity_list.index(item) for item in self.dataset.item_list]
        user_index = [self.dataset.entity_list.index(user) for user in self.dataset.user_list]
        brand_index = [self.dataset.entity_list.index(brand) for brand in self.dataset.brand_list]

        # user-itemの組に対して予測
        u_i_mat = []
        for i in user_index:
            #pred = torch.tensor([], device=device)
            u_i_vec = np.array([])
            for j in range(int(len(self.dataset.item_list) / batch_size) + 1):
                # modelにuser,itemを入力
                user_tensor = torch.tensor([i for k in range(batch_size)], dtype=torch.long, device=device)
                item_tensor = torch.tensor(item_index[j*batch_size : (j+1)*batch_size],
                                            dtype=torch.long, device=device)
                ### user ->(buy) itemはrelationが0であることに注意 ###
                relation_tensor = torch.tensor([0 for k in range(batch_size)], dtype=torch.long, device=device)
                
                if len(user_tensor) > len(item_tensor):
                    user_tensor = torch.tensor([i for k in range(len(item_tensor))],
                                            dtype=torch.long, device=device)
                    relation_tensor = torch.tensor([0 for k in range(len(item_tensor))],
                                                    dtype=torch.long, device=device)

                pred = np.array(model.predict(user_tensor, item_tensor, relation_tensor).cpu()) 
                u_i_vec = np.concatenate([u_i_vec, pred])
            u_i_mat.append(u_i_vec)
        u_i_mat = np.array(u_i_mat)

        # item-itemの組に対して予測
        # relationは also_buyとalso_viewの二つ
        i_i_b_mat = []
        i_i_v_mat = []
        for i in item_index:
            #pred = torch.tensor([], device=device)
            i_i_b_vec = np.array([])
            i_i_v_vec = np.array([])
            for j in range(int(len(self.dataset.item_list) / batch_size) + 1):
                # modelにuser,itemを入力
                h_item_tensor = torch.tensor([i for k in range(batch_size)], dtype=torch.long, device=device)
                t_item_tensor = torch.tensor(item_index[j*batch_size : (j+1)*batch_size],
                                            dtype=torch.long, device=device)
                ### item ->(also_buy) itemはrelationが2であることに注意 ###
                ### item ->(also_view) itemはrelationが3であることに注意 ###
                b_relation_tensor = torch.tensor([2 for k in range(batch_size)], dtype=torch.long, device=device)
                v_relation_tensor = torch.tensor([3 for k in range(batch_size)], dtype=torch.long, device=device)
                
                if len(h_item_tensor) > len(t_item_tensor):
                    h_item_tensor = torch.tensor([i for k in range(len(item_tensor))],
                                            dtype=torch.long, device=device)
                    b_relation_tensor = torch.tensor([2 for k in range(len(item_tensor))],
                                                    dtype=torch.long, device=device)
                    v_relation_tensor = torch.tensor([3 for k in range(len(item_tensor))],
                                                    dtype=torch.long, device=device)

                b_pred = np.array(model.predict(user_tensor, item_tensor, relation_tensor).cpu()) 
                v_pred = np.array(model.predict(user_tensor, item_tensor, relation_tensor).cpu()) 
                i_i_b_vec = np.concatenate([i_i_b_vec, pred])
                i_i_v_vec = np.concatenate([i_i_v_vec, pred])
            i_i_b_mat.append(i_i_b_vec)
            i_i_v_mat.append(i_i_v_vec)

            



if __name__ == '__main__':
    # model load
    model = pickle.load(open('model.pickle', 'rb'))