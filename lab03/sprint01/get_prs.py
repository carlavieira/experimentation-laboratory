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

URL = 'https://api.github.com/graphql'
TOKEN_LIST = json.loads(os.getenv("GITHUB_ACCESS_TOKENS"))

def generate_new_header():
    global token_index
    headers = {
		'Content-Type': 'application/json',
		'Authorization': f'bearer {TOKEN_LIST[token_index]}'
	}
    if token_index < len(TOKEN_LIST) -1 :
        token_index += 1
    else:
        token_index = 0
    return headers


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
						id
						databaseId
						createdAt
						additions
						deletions
						closed
						closedAt
						merged
						mergedAt
						body
						participants {
						  totalCount
						}
						comments {
						  totalCount
						}
						reviews {
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

def calculate_duration(date_creation, date_action):
	date_time_obj_start = datetime.strptime(date_creation, "%Y-%m-%dT%H:%M:%SZ")
	date_time_obj_end = datetime.strptime(date_action, "%Y-%m-%dT%H:%M:%SZ")
	duration_in_s =  (date_time_obj_end - date_time_obj_start).total_seconds()
	return divmod(duration_in_s, 3600)[0]


def load_json(filename='repos_info.json'):
	try:
		with open(filename, 'r') as read_file:
			return json.load(read_file)

	except FileNotFoundError:
		print(f'Failed to read data... Perform get_repos and assure data.json is in folder.')


def save_data(dataframe, status):
	# with open('data_processed.json', 'a') as fp:
	# 	dataframe_tojson = dataframe.to_json()
	# 	json.dump(dataframe_tojson, fp, sort_keys=True, indent=4)
	dataframe.to_csv(os.path.abspath(os.getcwd()) + f'/{status}_export_dataframe.csv', index=False, header=True)

def do_github_request(repo, status, headers, pr_cursor, response):
	response = requests.post(
		f'{URL}',
		json={'query': create_query(cursor=pr_cursor, owner=repo['owner'], name=repo['name'], state=status.upper())},
		headers=headers)
	response.raise_for_status()
	return (dict(response.json()), response)

def save_clean_data(data, repo, status, prs):
	for d in data['data']['repository'][status.upper()]['nodes']:
		if d['databaseId'] not in prs['databaseId'].values:
			cleaned_data = dict()
			cleaned_data['owner'], cleaned_data['name'] = repo['owner'], repo['name']
			cleaned_data['id'], cleaned_data['databaseId'], cleaned_data['createdAt'], cleaned_data['additions'], \
			cleaned_data['deletions'], cleaned_data['closed'], cleaned_data['closedAt'], cleaned_data['merged'], \
			cleaned_data['mergedAt'], cleaned_data['body'], cleaned_data['participants'], cleaned_data['comments'], \
			cleaned_data['reviews'] = d['id'], d['databaseId'], d['createdAt'], d['additions'], d['deletions'], d['closed'], \
									  d['closedAt'], d['merged'], d['mergedAt'], len(d['body']), d['participants']['totalCount'], \
									  d['comments']['totalCount'], d['reviews']['totalCount']
			if status == 'merged':
				if cleaned_data['mergedAt']:
					cleaned_data['duration'] = calculate_duration(cleaned_data['createdAt'], cleaned_data['mergedAt'])
			elif status == 'closed':
				if cleaned_data['closedAt']:
					cleaned_data['duration'] = calculate_duration(cleaned_data['createdAt'], cleaned_data['closedAt'])

			if cleaned_data['reviews'] > 0 and cleaned_data['duration'] > 1:
				prs = prs.append(cleaned_data, ignore_index=True)
	return prs


if __name__ == "__main__":
	print(f"\n**** Starting GitHub API Requests *****\n")
	repos = list(load_json("repos_info.json"))
	list_status = ['merged', 'closed']
	token_index = 0
	remaining_nodes = 5000
	headers = generate_new_header()
	pr_cursor = None
	response= ""
	for status in list_status:
		prs = pd.read_csv(os.path.abspath(os.getcwd()) + f"/{status}_export_dataframe.csv")
		for repo in repos:
			print('Starting {} PRs for repository {}/{}...'.format(status, repo['owner'], repo['name']))
			page_counter=0
			totalcount_name= "prs_"+status
			total_pages = repo[totalcount_name] // 10
			hasNextPage = True
			while hasNextPage:
				try:
					if remaining_nodes < 200:
						print('Changing GitHub Access Token...')
						headers = generate_new_header()

					data, response = do_github_request(repo, status, headers, pr_cursor, response)

					prs = save_clean_data(data, repo, status, prs)

					pr_cursor = data['data']['repository'][status.upper()]['pageInfo']['endCursor']
					hasNextPage = data['data']['repository'][status.upper()]['pageInfo']['hasNextPage']
					remaining_nodes = data['data']['rateLimit']['remaining']

					if hasNextPage:
						print('Continuing with same repository {}/{}...'.format(repo['owner'], repo['name']))

					else:
						print('Changing to next repository...')

				except requests.exceptions.ConnectionError:
					print(f'Connection error during the request')

				except requests.exceptions.HTTPError:
					print(f'HTTP request error. STATUS: {response.status_code}')

				except FileNotFoundError:
					print(f'File not found.')

				finally:
					print('Completed page {}/{} of {} PRs for repository {}/{}'.format(page_counter, total_pages, status, repo['owner'], repo['name']))
					save_data(prs, status)
					page_counter +=1
