import os
import json
import requests
import time

import dotenv

NUM_ITERATION = 5

dotenv.load_dotenv()

URL = 'https://api.github.com/graphql'
TOKEN_LIST = json.loads(os.getenv("GITHUB_ACCESS_TOKENS"))


def generate_new_header():
    new_header = {
        'Content-Type': 'application/json',
        'Authorization': f'bearer {TOKEN_LIST[0]}'
    }
    return new_header


def create_query(cursor=None, complete=False):
    if cursor is None:
        cursor = 'null'

    else:
        cursor = '\"{}\"'.format(cursor)
    query = """
    query github {
        search (query: "location:US",  type: USER, first: 5, after: %s) {
            edges {
              node {
                ... on User {
                  id
                }
              }
            }
            pageInfo {
              endCursor
            }
          }
        }
    """ % (cursor)

    if complete:
        query = """
        query github {
            search (query: "location:US",  type: USER, first: 5, after: %s) {
                edges {
                  node {
                    ... on User {
                      id
                    }
                  }
                }
                pageInfo {
                  endCursor
                }
              }
            }
        """ % (cursor)
    return query


if __name__ == "__main__":
    print(f"\n**** Starting APIs Reports *****\n")
    print(f"\n**** Starting GraphQL *****\n")
    headers = generate_new_header()
    print(f"\n**** One attribute *****\n")
    print(f"\n**** No pagination *****\n")
    iteration = 1
    last_cursor = None
    while iteration <= NUM_ITERATION:
        try:
            start = time.time()
            response = requests.post(f'{URL}', json={'query': create_query(last_cursor)}, headers=headers)
            end = time.time()
            size = len(str(response.json()))

        except requests.exceptions.ConnectionError:
            print(f'Connection error during the request')

        except requests.exceptions.HTTPError:
            print(f'HTTP request error. STATUS: {response.status_code}')

        except requests.exceptions.ChunkedEncodingError:
            print('A bizarre error occurred...')

        else:
            print(f"[GRAPHQL; ONE ATTRIBUTE; NO PAGINATION] Iteration {iteration}\nTime:{end - start}\nSize:{size}\n")
            iteration+=1

    print(f"\n**** With pagination *****\n")
    iteration = 1
    while iteration <= NUM_ITERATION:
        try:
            size = 0
            last_cursor = None
            start = time.time()
            for _ in range(100):
                response = requests.post(f'{URL}', json={'query': create_query(last_cursor)}, headers=headers)
                response.raise_for_status()
                last_cursor = dict(response.json())['data']['search']['pageInfo']['endCursor']
                size += len(str(response.json()))
            end = time.time()

        except requests.exceptions.ConnectionError:
            print(f'Connection error during the request')

        except requests.exceptions.HTTPError:
            print(f'HTTP request error. STATUS: {response.status_code}')

        except requests.exceptions.ChunkedEncodingError:
            print('A bizarre error occurred...')

        else:
            print(f"[GRAPHQL; ONE ATTRIBUTE; WITH PAGINATION]Iteration {iteration}\nTime:{end - start}\nSize:{size}\n")
            iteration += 1
