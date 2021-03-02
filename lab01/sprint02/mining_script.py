import dotenv
import os
import requests
import pandas as pd

num_sprint="02"
num_nodes_total=1000
num_nodes_request=5

# Retrieves Github API Token from .env
dotenv.load_dotenv(dotenv.find_dotenv())
TOKEN = os.getenv("GITHUB_ACCESS_TOKEN")
HEADERS = {
    'Content-Type': 'application/json',
    'Authorization': f'bearer {TOKEN}'
}
URL = 'https://api.github.com/graphql'

# Query to be made on the current test
def create_query(last_cursor):
    QUERY = """
     query github {
        search (query: "stars:>10000", type:REPOSITORY, first:"""+str(num_nodes_request)+""") {
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
    if last_cursor is not None:
        QUERY = """
         query github {
            search (query: "stars:>10000", type:REPOSITORY, first:"""+str(num_nodes_request)+""", after:"""+"\""+(last_cursor)+"\""+""") {
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
    return QUERY


# RQ 01 -> ON REPOSITORY/CREATED AT
# RQ 02 -> pullRequests(merged)/totalCount
# RQ 03 -> releases/totalCount
# RQ 04 -> ON REPOSITORY/PUSHED AT
# RQ 05 -> primaryLanguage / name
# RQ 06 -> closedIssues / totalCount

last_cursor = None
nodes = pd.DataFrame()
pages = num_nodes_total // num_nodes_request
print(f"It will take {pages} pages")
for page in range(pages):

    condition = True
    while condition:

        try:
            response = requests.post(f'{URL}', json={'query': create_query(last_cursor)}, headers=HEADERS)
            response.raise_for_status()
            data = dict(response.json())
            last_cursor=data['data']['search']['pageInfo']['endCursor']
            df = pd.DataFrame(data['data']['search']['nodes'])
            nodes = nodes.append(df)

        except requests.exceptions.ConnectionError:
            print(f'Connection error during the request')

        except requests.exceptions.HTTPError:
            print(f'HTTP request error. STATUS: {response.status_code}')

        except FileNotFoundError:
            print(f'File not found.')

        else:
            print(f"Page {page}/{pages} succeeded!")
            condition = False

nodes.to_csv(os.path.abspath(os.getcwd()) + f'/sprint{num_sprint}/export_dataframe.csv', index=False, header=True)
print("Successful mining! Saved csv with mining results")
