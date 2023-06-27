from itertools import count
from tkinter import ANCHOR
import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
#py -m streamlit run Montecarlo.py


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


def getActionss(features, trig_buy_cross=0, trig_buy_rsi=30, trig_buy_sigma=0.01, trig_sell_cross=-0.01,trig_sell_rsi= 70, trig_sell_obv=0):
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
    # data['gatillo']=actions['gatillo']

    #permite que el primero en el DF siempres sea comrpa y el ultimo siempre sea una venta

    if actions.iloc[0].loc['gatillo']== 'venta':
        actions= actions.iloc[1:]
    if actions.iloc[-1].loc['gatillo']== 'compra':
        actions = actions.iloc[:-1] 
    
   
    
    return actions


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




import random 


samples = {'trig_buy_sigma': [i/500 for i in range(20)],
           'trig_buy_rsi': [i for i in range(50,70)],
           'trig_buy_cross': [-0.05+1/100 for i in range(20)],
           'trig_sell_rsi': [i for i in range(40,60)],
           'trig_sell_cross': [-0.1+i/100 for i in range(20)],
           'trig_sell_obv': [-2+i/10 for i in range(40)]}
           
def getTriggers():
    triggers= {}
    for key in samples.keys():
        triggers[key]= round(random.choice(samples[key]),4)

    return triggers

getTriggers()
           
#AQUI ESTAN LOS FEATURES A CAMBIAR
nombre= 'AMZN'
data=getData(nombre, data_from='2000-01-01',data_to='2022-11-20')
features= getFeatures(data, n_obv=70, n_sigma=40, n_rsi=20, fast= 10, slow=200)
           
           
           


l=[]
for sample in range(5000):
    triggers=getTriggers()
    actions=getActionss(features, trig_buy_cross=triggers['trig_buy_cross'], trig_buy_rsi=triggers['trig_buy_rsi'], trig_buy_sigma=triggers['trig_buy_sigma'], trig_sell_rsi=triggers['trig_buy_rsi'], trig_sell_obv=triggers['trig_sell_obv'])
    trades= getTrades(actions) 
    resultados_df, resultados_dict= resumen(trades)
    for key in samples.keys():
       resultados_dict[key]= triggers[key]
       l.append(resultados_dict)

results= pd.DataFrame(l)


top20= results.dropna().sort_values('TEA', ascending=False).head(20)
st.title('Top 20 parametros en funcion de TEA')
st.write(top20)


actions=getActions(features,trig_buy_cross=-0.04, trig_buy_rsi=67, trig_buy_sigma=0.01, trig_sell_cross=-0.03, trig_sell_rsi=40, trig_sell_obv=-0.9)
trades= getTrades(actions)
res= resumen(trades)
st.write(res[0], res[1])


pay= eventDrivenLong(data)
results=pay.iloc[:,-2:].add(1).cumprod()



                                                                                   
st.subheader('Resultados')

a=float(results['pct_change'].sum())
b=float(results['strategy'].sum())
if (a-b)<0:
    
    t= 'Comparacion Hold vs Strategy'
    st.set_option('deprecation.showPyplotGlobalUse', False)
    results.plot(figsize=(15,6), title=t,grid=True,logy=True)  
    st.pyplot()        
else:
    st.write('Hold is > Strategy') 
    
t =resumen(trades)

a=t[0].loc['Rendimiento x Trade'] * t[0].loc['Cantidad']


df= data.iloc[:]
compras= actions.loc[actions.gatillo=='compra']
ventas= actions.loc[actions.gatillo== 'venta']

fig, ax= plt.subplots(figsize=(18,8))
ax.plot(df.Close, '--k', alpha=0.4, lw=1, label='Precio de {}'.format(nombre))
ax.plot(compras.Close*0.95, marker='^', lw=0,markersize= 10, color='g',label='compras')
ax.plot(ventas.Close*0.95, marker='v', lw=0,markersize= 10, color='red',label='compras')
ax.legend()
ax.set_yscale('log')
ax.grid(axis='both')
st.pyplot(fig)
