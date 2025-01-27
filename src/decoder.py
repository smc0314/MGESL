import random

from torch.nn import functional as F
import torch
# smc
torch.backends.cudnn.enabled = False
from torch.nn.parameter import Parameter
import math
import os
path_dir = os.getcwd()


class TimeConvTransR(torch.nn.Module):
    def __init__(self, num_relations, embedding_dim, input_dropout=0, hidden_dropout=0, feature_map_dropout=0, channels=50, kernel_size=3, use_bias=True):
        super(TimeConvTransR, self).__init__()
        self.inp_drop = torch.nn.Dropout(input_dropout)
        self.hidden_drop = torch.nn.Dropout(hidden_dropout)
        self.feature_map_drop = torch.nn.Dropout(feature_map_dropout)
        self.loss = torch.nn.BCELoss()

        self.conv1 = torch.nn.Conv1d(2, channels, kernel_size, stride=1,
                               padding=int(math.floor(kernel_size / 2)))  # kernel size is odd, then padding = math.floor(kernel_size/2)
        self.bn0 = torch.nn.BatchNorm1d(2)
        self.bn1 = torch.nn.BatchNorm1d(channels)
        self.bn2 = torch.nn.BatchNorm1d(embedding_dim)
        self.register_parameter('b', Parameter(torch.zeros(num_relations*2)))
        self.fc = torch.nn.Linear(embedding_dim * channels, embedding_dim)

    def forward(self, embedding, emb_rel, emb_time, triplets, nodes_id=None, mode="train", negative_rate=0, partial_embeding=None):

        e1_embedded_all = F.tanh(embedding)
        batch_size = len(triplets)
        e1_embedded = e1_embedded_all[triplets[:, 0]].unsqueeze(1)
        e2_embedded = e1_embedded_all[triplets[:, 2]].unsqueeze(1)
        # emb_time_1, emb_time_2 = emb_time
        # emb_time_1 = emb_time_1.unsqueeze(1)
        # emb_time_2 = emb_time_2.unsqueeze(1)

        # stacked_inputs = torch.cat([e1_embedded, e2_embedded, emb_time_1, emb_time_2], 1)
        stacked_inputs = torch.cat([e1_embedded, e2_embedded], 1)
        stacked_inputs = self.bn0(stacked_inputs)
        x = self.inp_drop(stacked_inputs)
        x = self.conv1(x)
        x = self.bn1(x)
        x = F.relu(x)
        x = self.feature_map_drop(x)
        x = x.view(batch_size, -1)
        x = self.fc(x)
        x = self.hidden_drop(x)
        x = self.bn2(x)
        x = F.relu(x)
        if partial_embeding is None:
            x = torch.mm(x, emb_rel.transpose(1, 0))
        else:
            # # smc
            # emb_rel = emb_rel[:-1]
            # # /smc
            x = torch.mm(x, emb_rel.transpose(1, 0))
            x = torch.mul(x, partial_embeding)
        return x


class TimeConvTransE(torch.nn.Module):
    def __init__(self, num_entities, embedding_dim, input_dropout=0, hidden_dropout=0, feature_map_dropout=0, channels=50, kernel_size=3, use_bias=True):

        super(TimeConvTransE, self).__init__()

        self.inp_drop = torch.nn.Dropout(input_dropout)
        self.hidden_drop = torch.nn.Dropout(hidden_dropout)
        self.feature_map_drop = torch.nn.Dropout(feature_map_dropout)
        self.loss = torch.nn.BCELoss()

        self.conv1 = torch.nn.Conv1d(2, channels, kernel_size, stride=1,
                               padding=int(math.floor(kernel_size / 2)))
        self.bn0 = torch.nn.BatchNorm1d(2)
        self.bn1 = torch.nn.BatchNorm1d(channels)
        self.bn2 = torch.nn.BatchNorm1d(embedding_dim)
        self.register_parameter('b', Parameter(torch.zeros(num_entities)))
        self.fc = torch.nn.Linear(embedding_dim * channels, embedding_dim)

    def forward(self, embedding, emb_rel, emb_time, triplets, nodes_id=None, mode="train", negative_rate=0, partial_embeding=None):
        e1_embedded_all = F.tanh(embedding)
        batch_size = len(triplets)
        e1_embedded = e1_embedded_all[triplets[:, 0]].unsqueeze(1)  # batch_size,1,h_dim
        rel_embedded = emb_rel[triplets[:, 1]].unsqueeze(1)  # batch_size,1,h_dim
        # emb_time_1, emb_time_2 = emb_time
        # emb_time_1 = emb_time_1.unsqueeze(1)
        # emb_time_2 = emb_time_2.unsqueeze(1)

        # stacked_inputs = torch.cat([e1_embedded, rel_embedded, emb_time_1, emb_time_2], 1)  # batch_size,2,h_dim
        stacked_inputs0 = torch.cat([e1_embedded, rel_embedded], 1)  # batch_size,2,h_dim
        stacked_inputs = self.bn0(stacked_inputs0)  # batch_size,2,h_dim
        x = self.inp_drop(stacked_inputs)  # batch_size,2,h_dim
        x = self.conv1(x)  # batch_size,2,h_dim
        x = self.bn1(x)  # batch_size,channels,h_dim
        x = F.relu(x)
        x = self.feature_map_drop(x)
        x = x.view(batch_size, -1)  # batch_size,channels*h_dim
        x = self.fc(x)  # batch_size,channels*h_dim
        x = self.hidden_drop(x)  # batch_size,h_dim
        if batch_size > 1:
            x = self.bn2(x)
        x = F.relu(x)
        if partial_embeding is None:
            x = torch.mm(x, e1_embedded_all.transpose(1, 0))
        else:
            x = torch.mm(x, e1_embedded_all.transpose(1, 0))
            x = torch.mul(x, partial_embeding)
        return x

    # def forward_slow(self, embedding, emb_rel, triplets):
    #
    #     e1_embedded_all = F.tanh(embedding)
    #     batch_size = len(triplets)
    #     e1_embedded = e1_embedded_all[triplets[:, 0]].unsqueeze(1)
    #     rel_embedded = emb_rel[triplets[:, 1]].unsqueeze(1)
    #     stacked_inputs = torch.cat([e1_embedded, rel_embedded], 1)
    #     stacked_inputs = self.bn0(stacked_inputs)
    #     x = self.inp_drop(stacked_inputs)
    #     x = self.conv1(x)
    #     x = self.bn1(x)
    #     x = F.relu(x)
    #     x = self.feature_map_drop(x)
    #     x = x.view(batch_size, -1)
    #     x = self.fc(x)
    #     x = self.hidden_drop(x)
    #     if batch_size > 1:
    #         x = self.bn2(x)
    #     x = F.relu(x)
    #     e2_embedded = e1_embedded_all[triplets[:, 2]]
    #     score = torch.sum(torch.mul(x, e2_embedded), dim=1)
    #     pred = score
    #     return pred


# 实现打分,采用ConvE
class ConvE(torch.nn.Module):
    def __init__(self, num):
        super(ConvE, self).__init__()

        self.bn0 = torch.nn.BatchNorm2d(1)
        self.bn1 = torch.nn.BatchNorm2d(200)
        self.bn2 = torch.nn.BatchNorm1d(200)

        self.dp0 = torch.nn.Dropout(0.1)
        self.dp1 = torch.nn.Dropout2d(0.1)
        self.dp2 = torch.nn.Dropout(0.1)

        self.conv0 = torch.nn.Conv2d(1, out_channels=200,
                                     kernel_size=(5, 5), stride=1, padding=0, bias=False)
        k_w_flat = 2*10 - 5 + 1
        k_h_flat = 20 - 5 + 1
        self.size_flat = k_w_flat*k_h_flat*200
        self.fc = torch.nn.Linear(self.size_flat, 200)
        self.bias = torch.nn.Parameter(torch.zeros(num))

    def forward(self, embedding, emb_rel, emb_time, triplets, nodes_id=None, mode="train", negative_rate=0, partial_embeding=None):
        e1_embedded_all = F.tanh(embedding)
        e1_embedded = e1_embedded_all[triplets[:, 0]].unsqueeze(1)  # batch_size,1,h_dim
        rel_embedded = emb_rel[triplets[:, 1]].unsqueeze(1)  # batch_size,1,h_dim
        stack_inp = self.concat(e1_embedded, rel_embedded)
        x = self.bn0(stack_inp)
        x = self.dp0(x)
        x = self.conv0(x)
        x = self.bn1(x)
        x = F.relu(x)
        x = self.dp2(x)
        x = x.view(x.shape[0], -1)
        x = self.fc(x)
        x = self.dp2(x)
        x = self.bn2(x)
        x = F.relu(x)
        if partial_embeding is None:
            x = torch.mm(x, e1_embedded_all.transpose(1, 0))
        else:
            x = torch.mm(x, e1_embedded_all.transpose(1, 0))
            x = torch.mul(x, partial_embeding)
        x = x + self.bias.expand_as(x)
        pred = torch.sigmoid(x)

        return pred

    def concat(self, sub, rel):
        stack_inp = torch.cat([sub, rel], 1)
        stack_inp = torch.transpose(stack_inp, 2, 1).reshape(-1, 1, 2*10, 20)

        return stack_inp


# 实现打分,采用ConvR
class ConvR(torch.nn.Module):
    def __init__(self, num):
        super(ConvR, self).__init__()

        self.bn0 = torch.nn.BatchNorm2d(1)
        self.bn1 = torch.nn.BatchNorm2d(200)
        self.bn2 = torch.nn.BatchNorm1d(200)

        self.dp0 = torch.nn.Dropout(0.1)
        self.dp1 = torch.nn.Dropout2d(0.1)
        self.dp2 = torch.nn.Dropout(0.1)

        self.conv0 = torch.nn.Conv2d(1, out_channels=200,
                                     kernel_size=(5, 5), stride=1, padding=0, bias=False)
        k_w_flat = 2*10 - 5 + 1
        k_h_flat = 20 - 5 + 1
        self.size_flat = k_w_flat*k_h_flat*200
        self.fc = torch.nn.Linear(self.size_flat, 200)
        self.bias = torch.nn.Parameter(torch.zeros(num))

    def forward(self, embedding, emb_rel, emb_time, triplets, nodes_id=None, mode="train", negative_rate=0, partial_embeding=None):
        e1_embedded_all = F.tanh(embedding)
        e1_embedded = e1_embedded_all[triplets[:, 0]].unsqueeze(1)  # batch_size,1,h_dim
        e2_embedded = e1_embedded_all[triplets[:, 2]].unsqueeze(1)
        stack_inp = self.concat(e1_embedded, e2_embedded)
        x = self.bn0(stack_inp)
        x = self.dp0(x)
        x = self.conv0(x)
        x = self.bn1(x)
        x = F.relu(x)
        x = self.dp2(x)
        x = x.view(x.shape[0], -1)
        x = self.fc(x)
        x = self.dp2(x)
        x = self.bn2(x)
        x = F.relu(x)
        if partial_embeding is None:
            x = torch.mm(x, emb_rel.transpose(1, 0))
        else:
            x = torch.mm(x, emb_rel.transpose(1, 0))
            x = torch.mul(x, partial_embeding)
        x = x + self.bias.expand_as(x)
        pred = torch.sigmoid(x)

        return pred

    def concat(self, sub, rel):
        stack_inp = torch.cat([sub, rel], 1)
        stack_inp = torch.transpose(stack_inp, 2, 1).reshape(-1, 1, 2*10, 20)

        return stack_inp