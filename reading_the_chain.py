import random
import json
from web3 import Web3
from web3.middleware import ExtraDataToPOAMiddleware
from web3.providers.rpc import HTTPProvider


# If you use one of the suggested infrastructure providers, the url will be of the form
# now_url  = f"https://eth.nownodes.io/{now_token}"
# alchemy_url = f"https://eth-mainnet.alchemyapi.io/v2/{alchemy_token}"
# infura_url = f"https://mainnet.infura.io/v3/{infura_token}"

def connect_to_eth():
	# Using the Infura URL from the API key file
	url = "https://mainnet.infura.io/v3/40fd20c85d75423692cc1eba75727f5f"
	w3 = Web3(HTTPProvider(url))
	assert w3.is_connected(), f"Failed to connect to provider at {url}"
	return w3


def connect_with_middleware(contract_json):
	# Load contract information
	with open(contract_json, "r") as f:
		d = json.load(f)
		d = d['bsc']
		address = d['address']
		abi = d['abi']

	# Connect to BNB testnet
	bnb_url = "https://data-seed-prebsc-1-s1.binance.org:8545/"
	w3 = Web3(HTTPProvider(bnb_url))
	w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)
	
	# Verify connection
	assert w3.is_connected(), f"Failed to connect to BNB provider at {bnb_url}"

	# Create contract object
	contract = w3.eth.contract(address=address, abi=abi)

	return w3, contract


def is_ordered_block(w3, block_num):
	"""
	Takes a block number
	Returns a boolean that tells whether all the transactions in the block are ordered by priority fee

	Before EIP-1559, a block is ordered if and only if all transactions are sorted in decreasing order of the gasPrice field

	After EIP-1559, there are two types of transactions
		*Type 0* The priority fee is tx.gasPrice - block.baseFeePerGas
		*Type 2* The priority fee is min( tx.maxPriorityFeePerGas, tx.maxFeePerGas - block.baseFeePerGas )

	Conveniently, most type 2 transactions set the gasPrice field to be min( tx.maxPriorityFeePerGas + block.baseFeePerGas, tx.maxFeePerGas )
	"""
	block = w3.eth.get_block(block_num, full_transactions=True)
	ordered = False

	# Get all transactions in the block
	transactions = block.transactions
	
	if len(transactions) <= 1:
		# A block with 0 or 1 transaction is considered ordered
		ordered = True
	else:
		# Calculate priority fees for all transactions
		priority_fees = []
		base_fee_per_gas = block.get('baseFeePerGas', 0)
		
		for tx in transactions:
			# Check if this is a type 2 transaction (has maxPriorityFeePerGas)
			if hasattr(tx, 'maxPriorityFeePerGas') and tx.maxPriorityFeePerGas is not None:
				# Type 2 transaction
				max_priority_fee = tx.maxPriorityFeePerGas
				max_fee = tx.maxFeePerGas if hasattr(tx, 'maxFeePerGas') and tx.maxFeePerGas is not None else tx.gasPrice
				priority_fee = min(max_priority_fee, max_fee - base_fee_per_gas)
			else:
				# Type 0 transaction (legacy)
				if base_fee_per_gas > 0:
					# Post EIP-1559, priority fee = gasPrice - baseFeePerGas
					priority_fee = tx.gasPrice - base_fee_per_gas
				else:
					# Pre EIP-1559, priority fee = gasPrice
					priority_fee = tx.gasPrice
			
			priority_fees.append(priority_fee)
		
		# Check if the priority fees are in decreasing order
		ordered = all(priority_fees[i] >= priority_fees[i+1] for i in range(len(priority_fees)-1))

	return ordered


def get_contract_values(contract, admin_address, owner_address):
	"""
	Takes a contract object, and two addresses (as strings) to be used for calling
	the contract to check current on chain values.
	The provided "default_admin_role" is the correctly formatted solidity default
	admin value to use when checking with the contract
	To complete this method you need to make three calls to the contract to get:
	  onchain_root: Get and return the merkleRoot from the provided contract
	  has_role: Verify that the address "admin_address" has the role "default_admin_role" return True/False
	  prime: Call the contract to get and return the prime owned by "owner_address"

	check on available contract functions and transactions on the block explorer at
	https://testnet.bscscan.com/address/0xaA7CAaDA823300D18D3c43f65569a47e78220073
	"""
	default_admin_role = int.to_bytes(0, 32, byteorder="big")

	# Get the merkleRoot from the contract
	onchain_root = contract.functions.merkleRoot().call()
	
	# Check if the admin_address has the default admin role
	has_role = contract.functions.hasRole(default_admin_role, admin_address).call()
	
	# Get the prime owned by the owner_address
	prime = contract.functions.getPrimeByOwner(owner_address).call()

	return onchain_root, has_role, prime


"""
	This might be useful for testing (main is not run by the grader feel free to change 
	this code anyway that is helpful)
"""
if __name__ == "__main__":
	# These are addresses associated with the Merkle contract (check on contract
	# functions and transactions on the block explorer at
	# https://testnet.bscscan.com/address/0xaA7CAaDA823300D18D3c43f65569a47e78220073
	admin_address = "0xAC55e7d73A792fE1A9e051BDF4A010c33962809A"
	owner_address = "0x793A37a85964D96ACD6368777c7C7050F05b11dE"
	contract_file = "contract_info.json"

	eth_w3 = connect_to_eth()
	cont_w3, contract = connect_with_middleware(contract_file)

	latest_block = eth_w3.eth.get_block_number()
	london_hard_fork_block_num = 12965000
	assert latest_block > london_hard_fork_block_num, f"Error: the chain never got past the London Hard Fork"

	n = 5
	for _ in range(n):
		block_num = random.randint(1, latest_block)
		ordered = is_ordered_block(eth_w3, block_num)
		if ordered:
			print(f"Block {block_num} is ordered")
		else:
			print(f"Block {block_num} is not ordered")

	# Test the contract functions
	try:
		onchain_root, has_role, prime = get_contract_values(contract, admin_address, owner_address)
		print(f"Merkle Root: {onchain_root.hex()}")
		print(f"Admin has role: {has_role}")
		print(f"Prime owned by {owner_address}: {prime}")
	except Exception as e:
		print(f"Error calling contract functions: {e}")
