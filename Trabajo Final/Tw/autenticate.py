
import tweepy

'''
Función utilizada para utilizar la Api de Twitter
'''
def get_auth():
    consumer_key=  'PBiSl1puKpSXsxOS4Yh8CVAPA'

    consumer_secret='8l6aqlblI3GAuOhCbkrPu9oyyhtzg5eCZKhjbFt8es80rdYUJG'

    access_token='1580281519087681536-iuhq2uYiPAqNSqqzt2ykr5wXUUfruz'

    access_token_secret='7IcXYRrEkCr2CfXUp2IC6BZbxxjuMINEF2zwcq6O5GQfd'
    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token, access_token_secret)
    return auth


