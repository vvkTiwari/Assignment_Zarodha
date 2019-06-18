import cherrypy
import os
from pytz import timezone
from tzlocal import get_localzone
from io import BytesIO
from zipfile import ZipFile
from urllib.request import urlopen
import redis
from datetime import datetime

redis_host = "SG-Vivek-22108.servers.mongodirector.com"
redis_port = 6379
redis_password = "8aGkVs9OKyPKfG0aRS4IuuvAdrab9VXW"

class Bhavcopy(object):

	# Creating connection to redis.

	try:
		r = redis.StrictRedis(host=redis_host, port=redis_port, password=redis_password, decode_responses=True)
	except Exception as e:
		print(e)

	def __init__(self):
		self.upload_data(self.r)


# Function to upload data to redis.

	def upload_data(self,r):

		# Assuming that the BhavCopy is uploaded every weekday after 7pm.

		format_accepted = "%Y-%m-%d %H %A"
		now_utc = datetime.now(timezone('UTC'))
		local_time = now_utc.astimezone(get_localzone()).strftime(format_accepted)
		split_local_time = local_time.split(' ')
		date = split_local_time[0].split("-")
		day = split_local_time[2]
		Date = str(date[2])+str(date[1])+str(date[0][2:])
		#print(Date,"fasldkfj;adsklfjkdsl")

		r.set("url", "http://www.bseindia.com/download/BhavCopy/Equity/EQ180619_CSV.ZIP")

		# On offdays, the previous bhavcopy will be shown.

		off_days = ['Saturday','Sunday']
		#print(split_local_time,"fsldkfjsldkfjadskfj;lskdjf")
		if day not in off_days and int(split_local_time[1]) >= 19:
			url = "http://www.bseindia.com/download/BhavCopy/Equity/EQ"+Date+"_CSV.ZIP"
			#url = "http://www.bseindia.com/download/BhavCopy/Equity/EQ"+date+"_CSV.ZIP"
			r.set("url", url)
		else:
			url = r.get('url')

		resp = urlopen(url=url)
		zipfile = ZipFile(BytesIO(resp.read()))
		file = zipfile.namelist()
		try:
			i = 0
			r.set("fields","code,name,open,high,low,close")
			for line in zipfile.open(file[0]).readlines():
				data_string = line.decode(encoding='utf')
				data_list = data_string.split(',')
				index = [0, 1, 4, 5, 6, 7]

				col_append= ''
				for j in range(len(data_list)):
					if j in index:
						col_append += str(data_list[j]) + ','
				col_append = col_append[:-1].strip()

				r.set("key"+str(i), col_append)
				i += 1
			#print(i,"adfkladsjflk;sdjflksdjflkd")
		except Exception as e:
			print(e)
		return "success"


# Home page for the application

	@cherrypy.expose
	def index(self):
		try:
			datatable = []
			table=""
			for i in range(11):
				datatable.append(Bhavcopy.r.get("key"+str(i)).rstrip().split(','))
			for i in range(11):
				table = table[0:]+"<tr>"
				for j in range(6):
					if i == 0:
						table = table[0:]+"<th>"+str(datatable[i][j])+"</th>"
					else:
						table = table[0:]+"<td>"+str(datatable[i][j])+"</td>"
				table += "</tr>"
		except Exception as e:
			print(e)
		return("""	<html>
					<head>
						<link href="/static/css/bootstrap.min.css" rel="stylesheet">
						<link href="/static/css/styles.css" rel="stylesheet">
					</head>
					<body>
						<div class="container top-ten">
							<h2>Top Ten Stocks</h2>
							<table class="table table-bordered table-responsive">"""+table+"""</table>
							<form action="search_box" method="get">
								<label>Search:</label> <input class="search" type="text" name="search_input">
								<input class="btn-sm btn-default" type="submit" value="Submit"/>
							</form>
						</div>
					</body>
					</html>""")
		
	# Function to search the stock by its name

	@cherrypy.expose()
	def search_box(self,search_input):
		name = search_input
		table = ""
		for i in range(2906):
			vals = Bhavcopy.r.get("key" + str(i)).rstrip().split(',')
			if i == 0:
				table = table[0:] + "<tr>"
				x = Bhavcopy.r.get("key" + str(0)).rstrip().split(',')
				for j in range(6):
					table = table[0:] + "<th>" + str(x[j]) + "</th>"
				table += "</tr>"
			elif vals[1].strip() == name.upper():
				table = table[0:] + "<tr>"
				for j in range(6):
					table = table[0:] + "<td>" + str(vals[j]) + "</td>"
				table += "</tr>"
		return ("""<html>
					<body>
					<head>
						<link href="/static/css/bootstrap.min.css" rel="stylesheet">
						<link href="/static/css/styles.css" rel="stylesheet">
					</head>
					<body>
						<div class="search-output container">
							<h2>Search Results</h2>
							<table class="table table-bordered table-responsive">""" + table + """</table>
						</div>
					</body>
					</html>""")

if __name__ == '__main__':

	conf = {
		'/': {
			'tools.sessions.on': True,
			'tools.staticdir.root': os.path.abspath(os.getcwd())
		},
		'/static': {
			'tools.staticdir.on': True,
			'tools.staticdir.dir': './public'
		}
	}
	cherrypy.quickstart(Bhavcopy(), '/', conf)
