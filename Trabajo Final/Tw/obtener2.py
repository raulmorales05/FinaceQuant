import tweepy
import csv
from datetime import date, datetime,timedelta 
import os
from autenticate import get_auth

import re 



def almacenar_tweet(tw):
    csvfile = open('DXY.csv','a',newline='')
    csvwriter = csv.writer(csvfile)
    texto = tw
    linea =[texto]
    linea = linea
    csvwriter.writerow(linea)
    print("Almacenamos Tweet")
    csvfile.close()
    
    
#limpiar los tws
def cleanTwt(twt):
    if twt is not False and twt.text is not None:
        try:
            texto = twt.extended_tweet["full_text"]
        except AttributeError:
            texto = twt.text
        texto = re.sub('#dxy', 'dxy', texto) #Remueve el #
        texto = re.sub('#Dxy', 'dxy', texto)# Remueve el #
        texto = re.sub('#[A-Za-z0-9]+', '', texto) # remueve los string con #
        texto = re.sub('\\n', '', texto)     #remueve los \n (salto de espacio)
        texto = re.sub(r'\w+:\/{2}[\d\w-]+(\.[\d\w-]+)*(?:(?:\/[^\s/]*))*', '', texto)    #remueve los link
        return texto
    print('Error Clear')

if __name__ == '__main__':
    print("Extractor de Tweets")
    auth = get_auth()
    api = tweepy.API(auth)

    if os.path.isfile(
        'DXY.csv'):
        print("Preparando el fichero")
    else:
        print("No existe el fichero")
        csvFile = open('DXY.csv', 'w',newline='')
        csvWriter = csv.writer(csvFile)
        cabecera=['Texto', 'Truncado']
        csvWriter.writerow(cabecera)
        csvFile.close()
        print("Se creo el header")

    # start_date = date(2022, 11, 9)    ESTO ES PARA ALGUNA FECHA EN ESPECIFICO
    end_date = date.today()
    start_date = end_date - timedelta(days= 1)  # AQUI ES DESDE EL DIA ANTERIOR
    tweets = []

    for tweet in tweepy.Cursor(api.search_tweets, "#dxy -filter:retweets",
                             ).items(500):
        
        
            if tweet.text not in tweets:
                
                tweets.append(tweet)
                tw = cleanTwt(tweet)
                almacenar_tweet(tw)

print("Terminado")

