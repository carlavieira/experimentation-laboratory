import os
import dotenv
import requests
import pandas as pd
from datetime import date, datetime

num_sprint = "02"
num_nodes_total = 200
num_nodes_request = 5

# Retrieves Github API Token from .env
dotenv.load_dotenv(dotenv.find_dotenv())
TOKEN = os.getenv("GITHUB_ACCESS_TOKEN")
HEADERS = {
    'Content-Type': 'application/json',
    'Authorization': f'bearer {TOKEN}'
}
URL = 'https://api.github.com/graphql'


# Query to be made on the current test
def create_query(cursor):
    query = """
     query github {
        search (query: "stars:>10000", type:REPOSITORY, first:""" + str(num_nodes_request) + """) {
            pageInfo {
                endCursor
                }
            nodes {
              ... on Repository {
                nameWithOwner
                createdAt  # RQ 01
                pushedAt
                primaryLanguage {
                  name
                } 
                stargazers {
                  totalCount
                }
                releases {
                  totalCount
                } # RQ 03
                mergedPRs: pullRequests(states: MERGED) {
                  totalCount
                }
                closedIssues: issues(states: CLOSED) {
                  totalCount
                } 
                totalIssues: issues {
                  totalCount
                }
              }
            }
        }
    }
    """
    if cursor is not None:
        query = """
         query github {
            search (query: "stars:>10000", type:REPOSITORY, first:""" + str(
            num_nodes_request) + """, after:""" + "\"" + cursor + "\"" + """) {
                pageInfo {
                    endCursor
                    }
                nodes {
                  ... on Repository {
                    nameWithOwner
                    createdAt
                    pushedAt
                    primaryLanguage {
                      name
                    } 
                    stargazers {
                      totalCount
                    }
                    releases {
                      totalCount
                    } # RQ 03
                    mergedPRs: pullRequests(states: MERGED) {
                      totalCount
                    }
                    closedIssues: issues(states: CLOSED) {
                      totalCount
                    } 
                    totalIssues: issues {
                      totalCount
                    }
                  }
                }
            }
        }
        """
    return query


def calculate_age(date_time_string):
    today = datetime.today()
    date_time_obj = datetime.strptime(date_time_string[0:10], "%Y-%m-%d")
    return (today - date_time_obj).days


def calculate_closed_issues_percent(op1, op2):
    if op2 > 0:
        return (op1/op2)*100

    return None


last_cursor = None
nodes = pd.DataFrame()
pages = num_nodes_total // num_nodes_request
print(f"It will take {pages} pages")
response = ""
for page in range(pages):

    condition = True
    while condition:

        try:
            response = requests.post(f'{URL}', json={'query': create_query(last_cursor)}, headers=HEADERS)
            response.raise_for_status()
            data = dict(response.json())
            last_cursor = data['data']['search']['pageInfo']['endCursor']

            df = pd.DataFrame(data['data']['search']['nodes'])
            nodes = nodes.append(df)

        except requests.exceptions.ConnectionError:
            print(f'Connection error during the request')

        except requests.exceptions.HTTPError:
            print(f'HTTP request error. STATUS: {response.status_code}')

        except FileNotFoundError:
            print(f'File not found.')

        else:
            print(f"Page {page+1}/{pages} succeeded!")
            condition = False

nodes['Repository Age'] = ''
nodes['Accepted Pull Requests'] = ''
nodes['Total Releases'] = ''
nodes['Time Since Last Update'] = ''
nodes['Language'] = ''
nodes['Closed Issues Percent'] = ''

for index, row in nodes.iterrows():

    nodes.loc[index, 'Repository Age'] = calculate_age(row['createdAt'])
    nodes.loc[index, 'Accepted Pull Requests'] = row['mergedPRs']['totalCount']
    nodes.loc[index, 'Total Releases'] = row['releases']['totalCount']
    nodes.loc[index, 'Days Since Last Update'] = calculate_age(row['pushedAt'])
    nodes.loc[index, 'Closed Issues Percent'] = calculate_closed_issues_percent(row['closedIssues']['totalCount'],
                                                                                row['totalIssues']['totalCount'])
    if row['primaryLanguage']:
        nodes.loc[index, 'Language'] = row['primaryLanguage']['name']
    else:
        nodes.loc[index, 'Language'] = None


nodes.to_csv(os.path.abspath(os.getcwd()) + f'/sprint{num_sprint}/export_dataframe.csv', index=False, header=True)
print("Successful mining! Saved csv with mining results")
