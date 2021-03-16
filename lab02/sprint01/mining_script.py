import os
import dotenv
import requests
import pandas as pd
from datetime import datetime
from github import Github

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

print("\n****  GitHub API Requests Succeeded *****\n")

print("\n****  Starting Cloning Process *****\n")

github = Github("admited", TOKEN)
github_user = github.get_user()

# repos = nodes["Owner/Repository"]

nodes['CBO'] = ''
nodes['DIT'] = ''
nodes['WMC'] = ''
nodes['LOC'] = ''

for index, row in nodes.iterrows():
    original_repo = github.get_repo(row['Owner/Repository'])
    cmd = "git clone {}".format(original_repo.clone_url)
    print("Starting to clone {}. The {}th repo...".format(original_repo.name, index))
    print("Running command '{}'".format(cmd))

    try:
        os.system(cmd)
        print("Finished cloning {}".format(original_repo.name))

        print("Calculating metrics..")
        cmd = "java -jar ck.jar {}/{}/ 1 0 0".format(os.path.abspath(os.getcwd()), original_repo.name)
        success = os.system(cmd)
        # Leitura do csv criado pelo CK, selecionando apenas as colunas que importam para o estudo
        metrics_df = pd.read_csv(os.path.abspath(os.getcwd()) + "/class.csv", usecols=['cbo', 'dit', 'wmc', 'loc'])
        # Cálculo das medianas de cada métrica do repositório atual
        medians = metrics_df.median(skipna=True)
        """
        Se definirmos skipna=True, ele ignora a NaN no campo de dados.
        Isto nos permite calcular a mediana do DataFrame ao longo do eixo da coluna, ignorando os valores NaN.
        """
        # Adicionando os valores calculados no DataFrame principal na linha correspondente ao repositório
        nodes.loc[index, 'CBO'] = medians['cbo']
        nodes.loc[index, 'DIT'] = medians['dit']
        nodes.loc[index, 'WMC'] = medians['wmc']
        nodes.loc[index, 'LOC'] = medians['loc']

        # Comando para apagar o repositório clonado a cada iteração
        cmd = "rm -rf {}".format(original_repo.name)
        os.system(cmd)
        print("Finished removing {}".format(original_repo.name))
        print("#####################################")
        print("")
        if success != 0:
            raise Exception("Error when apply metrics...")

    except Exception as e:
        print('Failure at repo {}'.format(original_repo.name))
        print(e)

nodes.to_csv(os.path.abspath(os.getcwd()) + f'/export_dataframe.csv', index=False, header=True)
print("Successful mining! Saved csv with mining results")
