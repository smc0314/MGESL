#!/usr/bin/env python
# -*- coding: utf-8 -*-
# @Time : 2021/8/10 4:23
# @Author : ZM7
# @File : save_data.py
# @Software: PyCharm

import os
import datetime
import warnings
import argparse
from utils import myFloder, Collate, mkdir
from torch.utils.data import DataLoader
from dgl.data.utils import save_graphs
from load_data import load_data
warnings.filterwarnings('ignore')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Save_data')
    parser.add_argument('--data', default='Sample', help='data name: sample')
    parser.add_argument('--max_length', type=int, default=10, help='max_length')
    parser.add_argument('--max_batch', type=int, default=100, help='max_length')
    parser.add_argument('--no_batch', action='store_true', help='no_batch')
    parser.add_argument('--k_hop', type=int, default=2, help='max hop')
    parser.add_argument('--encoder', default='regcn')
    parser.add_argument('--decoder', default='rgat_r1')
    parser.add_argument("--gpu", default='0', help="gpu")
    args = parser.parse_args()
    print(args)
    os.environ["CUDA_VISIBLE_DEVICES"] = args.gpu

    print("loading graph data")
    num_nodes, num_rels, train_list, valid_list, test_list, total_data, all_ans_list_test, all_ans_list_r_test, \
    all_ans_list_valid, all_ans_list_r_valid, graph, node_id_new, s_t, s_f, s_l, train_sid, valid_sid, test_sid, \
    total_times, time_idx = load_data(args.data)
    train_set = myFloder(train_list, max_batch=args.max_batch, start_id=train_sid, no_batch=True, mode='train')
    val_set = myFloder(valid_list, max_batch=100, start_id=valid_sid, no_batch=True, mode='test')
    test_set = myFloder(test_list, max_batch=args.max_batch, start_id=test_sid, no_batch=True, mode='test')
    co = Collate(num_nodes, num_rels, s_f, s_t, len(total_data), args.data, args.encoder, args.decoder,
                 max_length=args.max_length, all=False, graph=graph, k=args.k_hop)
    train_dataset = DataLoader(dataset=train_set, batch_size=1, collate_fn=co.collate_rel, shuffle=False, pin_memory=True,
                               num_workers=6)   # 瞎搞，应该改成shuffle=False吧
    val_dataset = DataLoader(dataset=val_set, batch_size=1, collate_fn=co.collate_rel, shuffle=False, pin_memory=True,
                             num_workers=4)
    test_dataset = DataLoader(dataset=test_set, batch_size=1, collate_fn=co.collate_rel, shuffle=False, pin_memory=True,
                              num_workers=2)

    # train_path = '/home/smc/mgesl/data/'+ args.data + '/' + 'noleak_length_' + str(args.max_length) \
    #              + '_encoder_' + args.encoder + '_decoder_' + args.decoder + '_hop_' + str(args.k_hop) + '/train/'
    # val_path = '/home/smc/mgesl/data/' + args.data + '/' + 'noleak_length_' + str(args.max_length) \
    #             + '_encoder_' + args.encoder + '_decoder_' + args.decoder + '_hop_' + str(args.k_hop) + '/val/'
    # test_path = '/home/smc/mgesl/data/' + args.data + '/' + 'noleak_length_' + str(args.max_length) \
    #             + '_encoder_' + args.encoder + '_decoder_' + args.decoder + '_hop_' + str(args.k_hop) + '/test/'

    train_path = '/public/home/detian/smc/mgesl/data/' + args.data + '/' + 'noleak_length_' + str(args.max_length) \
                 + '_encoder_' + args.encoder + '_decoder_' + args.decoder + '_hop_' + str(args.k_hop) + '/train/'
    val_path = '/public/home/detian/smc/mgesl/data/' + args.data + '/' + 'noleak_length_' + str(args.max_length) \
               + '_encoder_' + args.encoder + '_decoder_' + args.decoder + '_hop_' + str(args.k_hop) + '/val/'
    test_path = '/public/home/detian/smc/mgesl/data/' + args.data + '/' + 'noleak_length_' + str(args.max_length) \
                + '_encoder_' + args.encoder + '_decoder_' + args.decoder + '_hop_' + str(args.k_hop) + '/test/'


    mkdir(train_path)
    mkdir(val_path)
    mkdir(test_path)
    print('Start loading train set: ', datetime.datetime.now(), '=============================================')
    for i, train_data_list in enumerate(train_dataset):
        print("hhhhhh",i+1)  # 因为train_dataset把第0个时间步去掉了m，所以是从第一个开始的
        print("wwwwwww", train_data_list['t'])
        save_graphs(train_path + str(i+1) + '_' + 'bin',
                    [train_data_list.pop('sub_e_graph'), train_data_list.pop('sub_d_graph')], train_data_list)
    print('Start loading validation set: ', datetime.datetime.now(), '=============================================')
    for i, val_data_list in enumerate(val_dataset):
        save_graphs(val_path + str(i) + '_' + 'bin',
                    [val_data_list.pop('sub_e_graph'), val_data_list.pop('sub_d_graph')], val_data_list)
    print('Start loading test set: ', datetime.datetime.now(), '=============================================')
    for i, test_data_list in enumerate(test_dataset):
        save_graphs(test_path + str(i) + '_' + 'bin',
                    [test_data_list.pop('sub_e_graph'), test_data_list.pop('sub_d_graph')], test_data_list)
    print('end', datetime.datetime.now(), '=============================================')