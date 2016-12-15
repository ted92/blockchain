# Paying for Bandwidth in Blockchain Internet Applications - University of Tromsø

Observing the Bitcoin blockchain in real time. The system will retreive portion of the Bitcoin blockchain, do data analysis, generating models and plotting the results.

## Getting Started

```
The folder \thesis contains the thesis in .pdf format
The folder \src contains the source code in Python for the blockchain analytics system
The analytics system is built in observ.py
blockchain.txt contains the local blockchain
The folder \plot contains the graphs generated after the blockchain analysis
```

### Prerequisites

Make sure you have installed all the libraries necessary before running the app.
eg:

```
pip install numpy
pip install matplotlib
```

## Usage

Usage of the blockchain alaytics system:


```
python observ.py -t number
    -h | --help         : usage
    -i                  : gives info of the blockchain in the file .txt
    -t number           : add on top a number of blocks. The blocks retreived will be the most recent ones. If the blockchain growth more than the block requested do -u (update)
    -e number           : append blocks at the end of the .txt file. Fetch older blocks starting from the last retrieved
    -P                  : plot all
    -p start [end]      : plot data in .txt file in a certain period of time, from start to end. If only start then consider from start to the end of the .txt file
    -R                  : plot the regression and the models that predict the blockchain
    -r start [end]      : plot the regression and the models in a certain period of time, from start to end. If only start then consider from start to the end of the .txt file
    -u                  : update the local blockchain to the last block created
```
eg:
begin using -t command if the blockchain.txt file still doesn't exist,
then use the commands -u and -e according to update or append at the end of the file.

to begin: add on top 10 blocks -- IF blockchain.txt DOES NOT EXIST YET
```
python observ.py -t 10
```
otherwise is better always to UPDATE the blockchain with the command:
```
python observ.py -u
```
append at the end 10 blocks
```
python observ.py -e 10
```
plot the results
```
python observ.py -P
```
plot the regressions
```
python observ.py -R
```
plot the results between a range of blocks.
Note: the range must be in between the number of block fetched in the blockchain.txt file
```
python observ.py -p 5 15
```
Plots generated with P command:
```
time_per_block.png				: (block number, time) shows the block creation time for each block in the local blockchain.txt file
byte_per_block.png				: (block number, size) represents the size for each block in the local blockchain
growth_blockchain.png			: (number of blocks, time) shows the blockchain growth
fee_bandwidth.png				: (creation time, fee) shows the relation between the creation time and the fee paid to the miner
bandwidth.png					: (block number, read bandwidth) shows the read bandwidth for each block retrieved
efficiency.png					: (block number, [size, transactions, creation time]) shows the relation between the size, the number of transactions and the creation time for the blocks in the local blockchain
transaction_visibility.png		: (block number, time) shows the average time for every block that a transaction need to be visibile since its creation 
fee_transactions.png			: (fee, transaction visibility time) represents the relation between the average time for a transaction to be visible in a block and the average fee paid from each transaction
```
Plots generated with R command:
```
growth_blockchain.png			: (number of blocks, time) shows the blockchain growth with its 3x time regression and prevision
fee_bandwidth.png				: (creation time, fee) shows the relation between the creation time and the fee paid to the miner with its regression
fee_transactions.png created	: (fee, transaction visibility time) represents the relation between the average time for a transaction to be visible in a block and the average fee paid from each transaction with its regression
```
## Built With

* [Python]	:v2.7.12
* [PyCharm]	:v2016.2.3

## Enrico Tedeschi @ UiT - University of Tromsø (ete011)
