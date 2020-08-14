# blockchain example in python

# date and time for block timestamp
import datetime
# hashlib to create hashes from data
import hashlib
# json lib for working with json
import json
# import flask class and jsonify for displaying web app and json response
from flask import Flask, jsonify


# define the blockchain
class Blockchain:
    def __init__(self):
        # list to represent the chain
        self.chain = []
        # genesis block or the first block in the chain
        self.create_block(proof=1, previous_hash='0')

    # define block structure with 4 essential keys exluding 'data'
    def create_block(self, proof, previous_hash):
        block = {'index': len(self.chain) + 1,
                 'timestamp': str(datetime.datetime.now()),
                 'proof': proof,
                 'previous_hash': previous_hash, }
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


# create web app
app = Flask(__name__)

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
    # get new block dict
    block = blockchain.create_block(proof, previous_hash)
    # display results in json format
    response = {'message': 'you have added a block',
                'index': block['index'],
                'timestamp': block['timestamp'],
                'proof': block['proof'],
                'previous_hash': block['previous_hash']}
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


# Running the app
app.run(host='0.0.0.0', port=5000)
