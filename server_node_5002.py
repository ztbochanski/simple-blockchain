# blockchain with transactions in python

# date and time for block timestamp
import datetime
# hashlib to create hashes from data
import hashlib
# json lib for working with json
import json
# import flask class and jsonify for displaying web app and json response
from flask import Flask, jsonify, request
# used to catch the correct node for concensus
import requests
# functions used for each node in the network and to parce nodes
from uuid import uuid4
from urllib.parse import urlparse


######################################################################
# 1 define the blockchain
######################################################################
class Blockchain:
    def __init__(self):
        # list to represent the chain
        self.chain = []
        # list to represent the transactions
        self.transactions = []
        # genesis block or the first block in the chain
        self.create_block(proof=1, previous_hash='0')
        # initialize nodes as a set
        self.nodes = set()

    # define block structure with keys
    def create_block(self, proof, previous_hash):
        block = {'index': len(self.chain) + 1,
                 'timestamp': str(datetime.datetime.now()),
                 'proof': proof,
                 'previous_hash': previous_hash,
                 'tranactions': self.transactions}
        # make sure to empty transactions so they are only assigned to one block.
        self.transactions = []
        self.chain.append(block)
        return block

    # get last block in chain
    def get_previous_block(self):
        return self.chain[-1]

    # return the proof value that is 'true'
    # this function generates hashes until it finds one that meets the parameters defiend
    # its purpose is to create work used in the 'mining' scenario
    def proof_of_work(self, previous_proof):
        new_proof = 1
        check_proof = False
        # iterate though hash solutions until get a match set proof to True
        while check_proof is False:
            hash_operation = hashlib.sha256(
                str(new_proof**2 - previous_proof**2).encode()).hexdigest()
            if hash_operation[:4] == '0000':
                check_proof = True
            else:
                new_proof += 1
        return new_proof

    # return sha256 hash of the block
    def hash(self, block):
        encoded_block = json.dumps(block, sort_keys=True).encode()
        # return hexidecimal format
        return hashlib.sha256(encoded_block).hexdigest()

    # check if the entire chain is valid
    def is_chain_valid(self, chain):
        previous_block = chain[0]
        block_index = 1
        while block_index < len(chain):
            block = chain[block_index]
            if block['previous_hash'] != self.hash(previous_block):
                return False
            previous_proof = previous_block['proof']
            proof = block['proof']
            hash_operation = hashlib.sha256(
                str(proof**2 - previous_proof**2).encode()).hexdigest()
            if hash_operation[:4] != '0000':
                return False
            previous_block = block
            block_index += 1
        return True

    # add data  or 'transaction' to block
    def add_transaction(self, sender, reciever, amount):
        self.transactions.append({'sender': sender,
                                  'reciever': reciever,
                                  'amount': amount})

        # only add to new oncoming block
        previous_block = self.get_previous_block()
        return previous_block['index'] + 1

    # add address as a node
    def add_node(self, address):
        # use url parse lib to process address into an obj
        parsed_url = urlparse(address)
        # add netloc from address IOT ID node and add that to the set
        self.nodes.add(parsed_url.netloc)

    def replace_chain(self):
        network = self.nodes
        longest_chain = None
        # initialize length of chain as the current node
        max_length = len(self.chain)
        for node in network:
            response = requests.get(f'http://{node}/get_chain')
            # check if response is ok and get length of chain and the chain
            if response.status_code == 200:
                length = response.json()['length']
                chain = response.json()['chain']
                # check if length is bigger than another node and if that chain is valid
                if length > max_length and self.is_chain_valid(chain):
                    # set this chain length to the max length
                    max_length = length
                    # set this chain to the longest chain
                    longest_chain = chain
                # if longest_chain is NOT None, make the class's chain equal to longest chain
                if longest_chain:
                    self.chain = longest_chain
                    return True
                # else return false if the chain was not replaced or not the longest chain
                return False


######################################################################
# 2 create the blockchain
######################################################################
# create web app
app = Flask(__name__)


# create an address for the node on Port 5000 so we know what node had a transaction
# uuid is used to create a unique id for the address
# get rid of '-' with replace method
node_address = str(uuid4()).replace('-', '')


# create a chain instance
blockchain = Blockchain()


# add a block/get a new block
@app.route('/add_block', methods=['GET'])
def add_block():
    # get prvious block
    previous_block = blockchain.get_previous_block()
    # get the proof from that block
    previous_proof = previous_block['proof']
    # get a new proof
    proof = blockchain.proof_of_work(previous_proof)
    # get the previous blocks hash
    previous_hash = blockchain.hash(previous_block)
    # add the transaction information to the block
    blockchain.add_transaction(
        sender=node_address, reciever='Person2Node2', amount=1)
    # get new block dict
    block = blockchain.create_block(proof, previous_hash)
    # display results in json format
    response = {'message': 'you have added a block',
                'index': block['index'],
                'timestamp': block['timestamp'],
                'proof': block['proof'],
                'previous_hash': block['previous_hash'],
                'transactions': block['transactions']}
    return jsonify(response), 200


# get the full chain
@app.route('/get_chain', methods=['GET'])
def get_chain():
    response = {'chain': blockchain.chain,
                'length': len(blockchain.chain)}
    return jsonify(response), 200


# check if the blockchain is valid
@app.route('/is_valid', methods=['GET'])
def is_valid():
    is_valid = blockchain.is_chain_valid(blockchain.chain)
    if is_valid:
        response = {'message': 'chain is valid.'}
    else:
        response = {'message': 'chain NOT valid.'}
    return jsonify(response), 200


# add transaction info to current newly added block
@app.route('/add_transaction', methods=['POST'])
def add_transaction():
    json = request.get_json()
    transaction_keys = ['sender', 'receiver', 'amount']
    if not all(key in json for key in transaction_keys):
        return 'Some elements of the transaction are missing', 400
    # call add_transaction which already handles current index of block pass in VALUES of keys
    index = blockchain.add_transaction(
        json['sender'], json['receiver'], json['amount'])
    response = {'message': f'this transaction will be added to block {index}'}
    # 201 created response
    return jsonify(response), 201


######################################################################
# 3 decentralize the blockchain
######################################################################
# connect new nodes
@app.route('/connect_node', methods=['POST'])
def connect_node():
    json = request.get_json()
    nodes = json.get('nodes')
    if nodes is None:
        return "No node", 400
    for node in nodes:
        blockchain.add_node(node)
    response = {'message': 'all the nodes are connected, this blockchain contains the following nodes:',
                'total_nodes': list(blockchain.nodes)}
    return jsonify(response), 201


# replace all nodes with longest chain if needed
@app.route('/replace_chain', methods=['GET'])
def replace_chain():
    is_chain_replaced = blockchain.replace_chain()
    if is_chain_replaced:
        response = {'message': 'the nodes had different chains so the chain was replaced by the longest.',
                    'new_chain': blockchain.chain}
    else:
        response = {'message': 'This is the longest one(most up-to-date).',
                    'actual_chain': blockchain.chain}
    return jsonify(response), 200


# Running the app
app.run(host='0.0.0.0', port=5002)
