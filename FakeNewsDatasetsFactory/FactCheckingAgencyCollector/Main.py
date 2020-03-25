import sys
import pandas as pd
import feedparser
# To text preprocessing
import xml.sax.saxutils as saxutils
import ast
import re
# To get claimReview
from bs4 import BeautifulSoup
import requests
import crawlerFactChecking as fact
import csv

from nltk.corpus import stopwords 
from nltk.tokenize import word_tokenize

if sys.version_info[0] >= 3:
    import crawlerTwitterWeb as craw
else:
    sys.exit()

def main():	
	
	#Process to update LabeledNews file through Fact Checking Agencies
	fact.DataCollector.collect()

	#Read LabeledNews file
	dataset = pd.read_csv("./Dataset/LabeledNews.csv", index_col=0, header = 0)
	toprow = ['id','news_url','title','tweet_ids']
	
	#Stop words initialization
	stop_words = set(stopwords.words('portuguese')) 
	newStopWords = ['Checamos','Agência','Lupa','Pública','Aos','fatos','Fake','FAKE','fake',',',':',';','mentira','verdade','falso','.','O','A','Os','As','Em','Na', 'No']
	stop_words = stop_words.union(newStopWords)	
	newsList = []
	
	for index, row in dataset.iterrows():
		#Removing stop words
		word_tokens = word_tokenize(row[3])   
		filtered_sentence = []   
		for w in word_tokens: 
			if w not in stop_words: 
				filtered_sentence.append(w)
		query = filtered_sentence
		query = [ele for ele in query if not ele.startswith("'")]	
		
		if (len(query) > 8):
			query = query[0:8]
		qry = re.sub(u'[^a-zA-Z0-9áéíóúÁÉÍÓÚâêîôÂÊÎÔãõÃÕçÇ: ]', '', str(query))
		print (qry)
		#Searching in twitter
		tweetCriteria = craw.manager.TweetCriteria().setQuerySearch(qry +" -fake -filter:replies").setSince("2000-01-01").setMaxTweets(10)
		tweets = craw.manager.TweetManager.getTweets(tweetCriteria)
		concTweet = ""
		for tweet in tweets:
			if (concTweet != ""):
				concTweet = concTweet + str("\t") + str(tweet.id)
			else:
				concTweet = str(tweet.id)
		line = []	
		aux = saxutils.unescape(str(index).replace('&quot;', ''))
		line.append(index)
		line.append(row[0])
		line.append(row[3])
		line.append(concTweet)
		newsList.append(line)

	process2Result = pd.DataFrame(newsList, columns=toprow)
	process2Result = process2Result.set_index('id')
	process2Result.to_csv("./Dataset/NewsSocialMediaAssociation.csv", encoding='utf-8-sig', index=True)
if __name__ == '__main__':
	main()
