from itertools import count
from tkinter import ANCHOR
import streamlit as st
import numpy as np
import pandas as pd
from pandas import DataFrame
from textblob import TextBlob
import matplotlib.pyplot as plt
#py -m streamlit run plot.py

def getSubj(twt):
    return TextBlob(twt).sentiment.subjectivity

def getPol(twt):
    return TextBlob(twt).sentiment.polarity

def sentiment(score):
    if score < 0: 
        return 'Negativo'
    elif score == 0:
        return 'Neutral'
    else: 
        return 'Positivo'

df = pd.read_csv("DXY.csv")
df['subjectivity'] = df['Texto'].apply(getSubj) # se crea la columna de subjetividad 
df['polarity'] = df['Texto'].apply(getPol)      #se crea la columna de polaridad 
df['sentiment'] = df['polarity'].apply(sentiment)
# print(df)

st.title('Sentiment Twitter -> DXY')

st.write('''Polaridad hace referencia a cómo positivo o negativo el tono de las tasas de
texto de entrada de -1 a + 1, por -1 son más negativo y + 1 está más positiva.
Subjetividad hace referencia a cómo subjetiva las tasas de instrucción de 0 a 1, 
siendo 1 el alta subjetiva.''')
st.write(" Estadisticas de Polaridad")
st.write("Media", df["polarity"].mean())
st.write("Max", df["polarity"].max())
st.write("Min", df["polarity"].min())
st.write("Estadisticas de Subjectividad")
st.write("Media", df["subjectivity"].mean())
st.write("Max", df["subjectivity"].max())
st.write("Min", df["subjectivity"].min())


import seaborn as sns


# diagrama de dispersion para mostrar la subjetividad y polaridad
sns.set(font_scale=1.4)
plt.figure(figsize= (8,16))

for i in range(0, df.shape[0]):
    
    plt.scatter(df['polarity'][i],df['subjectivity'][i], color = 'green')    

plt.title('Analisis de sentimiento')
plt.xlabel('Polaridad')
plt.ylabel('subjetividad')
st.set_option('deprecation.showPyplotGlobalUse', False)
st.pyplot()



plt.subplot(2, 1, 1)
for i in range(0, df.shape[0]):
    
    plt.scatter(df['polarity'][i],1, color = 'red')    

plt.title('Polaridad')



plt.subplot(2, 1, 2)
for i in range(0, df.shape[0]):
    
    plt.scatter(df['subjectivity'][i],1, color = 'green')    


plt.xlabel('Subjetividad')
st.set_option('deprecation.showPyplotGlobalUse', False)
st.pyplot()



#primer grafico de barras
sns.set(font_scale=1.4)
plt.subplot(2, 1, 1)
df['sentiment'].value_counts().plot(kind='barh',  figsize=(8, 8), rot=0) 
plt.title('Analsis de sentimiento Bar plot',  y=1.02)

plt.ylabel('Numero de Tweets', labelpad=14)
#segundo grafico de circulos
l=['Neutral', 'Positivo', 'Negativo']
c= ['white','green', 'red']
plt.subplot(2, 1, 2)
plt.pie(df['sentiment'].value_counts(), labels= l, colors=c, shadow = True)

st.set_option('deprecation.showPyplotGlobalUse', False)
st.pyplot()





    


