import requests
import json

def pin_to_ipfs(data):
	assert isinstance(data,dict), f"Error pin_to_ipfs expects a dictionary"
	#YOUR CODE HERE
	
	# Convert dictionary to JSON string
	json_data = json.dumps(data)
	
	# Pinata API configuration
	pinata_jwt = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VySW5mb3JtYXRpb24iOnsiaWQiOiI2MmJlMTQzMC03ODM2LTRjYjQtOTgyZi00OTI4M2U3MzMyYmMiLCJlbWFpbCI6Imxpd2VpamlldG9ueUBvdXRsb29rLmNvbSIsImVtYWlsX3ZlcmlmaWVkIjp0cnVlLCJwaW5fcG9saWN5Ijp7InJlZ2lvbnMiOlt7ImRlc2lyZWRSZXBsaWNhdGlvbkNvdW50IjoxLCJpZCI6IkZSQTEifSx7ImRlc2lyZWRSZXBsaWNhdGlvbkNvdW50IjoxLCJpZCI6Ik5ZQzEifV0sInZlcnNpb24iOjF9LCJtZmFfZW5hYmxlZCI6ZmFsc2UsInN0YXR1cyI6IkFDVElWRSJ9LCJhdXRoZW50aWNhdGlvblR5cGUiOiJzY29wZWRLZXkiLCJzY29wZWRLZXlLZXkiOiI0NWU4ZDMyMzllYzdhNzIwMzE5YyIsInNjb3BlZEtleVNlY3JldCI6IjMyNzZhMmRjM2EyMDI5ZDM3ZGMyNTgzNzQ4NTlkYjc5NzdjNTAwMjdmYWRmNjdlZmVjNjE2NDMzYTk4MDkwM2QiLCJleHAiOjE3ODI2NjQ4MzB9.FDPeA-3WmfO0yFDwVGdYi4K2tWP_rMCo-y61uTEYvx0"
	
	# Upload to Pinata IPFS
	url = "https://api.pinata.cloud/pinning/pinJSONToIPFS"
	headers = {
		"Authorization": f"Bearer {pinata_jwt}",
		"Content-Type": "application/json"
	}
	
	payload = {
		"pinataContent": data
	}
	
	response = requests.post(url, json=payload, headers=headers)
	response.raise_for_status()
	
	# Extract CID from response
	result = response.json()
	cid = result['IpfsHash']
	
	return cid

def get_from_ipfs(cid,content_type="json"):
	assert isinstance(cid,str), f"get_from_ipfs accepts a cid in the form of a string"
	#YOUR CODE HERE	
	
	# Retrieve data from Pinata gateway
	url = f"https://gateway.pinata.cloud/ipfs/{cid}"
	
	response = requests.get(url)
	response.raise_for_status()
	
	# Parse JSON response
	data = response.json()

	assert isinstance(data,dict), f"get_from_ipfs should return a dict"
	return data
