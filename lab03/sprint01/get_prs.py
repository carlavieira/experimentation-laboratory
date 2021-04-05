# -*- coding: utf-8 -*-
"""
Created on Thu Apr  1 21:56:31 2021

@author: 1149425
"""
import os
from dotenv import load_dotenv
import json
import requests
import pandas as pd
from datetime import datetime

load_dotenv()

TOKEN = os.getenv("GITHUB_ACCESS_TOKEN")
HEADERS = {
	'Content-Type': 'application/json',
	'Authorization': f'bearer {TOKEN}'
}
URL = 'https://api.github.com/graphql'


# TODO refinar query para pegar todos os dados
def create_query(cursor=None, owner=None, name=None, state=None):
	if cursor is None:
		cursor = 'null'

	else:
		cursor = '\"{}\"'.format(cursor)

	return """
		{
			repository(owner: "%s", name: "%s") {
				%s: pullRequests(first: 10, after: %s, states: %s) {
					pageInfo {
						endCursor
						hasNextPage
					}
					nodes {
						createdAt
						closedAt
						mergedAt
						bodyText
						id
						reviews {
							totalCount
						}
						participants {
							totalCount
						}
						files {
							totalCount
						}
					}
				}
			}
			rateLimit {
				remaining
			}
		}
	""" % (owner, name, state, cursor, state)


def calculate_age(date_time_string):
	today = datetime.today()
	date_time_obj = datetime.strptime(date_time_string[0:10], "%Y-%m-%d")
	return (today - date_time_obj).days


def load_json(filename='data.json'):
	try:
		with open(filename, 'r') as read_file:
			return json.load(read_file)

	except FileNotFoundError:
		print(f'Failed to read data... Perform get_repos and assure data.json is in folder.')


def save_data(dict):
	with open('data_processed.json', 'a') as fp:
		json.dump(dict, fp, sort_keys=True, indent=4)

	df = pd.DataFrame(dict)
	df.to_csv(os.path.abspath(os.getcwd()) + f'/export_dataframe.csv', index=False, header=True)
	print("Saved csv with mining results")


if __name__ == "__main__":
	print(f"\n**** Starting GitHub API Requests *****\n")
	repos = list(load_json())
	processed_data = list(load_json(filename='processed_data.json'))
	condition = True
	response = ""
	index = 0
	data_array = []
	for repo in repos:

		try:
			response = requests.post(
				f'{URL}',
				json={'query': create_query(owner=repo['owner'], name=repo['name'], state='MERGED')},
				headers=HEADERS)
			response.raise_for_status()
			data = dict(response.json())

			for d in data['data']['repository']['MERGED']['nodes']:
				cleaned_data = dict()
				cleaned_data['owner'], cleaned_data['name'] = repo['owner'], repo['name']
				cleaned_data['createdAt'], cleaned_data['closedAt'] = d['createdAt'], d['closedAt']
				data_array.append(cleaned_data)
				index += 1
			# TODO -> get nodes and append to data_array

			pr_cursor = data['data']['repository']['MERGED']['pageInfo']['endCursor']
			hasNextPage = data['data']['repository']['MERGED']['pageInfo']['hasNextPage']
			remaining_nodes = data['data']['rateLimit']['remaining']

			while hasNextPage and remaining_nodes > 200:
				response = requests.post(
					f'{URL}',
					json={'query': create_query(owner=repo['owner'], name=repo['name'], state='MERGED', cursor=pr_cursor)},
					headers=HEADERS)
				response.raise_for_status()
				data = dict(response.json())
				for d in data['data']['repository']['MERGED']['nodes']:
					cleaned_data = dict()
					cleaned_data['owner'], cleaned_data['name'] = repo['owner'], repo['name']
					cleaned_data['createdAt'], cleaned_data['closedAt'] = d['createdAt'], d['closedAt']
					data_array.append(cleaned_data)
					index += 1

				# TODO -> get nodes and append to data_array
				pr_cursor = data['data']['repository']['MERGED']['pageInfo']['endCursor']
				hasNextPage = data['data']['repository']['MERGED']['pageInfo']['hasNextPage']
				remaining_nodes = data['data']['rateLimit']['remaining']
				if hasNextPage and remaining_nodes > 200:
					print('continuing with same repo')

				else:
					print('changing repo...')

		except requests.exceptions.ConnectionError:
			print(f'Connection error during the request')

		except requests.exceptions.HTTPError:
			print(f'HTTP request error. STATUS: {response.status_code}')

		except FileNotFoundError:
			print(f'File not found.')

		finally:
			save_data(data_array)
			break

	print(index)
