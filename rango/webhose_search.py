import json
import urllib.parse
import urllib.request
from os import chdir


def read_webhose_key():
    """
    Reads the Webhouse API key from a file called 'search.key'.
    :return: None (if no key) or the key as a string.
    """
    webhose_api_key = None
    try:
        with open('search.key', 'r') as f:
            webhose_api_key = f.readline().strip()
    except:
        raise IOError('search.key file not found')

    return webhose_api_key


def run_query(search_terms, size=10):
    """
    :param search_terms: String containing search terms.
    :param size:         Number of results to return.
    :return:             List of results from Webhose API, each with title,
                            link, and summary.
    """
    webhose_api_key = read_webhose_key()

    if not webhose_api_key:
        raise KeyError('Webhose key not found')

    # Base URL for Webhose API
    root_url = 'http://webhose.io/search'

    # Format the query string - escape special characters
    query_string = urllib.parse.quote(search_terms)

    # Construct complete API URL.
    search_url = ('{root_url}?token={key}&format=json&q={query}'
                  '&sort=relevancy&size={size}').format(
                    root_url=root_url,
                    key=webhose_api_key,
                    query=query_string,
                    size=size)

    results = []

    try:
        # Connect to API and convert response to Python dictionary.
        response = urllib.request.urlopen(search_url).read().decode('utf-8')
        json_response = json.loads(response)

        # Loop through the posts, appending each to results list as a
        # dictionary. Restrict summary to 200 characters.
        for post in json_response['posts']:
            results.append({'title': post['title'],
                            'link': post['url'],
                            'summary': post['text'][:200]})
    except:
        print("Error when querying the Webhouse API")

    # Return the list of results to the calling function.
    return results


if __name__ == '__main__':
    chdir('..')
    search = input("Enter search terms:\n")
    result = run_query(search)
    print(result)