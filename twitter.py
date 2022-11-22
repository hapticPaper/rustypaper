import requests
import os
import json
from dotenv import load_dotenv

load_dotenv(os.path.join('.secrets','.secrets')

# To set your environment variables in your terminal run the following line:
# export 'BEARER_TOKEN'='<your_bearer_token>'
bearer_token = os.environ.get("TWITTER_BEARER")

API_URL = "https://api.twitter.com/2"

# Optional params: start_time,end_time,since_id,until_id,max_results,next_token,
# expansions,tweet.fields,media.fields,poll.fields,place.fields,user.fields
query_params = {'query': '(from:twitterdev -is:retweet) OR #twitterdev','tweet.fields': 'author_id'} 
basic_query={'query': 'entity:"Ukraine" OR entity:"2024 Election" OR entity:"DeSantis" OR entity:"Biden" is:verified lang:en', 
             'tweet.fields': 'attachments,author_id,conversation_id,created_at,edit_controls,edit_history_tweet_ids,geo,id,in_reply_to_user_id,lang,possibly_sensitive,public_metrics,referenced_tweets,reply_settings,source,text,withheld',
             #'created_at,lang,conversation_id,author_id,text', #attachments,entities,geo,in_reply_to_user_id,non_public_metrics_possibly_sensitive,public_metrics_witheld,source,promoted_metrics,referenced_tweets',
             'max_results':20,
             'sort_order':'relevancy' }


def bearer_oauth(r):
    """
    Method required by bearer token authentication.
    """

    r.headers["Authorization"] = f"Bearer {bearer_token}"
    r.headers["User-Agent"] = "v2RecentSearchPython"
    return r



def connect_to_endpoint(url = API_URL, endpoint="/tweets/search/recent", params=basic_query):
    response = requests.get(f"{url}{endpoint}", auth=bearer_oauth, params=params)
    print(response.status_code)
    if response.status_code != 200:
        raise Exception(response.status_code, response.text)
    return response.json()

def getSampleTweets():
    tweets = connect_to_endpoint(params=basic_query)
    authors = connect_to_endpoint(endpoint="/users", params={'ids':','.join([t['author_id'] for t in tweets['data']])})
    authors = {a['id']:f"{a['name']} (@{a['username']})" for a in authors['data']}
    return {authors[n['author_id']]:n['text'] for n in tweets['data']}