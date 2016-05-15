# activesoup

A simple library for interacting with the web from python 

## Description

`activesoup` combines familiar python web capabilities for convenient headless "browsing" functionality:
* Modern HTTP support with [requests](http://www.python-requests.org/) - connection pooling, sessions, ...
* Convenient access to the web page with [beautifulsoup](https://www.crummy.com/software/BeautifulSoup/) - convenient HTML navigation
* Robust HTML parsing with [html5lib](https://html5lib.readthedocs.org/en/latest/) - parse the web like browsers do

## Use cases

Consider using `activesoup` when:
* You need to actively interact with some web-page from python (e.g. submitting forms, downloading files)
* You don't control the site you need to interact with (if you do, just make an API)
* You don't need javascript support (you'll need [selenium](http://www.seleniumhq.org/projects/webdriver/) or [phantomjs](http://phantomjs.org/))

## Usage examples

Log into a website, and download a CSV file that's access-protected:
```
from activesoup import driver

d = driver.Driver()
login_page = d.get('https://my-site.com/login')
login_form = login_page.form
member_portal = login_form.submit({'username': secret_store['username'],
					'password': secret_store['password']})

if member_portal.response.status_code not in range(200, 300):
	raise RuntimeError("Couldn't log in")

# Logged in now

csv_report = d.get('/members_area/file.csv')
csv_report.save_to('~/interesting_resport.csv')
```
