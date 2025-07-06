from web3 import Web3
from web3.providers.rpc import HTTPProvider
import requests
import json

bayc_address = "0xBC4CA0EdA7647A8aB7C2061c2E118A18a936f13D"
contract_address = Web3.to_checksum_address(bayc_address)

# You will need the ABI to connect to the contract
# The file 'abi.json' has the ABI for the bored ape contract
# In general, you can get contract ABIs from etherscan
# https://api.etherscan.io/api?module=contract&action=getabi&address=0xBC4CA0EdA7647A8aB7C2061c2E118A18a936f13D
with open('ape_abi.json', 'r') as f:
    abi = json.load(f)

############################
# Connect to an Ethereum node
api_url = "https://mainnet.infura.io/v3/40fd20c85d75423692cc1eba75727f5f"  # Infura API URL
provider = HTTPProvider(api_url)
web3 = Web3(provider)

# Create contract instance
contract = web3.eth.contract(address=contract_address, abi=abi)


def get_ape_info(ape_id):
    assert isinstance(ape_id, int), f"{ape_id} is not an int"
    assert 0 <= ape_id, f"{ape_id} must be at least 0"
    assert 9999 >= ape_id, f"{ape_id} must be less than 10,000"

    data = {'owner': "", 'image': "", 'eyes': ""}

    # Get the owner of the NFT
    owner = contract.functions.ownerOf(ape_id).call()
    data['owner'] = owner
    
    # Get the token URI
    token_uri = contract.functions.tokenURI(ape_id).call()
    
    # Convert IPFS URI to HTTP gateway URL
    if token_uri.startswith('ipfs://'):
        # Remove 'ipfs://' prefix and use Pinata gateway
        ipfs_hash = token_uri[7:]  # Remove 'ipfs://' prefix
        gateway_url = f"https://gateway.pinata.cloud/ipfs/{ipfs_hash}"
        
        # Fetch metadata from IPFS
        response = requests.get(gateway_url)
        if response.status_code == 200:
            metadata = response.json()
            
            # Extract image URL
            data['image'] = metadata.get('image', '')
            
            # Extract eyes attribute
            attributes = metadata.get('attributes', [])
            for attribute in attributes:
                if attribute.get('trait_type') == 'Eyes':
                    data['eyes'] = attribute.get('value', '')
                    break

    assert isinstance(data, dict), f'get_ape_info{ape_id} should return a dict'
    assert all([a in data.keys() for a in
                ['owner', 'image', 'eyes']]), f"return value should include the keys 'owner','image' and 'eyes'"
    return data
