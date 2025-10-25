# Medical Blockchain

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Jul 12 23:08:11 2025

@author: wangruiqi
"""
# import libraries
import datetime
import hashlib
import json
from flask import Flask, jsonify, request
import requests
from uuid import uuid4
from urllib.parse import urlparse

# Part 1 - Building a Blockchain

class Blockchain:
    
    def __init__(self):
        self.chain = []
        self.transactions = []
        self.create_block(proof = 1, previous_hash = '0') #Genesis block, first block in blockchain
        self.nodes = set() # no order so use set
        
    def create_block(self, proof, previous_hash):  
        block = {'index': len(self.chain)+1,
                 'timestamp': str(datetime.datetime.now()),
                 'proof': proof, # computational effort by miner to find a valid hash, same role as Nonce
                 'previous_hash': previous_hash,
                 'transactions': self.transactions
                 }
        self.transactions = []
        self.chain.append(block)
        return block
    
    def get_previous_block(self):
        return self.chain[-1]
    
    def proof_of_work(self, previous_proof):
        new_proof = 1
        check_proof = False
        while check_proof is False:
            hash_operation = hashlib.sha256(str(new_proof**2 - previous_proof**2).encode()).hexdigest()
            if hash_operation[:4] == '0000':
                check_proof = True
            else:
                new_proof +=1
        return new_proof
    
    def hash(self, block):
        # dumps: Python dict to JSON string
        encoded_block = json.dumps(block, sort_keys = True).encode()
        return hashlib.sha256(encoded_block).hexdigest()
            
     
    def is_chain_valid(self, chain):
        previous_block = chain[0]
        block_index = 1
        while block_index < len(chain):
            block = chain[block_index]
            if block['previous_hash'] != self.hash(previous_block):
                return False
            
            previous_proof = previous_block['proof']
            proof = block['proof']
            hash_operation = hashlib.sha256(str(proof**2 - previous_proof**2).encode()).hexdigest()
            if hash_operation[:4] != '0000':
                return False
            
            #Iterate
            previous_block = block
            block_index +=1
        return True
    
    def add_transaction(self, patient, doctor, permission):
        self.transactions.append({'patient': patient,
                                  'doctor': doctor,
                                  'permission': permission}) # authorization
        
        previous_block = self.get_previous_block()
        return previous_block['index'] + 1
    
    def add_node(self, address):  
        parsed_url = urlparse(address)    #address = "http://127.0.0.1:5000/"
        self.nodes.add(parsed_url.netloc) #parsed_url = urlparse(address)
                                          #parsed_url
                                          #Out[4]: ParseResult(scheme='http', netloc='127.0.0.1:5000', path='/', params='', query='', fragment='')
    def replace_chain(self):              #node = parsed_url.netloc
        network = self.nodes              # node
        longest_chain = None              #Out[7]: '127.0.0.1:5000'
        max_length = len(self.chain)
        for nodes in network:
            response = requests.get(f'http://{nodes}/get_chain') #each node has diiferent netloc
            if response.status_code == 200:
                length = response.json()['length']
                chain = response.json()['chain']
                if length > max_length and self.is_chain_valid(chain):
                    max_length = length
                    longest_chain = chain
        if longest_chain: # is longest_chain isn't None
            self.chain = longest_chain
            return True
        return False 
            
        


# Part 2 - Mining our Blockchain

# Creating a Web App
app = Flask(__name__)
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = False

# Creating an address for the node on Port 5001
node_address = str(uuid4()).replace('-', '') # Coinbase: There is a transaction from coinbase to miner


# creating a Blockchain
blockchain = Blockchain()

# Mining a new block

@app.route('/mine_block', methods=['GET'])
def mine_block():
    previous_block =  blockchain.get_previous_block()
    previous_proof = previous_block['proof']
    proof = blockchain.proof_of_work(previous_proof)
    previous_hash = blockchain.hash(previous_block)
    blockchain.add_transaction(patient = node_address, doctor = 'First doctor', permission = 100)
    block = blockchain.create_block(proof, previous_hash)
    response = {'message': "Mine a block succesfully",
                'index': block['index'],
                'timestamp': block['timestamp'],
                'proof': block['proof'], 
                'previous_hash': block['previous_hash'],
                'transaction': block['transactions']
                }
    return jsonify(response), 200 # 200: ok

# Getting the full Blockchain
@app.route('/get_chain', methods=['GET'])
def get_chain():
    response = {'chain': blockchain.chain,
                'length': len(blockchain.chain)}
    return jsonify(response), 200

# Checking if the blockchain is valid
@app.route('/is_valid', methods=['GET'])
def is_valid():
    response = {'is_valid': blockchain.is_chain_valid(blockchain.chain)
              }
    return jsonify(response), 200

# Adding a new transaction to the block
@app.route('/add_transaction', methods=['POST'])
def add_transaction():
    json = request.get_json() # when you send JSON to an endpoint using a POST or PUT request, you can retrieve it using get_json()
    transaction_keys = ['patient', 'doctor', 'permission']
    if not all (key in json for key in transaction_keys):
        return 'Some elements of the transaction are misssing', 400
    index = blockchain.add_transaction(json['patient'], json['doctor'], json['permission'])
    response = {'message': f'This transaction will be added to Block {index}'}
    return jsonify(response), 201


# Part 3 - Decentralizing our Blockchain (keep all nodes updated)

# Connecting new nodes
@app.route('/connect_node', methods=['POST'])
def connect_node():
    json = request.get_json()
    nodes = json.get('nodes')
    if nodes is None:
        return 'No node', 400
    for node in nodes:
        blockchain.add_node(node)
    response = {'message': 'All nodes are now connected, the medical blockchain now contains the:', 
                'total_nodes': list(blockchain.nodes)}
    return jsonify(response), 201

# Replacing the chain by the longest chain if needed
@app.route('/replace_chain', methods=['GET'])
def replace_chain():
    is_chain_replaced = blockchain.replace_chain()
    if is_chain_replaced:
        response = {'message': 'The nodes had different chains so the chain was replaced by the longest chain',
              'new_chain': blockchain.chain}
    else: 
        response = {'message': 'The chain is the longest one',
              'actual_chain': blockchain.chain}
    return jsonify(response), 200

# Running the App
app.run(host = '0.0.0.0', port = 5002)


'''
    the client is the user's device or application that initiates requests for resources or services, 
            while the server is the system that manages and provides those resources or services
    client: send requests to the server, receive and process responses from the server, displaying info., 
            performing actions (Chrome)
    server: handle requests from clients, providing access to data, applications, and other resources.
    
    json is a data format used for exchanging data btwn. client <-> server
    
    
response — Server or Client Response Object

In Flask: You return a response (JSON, HTML, etc.) to the client.
from flask import jsonify
@app.route('/data')
def data():
    return jsonify({'message': 'Hello World'}), 200

In requests: It’s the object you get when calling requests.get() or requests.post():
response = requests.get("http://localhost:5000/get_chain")
print(response.text)       # Raw response
print(response.json())     # Parsed JSON data

Flask is a web framework: It's a Python module that helps you build web applications easily, 
                          allowing you to develop web applications. 
                          
A Response in Flask is an object: It represents the data sent back to the client after processing a request.



| Term                 | Context                    | Purpose                                 |
| -------------------- | -------------------------- | --------------------------------------- |
| `json`               | Python stdlib              | Convert between JSON ↔️ Python dict     |
| `request.get_json()` | Flask (server-side)        | Parse incoming JSON from client request |
| `requests.get()`     | Requests lib (client-side) | Send a GET request to a server          |
| `response`           | Client or Server           | Holds the HTTP response data            |

parsing: converting data from one format into another
parsing json: Using the json module to convert JSON strings into Python dictionaries or lists.

The terms requests.get, request.get_json, and response.json refer to different functionalities in Python, primarily within the context of web requests and web frameworks like Flask.

requests.get():
This is a function from the requests library, a popular library for making HTTP requests in Python.
It is used to send an HTTP GET request to a specified URL.
Its primary purpose is to retrieve data from a server.
It returns a Response object, which contains information about the server's response, including status codes, headers, and the response body.
Example: response = requests.get('https://api.example.com/data')

request.get_json():
This is a method typically found within web frameworks like Flask, accessible via the request object that represents the incoming HTTP request.
It is used to parse incoming JSON data from the request body.
It assumes the Content-Type header of the incoming request is application/json.
It returns a Python dictionary representing the JSON data, or None if the content type is not application/json (unless force=True is used).
It provides more control and error handling capabilities compared to request.json.
Example (in Flask): data = request.get_json()

response.json():
This is a method available on the Response object returned by the requests library (after making a client-side request like requests.get()).
It attempts to parse the response body as JSON and returns a Python dictionary or list.
This is a convenient way to directly access JSON data from an API response without manual parsing.
Example: data = response.json() (where response is the object returned by requests.get())


In summary:
requests.get() is for making outbound HTTP GET requests to retrieve data from external resources.
request.get_json() is for parsing JSON data from an incoming server-side request.
response.json() is for parsing JSON data from a client-side HTTP response received after making a request.
'''   
    