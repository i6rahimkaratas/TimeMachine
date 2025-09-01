import tweepy
import csv
import json
from datetime import datetime, timezone
import time
import os

class TwitterScraper:
    def __init__(self, bearer_token):
        self.client = tweepy.Client(bearer_token=bearer_token)
    
    def get_user_tweets(self, username, start_date=None, end_date=None, max_tweets=100):
        tweets_data = []
        try:
            user = self.client.get_user(username=username)
            if not user.data:
                print(f"Kullanıcı bulunamadı: {username}")
                return []
            user_id = user.data.id
            print(f"Kullanıcı bulundu: {username} (ID: {user_id})")
            tweet_fields = [
                'created_at', 'public_metrics', 'text', 'author_id',
                'conversation_id', 'in_reply_to_user_id', 'referenced_tweets'
            ]
            kwargs = {
                'user_id': user_id,
                'tweet_fields': tweet_fields,
                'max_results': min(max_tweets, 100)
            }
            if start_date:
                kwargs['start_time'] = f"{start_date}T00:00:00Z"
            if end_date:
                kwargs['end_time'] = f"{end_date}T23:59:59Z"
            tweets = tweepy.Paginator(
                self.client.get_users_tweets,
                **kwargs
            ).flatten(limit=max_tweets)
            for tweet in tweets:
                tweet_data = {
                    'id': tweet.id,
                    'text': tweet.text,
                    'created_at': tweet.created_at.isoformat() if tweet.created_at else None,
                    'retweet_count': tweet.public_metrics['retweet_count'] if tweet.public_metrics else 0,
                    'like_count': tweet.public_metrics['like_count'] if tweet.public_metrics else 0,
                    'reply_count': tweet.public_metrics['reply_count'] if tweet.public_metrics else 0,
                    'quote_count': tweet.public_metrics['quote_count'] if tweet.public_metrics else 0,
                    'url': f"https://twitter.com/{username}/status/{tweet.id}"
                }
                tweets_data.append(tweet_data)
                time.sleep(0.1)
            print(f"{len(tweets_data)} tweet çekildi.")
            return tweets_data
        except tweepy.TooManyRequests:
            print("Rate limit aşıldı. 15 dakika bekleyin.")
            return tweets_data
        except tweepy.Unauthorized:
            print("Yetkilendirme hatası. API anahtarınızı kontrol edin.")
            return tweets_data
        except Exception as e:
            print(f"Hata oluştu: {str(e)}")
            return tweets_data
    
    def save_to_text_file(self, tweets_data, filename, format_type='simple'):
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                if format_type == 'simple':
                    for tweet in tweets_data:
                        f.write(f"{tweet['text']}\n")
                        f.write("-" * 50 + "\n")
                elif format_type == 'detailed':
                    for tweet in tweets_data:
                        f.write(f"Tarih: {tweet['created_at']}\n")
                        f.write(f"Tweet ID: {tweet['id']}\n")
                        f.write(f"URL: {tweet['url']}\n")
                        f.write(f"Beğeni: {tweet['like_count']} | Retweet: {tweet['retweet_count']} | Yanıt: {tweet['reply_count']}\n")
                        f.write(f"Metin: {tweet['text']}\n")
                        f.write("=" * 80 + "\n\n")
                elif format_type == 'json':
                    json.dump(tweets_data, f, indent=2, ensure_ascii=False)
            print(f"Tweet'ler {filename} dosyasına kaydedildi.")
        except Exception as e:
            print(f"Dosya kaydetme hatası: {str(e)}")

    def save_to_csv(self, tweets_data, filename):
        try:
            with open(filename, 'w', newline='', encoding='utf-8') as f:
                if tweets_data:
                    fieldnames = tweets_data[0].keys()
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(tweets_data)
            print(f"Tweet'ler {filename} dosyasına CSV formatında kaydedildi.")
        except Exception as e:
            print(f"CSV kaydetme hatası: {str(e)}")

def main():
    BEARER_TOKEN = "YOUR_BEARER_TOKEN_HERE"
    scraper = TwitterScraper(BEARER_TOKEN)
    username = input("X kullanıcı adını girin (@ olmadan): ")
    start_date = input("Başlangıç tarihi (YYYY-MM-DD) veya boş bırakın: ") or None
    end_date = input("Bitiş tarihi (YYYY-MM-DD) veya boş bırakın: ") or None
    max_tweets = int(input("Maksimum tweet sayısı (varsayılan 100): ") or 100)
    print(f"\n{username} kullanıcısından tweet'ler çekiliyor...")
    tweets = scraper.get_user_tweets(
        username=username,
        start_date=start_date,
        end_date=end_date,
        max_tweets=max_tweets
    )
    if tweets:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_filename = f"tweets_{username}_{timestamp}"
        scraper.save_to_text_file(tweets, f"{base_filename}_simple.txt", 'simple')
        scraper.save_to_text_file(tweets, f"{base_filename}_detailed.txt", 'detailed')
        scraper.save_to_text_file(tweets, f"{base_filename}.json", 'json')
        scraper.save_to_csv(tweets, f"{base_filename}.csv")
        print(f"\nToplam {len(tweets)} tweet kaydedildi.")
        print("Dosyalar:")
        print(f"- {base_filename}_simple.txt (sadece metin)")
        print(f"- {base_filename}_detailed.txt (detaylı)")
        print(f"- {base_filename}.json (JSON format)")
        print(f"- {base_filename}.csv (CSV format)")
    else:
        print("Hiç tweet bulunamadı.")

if __name__ == "__main__":
    main()
