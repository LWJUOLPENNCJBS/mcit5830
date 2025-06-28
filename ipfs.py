import requests
import json
import base64

def pin_to_ipfs(data):
	assert isinstance(data,dict), f"Error pin_to_ipfs expects a dictionary"
	#YOUR CODE HERE
	
	# Convert dictionary to JSON string
	json_data = json.dumps(data)
	
	# Upload to Infura IPFS with Basic authentication
	project_id = "40fd20c85d75423692cc1eba75727f5f"
	url = "https://ipfs.infura.io:5001/api/v0/add"
	files = {'file': ('data.json', json_data, 'application/json')}
	headers = {'Authorization': f'Basic {base64.b64encode(project_id.encode()).decode()}'}
	
	response = requests.post(url, files=files, headers=headers)
	response.raise_for_status()
	
	# Extract CID from response
	result = response.json()
	cid = result['Hash']
	
	return cid

def get_from_ipfs(cid,content_type="json"):
	assert isinstance(cid,str), f"get_from_ipfs accepts a cid in the form of a string"
	#YOUR CODE HERE	
	
	# Retrieve data from public IPFS gateway
	url = f"https://ipfs.io/ipfs/{cid}"
	
	response = requests.get(url)
	response.raise_for_status()
	
	# Parse JSON response
	data = response.json()

	assert isinstance(data,dict), f"get_from_ipfs should return a dict"
	return data
