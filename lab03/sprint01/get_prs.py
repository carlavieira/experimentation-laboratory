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
def create_query(cursor, owner, name, state):
	if cursor is None:
		cursor = 'null'

	else:
		cursor = '\"{}\"'.format(cursor)

	return """
		{
			repository(owner: "%s", name: "%s") {
				%s: pullrequests(first: 3, after: %s, states: %s) {
					pageInfo {
						endCursor
						hasNextPage
					}
					nodes {
						createdAt
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


if __name__ == "__main__":
	print(f"\n**** Starting GitHub API Requests *****\n")
	repos = list(load_json())
	processed_data = list(load_json(filename='processed_data.json'))
	condition = True
	response = ""
	index = 0
	data_array = []
	for repo in repos:
		print(repo in processed_data)
		while condition:
			try:
				response = requests.post(
					f'{URL}',
					json={'query': create_query(json_data., owner, name, state)},
					headers=HEADERS)
				response.raise_for_status()
				data = dict(response.json())
				for d in data['data']['search']['nodes']:
					# TODO -> get nodes and append to data_array

				last_cursor = data['data']['search']['pageInfo']['endCursor']
				condition = data['data']['search']['pageInfo']['hasNextPage']

			except requests.exceptions.ConnectionError:
				print(f'Connection error during the request')

			except requests.exceptions.HTTPError:
				print(f'HTTP request error. STATUS: {response.status_code}')

			except FileNotFoundError:\
				print(f'File not found.')

			finally:
				print("last_cursor {}".format(last_cursor))
