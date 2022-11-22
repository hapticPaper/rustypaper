import requests, json



def token():
    # Request
    # POST https://api.twitter.com/oauth2/token

    try:
        response = requests.post(
            url="https://api.twitter.com/oauth2/token",
            params={
                "grant_type": "client_credentials",
            },
            headers={
                "Authorization": "Basic WjZ6WEtXNEpRUVRXZGhsMGpRaHRBRjJONDp0SzhDcXBHTEo2RHBNWHhLamM3Mmh0YmhPUGx5OU5xcXRYQ2NIeWNNelpaaldnRndSaA==",
                "Content-Type": "text/plain; charset=utf-8",
            },
            data="grant_type=client_credentials"
        )
        print('Response HTTP Status Code: {status_code}'.format(
            status_code=response.status_code))
        print('Response HTTP Response Body: {content}'.format(
            content=response.content))
        return json.loads(response.content)
    except requests.exceptions.RequestException:
        print('HTTP Request failed')


def readFile(file):
    try:   
        with open(file, 'r') as inf:    
            data = inf.read()
        return data
    except Exception as e: 
        print("Couldnt load data: ", e)
        return


def searchTweets(searchTerm, token):
    try:
        response = requests.get(
            url='https://api.twitter.com/1.1/search/tweets.json',
            headers = {
                'authorization': f'Bearer {token}', 
                'content-type': 'application/json'
            },
            params = {'q': searchTerm,
                      'count':4,
                      'result_type' : 'mixed'

            }
        )
        print('Response HTTP Status Code: {status_code}'.format(
            status_code=response.status_code))
        print('Response HTTP Response Body: {content}'.format(
            content=response))
        #print(response.content)
        return json.loads(response.content)
    except requests.exceptions.RequestException as e:
        print(e)
        return e

bearer = readFile('private/twitter.bearer')
print(bearer)
for term in ['elizabeth warren','bernie sanders','trump','impeach','2020 election']:
    try:            
        tweets = searchTweets(term, bearer)
        print([[t['id'], t['text']] for t in tweets['statuses']])
    except Exception as e:
        print(f"Problem getting tweets - {e}, {tweets}")