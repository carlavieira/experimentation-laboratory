import os
import dotenv
import requests
import pandas as pd
from datetime import date, datetime
from github import Github
# from ds4se.metrics_java import JavaAnalyzer

num_sprint = "01"
num_nodes_total = 100
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
        search (query: "language:java", type:REPOSITORY, first:""" + str(num_nodes_request) + """) {
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
            search (query: "language:java", type:REPOSITORY, first:""" + str(
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
nodes = pd.DataFrame()
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

nodes = nodes.rename(columns={'nameWithOwner': 'Owner/Repository', 'stargazers': 'Stars', 'createdAt': 'Repository Age', 'releases': 'Total Releases'})
nodes['Stars'] = nodes['Stars'].apply(lambda x : x['totalCount'])
nodes['Repository Age'] = nodes['Repository Age'].apply(calculate_age)
nodes['Total Releases'] = nodes['Total Releases'].apply(lambda x : x['totalCount'])


print("\n****  GitHub API Requests Succeeded *****\n")

print("\n****  Starting Cloning Process *****\n")



github = Github("admited", TOKEN)
github_user = github.get_user()

#repos = nodes["Owner/Repository"]
repos = ["freeCodeCamp/freeCodeCamp", ]


for repo in repos:
    original_repo = github.get_repo(repo)
    cmd = "git clone {}".format(original_repo.clone_url)
    print("Starting to clone {}".format(original_repo.name))
    print("Running command '{}'".format(cmd))
    os.system(cmd)
    print("Finshed cloning {}".format(original_repo.name))

    print("Calculando métricas..")

    cmd = "rm -rf {}".format(original_repo.name)
    os.system(cmd)
    print("Finshed removing {}".format(original_repo.name))
    print("#####################################")
    print("")



nodes.to_csv(os.path.abspath(os.getcwd()) + f'/sprint{num_sprint}/export_dataframe.csv', index=False, header=True)
print("Successful mining! Saved csv with mining results")
