import tweepy
import csv
import time
import datetime
import glob
import os
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

CSV_DIR = '/data/'
#CSV_DIR = 'data/'

hashtags = ["#brownuniversity", "@brownuniversity"]
analyzer = SentimentIntensityAnalyzer()

with open('twitter-api-credentials.txt', 'r') as f:
    consumer_key = f.readline().rstrip('\n')
    consumer_secret = f.readline().rstrip('\n')

auth = tweepy.AppAuthHandler(consumer_key, consumer_secret)
api = tweepy.API(auth)

newly_analyzed = 0

brown_accounts = []
with open('brown-affiliated-accounts.txt', 'r') as f:
    for i, line in enumerate(f):
        brown_accounts.append(line.lower().rstrip('\n'))

for tag in hashtags:
    if not os.path.exists(CSV_DIR + tag):
        os.makedirs(CSV_DIR + tag) # potential race condition.. unlikely
    newest = None
    # find the newest file and take the ID from the first non-header row
    for f in sorted(glob.glob(CSV_DIR + tag + "/*.csv")):
        with open(f) as file:
            r = csv.reader(file)
            for row in r:
                if not row[0] == 'ID':
                    newest = int(row[0])
                    break
            break

    q = tag + ' -filter:retweets'
    if newest:
        tweets = tweepy.Cursor(
            api.search, q=q, tweet_mode='extended',
            count=100, result_type='recent', since_id=newest).items()
    else:
        tweets = tweepy.Cursor(
            api.search, q=q, tweet_mode='extended',
            count=100, result_type='recent').items()

    d = datetime.datetime.now().strftime('%m-%d-%Y')

    original = CSV_DIR + tag + "/" + d + ".csv"
    fname = original
    exists = os.path.exists(original)
    if exists:
        fname = CSV_DIR + tag + "/" + d + "-temp.csv"

    with open(fname, 'w+', newline='') as f:
        w = csv.writer(f, delimiter=',')
        while True:
            try:
                tweet = tweets.next()
                row = [
                    tweet.id_str,
                    tweet.user.screen_name,
                    tweet.created_at.timestamp(),
                    tweet.retweet_count,
                    tweet.favorite_count,
                    # strip UTF-8 emojis
                    tweet.full_text.encode('ascii', 'ignore').decode('ascii')
                ]
                if not row[1].lower() in brown_accounts:
                    row[5] = row[5].replace('\n', '')
                    analysis = analyzer.polarity_scores(row[5])
                    row.append(analysis['compound'])
                    row.append(analysis['pos'])
                    row.append(analysis['neg'])
                    w.writerow(row)
                    newly_analyzed = newly_analyzed + 1
            except tweepy.error.TweepError as e:
                wait_to = api.rate_limit_status()['resources']['search']['/search/tweets']['reset']
                wait = int((wait_to + 3) - time.time())
                print("Hit rate limit, waiting " + str(wait) + " seconds")
                time.sleep(wait)
                print("Resuming...")
            except StopIteration:
                break
        if exists:
            with open(original, 'r', newline='') as f_old:
                r = csv.reader(f_old)
                for row in r:
                    if not row[0] == 'ID':
                        w.writerow(row)
    if exists:
        os.remove(original)
        os.rename(fname, original)

print("analyzed " + str(newly_analyzed) + " new tweets")
