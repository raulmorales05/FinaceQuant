from itertools import count
from tkinter import ANCHOR
import streamlit as st
import pandas as pd
import seaborn as sns
import numpy as np
#Asi se ejecuta la App
# py -m streamlit run Mostrar.py
import yfinance as yf
import pandas as pd
import matplotlib.pyplot as plt
import time





def getData(ticker, data_from, data_to):
    data= yf.download(ticker, auto_adjust=True, progress=False, start= data_from, end=data_to)
    return data

def getFeatures(data, n_obv= 100, n_sigma= 40, n_rsi=15,fast=30,slow=200, cross_price=50,fast1=50,slow1=200,rsi_m=10,obv_m=100):
    data['Balance']= np.where(data.Close>data.Close.shift(),data['Volume'],np.where(data.Close < data.Close.shift(), -data['Volume'], 0))
    data['OBV']= data['Balance'].cumsum()
    dif= data['Close'].diff()
    win=pd.DataFrame(np.where(dif>0,dif,0),index=data.index)
    loss=pd.DataFrame(np.where(dif<0,abs(dif),0),index=data.index)
    ema_win= win.ewm(alpha=1/n_rsi).mean()
    ema_loss= loss.ewm(alpha=1/n_rsi).mean()
    rs=ema_win/ema_loss
    
    data['cruce']=data.Close.rolling(fast).mean()/ data.Close.rolling(slow).mean()-1
    data['rsi']= 100 - (100 / (1+rs))
    data['sigma']= data.Close.pct_change().rolling(n_sigma).std()
    data['OBV_osc']= (data.OBV - data.OBV.rolling(n_obv).mean())/ (data.OBV.rolling(n_obv).std())
    data['cruce_volumen'] = data.Volume / data.Volume.rolling(20).mean()
    data['cruce_precio'] = (data.Close/data.Close.rolling(cross_price).mean()) #precio y media de 50
    data['cruce_50_200'] = (data.Close.rolling(fast1).mean()/data.Close.rolling(slow1).mean())
#en btc es mejor la de 20 y 100
    data['cruce_20_100'] = (data.Close.ewm(span=20).mean()/data.Close.ewm(span=100).mean())
    
    data['rsi_media']= (data['rsi'].rolling(rsi_m).mean())
    data['OBV_media']= (data['OBV']/data.OBV.rolling(obv_m).mean())
    
    
    
    
    features=data.dropna()
    return features


def getActions(features, trig_buy_cross=0, trig_buy_rsi=30, trig_buy_sigma=0.01, trig_sell_cross=-0.01,trig_sell_rsi= 70, trig_sell_obv=0):
    #gatillos compra
    gatillos_compra= pd.DataFrame(index = features.index)
    gatillos_compra['cruce']= np.where(features.cruce > trig_buy_cross , True, False)
    gatillos_compra['rsi']= np.where(features.rsi > trig_buy_rsi, True, False)
    gatillos_compra['sigma']= np.where(features.sigma > trig_buy_sigma, True, False)
    gatillos_compra['cruce_volumen']= np.where(features.cruce_volumen > 1, True, False)
    gatillos_compra['cruce_precio']= np.where(features.cruce_precio > 1 , True, False)
    gatillos_compra['cruce_50_200']= np.where(features.cruce_50_200 > 1 , True, False)
    gatillos_compra['cruce_20_100']= np.where(features.cruce_20_100 > 1 , True, False)
    gatillos_compra['rsi_media']= np.where(features.rsi_media > 1 , True, False)
    gatillos_compra['OBV_media']= np.where(features.OBV_media > 1 , True, False)
    
    
    mascara_compra= gatillos_compra.all(axis= 1)
  
    #gatillos venta
    gatillos_venta= pd.DataFrame(index = features.index)
    gatillos_venta['cruce_20_100']= np.where(features.cruce < trig_sell_cross, True , False)  #     tiene que ser menor a 0      EL ERROR ESTABA EN EL INDICADOR QUE HAY QUE MODIFICARLO
    
    gatillos_venta['rsi']= np.where(features.rsi < trig_sell_rsi, True , False)
    gatillos_venta['obv']= np.where(features.OBV_osc > trig_sell_obv, True , False)
    gatillos_compra['cruce_volumen']= np.where(features.cruce_volumen < trig_sell_cross, True, False)
    gatillos_compra['cruce_precio']= np.where(features.cruce_precio < trig_buy_cross , True, False)
    gatillos_compra['cruce_50_200']= np.where(features.cruce_50_200 < trig_buy_cross , True, False)
    gatillos_compra['cruce_20_100']= np.where(features.cruce_20_100 < trig_buy_cross , True, False)
    gatillos_compra['rsi_media']= np.where(features.rsi_media < 1 , True, False)
    gatillos_compra['OBV_media']= np.where(features.OBV_media < 1 , True, False)
 
    mascara_venta= gatillos_venta.all(axis=1)
    
    
    

    #Tabla de acciones 
    #separa en compra y venta segun sea True y vacio si no los dos son false

    data_aux = data.dropna()
    data_aux['gatillo']= np.where(mascara_compra, 'compra', np.where(mascara_venta, 'venta', ''))
    actions= data_aux.loc[data_aux['gatillo']!= ''].copy()
    actions['gatillo']= np.where(actions['gatillo'] != actions.gatillo.shift(),actions.gatillo, '') 

    actions= actions.loc[actions['gatillo'] != ''].copy()
    data['gatillo']=actions['gatillo']

    #permite que el primero en el DF siempres sea comrpa y el ultimo siempre sea una venta

    if actions.iloc[0].loc['gatillo']== 'venta':
        actions= actions.iloc[1:]
    if actions.iloc[-1].loc['gatillo']== 'compra':
        actions = actions.iloc[:-1] 
    
   
    
    return actions



def getTrades(actions):
    import datetime as dt
    pares= actions.iloc[::2].loc[:,['Close']].reset_index()
    impares= actions.iloc[1::2].loc[:,['Close']].reset_index()
    trades = pd.concat([pares,impares],axis= 1)


    CT= 0
    trades.columns = ['fecha_compra','px_compra', 'fecha_venta', 'px_venta']
    trades['rendimiento']= trades['px_venta']/(trades['px_compra']-1)
    trades['rendimiento']-= CT
    trades['dias']= (trades.fecha_venta - trades.fecha_compra).dt.days
    if len(trades): 
        trades['resultados']= np.where(trades['rendimiento']>0, 'Ganador','Perdedor')
        trades['rendimientoAcumulado']= ((trades['rendimiento']+1).cumprod()-1)
    return trades

def resumen(trades):
    if len(trades):
        resultado=float(trades.iloc[-1:].rendimientoAcumulado-1)
        agg_cant= trades.groupby('resultados').size()
        agg_rend= trades.groupby('resultados').mean()['rendimiento']
        agg_tiempos= trades.groupby('resultados').sum()['dias']
        agg_tiempos_medio= trades.groupby('resultados').mean()['dias']
        
        
        r=pd.concat([agg_cant,agg_rend,agg_tiempos, agg_tiempos_medio], axis=1)
        r.columns= ['Cantidad', 'Rendimiento x Trade', 'Dias total','Dias x Trade']
        resumen= r.T
        
        
        try: 
            t_win= r['Dias total']['Ganador']
        except: 
            t_win=0
        
        try: 
            t_loss= r['Dias total']['Perdedor']
        except: 
            t_loss=0
        
        t= t_win+ t_loss
        tea= ((resultado+1)**(365/t)-1) if t > 0 else 0
        metricas={'rendimiento': round(resultado,4), 'dias_in': round(t,4), 'TEA': round(tea,4)}
    else:
        resumen=pd.DataFrame()
        metricas={'rendimiento':0, 'dias_in': 0, 'TEA':0}
    return resumen, metricas

###                 ESTPAS DE ANALISIS Y METRICAS
def eventDrivenLong(df):
    df['pct_change'] = df['Close'].pct_change()
    signals=df['gatillo'].tolist()
    pct_changes= df['pct_change'].tolist()
    
    total= len(signals)
    i , results = 1, [0]
    
    while i < total:
        if signals[i-1]== 'compra':
            j=i 
            while j < total:
                results.append(pct_changes[j])
                j+=1
                
                if signals[j-1]=='venta':
                    i = j
                    break
                if j == total:
                    i=j
                    print('Compra abierta')
                    break
        else: 
            results.append(0)
            i+=1
            
            
            
    result = pd.concat([df,pd.Series(data=results, index = df.index)], axis=1)
    result.columns.values[-1]= "strategy"
    return result



# MAIN

st.set_page_config(page_title="Sales Dashboard",page_icon="bar_chart:", layout="wide")
st.title('Trabajo Práctico Final de finanzas')




df = yf.download('SPY', auto_adjust=True)



df['pctChange'] = df.Close.pct_change() *100
df['sigma_250'] = df.pctChange.rolling(250).std() * 250**0.5
df['cruce_volumen'] = df.Volume / df.Volume.rolling(20).mean()
df = df.dropna()
data = df.copy()

#RSI
ruedas = 14
df['dif']= df['Close'].diff()
df['win']= np.where(df['dif'] > 0, df['dif'], 0)
df['loss']= np.where(df['dif'] < 0, abs(df['dif']), 0)

df['ema_win'] = df.win.ewm(alpha=1/ruedas).mean()
df['ema_loss'] = df.loss.ewm(alpha=1/ruedas).mean()
df['rs']= df.ema_win/ df.ema_loss
df['rsi']= 100 - (100 / (1+df.rs))

#On Balance Volume

df['Balance']= np.where(df.Close>df.Close.shift(),df['Volume'],np.where(df.Close < df.Close.shift(), -df['Volume'], 0))
df['OBV']= df['Balance'].cumsum()



#
bins_sigmas = [0,10,15,20,25,30,1000]
labels = ['Muy Bajo','Bajo','Medio','Alto','Muy Alto','Outlier']


bins_volumen = [0, 0.5, 0.75, 1, 1.25, 1.5,1000]
data['reg_volumen'] = pd.cut(data.cruce_volumen, bins=bins_volumen, labels=labels).shift()
data['cruce_precio'] = (data.Close/data.Close.rolling(300).mean()).shift()
data['cruce_30_200'] = (data.Close.rolling(30).mean()/data.Close.rolling(200).mean()).shift()
data['cruce_50_100'] = (data.Close.ewm(span=50).mean()/data.Close.ewm(span=100).mean()).shift()
data['rsi']= (df['rsi']/df['rsi'].rolling(50).mean()).shift()
data['OBV']= (df['OBV']/df.OBV.rolling(100).mean()).shift()

data.drop(['Open','High','Low'], axis=1, inplace=True)
data = data.dropna()




data = data.dropna()
frisk = 0.005 # ya esta en % es un 0.00005 sobre la unidad, equivale a 1.25% anual

sigmas_low = ['Muy Bajo','Bajo']
volumen_high = ['Medio','Alto','Muy Alto','Outlier']

sinteticos = pd.DataFrame(index=data.index)
sinteticos['BuyHold'] = data.pctChange
sinteticos['cruce_30_200'] = np.where(data.cruce_30_200 > 1, data.pctChange, frisk)
sinteticos['cruce_50_100'] = np.where(data.cruce_50_100 > 1, data.pctChange, frisk)
sinteticos['cruce_precio'] = np.where(data.cruce_precio > 1, data.pctChange, frisk)
sinteticos['highVolume'] = np.where(np.isin(data.reg_volumen, volumen_high), data.pctChange, frisk)
sinteticos['rsi'] = np.where(data.rsi > 1, data.pctChange, frisk)
sinteticos['OBV'] = np.where(data.OBV > 1, data.pctChange, frisk)

w = {'BuyHold':0, 'cruce_30_200':0.25, 'cruce_50_100':0.25,'cruce_precio':0.25 ,'highVolume':0.25, 'rsi': 0.25, 'OBV': 0.25}
weights = np.array(list(w.values()))    

sinteticos['composicion_final'] = np.dot(sinteticos, weights)

st.write(''' Backtesting:
El backtesting es la principal diferencia entre el trading discrecional y el trading cuantitativo. Es el estudio de los hipotéticos trades de una estrategia de trading que fue definida con anterioridad, con la finalidad de saber los resultados que hubiera tenido en el mercado si se hubiese aplicado, para evaluar este comportamiento se utilizan diferentes ratios y métricas de rendimiento.
Bots swing -Trading del tipo trend-following 
Es una estrategia comercial según la cual uno debe comprar un activo cuando su tendencia de precios sube, se intenta aprovechar la mayor parte de dicha tendencia y se vende por un determinado take-profit, stop loss o bien una nueva señal de salida que indique que se ha perdido la tendencia. 
El objetivo es capturar las tendencias del precio a corto plazo.    
Los inputs elegidos
Los Activos que se usaran son los siguientes: Acciones que componen al SP500 & BTC. Pertenecientes al Mercado Bursátil Americano y Cripto. Cuyo Timeframe trabajado será el diario.
1) Etapa de Datos 
Preparación de Datos:
Se trabajó con la fuente datos de yfinance, para continuar con el filtrado, procesado, normalizado de datos.

2) Etapa de investigación 
Una vez identificados los condicionantes previos, lo primero para desarrollar el sistema de trading es tener una lógica o idea inicial. La lógica del sistema está constituida por el conjunto de variables y condiciones que determinan los puntos de entrada y de salida. Constituye el núcleo de la estrategia, susceptible de ser mejorada.
Planteo de Racional:
Primero se trabaja con la lógica operacional, parametrización y gatillos. Luego buscar indicadores que sirvan para darnos señales y por último, la construcción de indicadores/Features
Luego se realiza: 
Filtro de datos, tabla de posibles trades, tiempo in/out y resultados y por último, el porcentaje de trades positivos y negativos.
 ''')
st.subheader('Testeo de Features en SP500')
st.set_option('deprecation.showPyplotGlobalUse', False)
sinteticos_px = (sinteticos/100+1).cumprod()
sinteticos_px.plot(logy=True, grid=True, figsize=(15,7))
st.pyplot()

     


###



plt.style.use('default')
fig, ax = plt.subplots(figsize=(15,7))


st.subheader('Composición sobre subyacente')
ax.plot(sinteticos_px.BuyHold, lw=1, c='gray', label = 'Buy & Hold')
ax.plot(sinteticos_px.composicion_final, c='r', label = 'Composición sobre subyacente')
ax.legend()
ax.grid()
st.pyplot(fig)

st.set_option('deprecation.showPyplotGlobalUse', False)
st.write(''' 3) Etapa de análisis y métricas:
Calcular todo tipo de ratios de la estrategia que van a ser nuestras métricas. La idea de las métricas es tener indicadores comparables de performance para después comparar estrategias y decidirse por la mejor a implementar de toda la lista que tengamos 
Se realiza la tabla de resultados por trade y la comparación con el buy&hold
Métricas:
Usaremos el Enfoque Event Driven y Métricas de riesgo. Estas métricas permiten conocer el rendimiento del sistema y proporcionan un buen punto de partida para probar una estrategia de trading. 

4) Etapa de parametrización
Aquí se debe evitar el over fiting, básicamente vamos a analizar la sensibilidad de nuestro modo o racional evaluado en alguna métrica que consideremos relevante, en función de los parámetros variables del racional.

5) Resultados:
Base de datos:
Se trabajó con WorkBench para la creación de la BD con SQL, ésta registra los trades realizados, los features y los triggers de compra/venta.
Ploteo:
Se graficó por medio de Streamlit, un “framework” de Python de código abierto que permite de manera integrada desarrollar aplicaciones, muy usado para la ciencia de datos.


Desarrollo:

Los Activos que se usaran son los siguientes: Acciones que componen al SP500 & BTC. Pertenecientes al Mercado Bursátil Americano y Cripto. Cuyo Timeframe trabajado será el diario.
El paso siguiente es hacer un filtrado de las empresas en función de los resultados de la estrategia aplicada a las acciones del sp500 
 ''')



### PARTE DE MOSTRAS LA SELECCION DE EMPRESAS





sp500=pd.read_html('https://en.wikipedia.org/wiki/List_of_S%26P_500_companies')[0]#este es el dataframe completo
sp500_tickers=list(sp500.Symbol)# ACA paso a lista una columna del dataframe (symbol)
tickers=[e for e in sp500_tickers if e not in ('BRK.B','BF.B','CEG')]

dicc=pd.DataFrame()

for i in tickers:                  
        try:
            data=pd.DataFrame()
            features=pd.DataFrame()
            data= getData( i, data_from='2000-01-01',data_to='2022-11-20')
            features= getFeatures(data, n_obv=70, n_sigma=40, n_rsi=20, fast= 50, slow=200)
            actions=getActions(features, trig_buy_cross=-0.04, trig_buy_rsi=67, trig_buy_sigma=0.01, trig_sell_cross=-0.03, trig_sell_rsi=40, trig_sell_obv=-0.9)
            trades= getTrades(actions)
            resumen(trades)

        
            t =resumen(trades)
            pay= eventDrivenLong(data)
            results=pay.iloc[:,-2:].add(1).cumprod()
            
            p=float(results['pct_change'].sum())
            b=float(results['strategy'].sum())
            
            # Si la extrategia es mayor al benchmark
            a=p-b
            c = float(results['pct_change'][-1:] - results['strategy'][-1:])
            if a and c < 0: 
                dicc[i]=a
            
        except:
            print(i,'falla')
            pass
        

        
                                                                                           



lista1=list(dicc.columns.values)



dicc2=pd.DataFrame()
for i in lista1:
        data=pd.DataFrame()
        features=pd.DataFrame()
        data= getData( i, data_from='2000-01-01',data_to='2022-11-20')
        try:
            features= getFeatures(data, n_obv=70, n_sigma=40, n_rsi=20, fast= 50, slow=200)
            actions=getActions(features, trig_buy_cross=-0.04, trig_buy_rsi=67, trig_buy_sigma=0.01, trig_sell_cross=-0.03, trig_sell_rsi=40, trig_sell_obv=-0.9)
            trades= getTrades(actions)
            resumen(trades)

    
            t =resumen(trades)
            #Cuanto es el monto de ganancia/perdida
            try:
                a=t[0].loc['Rendimiento x Trade'] * t[0].loc['Cantidad']
                dicc2[i]=a
            except:
            
                pass
        except:
            print(i, 'falla')
            pass
        
        
        

# dicc2 = dicc2.iloc[0].sort_values(ascending=False)
        
                                                                                           

resultadosT=pd.DataFrame()
if 'Perdedor' in dicc2:
    resultadosT =  dicc2.loc['Ganador']- dicc2.loc['Perdedor'] 
else:
    resultadosT=  dicc2.loc['Ganador']


#Lista de empresas ganadoras ordenadas segun los resultados
ordenados = resultadosT.sort_values( ascending= False)

lista=(ordenados.keys())
lista = lista[:10]                                                                                   #modifi

dat = pd.read_html('https://en.wikipedia.org/wiki/List_of_S%26P_500_companies')[0][['Symbol', 'GICS Sector','GICS Sub-Industry']].set_index(['Symbol'])

sectores = list(set(dat['GICS Sector']))
sub_sectores= list(set(dat['GICS Sub-Industry']))

#Sub sectores de las Empresas
    
frame = yf.download(list(lista), start = '2000-01-01', progress= False)['Close']
frame= frame.reindex(columns=lista)
mean = frame.rolling(150).mean()


frame1= pd.DataFrame(np.where(frame.iloc[-1] >= mean.iloc[-1] ,1,1), index=frame.columns)
dat['>mean(150)']= frame1[0]


suma = pd.DataFrame()
for i in range(len(sub_sectores)):
    x= pd.DataFrame(dat['>mean(150)'][dat['GICS Sub-Industry']==str(sub_sectores[i])]).sum()
    suma= pd.concat([suma,x], axis=1)


suma.columns = sub_sectores
suma = suma.T


st.subheader('Sub sectores de las Empresas')
suma[suma['>mean(150)']>0].plot(kind='bar', figsize=(25,25),title='Empresas',  ylabel='Nro de empresas', xlabel='sub sectores', legend=False, rot=30)
st.pyplot()






#Sectores de las Empresas


frame1= pd.DataFrame(np.where(frame.iloc[-1] > mean.iloc[-1],1,1), index=frame.columns)
dat['>mean(150)']= frame1[0]


suma = pd.DataFrame()
for i in range(len(sectores)):
    x= pd.DataFrame(dat['>mean(150)'][dat['GICS Sector']==str(sectores[i])]).sum()
    suma= pd.concat([suma,x], axis=1)
suma.columns = sectores
suma = suma.T

st.subheader('Sectores de las Empresas')
suma[suma['>mean(150)']>0].plot(kind='bar', figsize=(15,10),title='Empresas',  ylabel='Nro de empresas', xlabel='sectores', legend=False, rot=30)
st.pyplot()

#  SE PLOTEA LAS 10 EMPRESAS SELECCIONADAS : LA LISTA ES LO QUE CONTIENE LOS TICKERS FILTRADOS

st.header('Backtestig de las 10 empresas seleccionadas, SPY & BTC')
# AGREGO A BTC y SP500

lista= list(lista)


lista.append('BTC-USD')
lista.append('SPY')
st.write('''Se analiza el rendimiento de la estrategia a comparación del Buy&Hold ''')
st.write('''Se grafican los gatillos de compra y venta que actúan en función de los indicadores ''')   

activos= pd.DataFrame(columns=lista)

#Se aplica el backtest a los activos seleccionados (10 activos)
for i in lista:
    data=getData(ticker= i, data_from='2000-01-01',data_to='2022-11-20')
    
    st.write(i)
    
    if i == 'BTC-USD':
        #ESTRATEGIA DE BTC (SI PONGO N_OBV EN 70 ES PARA MENOS TRADES Y 200 PARA MAS )
        features= getFeatures(data, n_obv=200, n_sigma=40, n_rsi=15, fast= 10, slow=90)
        actions=getActions(features, trig_buy_cross=-0.04, trig_buy_rsi=69, trig_buy_sigma=0.01, trig_sell_cross=-0.09, trig_sell_rsi=55, trig_sell_obv=-2)
        trades= getTrades(actions)
        print(resumen(trades))
        
    elif i == 'SPY':
        features= getFeatures(data, n_obv=70, n_sigma=40, n_rsi=20, fast= 10, slow=200,cross_price=50,fast1=50,slow1=200,rsi_m=10,obv_m=100)
        actions=getActions(features, trig_buy_cross=0.0, trig_buy_rsi=55, trig_buy_sigma=0.01, trig_sell_cross=-0.0, trig_sell_rsi=40, trig_sell_obv=0)
        trades= getTrades(actions)
        print(resumen(trades))
    else:

        #ESTRATEGIA DE ACCIONES
        features= getFeatures(data, n_obv=70, n_sigma=40, n_rsi=20, fast= 50, slow=200)
        actions=getActions(features, trig_buy_cross=-0.04, trig_buy_rsi=67, trig_buy_sigma=0.01, trig_sell_cross=-0.03, trig_sell_rsi=40, trig_sell_obv=-0.9)
        trades= getTrades(actions)
        print(resumen(trades))
        # guardar actions
        #se podria guardar los trades
        features.to_csv('featuresBTC.csv')
        actions.to_csv('actionsBTC.csv')
        trades.to_csv('tradesBTC.csv')
        

    
    



    pay= eventDrivenLong(data)
    results=pay.iloc[:,-2:].add(1).cumprod()

 
    st.write('Activo {}'.format(i))
    t= 'Comparacion Hold vs Strategy de {}'.format(i)
    results.plot(figsize=(15,6), title=t,grid=True,logy=True)  
    st.pyplot()           
    resumen(trades)

    df= data.iloc[:]
    compras= actions.loc[actions.gatillo=='compra']
    ventas= actions.loc[actions.gatillo== 'venta']

    
     
    fig, ax= plt.subplots(figsize=(18,8))
    ax.plot(df.Close, '--k', alpha=0.4, lw=1, label='Precio de {}'.format(i))
    ax.plot(compras.Close*0.95, marker='^', lw=0,markersize= 10, color='g',label='compras')
    ax.plot(ventas.Close*0.95, marker='v', lw=0,markersize= 10, color='red',label='ventas')
    ax.legend()
    ax.set_yscale('log')
    ax.grid(axis='both')
    
    st.pyplot(fig)
    
    
    
    
activos.to_csv('activos.csv')
    





