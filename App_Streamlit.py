"""
Created on Thu July 7th, 2022

@author: Ravi Byakod
"""

import streamlit as st
import warnings

# packages needed
import numpy as np
import pandas as pd
import tweepy
import json
from tweepy import OAuthHandler
import re
import textblob
from textblob import TextBlob
from wordcloud import WordCloud, STOPWORDS, ImageColorGenerator
import openpyxl
import time
import tqdm

# Viz Pkgs
import matplotlib.pyplot as plt
import matplotlib
import seaborn as sns

import dotenv

from dotenv import load_dotenv
from utils import process_tweet
from logistics_prediction import analyze_tweet_sentiment

matplotlib.use('Agg')

# To Hide Warnings
warnings.filterwarnings("ignore")
st.set_option('deprecation.showfileUploaderEncoding', False)
st.set_option('deprecation.showPyplotGlobalUse', False)

STYLE = """
<style>
img {
    max-width: 100%;
}
</style> """


def main():
    """ Common ML Dataset Explorer """
    # st.title("Live twitter Sentiment analysis")
    # st.subheader("Select a topic which you'd like to get the sentiment analysis on :")

    html_temp = """ 
    <div style="background-color:tomato;"><p style="color:white;font-size:40px;padding:9px">Live twitter Sentiment analysis</p></div>
    """
    st.markdown(html_temp, unsafe_allow_html=True)
    st.subheader("Select a topic which you'd like to get the sentiment analysis on :")

    # Twitter API Connection
    # 2.Set Connection
    # Get from developers.twitter.com/App->Setting->keys&tokens
    # Just assign the credentials
    # take environment variables from .env.
    load_dotenv()
    config = dotenv.dotenv_values(".env")
    print(config)

    #keys and tokens from the Twitter Dev Console
    consumer_key = config.get('consumer_key')
    consumer_secret = config.get('consumer_secret')
    access_token = config.get('access_token')
    access_token_secret = config.get('access_token_secret')



    # Use the above credentials to authenticate the API.
    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token, access_token_secret)
    api = tweepy.API(auth)

    df = pd.DataFrame(columns=["Date","User","IsVerified","Tweet","Likes","RT",'User_location'])
    
    # Write a Function to extract tweets:
    def get_tweets(Topic,Count):
        i=0
        # my_bar = st.progress(100) # To track progress of Extracted tweets
        for tweet in tweepy.Cursor(api.search_tweets, q=Topic,count=100, lang="en",exclude='retweets').items():
            # time.sleep(0.1)
            # my_bar.progress(i)
            df.loc[i,"Date"] = tweet.created_at
            df.loc[i,"User"] = tweet.user.name
            df.loc[i,"IsVerified"] = tweet.user.verified
            df.loc[i,"Tweet"] = tweet.text
            df.loc[i,"Likes"] = tweet.favorite_count
            df.loc[i,"RT"] = tweet.retweet_count
            df.loc[i,"User_location"] = tweet.user.location
            # df.to_csv("TweetDataset.csv",index=False)
            # df.to_excel('{}.xlsx'.format("TweetDataset"),index=False)   ## Save as Excel
            i=i+1
            if i>Count:
                break
            else:
                pass

    # # Function to Clean the Tweet.
    def clean_tweet(tweet):
        return ' '.join(re.sub('(@[A-Za-z0-9]+)|([^0-9A-Za-z \t])|(\w+:\/\/\S+)|([RT])', ' ', tweet.lower()).split())

    # Function to analyze Sentiment
    def analyze_sentiment(tweet):
        analysis = TextBlob(tweet)
        if analysis.sentiment.polarity > 0:
            return 'Positive'
        elif analysis.sentiment.polarity == 0:
            return 'Neutral'
        else:
            return 'Negative'
    
    # Function to Pre-process data for Wordcloud
    def prep_cloud(topic_text, topic):
        topic = str(topic).lower()
        topic= ' '.join(re.sub('([^0-9A-Za-z \t])', ' ', topic).split())
        topic = re.split("\s+", str(topic))
        stopwords = set(STOPWORDS)
        # Add our topic in Stopwords, so it doesnt appear in wordClous
        stopwords.update(topic)
        ###
        text_new = " ".join([txt for txt in topic_text.split() if txt not in stopwords])
        return text_new

    from PIL import Image
    image = Image.open('Logo1.jpg')
    st.image(image, caption='Twitter for Analytics',use_column_width=True)

    # Collect Input from user :
    Topic = str()
    Topic = str(st.text_input("Enter the topic you are interested in (Press Enter once done)"))     
    
    if len(Topic) > 0 :
        
        # Call the function to extract the data. pass the topic and filename you want the data to be stored in.
        with st.spinner("Please wait, Tweets are being extracted"):
            get_tweets(Topic , Count=200)
        st.success('Tweets have been Extracted !!!!')    

        # Call a function to get Clean tweets
        df['clean_tweet'] = df['Tweet'].apply(lambda x : process_tweet(x))
    
        # Call function to get the Sentiments
        raw_tweets = df['clean_tweet']
        df["Sentiment"] = analyze_tweet_sentiment(raw_tweets)


        # Write Summary of the Tweets
        st.write("Total Tweets Extracted for Topic '{}' are : {}".format(Topic,len(df.Tweet)))
        st.write("Total Positive Tweets are : {}".format(len(df[df["Sentiment"]=="Positive"])))
        st.write("Total Negative Tweets are : {}".format(len(df[df["Sentiment"]=="Negative"])))
        st.write("Total Neutral Tweets are : {}".format(len(df[df["Sentiment"]=="Neutral"])))
        
        # See the Extracted Data : 
        if st.button("See the Extracted Data"):
            # st.markdown(html_temp, unsafe_allow_html=True)
            st.success("Below is the Extracted Data :")
            st.write(df.head(50))

        # get the countPlot
        if st.button("Get Count Plot for Different Sentiments"):
            st.success("Generating A Count Plot")
            st.subheader(" Count Plot for Different Sentiments")
            st.write(sns.countplot(df["Sentiment"]))
            st.pyplot()
        
        # draw a Pie chart
        if st.button("Get Pie Chart for Different Sentiments"):
            st.success("Generating A Pie Chart")
            a=len(df[df["Sentiment"]=="Positive"])
            b=len(df[df["Sentiment"]=="Negative"])
            c=len(df[df["Sentiment"]=="Neutral"])
            d=np.array([a,b,c])
            explode = (0.1, 0.0, 0.1)
            st.write(plt.pie(d,shadow=True,explode=explode,labels=["Positive","Negative","Neutral"],autopct='%1.2f%%'))
            st.pyplot()

        # get the countPlot Based on Verified and unverified Users
        if st.button("Get Count Plot Based on Verified and unverified Users"):
            st.success("Generating A Count Plot (Verified and unverified Users)")
            st.subheader(" Count Plot for Different Sentiments for Verified and unverified Users")
            st.write(sns.countplot(df["Sentiment"],hue=df.IsVerified))
            st.pyplot()

        # Points to add
        # 1. Make Background Clear for Wordcloud
        # 2. Remove keywords from Wordcloud
        # Create a Worlcloud
        if st.button("Get WordCloud for all things said about {}".format(Topic)):
            st.success("Generating A WordCloud for all things said about {}".format(Topic))
            text = " ".join(review for review in df.clean_tweet)
            stopwords = set(STOPWORDS)
            text_newALL = prep_cloud(text,Topic)
            wordcloud = WordCloud(stopwords=stopwords,max_words=800,max_font_size=70).generate(text_newALL)
            st.write(plt.imshow(wordcloud, interpolation='bilinear'))
            st.pyplot()

        # Wordcloud for Positive tweets only
        if st.button("Get WordCloud for all Positive Tweets about {}".format(Topic)):
            st.success("Generating A WordCloud for all Positive Tweets about {}".format(Topic))
            text_positive = " ".join(review for review in df[df["Sentiment"]=="Positive"].clean_tweet)
            stopwords = set(STOPWORDS)
            text_new_positive = prep_cloud(text_positive,Topic)
            # text_positive=" ".join([word for word in text_positive.split() if word not in stopwords])
            wordcloud = WordCloud(stopwords=stopwords,max_words=800,max_font_size=70).generate(text_new_positive)
            st.write(plt.imshow(wordcloud, interpolation='bilinear'))
            st.pyplot()

        # Wordcloud for Negative tweets only
        if st.button("Get WordCloud for all Negative Tweets about {}".format(Topic)):
            st.success("Generating A WordCloud for all Positive Tweets about {}".format(Topic))
            text_negative = " ".join(review for review in df[df["Sentiment"]=="Negative"].clean_tweet)
            stopwords = set(STOPWORDS)
            text_new_negative = prep_cloud(text_negative,Topic)
            # text_negative=" ".join([word for word in text_negative.split() if word not in stopwords])
            wordcloud = WordCloud(stopwords=stopwords,max_words=800,max_font_size=70).generate(text_new_negative)
            st.write(plt.imshow(wordcloud, interpolation='bilinear'))
            st.pyplot()
        
    st.sidebar.header("About App")
    st.sidebar.info("A Twitter Sentiment analysis Project which will scrap twitter for the topic selected by the user. The extracted tweets will then be used to determine the Sentiments of those tweets. \
                    The different Visualizations will help us get a feel of the overall mood of the people on Twitter regarding the topic we select.")
    st.sidebar.text("Built with Streamlit")
    
    st.sidebar.header("For Any Queries/Suggestions Please reach out at :")
    st.sidebar.info("rbyakod@gmail.com")
    # st.sidebar.subheader("Scatter-plot setup")
    # box1 = st.sidebar.selectbox(label= "X axis", options = numeric_columns)
    # box2 = st.sidebar.selectbox(label="Y axis", options=numeric_columns)
    # sns.jointplot(x=box1, y= box2, data=df, kind = "reg", color= "red")
    # st.pyplot()

    if st.button("Exit"):
        st.balloons()


if __name__ == '__main__':
    main()

