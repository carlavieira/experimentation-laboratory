# -*- coding: utf-8 -*-
"""
Created on Thu Apr  1 21:56:31 2021

@author: 1149425
"""
import os
import json
import requests
import pandas as pd
from dotenv import load_dotenv


load_dotenv()

TOKEN = os.getenv("GITHUB_ACCESS_TOKEN")
HEADERS = {
    'Content-Type': 'application/json',
    'Authorization': f'bearer {TOKEN}'
}
URL = 'https://api.github.com/graphql'
TARGET = 100


def create_query(cursor=None):
	if cursor is None:
		cursor = 'null'

	else:
		cursor = '\"{}\"'.format(cursor)

	query = """
		query github {
			search(query: "stars:>1000", type: REPOSITORY, first: 1, after:%s) {
			    pageInfo {
			      	endCursor
			      	hasNextPage
			    }
			    nodes {
			      	... on Repository {
			        	nameWithOwner
			        	url
			        	id
			        	closed: pullRequests(states: CLOSED, first: 1) {
			          		totalCount
			        	}
			        	merged: pullRequests(states: MERGED, first: 1) {
			          		totalCount
			        	}
			      	}
			    }
			}
		}
	"""%(cursor)
	return query


if __name__ == "__main__":
	print(f"\n**** Obtaining GitHub 100 most rated repos *****\n")
	condition = True
	last_cursor = None
	response = ""
	index = 0
	data_array = []
	while condition:
	    try:
	    	response = requests.post(f'{URL}', json={'query': create_query(cursor=last_cursor)}, headers=HEADERS)
	    	response.raise_for_status()
	    	data = dict(response.json())
	    	for d in data['data']['search']['nodes']:
	    		prs_merged = d['merged']['totalCount']
	    		prs_closed = d['closed']['totalCount']
	    		if prs_closed + prs_merged >= 100:
		    		cleaned_data = dict()
		    		cleaned_data['owner'], cleaned_data['name'] = d['nameWithOwner'].split('/')
		    		cleaned_data['prs_merged'] = d['merged']['totalCount']
		    		cleaned_data['prs_closed'] = d['closed']['totalCount']
		    		cleaned_data['url'] = d['url']
		    		cleaned_data['id'] = d['id']
		    		cleaned_data['index'] = index
		    		data_array.append(cleaned_data)
		    		TARGET = TARGET-1
		    		index = index +1

	    	last_cursor = data['data']['search']['pageInfo']['endCursor']
	    	condition = data['data']['search']['pageInfo']['hasNextPage'] and TARGET > 0

	    except requests.exceptions.ConnectionError:
	        print(f'Connection error during the request')

	    except requests.exceptions.HTTPError:
	        print(f'HTTP request error. STATUS: {response.status_code}')


	print(data_array)
	with open('data.json', 'w') as fp:
		json.dump(data_array, fp, sort_keys=True, indent=4)


	df = pd.DataFrame(data_array)
	print("\n**** GitHub API Requests Succeeded *****\n")
	df.to_csv(os.path.abspath(os.getcwd()) + f'/export_dataframe.csv', index=False, header=True)
	print("Successful mining! Saved csv with mining results")