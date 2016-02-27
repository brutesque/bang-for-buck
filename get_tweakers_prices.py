import requests, time, sqlite3
from bs4 import BeautifulSoup

def read_from_db():
	conn = sqlite3.connect('site/octane_tweakers.db')
	c = conn.cursor()

	c.execute("SELECT chipset, multiGpu, nGpuUsed, nResults, score FROM octaneScores")

	data = {}
	i = 0
	for row in c.fetchall():
		data[i] = {'chipset': row[0], 'nGpuUsed': row[2], 'score': row[4], 'multiGpu': row[1], 'nResults': row[3]}
		i += 1
	
	c.close()
	conn.close()
	
	return data


def getPriceOffers(keywords, minMemory=4096):
	"""
		>>> getPriceOffers('GTX 980')
	"""

	#
	#	Get html contents from price-comparison site
	#

	url = 'http://tweakers.net/categorie/49/videokaarten/producten/'
	payload = {
		'k': keywords.lower().replace(' ', '+'), # keyword
		'i19': minMemory, # Minimum memory size
#		'si': 4, # Minimum rating n/5
		'of': 'price', # Sort field
		'od': 'asc', # Sort order
#		'dc': 'NL', 
		'pageSize': 100
	}

	# The following delay is added on purpose to prevent spamming the site we're scraping data from. It's best to leave it in.
	delay = 10
	time.sleep( delay - ( time.time() % delay ) )

	r = requests.get(url, params=payload, headers={'user-agent': 'curl/7.7.2 (powerpc-apple-darwin6.0) libcurl 7.7.2 (OpenSSL 0.9.6b)'})
	if r.status_code != 200:
		if r.status_code == 404: return {}
		raise Exception('Expected status code 200: %s' % r.status_code)

	#
	#	Extract results from html code
	#

	soup = BeautifulSoup(r.content)
	listing = soup.find('table', {'class': 'listing'})

	results = {}
	i = 0
	for row in listing.find_all('tr', {'class': 'largethumb'}):

		# extract price
		try: price = row.find('p', {'class': 'price'}).a.text.split(' ')[1].split(',')
		except AttributeError: continue
		price[0] = ''.join(price[0].split('.'))
		try: price[1] = '00' if price[1] == u'-' else price[1]
		except IndexError: pass
		price = float('.'.join(price))

		# extract url
		url = row.find('p', {'class': 'price'}).a['href']

		# extract name
		name = row.find('td', {'class': 'itemname'}).find('p', {'class': 'ellipsis'}).a['title']

		# extract spec
		spec = row.find('td', {'class': 'itemname'}).find('p', {'class': 'specline'}).a.text

		# make at least the name or spec contain all of the keywords
		skip=False
		for keyword in keywords.split(' '):
			if keyword.lower() not in name.lower() and keyword.lower() not in spec.lower(): skip=True
		if skip: continue

		results[i] = {
			'price': price, 
			'url': url, 
			'name': name,
			'spec': spec,
		}
		i += 1
	return results

def save_results(data):
	conn = sqlite3.connect('site/octane_tweakers.db')
	c = conn.cursor()

	c.execute("CREATE TABLE IF NOT EXISTS gpuPrices(chipset TEXT, price REAL, url TEXT, score INT, pricePerPoint REAL, name TEXT, spec TEXT)")
	c.execute("DELETE FROM gpuPrices")

	for key, value in data.items():
		if not value['price'] == None:
			c.execute("INSERT INTO gpuPrices (chipset, price, url, score, pricePerPoint, name, spec) VALUES (?, ?, ?, ?, ?, ?, ?)", (value['chipset'], value['price'], value['url'], value['score'], value['pricePerPoint'], value['name'], value['spec']))

	conn.commit()

	c.close()
	conn.close()


def collectOffers(octanebenchResults, keywords=None):
	"""
		First get your render scores
		>>> octanebenchResults = scrapeOctanebenchResults()

		Now collect best price for every chipset
		>>> collectBestPriceOffers(octanebenchResults)

		You can add extra keywords to get more specific results
		>>> collectBestPriceOffers(octanebenchResults, 'evga')
		>>> collectBestPriceOffers(octanebenchResults, 'evga superclocked')
	"""
	gpus = {}
	i = 0
	for key, value in octanebenchResults.items():

		if not keywords == None: gpu = ' '.join([value['chipset'], keywords])
		else: gpu = value['chipset']
		priceOffers = getPriceOffers(gpu)

		for j, priceOffer in priceOffers.items():
			pricePerPoint = None
			pricePerPoint = priceOffer['price'] / value['score']

			gpus[i] = {
				'chipset': value['chipset'],
				'price': priceOffer['price'],
				'url': priceOffer['url'],
				'name': priceOffer['name'],
				'spec': priceOffer['spec'],
				'pricePerPoint': pricePerPoint, 
				'score': value['score']
			}
			i += 1
	return gpus

if __name__ == "__main__":
	octanebenchResults = read_from_db()
	gpuPrices = collectOffers(octanebenchResults)
	save_results(gpuPrices)
	
