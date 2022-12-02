try:
  import googleclouddebugger
  googleclouddebugger.enable()
except ImportError:
  pass
import os, requests, json, pandas
from math import floor
from multiprocessing import Pool
from time import time
from flask import Flask, render_template, send_from_directory, request, Markup

from google.cloud import bigquery
from google.oauth2 import service_account as SA




class saClient:
    def __init__(self, service_account_path, scopes=[]):
        self.sa_file = service_account_path
        self.scopes = scopes

    def creds(self, scopes=None):
        return SA.Credentials.from_service_account_file(self.sa_file, scopes=(scopes or self.scopes))


app = Flask(__name__)

SAC = saClient(os.path.join('.secrets','googleSA.json'), ['https://www.googleapis.com/auth/bigquery'])
bigquery_client = bigquery.client.Client(project='rusty-dt', credentials=SAC.creds())

def readFile(file):
    try:   
        with open(file, 'r') as inf:
            data = inf.read()
        return data
    except Exception as e: 
        print("Couldnt load data: ", e)
        return


TW_BEARER = readFile(os.path.join('.secrets', 'twitter.bearer'))


getNextElection = """
		SELECT *
		FROM  `rusty-dt.ae_data.elections` 
		WHERE pollsClose>UNIX_SECONDS(CURRENT_TIMESTAMP())
		ORDER BY pollsClose
		LIMIT 1
		"""
def getSearchTerms():
	return f"""
			SELECT term
			FROM  `rusty-dt.ae_data.searchTerms` 
			WHERE year=cast((SELECT electionYear from `rusty-dt.ae_data.elections` WHERE pollsClose>UNIX_SECONDS(CURRENT_TIMESTAMP()) ORDER BY pollsClose LIMIT 1) as int64)
			"""



def searchTweets(p):
	searchTerm=p[0]
	token=p[1]
	try:
		response = requests.get(
			url='https://api.twitter.com/1.1/search/tweets.json',
			headers = {
				'authorization': f'Bearer {token}', 
				'content-type': 'application/json'
			},
			params = {'q': searchTerm,
						'count':3,
						'result_type' : 'mixed'

			}
		)
		print('Response HTTP Status Code: {status_code}'.format(
			status_code=response.status_code))
		print('Response HTTP Response Body: {content}'.format(
			content=response))
		#print(response.content)
		tweets = json.loads(response.content)
		return pandas.DataFrame([[t['id'], t['user']['screen_name'], t['user']['name'], t['text']] for t in tweets['statuses']], columns=['id', 'screen_name','name','text'])
		
	except requests.exceptions.RequestException as e:
		print(e)
		return e




@app.route('/tweets')
def tweets():
	searchTerms = bigquery_client.query(getSearchTerms()).result()
	terms = [t[0] for t in searchTerms]

	print("Search term in bq: ", terms)
	allTweets = []

	twPool = Pool(4)
	allTweets = twPool.map(searchTweets, [f for f in zip(terms, [TW_BEARER]*(len(terms)))])

	#print(allTweets)
	allTweets = pandas.concat(allTweets)
	allTweets = allTweets.drop_duplicates(subset='id')
	ids = allTweets.id.to_list()
	names = allTweets.name.to_list()
	text = allTweets.text.to_list()
	screen_names = allTweets.screen_name.to_list()
	data = list(zip(ids, screen_names, names, text))
	return render_template('/tweets.html', tweets = data)

@app.route('/')
def main():
	
	nextElection = bigquery_client.query(getNextElection).result()
	nextElection = [d for d in nextElection]
	electionYear, pollsClose, humanDT = nextElection[0]

	print("header: ", request.headers)
	#This works in GCP AppEngine
	if 'X-AppEngine-City' in request.headers:
		city = Markup(request.headers['X-AppEngine-City'].title())
		country = request.headers['X-AppEngine-Country']
		state = request.headers['X-AppEngine-Region'].upper()
	#This [sometimes] works in Heroku
	elif 'X-Forwarded-For' in request.headers:
		print(f"ip:{request.headers['X-Forwarded-For']}")
		locale = requests.get(f"http://ip-api.com/json/{request.headers['X-Forwarded-For']}").json()
		city=locale['city'] 
		country=locale['countryCode']
		state=locale['region']
		print(f"location api: {city}, {country}, {state}")
		print("full locale: ", locale)
	else:
		city, country, state = 'NA', 'US','NY'

	d = pollsClose - time() 
	return render_template('index.html', 
		electionYear = electionYear,
		humanDT = humanDT,
		days = int(floor(d/86400)), 
		hours= int((d % 86400)/3600), 
		mins = int((d % 86400 )/3600 %1 * 60 ),
		secs = int(((d % 86400 )/3600 %1 * 60 ) % 1 * 60 ), 
		city = city, state=state, country=country
		)

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')

if __name__ == '__main__':
	app.run(threaded=True, debug=True, host="0.0.0.0")

# [END gae_python37_bigquery]
