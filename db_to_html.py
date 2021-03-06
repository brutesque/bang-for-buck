import sqlite3, datetime

def read_from_db():
	conn = sqlite3.connect('octane_tweakers.db')
	c = conn.cursor()

	c.execute("SELECT chipset, price, url, score, pricePerPoint, name, spec FROM gpuPrices ORDER BY pricePerPoint")

	data = {}
	i = 0
	for row in c.fetchall():
		data[i] = {'chipset': row[0], 'price': row[1], 'url': row[2], 'score': row[3], 'pricePerPoint': row[4],'name': row[5],'spec': row[6]}
		i += 1
	
	c.close()
	conn.close()
	
	return data

data = read_from_db()

table = ''
for (key, row) in data.items():
	if not row['price'] == None:
		table += '<tr>%s</tr>' % (
			('<td>%s</td>'*6) % (
				row['chipset'],
				row['score'],
				'&euro;&nbsp;%s' % row['price'],
				'&euro;&nbsp;%s' % round(row['pricePerPoint'], 5),
				'<a href="%s" target="_blank">%s</a>' % (row['url'], row['name']),
				row['spec']
			)
		)

with open('template.html', 'r') as infile:
	template = infile.read()

timestamp = str(datetime.datetime.now()).split('.')[0]
newHtml = template % (
	timestamp,
	table
)

with open('octane_tweakers.html', 'w') as outfile:
	outfile.write(newHtml)
