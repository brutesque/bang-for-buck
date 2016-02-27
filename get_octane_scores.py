import requests
from bs4 import BeautifulSoup
import sqlite3

def scrapeOctanebenchResults():
	"""
		>>> scrapeOctanebenchResults()
	"""

	#
	#	Get html contents from otoy site
	#
	url = 'http://render.otoy.com/octanebench/results.php'
	payload = {
		'sort_by': 'avg',
		'singleGPU': 1
	}

	r = requests.get(url, params=payload)
	if r.status_code != 200: raise Exception('Expected status code 200')

	#
	#	Extract results from html code
	#

	soup = BeautifulSoup(r.content)

	# Check to see if there is a div with class 'mainResultDisplay'
	mainResultDisplay = soup.find('div',{'class': 'mainResultDisplay'})
	if mainResultDisplay == None: raise Exception('Could not find expected html tag')
	
	i = 0

	# We have found the div containing the results
	# Now we extract the data from every row
	results = {}
	for row in mainResultDisplay.find_all('a', {'class': 'summaryResultLink'}):

		# extract number of results
		nResults = int(row.find('div', {'class': 'systemID'}).span.text.strip('results )').strip('('))

		# extract multiGPU value
		try: multiGpu = True if row.find('div', {'class': 'systemID'}).sub.span.text == u'*' else False 
		except AttributeError, e: multiGpu = False

		# extract systemID value
		systemID = row.find('div', {'class': 'systemID'}).contents[0].strip('\n').strip('1x').strip('2x ')
		nGpuUsed = int(row.find('div', {'class': 'systemID'}).contents[0].strip('\n')[0:1])

		# extract render score
		score = int(row.find('span', {'class': 'summaryResult_resultValue'}).text)

		results[i] = {'chipset': systemID, 'nGpuUsed': nGpuUsed, 'score': score, 'multiGpu': multiGpu, 'nResults': nResults}
		i += 1
	return results

def save_results(data):
	conn = sqlite3.connect('octane_tweakers.db')
	c = conn.cursor()


	c.execute("CREATE TABLE IF NOT EXISTS octaneScores(chipset TEXT, multiGpu BOOL, nGpuUsed INT, nResults INT, score INT)")
	c.execute("DELETE FROM octaneScores")

	for key, value in data.items():
		c.execute("INSERT INTO octaneScores (chipset, multiGpu, nGpuUsed, nResults, score) VALUES (?, ?, ?, ?, ?)", (value['chipset'], value['multiGpu'], value['nGpuUsed'], value['nResults'], value['score']))

	conn.commit()

	c.close()
	conn.close()


if __name__ == "__main__":
	octanebenchResults = scrapeOctanebenchResults()
	save_results(octanebenchResults)
