# Fact-checking collector
import pandas as pd
import feedparser
import xml.sax.saxutils as saxutils
import ast
import re
from bs4 import BeautifulSoup
import requests
    
class DataCollector:
    def __init__(self):
        pass
    # Get links list from websites feed    
    def get_articles_url(url):
        d = feedparser.parse(url)
        linksList = []
        for post in d.entries: linksList.append(post.link)
        return linksList

    # Save dataset to csv file
    
    def save_csv_pandas(data, file_name):
        data.to_csv("./Dataset/" + file_name + ".csv", encoding='utf-8-sig', index=False)

    # Load dataset from csv file
    
    def load_csv_pandas(file_name):
        return pd.read_csv("./Dataset/" + file_name + ".csv", header = 0, index_col=False, sep=',')

    # Update dataset. URL is primary key.
    
    def update_dataset(dataset, new_entries):
        temp_df = dataset.append(new_entries)
        temp_df = temp_df.drop_duplicates(keep='first', subset=['claimReviewed'])
        count=1
        for index, row in temp_df.iterrows():
            temp_df.loc[index,'id'] = count
            count=count+1
        return temp_df
    
    def re_char(str):
        return re.sub('[^A-Za-z0-9 \!\@\#\$\%\&\*\:\,\.\;\:\-\_\"\'\]\[\}\{\+\á\à\é\è\í\ì\ó\ò\ú\ù\ã\õ\â\ê\ô\ç\|]+', '',str)

    # Text Preprocessing
    
    def text_pre_proc(str):
        aux = saxutils.unescape(str.replace('&quot;', ''))
        #remove not allowed characters
        aux = re.sub('[^A-Za-z0-9 \!\@\#\$\%\&\*\:\,\.\;\:\-\_\"\'\]\[\}\{\+\á\à\é\è\í\ì\ó\ò\ú\ù\ã\õ\â\ê\ô\ç\|]+', '',aux)
        my_dict = ast.literal_eval(aux)
        if "@graph" in my_dict:
            my_dict = my_dict['@graph'][0]        
        return my_dict

    # Get ClaimReview
    def get_claimReview(url):
        response = requests.get(url, timeout=30)
        content = BeautifulSoup(response.content, "html.parser")
        claimList = []
        count = 1
        for claimR in content.findAll('script', attrs={"type": "application/ld+json"}):
            linha = []
            try:
                my_dict = DataCollector.text_pre_proc(claimR.get_text(strip=True))
                linha.append(count)
                count=count+1;
                linha.append(url)
                linha.append(my_dict['author']['url'])
                linha.append(my_dict['datePublished'])
                if (my_dict['claimReviewed']):
                    linha.append(my_dict['claimReviewed'])
                else:   
                    linha.append(DataCollector.re_char(content.title.get_text().replace('<title>','').replace('</title>','')))
                try: linha.append(my_dict['reviewBody'])
                except:
                    try:
                        linha.append(my_dict['description'])
                    except:
                        linha.append('Empty')
                linha.append(DataCollector.re_char(content.title.get_text().replace('<title>','').replace('</title>','')))
                linha.append(my_dict['reviewRating']['ratingValue'])
                linha.append(my_dict['reviewRating']['bestRating'])
                linha.append(my_dict['reviewRating']['alternateName'])
                #linha.append(my_dict['itemReviewed']['@type'])
                claimList.append(linha)
            except:
                pass
        return claimList

    # Main Function
    @staticmethod
    def collect():
        #https:/apublica.org/tag/truco/feed/
        #websites = [ "https://www.boatos.org/feed","https://checamos.afp.com/rss/1558/rss.xml","https://politica.estadao.com.br/blogs/estadao-verifica/feed","https://www.e-farsas.com/feed","https://aosfatos.org/noticias/feed/", "https://piaui.folha.uol.com.br/lupa/feed/"]
        websites = [ "https://checamos.afp.com/rss/1558/rss.xml","https://aosfatos.org/noticias/feed/", "https://piaui.folha.uol.com.br/lupa/feed/"]
        toprow = ['id','URL', 'Author', 'datePublished', 'claimReviewed', 'reviewBody', 'title', 'ratingValue', 'bestRating', 'alternativeName']
        
        # Step 1 - Get links list of the last articles
        linksList = []
        for url in websites: linksList.extend(DataCollector.get_articles_url(url))
        print ("Numero de links: {}".format(len(linksList)))
        # Step 2 - Get Claim Review
        claimList = []
        count = 0
        for url in linksList:
            count = count + 1
            print ("{} de {} > ".format(count,len(linksList)) + url)
            lineList = DataCollector.get_claimReview(url)
            for line in lineList: claimList.append(line)
            
        # Step 3 - Create pandas DataFrame with the new entries
        new_entries = pd.DataFrame(claimList, columns=toprow)
        #new_entries = new_entries.set_index('URL')
        # Step 4 - Load the old version of the dataset, update and save
        dataset = DataCollector.load_csv_pandas('LabeledNews')
        process1Update = DataCollector.update_dataset(dataset, new_entries)
        DataCollector.save_csv_pandas(process1Update, 'LabeledNews')
        