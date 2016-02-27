import sqlite3

def read_from_db():
	conn = sqlite3.connect('site/octane_tweakers.db')
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
	table += '<tr>%s</tr>' % (
		('<td>%s</td>'*6) % (
			row['chipset'],
			row['score'],
			'&euro; %s' % row['price'],
			'&euro; %s' % row['pricePerPoint'],
			'<a href="%s">%s</a>' % (row['url'], row['name']),
			row['spec']
		)
	)

with open('template.html', 'r') as infile:
	template = infile.read()

	outfile.write(template%table)
with open('site/index.html', 'w') as outfile:
