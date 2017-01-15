from django.shortcuts import render
from django.http import HttpResponse
import requests
from bs4 import	BeautifulSoup
import re
import unicodedata as ucd
import json
from django.core.context_processors import csrf


art_dictionary = {}
def essays_home(request):
	context= {}
	context.update(csrf(request))
	link = request.POST.get('link', False)
	url_ext = []
	split = str(link).split('/')
	count = 0
	for s in split:
		count += 1
	for i in range(3,count-1):
		url_ext.append(split[i])  #parametres in the link
	if link and url_ext == []:
		pages = request.POST.get('page', False)
		if pages == False:
			crawl(1)
		else:
			crawl(pages)
		context['status'] = "success"	
	elif link and count == 5 and url_ext[-1] not in ['about','privacy','contact']: 
		# main + title (about/privacy/contact)
		content = get_url_details(link)
		with open(url_ext[-1]+"_article.json","w") as json_file:
			json.dump(content, json_file)
		context['status'] = "success"
	else: 
		#main+ else then title
		if link and url_ext[-1] not in ['about','privacy','contact']:
			get_catalogue(link)
			context['status'] = "success"
		elif link:
			context['status'] = "failed"
 	return render(request, "home.html", context)


def crawl(max_pages):
	page = 1
	while page <= max_pages:
		url = "https://www.essayforkids.com/page/"+ str(page) + "/"
		get_catalogue(url)  	
	page += 1

def get_catalogue(url):
	source_code = requests.get(url) #scrapping url here
	if source_code.status_code == 200:
		plain_text = source_code.text
		soup = BeautifulSoup(plain_text)
		articles = soup.find_all('article')
		for art in articles:
			dictionary = {}
			post_id = art.get("id")

			# title and link part one
			title_link =  art.select('h1.entry-title a[href]')
			for a in title_link:
				dictionary['title'] = (a.string)
				dictionary["link"] = a['href']

			# footer for meta data
			try:
				meta = art.find("footer")
				item = (meta.text).replace('Categories:','').replace('Tags','').replace('Author','').replace('Date','')
				item = item.split(':')
				dictionary["categories"] = item[0]
				dictionary["tags"] = item[1]
				dictionary["author"] = item[2]
				dictionary["date"] = item[3]
			except:
				pass
			
			#content in details from the link 
			content = get_url_details(dictionary['link'])
			dictionary['content'] = content
			art_dictionary[post_id] = dictionary
		with open("articles.json","w") as json_file:
			json.dump(art_dictionary, json_file)
	else:
		return HttpResponse('/')

def get_url_details(title_url):  #url = main + something
	source_code = requests.get(title_url)
	if source_code.status_code == 200:
		plain_text = source_code.text
		soup = BeautifulSoup(plain_text)
		content = {}

		# get image
		img_src =  soup.find("img", class_ = "wp-post-image")
		content["image"] = img_src.get("src")

		# collect table data
		table = soup.find("table")
		tbody = table.find("tbody")
		rows = tbody.find_all("tr")
		for row in rows:
			cols = row.find_all("td")
			cols = [ele.text for ele in cols]
			key = ''.join(map(lambda x: chr(ord(x)),cols[0]))
			# value = str(cols[1].replace(u'\xa0', u' '))
			value = ucd.normalize("NFKD", cols[1])
			value = value.replace('\u', '')
			content[key] = value

		# collect main essay	
		essay = soup.find("div", class_ = "entry-content").find_all(["p" ,"h3"])
		essay_line = []
		for line in essay:
			essay_line.append(line.text)
		del essay_line[-1]
		del essay_line[-1]
		essay_line = '\n'.join(essay_line)
		content["essay"] = essay_line # remove \u in this
		return content
	else:
		return HttpResponse('/')