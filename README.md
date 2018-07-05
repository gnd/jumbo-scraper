# jumbo-scraper
A Scrapy spider that extracts nutrition values from all Jumbo.com products

# usage
scrapy crawl jumbo -a maxpages=1950 -a recheck=1 -a delay=0.6

# args 
- maxpages: the bot scrapes the alphabetical list of all products first, only then starts scraping nutrition data of particular products. maxpages tells how many pages of the list it should go for. 
- recheck: should the bot check products which are already scraped in the db ?
- delay: a delay in seconds between consecutive requests
