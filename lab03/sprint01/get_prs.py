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
    new_header = {
        'Content-Type': 'application/json',
        'Authorization': f'bearer {TOKEN_LIST[token_index]}'
    }
    if token_index < len(TOKEN_LIST) - 1:
        token_index += 1
    else:
        token_index = 0
    return new_header


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
                        files {
                            totalCount
                        }
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
    duration_in_s = (date_time_obj_end - date_time_obj_start).total_seconds()
    return divmod(duration_in_s, 3600)[0]


def load_json(filename='repos_info.json'):
    try:
        with open(filename, 'r') as read_file:
            return json.load(read_file)

    except FileNotFoundError:
        print(f'Failed to read data... Perform get_repos and assure data.json is in folder.')


def save_data(dataframe):
    # with open('data_processed.json', 'a') as fp:
    # 	dataframe_toJson = dataframe.to_json()
    # 	json.dump(dataframe_toJson, fp, sort_keys=True, indent=4)
    dataframe.to_csv(os.path.abspath(os.getcwd()) + f'/{status}_export_dataframe.csv', index=False, header=True)


def do_github_request(repository):
    res = requests.post(
        f'{URL}',
        json={'query': create_query(cursor=pr_cursor, owner=repository['owner'],
                                    name=repository['name'], state=status.upper())},
        headers=headers)
    res.raise_for_status()
    return dict(res.json()), res


def save_clean_data(prs):
    for d in data['data']['repository'][status.upper()]['nodes']:
        if d['databaseId'] not in prs['databaseId'].values:
            cleaned_data = dict()
            cleaned_data['owner'] = repo['owner']
            cleaned_data['name'] = repo['name']
            cleaned_data['id'] = d['id']
            cleaned_data['databaseId'] = d['databaseId']
            cleaned_data['createdAt'] = d['createdAt']
            cleaned_data['additions'] = d['additions']
            cleaned_data['deletions'] = d['deletions']
            cleaned_data['number_of_files'] = d['files']['totalCount']
            cleaned_data['closed'] = d['closed']
            cleaned_data['closedAt'] = d['closedAt']
            cleaned_data['merged'] = d['merged']
            cleaned_data['mergedAt'] = d['mergedAt']
            cleaned_data['body'] = len(d['body'])
            cleaned_data['number_of_participants'] = d['participants']['totalCount']
            cleaned_data['number_of_comments'] = d['comments']['totalCount']
            cleaned_data['reviews'] = d['reviews']['totalCount']
            cleaned_data['totalLines'] = cleaned_data['additions'] + cleaned_data['deletions']

            if cleaned_data['number_of_files']:
                cleaned_data['linesFile'] = cleaned_data['totalLines'] / cleaned_data['number_of_files']
            else:
                cleaned_data['linesFile'] = 0

            if status == 'merged':
                if cleaned_data['mergedAt']:
                    cleaned_data['duration'] = calculate_duration(cleaned_data['createdAt'], cleaned_data['mergedAt'])
            elif status == 'closed':
                if cleaned_data['closedAt']:
                    cleaned_data['duration'] = calculate_duration(cleaned_data['createdAt'], cleaned_data['closedAt'])

            if cleaned_data['reviews'] > 0 and cleaned_data['duration'] >= 1:
                print('adding a pr to PRS')
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
    response = ""
    skip = True
    for status in list_status:
        prs = pd.read_csv(os.path.abspath(os.getcwd()) + f"/{status}_export_dataframe.csv")
        for repo in repos:
            print('Starting {} PRs for repository {}/{}...'.format(status, repo['owner'], repo['name']))
            page_counter = 0
            totalCount_name = "prs_" + status
            total_pages = round(repo[totalCount_name] / 10 + 0.5)
            hasNextPage = True
            while hasNextPage:
                try:
                    if remaining_nodes < 200:
                        print('Changing GitHub Access Token...')
                        headers = generate_new_header()

                    data, response = do_github_request(repo)
                    prs = save_clean_data(prs)

                    pr_cursor = data['data']['repository'][status.upper()]['pageInfo']['endCursor']
                    hasNextPage = data['data']['repository'][status.upper()]['pageInfo']['hasNextPage']
                    remaining_nodes = data['data']['rateLimit']['remaining']

                    if not hasNextPage:
                        print('Changing to next repository...')
                        pr_cursor = None

                except requests.exceptions.ConnectionError:
                    print(f'Connection error during the request')

                except requests.exceptions.HTTPError:
                    print(f'HTTP request error. STATUS: {response.status_code}')

                except FileNotFoundError:
                    print(f'File not found.')

                finally:
                    print('Completed page {}/{} of {} PRs for repository {}/{}'.format(
                        page_counter, total_pages, status, repo['owner'], repo['name']))
                    save_data(prs)
                    page_counter += 1
