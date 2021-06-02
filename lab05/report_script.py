import os
import json
import requests
import time

import dotenv

NUM_ITERATION = 5
NUM_PER_PAGE = 10
NUM_PAGES = 10

dotenv.load_dotenv()

URL_GRAPHQL = 'https://api.github.com/graphql'
URL_REST = f'https://api.github.com/search/users?q=location%3AUS&per_page={NUM_PER_PAGE}&page='
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


def create_query_graphql(cursor=None, all_attributes=False, with_pagination=False):
    if with_pagination:
        if cursor is None:
            cursor = 'null'

        else:
            cursor = '\"{}\"'.format(cursor)

    if not with_pagination and not all_attributes:
        query = """
        query github {
            search (query: "location:US",  type: USER, first: %s) {
                edges {
                  node {
                    ... on User {
                      id
                    }
                  }
                }
              }
            }
        """ % (NUM_PER_PAGE)

    elif with_pagination and not all_attributes:
        query = """
        query github {
            search (query: "location:US",  type: USER, first: %s, after: %s) {
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
        """ % (NUM_PER_PAGE, cursor)

    elif not with_pagination and all_attributes:
        query = """
         query github {
             search (query: "location:US",  type: USER, first: %s) {
                 userCount
                 edges {
                   node {
                     ... on User {
                       login
                       databaseId
                       id
                       avatarUrl
                       url
                       isSiteAdmin
                     }
                   }
                 }
               }
             }
         """ % (NUM_PER_PAGE)

    elif with_pagination and all_attributes:
        query = """
         query github {
             search (query: "location:US",  type: USER, first: %s, after: %s) {
                 userCount
                 edges {
                   node {
                     ... on User {
                       login
                       databaseId
                       id
                       avatarUrl
                       url
                       isSiteAdmin
                     }
                   }
                 }
                pageInfo {
                  endCursor
                }
              }
            }
        """ % (NUM_PER_PAGE, cursor)

    return query


def request_graphql(all_attributes=False, with_pagination=False):
    global header
    try:
        if not with_pagination:
            response = requests.post(f'{URL_GRAPHQL}',
                                     json={'query': create_query_graphql(None, all_attributes, with_pagination)},
                                     headers=header)
            response.raise_for_status()
            response_size = len(str(response.json()))
        else:
            response_size = 0
            last_cursor = None
            for _ in range(NUM_PAGES):
                response = requests.post(f'{URL_GRAPHQL}', json={
                    'query': create_query_graphql(last_cursor, all_attributes, with_pagination)}, headers=header)
                response.raise_for_status()
                last_cursor = dict(response.json())['data']['search']['pageInfo']['endCursor']
                response_size += len(str(response.json()))
    except requests.exceptions.ConnectionError:
        print(f'Connection error during the request')

    except requests.exceptions.HTTPError:
        print(f'HTTP request error. STATUS: {response.status_code}')

    except requests.exceptions.ChunkedEncodingError:
        print('A bizarre error occurred...')

    else:
        return response_size


def request_rest(with_pagination=False):
    global header
    try:
        if not with_pagination:
            url = URL_REST + '1'
            response = requests.get(url, headers=header)
            response.raise_for_status()
            response_size = len(str(response.json()))
        else:
            response_size = 0
            for page in range(1, NUM_PAGES + 1):
                url = URL_REST + str(page)
                condition = True
                while condition:
                    try:
                        response = requests.get(url, headers=header)
                        response.raise_for_status()
                    except requests.exceptions.HTTPError:
                        print(f'HTTP request error. STATUS: {response.status_code}')
                        print(response.json())
                        header = generate_new_header()
                    else:
                        response_size += len(str(response.json()))
                        condition = False

    except requests.exceptions.ConnectionError:
        print(f'Connection error during the request')

    except requests.exceptions.HTTPError:
        print(f'HTTP request error. STATUS: {response.status_code}')

    except requests.exceptions.ChunkedEncodingError:
        print('A bizarre error occurred...')

    else:
        return response_size


if __name__ == "__main__":
    global header
    token_index = 1
    header = generate_new_header()
    print(f"\n**** Starting APIs Reports *****\n")
    print(f'NUM_ITERATION = {NUM_ITERATION}\nNUM_PER_PAGE = {NUM_PER_PAGE}\nNUM_PAGES = {NUM_PAGES}')
    print(f"\n**** Starting GraphQL *****\n")
    for with_pagination in [False, True]:
        for all_attributes in [False, True]:
            iteration = 1
            last_cursor = None
            while iteration <= NUM_ITERATION:
                start = time.time()
                size = request_graphql(all_attributes, with_pagination)
                end = time.time()

                print(
                    f"[GRAPHQL;{'ALL ATTRIBUTES' if all_attributes else 'ONE ATTRIBUTE'}; {'WITH PAGINATION' if with_pagination else 'ONE PAGE'}] Iteration {iteration}\nTime:{end - start}\nSize:{size}\n")
                iteration += 1

    print(f"\n**** Starting REST *****\n")
    for with_pagination in [False, True]:
        for all_attributes in [False, True]:
            iteration = 1
            last_cursor = None
            while iteration <= NUM_ITERATION:
                start = time.time()
                size = request_rest(with_pagination)
                end = time.time()

                print(
                    f"[REST;{'ALL ATTRIBUTES' if all_attributes else 'ONE ATTRIBUTE'}; {'WITH PAGINATION' if with_pagination else 'ONE PAGE'}] Iteration {iteration}\nTime:{end - start}\nSize:{size}\n")
                iteration += 1
