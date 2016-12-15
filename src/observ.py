# -*- coding: utf-8 -*-
"""ete011 @Enrico Tedeschi - UiT
Observing the Bitcoin blockchain in real time. The system will retreive portion of the Bitcoin blockchain,
do data analysis, generating models and plotting the results.
Usage: observ.py -t number
    -h | --help         : usage
    -i                  : gives info of the blockchain in the file .txt
    -t number           : add on top a number of blocks. The blocks retreived will be the most recent ones. If the blockchain growth more than the block requested do -u (update)
    -e number           : append blocks at the end of the .txt file. Fetch older blocks starting from the last retrieved
    -P                  : plot all
    -p start [end]      : plot data in .txt file in a certain period of time, from start to end. If only start then consider from start to the end of the .txt file
    -R                  : plot the regression and the models that predict the blockchain
    -r start [end]      : plot the regression and the models in a certain period of time, from start to end. If only start then consider from start to the end of the .txt file
    -u                  : update the local blockchain to the last block created

"""

import sys, getopt
from docopt import docopt
import io
from blockchain import blockexplorer
import numpy as np
import string
import re
import os.path
import matplotlib.pyplot as plt
import datetime
import time
from time import sleep
import urllib2
import matplotlib.patches as mpatches
from forex_python.converter import CurrencyRates
from forex_python.bitcoin import BtcConverter
from scipy.optimize import curve_fit
import statsmodels.api as sm
import matplotlib.lines as mlines
import matplotlib.axis as ax

# ------ GLOBAL ------
global file_name
file_name = "blockchain.txt"
# --------------------

def main(argv):
    try:
        global plot_number
        plot_number = 0
        args_list = sys.argv
        args_size = len(sys.argv)
        earliest_hash = get_earliest_hash()
        start_v = None
        end_v = None

        opts, args = getopt.getopt(argv, "hiuRPp:t:e:r:")
        valid_args = False

        for opt, arg in opts:
            if(opt == "-t"):    # update on top
                print ("Adding at the top the latest " + arg + " blocks.")
                number_of_blocks = int(arg)
                get_blockchain(number_of_blocks)
                valid_args = True
            if(opt == "-e"):    # append blocks at the end
                print ("Appending at the end " + arg + " blocks.")
                number_of_blocks = int(arg)
                get_blockchain(number_of_blocks, earliest_hash)
                valid_args = True
            if(opt == "-u"):    # update with the missing blocks
                str = update_blockchain()
                valid_args = True
                if (str != None):
                    print str
            if(opt == "-i"):    # blockchain info
                print blockchain_info()
                valid_args = True
            if(opt == "-h"):    # usage
                print (__doc__)
                valid_args = True
            if(opt == "-P"):    # plot only
                plot_sequence(False, start_v, end_v)
                valid_args = True
            if(opt == "-p"):    # plot
                end_v = int(arg)
                if(args):
                    start_v = int(args[0])
                plot_sequence(False, start_v, end_v)
                valid_args = True
            if (opt == "-R"):  # regression only
                plot_sequence(True, start_v, end_v)
                valid_args = True
            if (opt == "-r"):  # plot regression with start and end
                end_v = int(arg)
                if (args):
                    start_v = int(args[0])
                plot_sequence(True, start_v, end_v)
                valid_args = True
        if(valid_args == False):
            print (__doc__)
    except getopt.GetoptError:
        print (__doc__)
        sys.exit(2)


def plot_sequence(regression, start_v, end_v):
    """
    @params:
      bool regression: if "-r" or "-R" is True, false otherwise
      int start_v: start value where the blockchain will be plotted
      int end_v: end value where the blockchain will be plotted
    :return:
    """
    if(regression):
        plot_data("growth_blockchain", 2, True, start=start_v, end=end_v)
        plot_data("fee_bandwidth", 3, True, start=start_v, end=end_v)
        plot_data("fee_transactions", 7, True, start=start_v, end=end_v)
    else:
        plot_data("time_per_block", 0, start=start_v, end=end_v)
        plot_data("byte_per_block", 1, start=start_v, end=end_v)
        plot_data("growth_blockchain", 2, start=start_v, end=end_v)
        plot_data("fee_bandwidth", 3, start=start_v, end=end_v)
        plot_data("bandwidth", 4, start=start_v, end=end_v)
        plot_data("efficiency", 5, start=start_v, end=end_v)
        plot_data("transaction_visibility", 6, start=start_v, end=end_v)
        plot_data("fee_transactions", 7, start=start_v, end=end_v)

# @profile
def get_blockchain(number_of_blocks, hash = None):
    """
    it retreives blocks from blockchain starting from the last block if hash is none,
    otherwise start from the block hash given in input
    @params:
     int number_of_blocks: blocks to retrieve
     str hash: hash of the block from where to start the retrieval
    :return: none
    """

    fetch_time_list = []
    epoch_list = []
    creation_time_list = []
    fee_list = []
    hash_list = []
    size_list = []
    height_list = []
    bandwidth_list = []
    avg_transaction_list = []
    list_transactions = []

    append_end = False

    # -------- PROGRESS BAR -----------
    index_progress_bar = 0
    printProgress(index_progress_bar, number_of_blocks, prefix='Saving Blockchain:', suffix='Complete',
                  barLength=50)
    # ---------------------------------

    if (hash):  # start the retrieval from there
        append_end = True
        last_block = blockexplorer.get_block(hash)
        start_time = datetime.datetime.now()
        current_block = blockexplorer.get_block(last_block.previous_block)
        end_time = datetime.datetime.now()
    else:
        last_block = blockexplorer.get_latest_block()
        hash_last_block = last_block.hash
        start_time = datetime.datetime.now()
        current_block = blockexplorer.get_block(hash_last_block)
        end_time = datetime.datetime.now()
        """
            you can append only if the blockchain will be consistent without gaps
            first check the last height, and if the n is bigger than the gap between the last height in the file and
            the height of the current block then don't append
        """
        if (os.path.isfile(file_name)):
            height_list_in_file = get_list_from_file("height")
            min_height_to_write = int(current_block.height) - int(height_list_in_file[0])
            if (number_of_blocks <= min_height_to_write):
                print ("\nWARNING: you are trying to retrieve " + str(number_of_blocks) +
                       " blocks when you have a gap in theblockchain of " + str(min_height_to_write) + "!")
                sys.exit()

    for i in range(number_of_blocks):
        # ---------- PROGRESS BAR -----------
        sleep(0.01)
        index_progress_bar += 1
        printProgress(index_progress_bar, number_of_blocks, prefix='Saving Blockchain:', suffix='Complete', barLength=50)
        # -----------------------------------


        # ---- List creation
        time_to_fetch = end_time - start_time
        time_in_seconds = get_time_in_seconds(time_to_fetch)
        fetch_time_list.append(time_in_seconds)
        epoch_list.append(current_block.time)
        hash_list.append(current_block.hash)
        fee_list.append(current_block.fee)
        size_list.append(current_block.size)
        height_list.append(current_block.height)
        avg_transaction_list.append(get_avg_transaction_time(current_block))

        block_size = float(current_block.size) / 1000000 # -------> calculate read Bandwidth with MB/s
        bandwidth = block_size / time_in_seconds
        bandwidth_list.append(bandwidth)

        transactions = current_block.transactions
        list_transactions.append(len(transactions))

        # --- creation time list
        start_time = datetime.datetime.now() # -------------------------------------------------------------------------
        prev_block = blockexplorer.get_block(current_block.previous_block)
        end_time = datetime.datetime.now()  # --------------------------------------------------------------------------
        prev_epoch_time = prev_block.time
        current_creation_time = current_block.time - prev_epoch_time
        creation_time_list.append(current_creation_time)

        add_mining_nodes(current_block)

        current_block = prev_block

    # writing all the data retrieved in the file
    write_blockchain(hash_list, epoch_list, creation_time_list, size_list, fee_list, height_list, bandwidth_list, list_transactions, avg_transaction_list, append_end)

    # check blockchain status
    print blockchain_info()

# @profile
def write_blockchain(hash, epoch, creation_time, size, fee, height, bandwidth, transactions, avg_tr_list, append_end):
    """
    write in blockchain.txt the blocks retrieved in get_blockchain().
    Add on the top if the block are newer than the existing one.
    Append on the bottom if the blocks are older.
    Do nothing if they are already in the blockchain.

    write a file with:
    hash
    epoch
    creation_time
    fee
    size
    height
    bandwidth
    transactions
    avgttime

    @params:
      list hash: hash list
      list epoch: epoch list
      list creation_time: creation time list
      list size: size list
      list fee: fee list
      list height: height list
      list bandwidth: bandwidth list
      list transactions: number of transactions in every block list
      list avg_tr_list: list with the average time that a transaction need to be visible in the blockchain in a certain block
      bool append_end: tells if is an append at the end of the file or at the beginning
    :return: None
    """

    n = len(hash)
    # ---------- PROGRESS BAR -----------
    index_progress_bar = 0
    printProgress(index_progress_bar, n, prefix='Writing .txt file:', suffix='Complete',
                  barLength=50)
    # -----------------------------------
    if (os.path.isfile(file_name)):
        # file already exists
        # retreive all the hashes check the first and the left in the file
        # add the non existing blocks

        if(append_end):
            with io.FileIO(file_name, "a+") as file:
                for i in range(n):
                    file.write("hash: " + str(hash[i]) + "\nepoch: " + str(epoch[i]) + "\ncreation_time: " + str(
                        creation_time[i]) + "\nsize: " + str(size[i]) + "\nfee: " + str(
                        fee[i]) + "\nheight: " + str(height[i]) + "\nbandwidth: " + str(
                        bandwidth[i]) + "\ntransactions: " + str(transactions[i]) + "\navgttime: " + str(
                        avg_tr_list[i]) + "\n\n")
                    # -------- PROGRESS BAR -----------
                    sleep(0.01)
                    index_progress_bar += 1
                    printProgress(index_progress_bar, n, prefix='Writing .txt file:', suffix='Complete',
                                  barLength=50)
                    # ---------------------------------
        else:
            hash_list_in_file = get_list_from_file("hash")
            first_hash = hash_list_in_file[0]

            elements = len(hash_list_in_file)
            last_hash = hash_list_in_file[elements-1]
            met_first = False
            met_last = False
            first_truncate = False

            with io.FileIO(file_name, "a+") as file:
                file.seek(0)
                existing_lines = file.readlines()
                file.seek(0)
                file.truncate()
                file.seek(0)

                i = 0
                while (i < n):
                    if (first_hash == hash[i]):
                        met_first = True
                    while((met_first == False) and (i < n)):
                        # append on top
                        file.write("hash: " + str(hash[i]) + "\nepoch: " + str(epoch[i]) + "\ncreation_time: " + str(
                            creation_time[i]) + "\nsize: " + str(size[i]) + "\nfee: " + str(
                            fee[i]) + "\nheight: " + str(height[i]) + "\nbandwidth: " + str(
                            bandwidth[i]) + "\ntransactions: " + str(transactions[i]) + "\navgttime: " + str(
                            avg_tr_list[i]) + "\n\n")

                        # -------- PROGRESS BAR -----------
                        sleep(0.01)
                        index_progress_bar += 1
                        printProgress(index_progress_bar, n, prefix='Writing .txt file:', suffix='Complete',
                                      barLength=50)
                        # ---------------------------------

                        i = i + 1
                        if ((i < n) and (first_hash == hash[i])):
                            met_first = True

                    file.writelines(existing_lines)


                    if ((i < n) and (last_hash == hash[i])):
                        met_last = True

                    while((met_last == False) and (i < n)):
                        # part of the blockchain already present in the file
                        if (last_hash == hash[i]):
                            met_last = True

                        # ---------- PROGRESS BAR -----------
                        sleep(0.01)
                        index_progress_bar += 1
                        printProgress(index_progress_bar, n, prefix='Writing .txt file:', suffix='Complete',
                                        barLength=50)
                        # -----------------------------------
                        i = i + 1

                    # append last elements in the file
                    while (i < n):
                        file.write("hash: " + str(hash[i]) + "\nepoch: " + str(epoch[i]) + "\ncreation_time: " + str(
                            creation_time[i]) + "\nsize: " + str(size[i]) + "\nfee: " + str(
                            fee[i]) + "\nheight: " + str(height[i]) + "\nbandwidth: " + str(
                            bandwidth[i]) + "\ntransactions: " + str(transactions[i]) + "\navgttime: " + str(
                            avg_tr_list[i]) + "\n\n")
                        # ---------- PROGRESS BAR -----------
                        sleep(0.01)
                        index_progress_bar += 1
                        printProgress(index_progress_bar, n, prefix='Writing .txt file:', suffix='Complete',
                                      barLength=50)
                        # -----------------------------------
                        i = i + 1
    else:
        with io.FileIO(file_name, "a+") as file:
            for i in range(n):
                # ---------- PROGRESS BAR -----------
                sleep(0.01)
                index_progress_bar += 1
                printProgress(index_progress_bar, n, prefix='Writing .txt file:', suffix='Complete',
                              barLength=50)
                # -----------------------------------

                file.write("hash: " + str(hash[i]) + "\nepoch: " + str(epoch[i]) + "\ncreation_time: " + str(
                    creation_time[i]) + "\nsize: " + str(size[i]) + "\nfee: " + str(
                    fee[i]) + "\nheight: " + str(height[i]) + "\nbandwidth: " + str(
                    bandwidth[i]) + "\ntransactions: " + str(transactions[i]) + "\navgttime: " + str(
                    avg_tr_list[i]) + "\n\n")


def create_growing_time_list(time_list):
    """
    given a time list with the creation time for each block, this method creates a new list containing the growing time
    every time a block is created.
    :param list time_list: a list with the creation time of all the blocks retrieved
    :return: list containig the growing time
    """
    # create growing time list
    reversed_time_list = time_list[::-1]
    time_to_append = 0
    previous_time = 0
    growing_time_list = []
    growing_time_list.append(previous_time)

    for time_el in reversed_time_list:
        # time in hours
        time_to_append = (float(time_el) / (60 * 60)) + previous_time
        growing_time_list.append(time_to_append)
        previous_time = time_to_append

    return growing_time_list


def create_growing_size_list(size_list):
    """
    given a list containig all the sizes for the blocks retrieved, create a list with the growth of the blockchain
    :param list size_list: list containing the sizes
    :return: the growth of the blockchain considering the blocks analyzed
    """
    reversed_size_list = size_list[::-1]
    growing_size_list = []
    value_to_append = 0
    size_back = 0
    growing_size_list.append(value_to_append)
    # create size growing list
    for size_el in reversed_size_list:
        value_to_append = size_el + size_back
        growing_size_list.append(value_to_append)
        size_back = value_to_append

    return growing_size_list


def get_list_from_file(attribute):
    """
        return a list of "attribute" values for all the blocks in blockchain.txt

        :param str attribute: it could be every attribute of a block such as "size", "epoch", "hash" ...
        :return: a list containing the attribute for all the blocks

     """

    list_to_return = []

    if (os.path.isfile(file_name)):
        # open the file and read in it
        with open(file_name, "r") as blockchain_file:
            for line in blockchain_file:
                # regular expression that puts in a list the line just read: ['hash', '<block_hash>']
                list = re.findall(r"[\w']+", line)

                if ((list) and (list[0] == attribute)):
                    list_to_return.append(list[1])
        return list_to_return
    else:
        return False


def get_time_in_seconds(time_to_fetch):
    """
    from time with format %H%M%S given in input return time in seconds
    :param time: time with format %H%M%S
    :return: time in seconds
    """
    # -------- TIME CONVERSION IN SECONDS ---------
    x = time.strptime(str(time_to_fetch).split('.')[0], '%H:%M:%S')
    # get the milliseconds to add at the time in second
    millisec = str(time_to_fetch).split('.')[1]
    millisec = "0." + millisec
    # get the time in seconds
    time_to_return = datetime.timedelta(hours=x.tm_hour, minutes=x.tm_min, seconds=x.tm_sec).total_seconds()
    time_to_return = float(time_to_return) + float(millisec)
    return time_to_return


def get_avg_transaction_time(block):
    """
    get the average time, per block, of the time that a transaction
    take to be visible in the blockchain after it has been requested.

    :param block: the block to be analized
    :return: int: return the average of the time of all the transactions in the block
    """
    # take transactions the block
    transactions = block.transactions

    # get block time -- when it is visible in the blockchain, so when it was created
    block_time = block.time

    # list of time of each transactions in one block
    transactions_time_list = []

    # list of the time that each transaction take to be visible, so when the block is visible in the blockchain
    time_to_be_visible = []

    for t in transactions:
        transactions_time_list.append(float(t.time))

    for t_time in transactions_time_list:
        time_to_be_visible.append(float(block_time - t_time))

    average_per_block = sum(time_to_be_visible) / len(time_to_be_visible)
    return average_per_block


def add_mining_nodes(block):
    """
    given a block add in a file all the new mining nodes and nodes involved in relying a transaction
    :param block: each block has a number of transactions and these transactions are relayed by a node
    :return: None
    """

    nodes_list = []
    nodes_list_new = []

    # if file already exist then read it and make a list of nodes out of it, this list will be appended to the file later
    with io.FileIO("nodes_in_the_network.txt", "a+") as file:
        if (os.path.isfile('nodes_in_the_network.txt')):
            file.seek(0)
            # get the list from the file
            for line in file:
                line = line.split()[0]
                nodes_list.append(line)

        transactions = block.transactions
        for t in transactions:
            node = str(t.relayed_by)
            if (node in nodes_list):
                pass
                # print node + " in list"
            elif(node in nodes_list_new):
                pass
                # print node + " in list new"
            else:
                nodes_list_new.append(node)

        for n in nodes_list_new:
            file.write(n + "\n")


    # for the mining nodes file, so the file containing the nodes which relay blocks
    node_list = []

    with io.FileIO("mining_nodes.txt", "a+") as file:
        if (os.path.isfile('nodes_in_the_network.txt')):
            file.seek(0)
            # get the list from the file
            for line in file:
                line = line.split()[0]
                nodes_list.append(line)
        node = str(block.relayed_by)
        if (node in nodes_list):
            pass
        else:
            file.write(node + "\n")

"""
Plotting

defined methods:
    - plot_blockchain(list, str, str)
"""

def plot_data(description, plot_number, regression = None, start = None, end = None):
    """
    Get the lists in the file and plots the data according to the description.
    :param description  - Required  : describe the type of plot created, it might be:
        time_per_block
        byte_per_block
        bandwidth
        growth_blockchain
        transaction_visibility
        efficiency
        fee_bandwidth
    :param plot_number  - Required  : number of the plot to be plotted and saved (progressive number)
    :param regression   - Optional  : write a regression on the plot generated
    :param start        - Optional  : block number where the plot starts
    :param end          - Optional  : block number where the plot ends
    """
    list_blockchain_time = datetime_retrieved(start, end)
    plt.figure(plot_number)
    plt.rc('lines', linewidth=1)

    if(description == "time_per_block"):
        x_vals = get_list_from_file("creation_time")
        x_vals[:] = [float(x) for x in x_vals]
        x_vals[:] = [x / 60 for x in x_vals]
        x_vals = x_vals[end:start]
        plt.plot(x_vals, 'g-', label=("creation time of a block\n" + str(list_blockchain_time[0]) + "\n" + str(list_blockchain_time[1])))
        plt.legend(loc="best")
        plt.ylabel("time (min)")
        plt.xlabel("block number")
        axes = plt.gca()
        axes.set_xlim([0, len(x_vals)])

        plt.savefig('plot/' + description + '(' + str(len(x_vals)) + ')')
        print("plot " + description + ".png created")
    elif(description == "byte_per_block"):
        x_vals = get_list_from_file("size")
        x_vals[:] = [float(i) for i in x_vals]
        x_vals[:] = [x / 1000000 for x in x_vals]
        x_vals = x_vals[end:start]
        plt.plot(x_vals, 'go', label=(
        "block size (Mb)\n" + str(list_blockchain_time[0]) + "\n" + str(list_blockchain_time[1])))
        plt.legend(loc="best")
        plt.ylabel("size (Mb)")
        plt.xlabel("block number")
        axes = plt.gca()
        axes.set_xlim([0, len(x_vals)])
        max_in_list = max(x_vals)
        axes.set_ylim([0, max_in_list*1.4])

        plt.savefig('plot/' + description + '(' + str(len(x_vals)) + ')')
        print("plot " + description + ".png created")
    elif(description == "bandwidth"):
        x_vals = get_list_from_file("bandwidth")
        x_vals[:] = [float(i) for i in x_vals]
        x_vals = x_vals[end:start]
        plt.plot(x_vals, 'c-', label=(
            "read bandwidth Mb/s\n" + str(list_blockchain_time[0]) + "\n" + str(list_blockchain_time[1])), lw=3)
        plt.legend(loc="best")
        plt.ylabel("read bandwidth (Mb/s)")
        plt.xlabel("block number")
        axes = plt.gca()
        axes.set_xlim([0, len(x_vals)])
        max_in_list = max(x_vals)
        axes.set_ylim([0, max_in_list * 1.2])

        plt.savefig('plot/' + description + '(' + str(len(x_vals)) + ')')
        print("plot " + description + ".png created")
    elif(description == "growth_blockchain"):
        time_list = get_list_from_file("creation_time")
        time_list[:] = [float(x) for x in time_list]

        size_list = get_list_from_file("size")
        size_list[:] = [float(x) for x in size_list]

        size_list = size_list[end:start]
        time_list = time_list[end:start]

        x_vals = create_growing_time_list(time_list)
        y_vals = create_growing_size_list(size_list)

        """# ---- get the exact data
        elements = len(y_vals)
        last_size = float(y_vals[elements-1])

        last_size = last_size/1000000
        print last_size

        elements = len(x_vals)
        last_time = float(x_vals[elements-1])
        print  last_time

        # ------------"""
        x_vals[:] = [float(x) for x in x_vals]
        x_vals[:] = [x / 60*60 for x in x_vals] # in hours

        y_vals[:] = [float(y) for y in y_vals]
        y_vals[:] = [y / 1000000000 for y in y_vals] # in GB

        plt.ylabel("size (GB)")
        plt.xlabel("time (h)")
        axes = plt.gca()
        # axes.set_xlim([0, max(x_vals)])

        if(regression):
            el = len(x_vals)
            last_el = x_vals[el - 1]

            # ---- get the predicted date time --------
            epoch_list = get_list_from_file("epoch")
            epoch_list = epoch_list[end:start]
            last_epoch = int(epoch_list[0])
            # add the hours to that epoch
            sec_to_add = (last_el*3) * 60 * 60
            last_epoch = last_epoch + sec_to_add
            prediction_date = epoch_datetime(last_epoch)
            # -----------------------------------------

            newX = np.linspace(0, last_el * 3)
            popt, pcov = curve_fit(myComplexFunc, x_vals, y_vals)
            plt.plot(newX, myComplexFunc(newX, *popt), 'g-', label=("prediction until\n" + str(prediction_date)), lw=3)
            lim = axes.get_ylim()
            axes.set_ylim([0, lim[1]])
            polynomial = np.polyfit(newX, myComplexFunc(newX, *popt), 2)
            print polynomial

        plt.plot(x_vals, y_vals, 'ro', label=(
            "growth retrieved\n" + str(list_blockchain_time[0]) + "\n" + str(list_blockchain_time[1])),
                 markevery=(len(x_vals) + 100) / 100)
        plt.legend(loc="best")

        plt.savefig('plot/' + description + '(' + str(len(x_vals)) + ')')
        print("plot " + description + ".png created")
    elif(description == "transaction_visibility"):
        x_vals = get_list_from_file("avgttime")
        x_vals[:] = [float(x) for x in x_vals]
        x_vals[:] = [x / 60 for x in x_vals]    # in minutes
        x_vals = x_vals[end:start]
        plt.plot(x_vals, 'b-', label=(
        "avg transaction visibility per block\n" + str(list_blockchain_time[0]) + "\n" + str(list_blockchain_time[1])))
        plt.legend(loc="best")
        plt.ylabel("time (min)")
        plt.xlabel("block number")
        axes = plt.gca()
        axes.set_xlim([0, len(x_vals)])


        plt.savefig('plot/' + description + '(' + str(len(x_vals)) + ')')
        print("plot " + description + ".png created")
    elif(description == "efficiency"):
        x_vals_size = get_list_from_file("size")
        x_vals_time = get_list_from_file("creation_time")
        x_vals_tr = get_list_from_file("transactions")

        x_vals_size = x_vals_size[end:start]
        x_vals_time = x_vals_time[end:start]
        x_vals_tr = x_vals_tr[end:start]

        x_vals_size[:] = [float(x) for x in x_vals_size]
        x_vals_size[:] = [x / 1000 for x in x_vals_size]
        x_vals_time[:] = [float(x) for x in x_vals_time]
        x_vals_tr[:] = [float(x) for x in x_vals_tr]

        plt.plot(x_vals_time, 'b-', label="Block Creation Time (sec)", lw=3)
        plt.plot(x_vals_tr, 'r-', label=("Number of Transactions (#)\n" + str(list_blockchain_time[0]) + "\n" + str(list_blockchain_time[1])))
        plt.plot(x_vals_size, 'go', label="Block Size (kb)")
        plt.legend(loc="best")
        plt.xlabel("block number")
        axes = plt.gca()
        axes.set_xlim([0, len(x_vals_size)])

        plt.savefig('plot/' + description + '(' + str(len(x_vals_size)) + ')')
        print("plot " + description + ".png created")
    elif(description == "fee_bandwidth"):
        x_vals = get_list_from_file("creation_time")
        x_vals[:] = [float(x) for x in x_vals]
        x_vals[:] = [x / 60 for x in x_vals] # in minutes

        y_vals = get_list_from_file("fee")
        y_vals[:] = [float(x) for x in y_vals]
        y_vals[:] = [x / 100000000 for x in y_vals] # in BTC

        x_vals = x_vals[end:start]
        y_vals = y_vals[end:start]

        plt.plot(x_vals, y_vals, 'ro', label=(
            "fee paid\n" + str(list_blockchain_time[0]) + "\n" + str(list_blockchain_time[1])))
        plt.ylabel("fee (BTC)")
        plt.xlabel("creation time (min)")
        axes = plt.gca()
        axes.set_xlim([0, max(x_vals)])
        axes.set_ylim([0, 2.5])

        if(regression):
            # logarithmic regression
            newX = np.logspace(0, 2, base=10)
            popt, pcov = curve_fit(myComplexFunc, x_vals, y_vals)
            plt.plot(newX, myComplexFunc(newX, *popt), 'g-', label="regression", lw=5)
            polynomial = np.polyfit(newX, myComplexFunc(newX, *popt), 2)
            print polynomial

        plt.legend(loc="best")
        plt.savefig('plot/' + description + '(' + str(len(x_vals)) + ')')
        print("plot " + description + ".png created")
    # --- future implementation
    elif(description == "fee_transactions"):
        y_vals = get_list_from_file("avgttime")
        y_vals[:] = [float(x) for x in y_vals]
        y_vals[:] = [x / 60 for x in y_vals] # in minutes

        x_vals = get_list_from_file("fee")
        x_vals[:] = [float(x) for x in x_vals]
        x_vals[:] = [x / 100000000 for x in x_vals]  # in BTC

        # divide the average fee paid fot the number of transaction in that block
        num_tr = get_list_from_file("transactions")
        num_tr[:] = [float(x) for x in num_tr]
        x_vals[:] = [x / y for x,y in zip(x_vals, num_tr)]

        x_vals = x_vals[end:start]
        y_vals = y_vals[end:start]

        plt.plot(x_vals, y_vals, 'ro', label=(
            "transaction visibility\n" + str(list_blockchain_time[0]) + "\n" + str(list_blockchain_time[1])))
        plt.xlabel("$\overline{T_p}$ (BTC)")
        plt.ylabel("transaction visibility (min)")
        axes = plt.gca()
        axes.set_ylim([0, max(y_vals)/10])
        axes.set_xlim([0, 0.006])

        if (regression):
            model = np.polyfit(x_vals, y_vals, 1)
            x_vals.sort()
            predicted = np.polyval(model, x_vals)
            plt.plot(x_vals, predicted, 'g-', label="regression", lw=4)
            polynomial = np.polyfit(x_vals, predicted, 2)
            print polynomial

        plt.legend(loc="best")
        plt.savefig('plot/' + description + '(' + str(len(x_vals)) + ')')
        print("plot " + description + ".png created")

def check_blockchain():
    """
    check if the element in the local blockchain are in order, if not, local blockchain is not in a good status,
    in that case is better to create a new file

    :return: True or False
    """
    check = True
    if (os.path.isfile(file_name)):
        list = get_list_from_file("height")
        number = int(list[0])
        length_list = len(list)
        for i in range(length_list):
            if (number != int(list[i])):
                check = False
            number = number - 1
    return check

def get_number_blocks():
    """
    :return: number of the current blocks saved in the local blockchain - 0 if file doesn't exist
    """
    number = 0
    if (os.path.isfile(file_name)):
        hash_list = get_list_from_file("hash")
        number = len(hash_list)
    return number

def get_earliest_hash():
    """
    if exists, get the earliest hash saved in the blockchain local file
    :return: the earliest hash in the local blockchain file - empty string if file doesn't exist
    """
    earliest_hash = ""
    if (os.path.isfile(file_name)):
        hash_list = get_list_from_file("hash")
        if (hash_list != False):
            length = len(hash_list)
            earliest_hash = hash_list[length - 1]
        else:
            earliest_hash = False
    return earliest_hash


def epoch_datetime(epoch):
    """
    convert epoch to datetime %Y-%m-%d %H:%M:%S
    :param epoch: time in epoch
    :return: time in datetime with %Y-%m-%d %H:%M:%S format
    """
    datetime = time.strftime('%d-%m-%Y %H:%M:%S', time.localtime(float(epoch)))
    return datetime

def datetime_retrieved(start = None, end = None):
    """
    @params:
        start   - Optional  : personalized start of the retrieval (eg, show only a portion of the blockchain)
        end     - Optional  : personalized end of the retrieved blockchain
    :return: a list containing  [0] --> end time of the blockchain retreived
                                [1] --> start time of the blockchain retrieved
    """
    # portion of the blockchain retrieved
    return_list = []
    epoch_l = get_list_from_file("epoch")
    epoch_l_length = len(epoch_l)

    if(start == None):
        start = epoch_l[epoch_l_length - 1]
    else:
        start = epoch_l[start]
    if (end == None):
        end = epoch_l[0]
    else:
        end = epoch_l[end]

    start_blockchain_time = start
    end_blockchain_time = end

    start_blockchain_time = epoch_datetime(start_blockchain_time)
    end_blockchain_time = epoch_datetime(end_blockchain_time)

    return_list.append(end_blockchain_time)
    return_list.append(start_blockchain_time)

    return return_list

"""
Progress bar -- from @Vladimir Ignatyev

"""
def printProgress (iteration, total, prefix = '', suffix = '', decimals = 1, barLength = 100):
    """
    call in a loop to create terminal progress bar
    @params:
        iteration   - Required  : current iteration (Int)
        total       - Required  : total iterations (Int)
        prefix      - Optional  : prefix string (Str)
        suffix      - Optional  : suffix string (Str)
        decimals    - Optional  : positive number of decimals in percent complete (Int)
        barLength   - Optional  : character length of bar (Int)
    """
    formatStr       = "{0:." + str(decimals) + "f}"
    percents        = formatStr.format(100 * (iteration / float(total)))
    filledLength    = int(round(barLength * iteration / float(total)))
    bar             = '█' * filledLength + '-' * (barLength - filledLength)
    sys.stdout.write('\r%s |%s| %s%s %s' % (prefix, bar, percents, '%', suffix)),
    if iteration == total:
        sys.stdout.write('\n')
    sys.stdout.flush()

def blockchain_info():
    """
    print the information regarding the local blockcahin
    :return: string containing the info from the blockchain text file
    """
    string_return = ""
    if (os.path.isfile(file_name)):
        blockchain_status = check_blockchain()
        if (blockchain_status == True):
            string_return+=(str(blockchain_status) + " -- Blockchain checked and in a correct status.\nNumber of blocks:\n   " + str(
                get_number_blocks()))
        else:
            string_return+=(str(blockchain_status) + " -- Blockchain not ordered correctly. Throw the file and make a new one")

        list_blockchain_time = datetime_retrieved()
        string_return+=("\nAnalysis in between:\n   " + str(list_blockchain_time[0]) + "\n   " + str(list_blockchain_time[1]))
    else:
        string_return = "File still doesn't exist. You need to fetch blocks first with -t command.\n" + str(__doc__)
    return string_return

def update_blockchain():
    """
    update the local blockchain retrieving the latest blocks that are missing
    :return: string with the status
    """
    string_return = None
    if (os.path.isfile(file_name)):
        # count how many nodes are missing
        height = get_list_from_file("height")
        last_retreived = int(height[0])
        current_block = blockexplorer.get_latest_block()
        last_total = int(current_block.height)
        diff = last_total - last_retreived
        if (diff > 0):
            print ("Updating the blockchain (" + str(diff) + " blocks missing)...")
            diff = diff + 1
            get_blockchain(diff)
        else:
            print ("Blockchain already up to date!")
    else:
        string_return = "File still doesn't exist. You need to fetch blocks first with -t command.\n" + str(__doc__)
    return string_return


def myComplexFunc(x, a, b, c):
    return a * np.power(x, b) + c

if __name__ == "__main__":
    main(sys.argv[1:])