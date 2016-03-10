import requests, time, sqlite3
from bs4 import BeautifulSoup

def read_from_db(tablename, filename):
	conn = sqlite3.connect(filename)
	c = conn.cursor()

	c.execute("SELECT chipset, multiGpu, nGpuUsed, nResults, score FROM " + tablename)

	data = []
	for row in c.fetchall():
		data.append({
			'chipset': row[0],
			'nGpuUsed': row[2],
			'score': row[4],
			'multiGpu': row[1],
			'nResults': row[3]
		})
	
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

#	r = requests.get(url, params=payload, headers={'user-agent': 'curl/7.7.2 (powerpc-apple-darwin6.0) libcurl 7.7.2 (OpenSSL 0.9.6b)'})
	r = requests.get(url, params=payload, headers={'user-agent': 'Custombot/1.0 (+http://brutesque.github.io/bang-for-buck)'})
	if r.status_code != 200:
		if r.status_code == 404: return {}
		raise Exception('Expected status code 200: %s' % r.status_code)

	#
	#	Extract results from html code
	#

	soup = BeautifulSoup(r.content, "html.parser")
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

def save_results(data, tablename='Untitled', filename='database.db', cleanup=True):

	keyAndTypeStrings = []
	for key in data[0].keys():
		if type(data[0][key]) is str: valueType = 'TEXT'
		elif type(data[0][key]) is int: valueType = 'INT'
		elif type(data[0][key]) is float: valueType = 'REAL'
		elif type(data[0][key]) is bool: valueType = 'BOOL'
		else: raise Exception('Unknown datatype %s for %s' % (type(data[0][key]), key))
		keyAndTypeStrings.append(" ".join([key, valueType]))
	
	conn = sqlite3.connect(filename)
	c = conn.cursor()
	
	c.execute("CREATE TABLE IF NOT EXISTS " + tablename + "(" + ", ".join(keyAndTypeStrings) + ")")
	if cleanup: c.execute("DELETE FROM " + tablename)

	for item in data:
		c.execute("INSERT INTO " + tablename + " (" + ", ".join(item.keys()) + ") VALUES (" + ("?"+",?"*(len(item.values())-1)) + ")", item.values())

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

def getTweakersFilterCodes(octanebenchResults):
		filterCodes = []
	
		url = 'http://tweakers.net/categorie/49/videokaarten/producten/'
		payload = {
			'dc': 'NL', 
			'pageSize': 25,
			'd1749': 5279, # Videochip manufacturer: Nvidia
		}
		r = requests.get(url, params=payload, headers={'user-agent': 'curl/7.7.2 (powerpc-apple-darwin6.0) libcurl 7.7.2 (OpenSSL 0.9.6b)'})
		if not r.status_code == 200: raise Exception('Expected status code 200: %s' % r.status_code)
		soup = BeautifulSoup(r.content, "html.parser")
		specificationFilter_22 = soup.find('div', {'id': 'specificationFilter_22'})
		options = specificationFilter_22.find('div', {'class': 'options'})
		listItems = options.find_all('li')
		for listItem in listItems:
			chipset = str( listItem.find('span', {'class': 'facetLabel'}).text )
			filtercode = str( listItem.find('input', {'name': 'f22'})['value'] )

			chipsetOctane = []
			for j in [str(i['chipset']) for i in octanebenchResults]:
				if j.lower().replace(' ','') in chipset.lower().replace(' ',''):
					chipsetOctane.append(j)
			chipsetOctane = max(chipsetOctane) if len(chipsetOctane) > 0 else ''

			filterCodes.append({
				'chipset': chipset,
				'filtercode': filtercode,
				'chipsetOctane': chipsetOctane
			})
		return filterCodes

def collectGpuPrices(octanebenchResults, filterCodes):
	filters = []
	for i in filterCodes:
		if i['chipsetOctane']: filters.append(i['filtercode'])
	
	endpoint = 'http://tweakers.net/categorie/49/videokaarten/producten/'
	payload = {
#		'k': keywords.lower().replace(' ', '+'), # keyword
#		'i19': minMemory, # Minimum memory size
#		'si': 4, # Minimum rating n/5
		'of': 'price', # Sort field
		'od': 'asc', # Sort order
		'dc': 'NL', 
		'pageSize': 100,
		'd1749': 5279, # Videochip manufacturer: Nvidia
		'f22': filters, # Videochip
		'page': 1
	}

	results = []
	i = 1
	while True:

		r = requests.get(endpoint, params=payload, headers={'user-agent': 'curl/7.7.2 (powerpc-apple-darwin6.0) libcurl 7.7.2 (OpenSSL 0.9.6b)'})
		if not r.status_code == 200: raise Exception('Expected status code 200: %s' % r.status_code)

		listing = BeautifulSoup(r.content, "html.parser").find_all('tr', {'class': 'largethumb'})

		for row in listing:

			name = str(row.find('p', {'class': 'ellipsis'}).a.text.encode('ascii', errors='ignore')).strip()

			spec = str(row.find('p', {'class': 'specline'}).a.text.encode('ascii', errors='ignore')).strip()

			url = str(row.find('td', {'class': 'pwimage'}).a['href'].encode('ascii', errors='ignore')).strip()

			try: price = str(row.find('p', {'class': 'price'}).a.text.encode('ascii', errors='ignore')).strip()
			except AttributeError, e: price = None
			if price:
				price = price.split(',')
				price[0] = ''.join(price[0].split('.'))
				try: price[1] = '00' if price[1] == '-' else price[1]
				except IndexError: pass
				price = float('.'.join(price))
			
			octaneChipset = {}
			for k in octanebenchResults:
				if k['chipset'].lower().replace(' ','') in name.lower().replace(' ','') or k['chipset'].lower().replace(' ','') in spec.lower().replace(' ',''):
					octaneChipset[str(k['chipset'])] = int(k['score'])
			chipset = max(octaneChipset.keys())
			score = octaneChipset[chipset]

			results.append({
				'name': name,
				'spec': spec.replace('\t', ''),
				'price': price,
				'url': url,
				'chipset': chipset,
				'score': score,
				'pricePerPoint': price/score if not price == None else None,
			})

		if len(listing) < payload['pageSize']:
			break
		payload['page'] += 1

	return results

if __name__ == "__main__":
	octanebenchResults = read_from_db('octaneScores', 'octane_tweakers.db')
	filterCodes = getTweakersFilterCodes(octanebenchResults)
#	print "&f22=".join([i['filtercode'] for i in filterCodes]); exit()
	save_results(filterCodes, 'tweakersFilterCodes', 'octane_tweakers.db')
	gpuPrices = collectGpuPrices(octanebenchResults, filterCodes)
	save_results(gpuPrices, 'gpuPrices', 'octane_tweakers.db')
