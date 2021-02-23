import dotenv
import os
import requests
import pandas as pd

# Retrieves Github API Token from .env
dotenv.load_dotenv(dotenv.find_dotenv())
TOKEN = os.getenv("GITHUB_ACCESS_TOKEN")
HEADERS = {
    'Content-Type': 'application/json',
    'Authorization': f'bearer {TOKEN}'
}
URL = 'https://api.github.com/graphql'

# Query to be made on the current test
QUERY = """
 query github {
    search (query: "stars:>10000", type:REPOSITORY, first:100) {
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
# RQ 01 -> ON REPOSITORY/CREATED AT
# RQ 02 -> pullRequests(merged)/totalCount
# RQ 03 -> releases/totalCount
# RQ 04 -> ON REPOSITORY/PUSHED AT
# RQ 05 -> primaryLanguage / name
# RQ 06 -> closedIssues / totalCount

condition = True

while condition:
    response = ''

    try:
        response = requests.post(f'{URL}', json={'query': QUERY}, headers=HEADERS)
        response.raise_for_status()
        data = dict(response.json())
        df = pd.DataFrame(data['data']['search']['nodes'])
        df.to_csv(os.path.abspath(os.getcwd()) + '/export_dataframe.csv', index=False, header=True)

    except requests.exceptions.ConnectionError:
        print(f'Connection error during the request')

    except requests.exceptions.HTTPError:
        print(f'HTTP request error. STATUS: {response.status_code}')

    except FileNotFoundError:
        print(f'File not found.')

    else:
        print("Nothing went wrong! Saved csv with mining results")
        condition = False
