from bs4 import BeautifulSoup 
from configparser import ConfigParser 
import requests
import pandas as pd
import time 
import re
import os
from tqdm import tqdm

pound = "£"

headers = {
		"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.150 Safari/537.36"
}

def findResults(url):
	r = requests.get(url, headers=headers)
	soup = BeautifulSoup(r.content,'lxml')
	results = soup.find('p',{'data-testid':'total-results'}).text
	results_num = re.findall(r'[0-9]+',results)
	return results_num[0]

def main(url):
	# url = "https://www.zoopla.co.uk/for-sale/property/london/?is_auction=false&page_size=25&q=London&radius=0&results_sort=newest_listings&pn=2"
	pages = int(findResults(url))//25
	title = getresultsTitle(url)
	print(title)
	if title:
		heading = title 
	else:
		heading = location 

	if pages <= 0:
		pages = 1
		print("Found 1 page.")
	else:
		print("Pages found: {}".format(pages))
	print()
	
	for i in range(1,pages+1):
		index = round(time.time())
		scrape_url = url+"&pn={}".format(i)
		r = requests.get(scrape_url,headers=headers)
		soup = BeautifulSoup(r.content, 'lxml')
		print("Extracting page {}.. Please wait..".format(i))
		# propertyInfo = soup.findAll("div",{"class":"css-hbmpg0-StyledWrapper e2uk8e27"})
		propertyInfo = soup.findAll("div",{"data-testid":"search-result"})
		start = time.time()
		mainData, featuresData, mapData, priceData, salesData = extractPropertyInfo(propertyInfo)
		stop = time.time()
		taken = stop-start
		hours = taken//3600
		minutes = taken//60
		seconds = taken%60

		print("finished scraping page {0} in : {1} hrs : {2} min : {3} sec".format(i,round(hours),round(minutes),round(seconds,2)))

		print("Saving to excel..")
		if mainData:
			maindf = pd.DataFrame(mainData,columns=["  Unique ID  ","Property","Pricing - Amount","Pricing - Frequency","Location","Radius - Value","Radius - Measurement","Status","Views : Last 30 days","Bedrooms","Bathrooms","Reception Rooms","Description","Agent Name","Agent Address","Agent Contact","Property Link"])
			featuresdf = pd.DataFrame(featuresData,columns=["  Unique ID  ","Features"])
			mapdf = pd.DataFrame(mapData,columns=["  Unique ID  ","Map & Nearby","Distance - Value","Distance - Measurement"])
			pricedf = pd.DataFrame(priceData,columns=["  Unique ID  ","Date","Details","Price History - Amount", "Price History - Frequency"])
			salesdf = pd.DataFrame(salesData,columns=["  Unique ID  ","Property","Location","Price - Value", "Price - Frequency"])
			filename = "{0}-page{1}-index{2}.xlsx".format(heading,i,index)
			os.chdir("PropertyInformation")
			writer = pd.ExcelWriter(filename,engine="xlsxwriter")
			maindf.to_excel(writer,sheet_name="Zoopla Output Tab",index=False)
			featuresdf.to_excel(writer,sheet_name="Supplement_Features",index=False)
			mapdf.to_excel(writer,sheet_name="Supplement_Map_and_Nearby",index=False)
			pricedf.to_excel(writer,sheet_name="Supplement_Price_History",index=False)
			salesdf.to_excel(writer,sheet_name="Recent Sales Nearby",index=False)
			writer.save()
			os.chdir("..")
			print("Done..")
		else:
			print("Error Occurred. Check the keywords file and try again..")
def getresultsTitle(url):
	r = requests.get(url,headers=headers)
	soup = BeautifulSoup(r.content, 'lxml')
	try:
		title = soup.find('h1',{"data-testid":"results-title"}).text 
	except:
		return None
	return title
def extractMoreInfo(url):
	resp = requests.get(url,headers=headers)
	soup = BeautifulSoup(resp.content, 'lxml')
	try:
		ulTag = soup.find('ul',{"class":"dp-features-list dp-features-list--counts ui-list-icons"})
		spanTags = ulTag.findAll("span",{"class":"dp-features-list__text"})
		bedrooms = spanTags[0].text
		bathrooms = spanTags[1].text
		receptionRooms = spanTags[2].text
		description = soup.find('div',{"class":"dp-description__text"}).text.strip()
		agentInfo = soup.find('div',{'class':'ui-agent__text'})
		agentName = agentInfo.find('h4',{'class':'ui-agent__name'}).text
		agentAddress = agentInfo.find('address',{'class':'ui-agent__address'}).text
		status = soup.find("li",{"class":"ui-property-indicators__item"}).text.strip()
		views = soup.find("p",{"class":"dp-view-count__legend"}).text.strip()
	except:
		return [None,None,None,None,None,None]
	return [bedrooms,bathrooms,receptionRooms,description,agentName,agentAddress,status,views]

def extractPropertyInfo(infoList):
	config.read("Keywords2.ini")

	Radii = []
	Radii_Measurement = []
	prices = []
	pricesFreq = []
	names = []
	locations = []
	contacts = []
	bedrooms = []
	bathrooms = []
	receptionRooms = []
	descriptions = []
	agentNames = []
	agentAddresses = []
	propertyLinks = []
	Views = []
	status = []

	mainID = []

	idLists_features = []
	featureList = []

	idLists_RecentSales = []
	Location_RecentSales = []
	Price_RecentSales = []
	Price_RecentSales_Freq = []
	Date_RecentSales = []
	Property_RecentSales = []

	idLists_map = []
	amenities = []
	distances_value = []
	distances_measurement = []

	idLists_history = []
	dates_history = []
	description_history = []
	price_history = []
	price_history_freq = []

	for info in tqdm(infoList,ncols=75):
		ID = round(time.time())
		time.sleep(.3)
		# Extract all the property features..
		priceTag = info.find("div",{"class":"css-1e28vvi-PriceContainer e2uk8e8"})
		price_regex = r'£[0-9]+,?[0-9]+'
		price_mr_price = ""
		realPrice = re.findall(price_regex,priceTag.text)
		if len(realPrice) >= 1:
			realPrice = realPrice[0]
			for pp in realPrice:
				if pp != "," and pp != "£":
					price_mr_price += pp
				else:
					price_mr_price += ""
			realPrice = eval(price_mr_price)
			price_frequency = "PCM"
		else:
			realPrice = ""
		
		
		propertyNameTag = info.find("a",{"data-testid":"listing-details-link"})
		name = propertyNameTag.find("h2").text
		location = propertyNameTag.find("p").text
		contact = info.find("a",{"data-testid":"agent-phone-number"}).text
		newHref = info.find("a",{"data-testid":"listing-details-image-link"})["href"]
		moreInfoUrl = "https://www.zoopla.co.uk"+newHref
		moreInfo = extractMoreInfo(moreInfoUrl)
		r = requests.get(moreInfoUrl,headers=headers)
		soup = BeautifulSoup(r.content, 'lxml')
		ul = soup.find("ul",{"class":"dp-features-list dp-features-list--bullets ui-list-bullets"})
		localUl = soup.find("ul",{"class":"ui-local-amenities__list ui-list-flat"})
		History = soup.find("section",{"class":"dp-price-history-block"})
		SalesNearby = soup.find("ul",{"class":"dp-recent-sales ui-list-flat"})		


		if None not in moreInfo and realPrice != "":
			try:
				for div in History.findAll("div",{"class":"dp-price-history__item"}):
					PPPrice = div.find("span",{"class":"dp-price-history__item-price"}).text
					opprice_regex = r"[0-9][0-9,]+"
					price_value = re.findall(opprice_regex,PPPrice)[0]
					pp = ""
					for val in price_value:
						if val != "," and val != "£":
							pp += val
						else:
							pp += ""
					pppprice = eval(pp)
					price_history.append(pppprice)
					price_history_freq.append("PCM")
					description_history.append(div.find("span",{"class":"dp-price-history__item-detail"}).text.strip())
					dates_history.append(div.find("span",{"class":"dp-price-history__item-date"}).text)
					idLists_history.append(ID)
			except:
				pass
			try:
				for li in ul.findAll("li"):
					featureList.append(li.text.strip())
					idLists_features.append(ID)
			except:
				pass
			try:
				for li in localUl.findAll("li"):
					idLists_map.append(ID)
					amenities.append(li.find("span",{"ui-local-amenities__text"}).text)
					dist = li.find("span",{"ui-local-amenities__distance"}).text
					distance_regex = r"[0-9].?[0-9]?"
					distance_value = eval(re.findall(distance_regex,dist)[0])
					distances_value.append(distance_value)
					distances_measurement.append("miles")
			except:
				pass
			try:
				for li in SalesNearby.findAll("li"):
					llocation = li.find("h4",{"class":"dp-recent-sales-title"}).text 
					if llocation == "":break
					priceNdate = li.findAll("li",{"class":"dp-recent-sales__row-item"})
					if priceNdate == []:break
					price = priceNdate[1].text 
					Property = li.find("span",{"class":"dp-recent-sales-type"}).text
					if Property == "":break
					Location_RecentSales.append(llocation)
					# Date_RecentSales.append(date)
					Property_RecentSales.append(Property)
					idLists_RecentSales.append(ID)
					opprice_regex = r"[0-9][0-9,]+"
					price_value = re.findall(opprice_regex,price)[0]
					pp = ""
					for val in price_value:
						if val != "," and val != "£":
							pp += val
						else:
							pp += ""
					price = eval(pp)
					Price_RecentSales.append(price)
					Price_RecentSales_Freq.append("PCM")
			except:
				pass

			prices.append(realPrice)
			pricesFreq.append(price_frequency)
			names.append(name)
			contacts.append(contact)
			beds = moreInfo[0]
			baths = moreInfo[1]
			receptionsss = moreInfo[2]
			bed_regex = r"[0-9]+"
			if 'bedroom' in beds:
				bedss = re.findall(bed_regex,beds)[0]
				beds = eval(bedss)
			if 'bathroom' in baths:
				bathss = re.findall(bed_regex,baths)[0]
				baths = eval(bathss)
			if 'reception' in receptionsss:
				rec = re.findall(bed_regex,receptionsss)[0]
				receptionsss = eval(rec) 

			radius = config.get("Search_Radius","radius")

			if radius != "":
				try:
					radius = eval(radius)
				except:
					radius = 0
			else:
				radius = 0
			bedrooms.append(beds)
			bathrooms.append(baths)
			receptionRooms.append(receptionsss)
			descriptions.append(moreInfo[3])
			agentNames.append(moreInfo[4])
			agentAddresses.append(moreInfo[5])
			propertyLinks.append(moreInfoUrl)
			locations.append(location)
			mainID.append(ID)
			status.append(moreInfo[-2])
			Views.append(moreInfo[-1])
			Radii.append(radius)
			Radii_Measurement.append("miles")
		else:
			continue




	mainData = {
	"  Unique ID  ":mainID,
	"Property":names,
	"Pricing - Amount":prices,
	"Pricing - Frequency":pricesFreq,
	"Location":locations,
	"Radius - Value":Radii,
	"Radius - Measurement":Radii_Measurement,
	"Status":status,
	"Views : Last 30 days":Views,
	"Bedrooms":bedrooms,
	"Bathrooms":bathrooms,
	"Reception Rooms":receptionRooms,
	"Description":descriptions,
	"Agent Name":agentNames,
	"Agent Address":agentAddresses,
	"Agent Contact":contacts,
	"Property Link":propertyLinks
	}

	featuresData = {
	"  Unique ID  ":idLists_features,
	"Features":featureList
	}

	mapData = {
	"  Unique ID  ":idLists_map,
	"Map & Nearby":amenities,
	"Distance - Value":distances_value,
	"Distance - Measurement":distances_measurement
	}

	priceData = {
	"  Unique ID  ":idLists_history,
	"Date":dates_history,
	"Details":description_history,
	"Price History - Amount":price_history,
	"Price History - Frequency":price_history_freq
	}

	RecentSalesData = {
	"  Unique ID  ":idLists_RecentSales,
	"Property":Property_RecentSales,
	"Location":Location_RecentSales,
	"Price - Value":Price_RecentSales,
	"Price - Frequency":Price_RecentSales_Freq
	}

	return (mainData,featuresData,mapData,priceData,RecentSalesData)




config = ConfigParser()
config.read("Keywords2.ini")

location = config.get("Search_Area","area")
formatted_loc = ""
unformatted_loc = ""
for char in location:
	if char == " ":
		char = "%20"
	formatted_loc += char
for char in location:
	if char == " ":
		char = "-"
	unformatted_loc += char


radius = config.get("Search_Radius","radius")

bedrooms_min = config.get("Bedrooms","min")
bedrooms_max = config.get("Bedrooms","max")
bedrooms_max = "&beds_max={}".format(bedrooms_max)
bedrooms_min = "&beds_min={}".format(bedrooms_min)

price_max = config.get("Price","max")
price_max = "&price_max={}".format(price_max)
price_min = config.get("Price","min")
price_min = "&price_min={}".format(price_min)

sort = config.get("Sort","sort")
sort = "&results_sort={}".format(sort) if sort != "" else "&results_sort=newest_listings"

added = config.get("Added_to_site","added")
added = "added={}".format(added)

property_type = config.get("Property_Type","type")
property_type = "&property_type={}".format(property_type)

is_sold = config.get("Added_To_Site_Under_offer_or_sold_STC","choice")
is_sold = "&include_sold=true" if is_sold == "y" or is_sold == "yes" else ""

is_retirement = config.get("Home_Type","retirement")
is_retirement = "retirement/" if is_retirement == "y" or is_retirement == "yes" else "property/"
is_preowned = config.get("Home_Type","preowned")
is_preowned = "&is_retirement_home=false" if is_preowned == "y" or is_preowned == "yes" else ""

is_auction = config.get("Buying_Options","Auction")
is_shared_ownership = config.get("Buying_Options","Shared_Ownership")

if is_auction == "" and is_shared_ownership == "":
	is_auction = "&is_auction=false"
	is_shared_ownership = "&is_shared_ownership=false"
if is_auction == "y" or is_auction == "yes" and is_shared_ownership == "y" or is_shared_ownership == "yes":
	is_auction = ""
	is_shared_ownership = ""
if is_preowned == "&is_retirement_home=false":
	if is_auction == "y" or is_auction == "yes" and is_shared_ownership == "n" or is_shared_ownership == "no" or is_shared_ownership == "": 
		is_auction = "&is_shared_ownership=false"
else:
	if is_auction == "y" or is_auction == "yes" and is_shared_ownership == "n" or is_shared_ownership == "no" or is_shared_ownership == "" and is_retirement == "retirement/":
		is_auction = "&is_shared_ownership=false"
if is_shared_ownership == "y" or is_shared_ownership == "yes" and is_auction == "n" or is_auction == "no" or is_auction == "":
	is_shared_ownership = "&is_auction=false"

help_to_buy = config.get("Buying_Options","Help_To_Buy")

if help_to_buy == "y" or help_to_buy == "yes":
	if is_preowned == "&is_retirement_home=false" or is_retirement == "retirement/":
		help_to_buy = ""
	else:
		help_to_buy = "&buyer_incentive=help_to_buy"


has_garden = config.get("Must_Haves","Garden")
has_garden = "&feature=has_garden" if has_garden == "y" or has_garden == "yes" else ""
# has_garden = "" if has_garden == "" or has_garden == "no" or has_garden == "n" else "&feature=has_garden"
has_balcony_terrace = config.get("Must_Haves","Balcony_Terrace")
has_balcony_terrace = '&feature=has_balcony_terrace' if has_balcony_terrace == "y" or has_balcony_terrace == "yes" else ""
has_wood_floors = config.get("Must_Haves","Wood_Floors")
has_wood_floors = "&feature=has_wood_floors" if has_wood_floors == "y" or has_wood_floors == "yes" else ""
is_rural_secluded = config.get("Must_Haves","Rural_Secluded")
is_rural_secluded = "&feature=is_rural_secluded" if is_rural_secluded == "y" or is_rural_secluded == "yes" else ""
has_parking_garage = config.get("Must_Haves","Parking_Garage")
has_parking_garage = "&feature=has_parking_garage" if has_parking_garage == "y" or has_parking_garage == "yes" else ""
has_porter_security = config.get("Must_Haves","Porter_Security")
has_porter_security = "&feature=has_porter_security" if has_porter_security == "y" or  has_porter_security == "yes" else ""
has_fireplace = config.get("Must_Haves","Fireplace")
has_fireplace = "&feature=has_fireplace" if has_fireplace == "y" or has_fireplace == "yes" else ""

chain_free = config.get("Property_Status","Chain_Free")
chain_free = "&chain_free=true" if chain_free == "y" or chain_free == "yes" else ""
reduced_price_only = config.get("Property_Status","Price_Reduced")
reduced_price_only = "&reduced_price_only=true" if reduced_price_only == "y" or reduced_price_only == "yes" else ""

keywords = config.get("Keywords","Keywords")
keywords = "&keywords={}".format(keywords)
if radius:
	try:
		radius = int(radius)
	except:
		radius = eval(radius)
		
url = "https://www.zoopla.co.uk/for-sale/"+is_retirement+unformatted_loc.lower()+"/?"+added+"&q={}".format(formatted_loc)+reduced_price_only+is_sold+chain_free+has_fireplace+has_porter_security+has_parking_garage+is_rural_secluded+has_wood_floors+has_balcony_terrace+has_garden+help_to_buy+is_shared_ownership+is_auction+property_type+is_preowned+bedrooms_min+bedrooms_max+price_max+price_min+sort+"&radius={}".format(radius)+keywords+"&page_size=25"+"&search_source=refine"

main(url)


# print(extractMoreInfo("https://www.zoopla.co.uk/for-sale/details/57813172?search_identifier=84a00d589fa59050b837641d285e08e6"))
# url = "https://www.zoopla.co.uk/for-sale/property/{0}/?is_auction=false&page_size=25&beds_max=&beds_min={1}&q={2}&radius={3}&price_max={4}&price_min=&property_type={5}&results_sort=newest_listings".format(unformatted_loc,bedrooms_min,formatted_loc,radius,price_max,property_type)
# print(url)
# main(location,radius,bedrooms,price_max,property_type)

# https://www.zoopla.co.uk/for-sale/property/south-london/?&is_auction=false&page_size=25&radius=0.25&results_sort=newest_listings&search_source=facets
# https://www.zoopla.co.uk/for-sale/property/South-London/?added=&q=South%20London&property_type=flats&beds_min=3&beds_max=&price_max=400000&price_min=&results_sort=newest_listings&radius=0.25&keywords=&page_size=25&search_source=facets
#




#https://www.zoopla.co.uk/for-sale/property/south-london/?added=14_days&property_type=houses&beds_min=3&is_auction=false&is_retirement_home=false&new_homes=exclude&page_size=25&price_max=400000&q=South%20London&radius=0.25&results_sort=lowest_price&search_source=facets
