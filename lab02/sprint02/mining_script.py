import os
import dotenv
import requests
import pandas as pd
from datetime import datetime


num_sprint = "01"
num_nodes_total = 1000
num_nodes_request = 10

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
        search (query: "stars:>100 language:java", type:REPOSITORY, first:""" + str(num_nodes_request) + """) {
            pageInfo {
                endCursor
                }
            nodes {
              ... on Repository {
                nameWithOwner
                createdAt
                stargazers {
                  totalCount
                }
                releases {
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
            search (query: "stars:>100 language:java", type:REPOSITORY, first:""" + str(
            num_nodes_request) + """, after:""" + "\"" + cursor + "\"" + """) {
                pageInfo {
                    endCursor
                    }
                nodes {
                  ... on Repository {
                    nameWithOwner
                    createdAt
                    stargazers {
                      totalCount
                    }
                    releases {
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


last_cursor = None
# nodes = pd.DataFrame()
repos_data_array = []
pages = num_nodes_total // num_nodes_request
print(f"\n**** Starting GitHub API Requests *****\n")
print(f"It will take {pages} pages\n")
response = ""
for page in range(pages):

    condition = True
    while condition:

        try:
            response = requests.post(f'{URL}', json={'query': create_query(last_cursor)}, headers=HEADERS)
            response.raise_for_status()
            data = dict(response.json())

            last_cursor = data['data']['search']['pageInfo']['endCursor']

            for d in data['data']['search']['nodes']:
                repos_data_array.append(d)

        except requests.exceptions.ConnectionError:
            print(f'Connection error during the request')

        except requests.exceptions.HTTPError:
            print(f'HTTP request error. STATUS: {response.status_code}')

        except FileNotFoundError:
            print(f'File not found.')

        else:
            print(f"Page {page + 1}/{pages} succeeded!")
            condition = False

nodes = pd.DataFrame(repos_data_array)

nodes = nodes.rename(columns={'nameWithOwner': 'Owner/Repository', 'stargazers': 'Stars', 'createdAt': 'Repository Age',
                              'releases': 'Total Releases'})
nodes['Stars'] = nodes['Stars'].apply(lambda x: x['totalCount'])
nodes['Repository Age'] = nodes['Repository Age'].apply(calculate_age)
nodes['Total Releases'] = nodes['Total Releases'].apply(lambda x: x['totalCount'])

nodes['CBO'] = ''
nodes['DIT'] = ''
nodes['WMC'] = ''
nodes['LOC'] = ''

print("\n****  GitHub API Requests Succeeded *****\n")

nodes.to_csv(os.path.abspath(os.getcwd()) + f'/export_dataframe.csv', index=False, header=True)
print("Successful mining! Saved csv with mining results")
