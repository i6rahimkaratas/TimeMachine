from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time
import json
from datetime import datetime
import re
import os

class TwitterScraperSelenium:
    def __init__(self, headless=True):
        self.tweets_data = []
        self.setup_driver(headless)
    
    def setup_driver(self, headless):
        try:
            chrome_options = Options()
            if headless:
                chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36")
            service = Service()
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            print("✅ Chrome WebDriver başlatıldı")
        except Exception as e:
            print(f"❌ WebDriver hatası: {str(e)}")
            print("Chrome ve ChromeDriver yüklü olduğundan emin olun:")
            print("brew install --cask google-chrome")
            print("brew install chromedriver")
            raise
    
    def scroll_and_collect_tweets(self, max_tweets=100, scroll_pause=2):
        tweets_collected = []
        last_height = self.driver.execute_script("return document.body.scrollHeight")
        scroll_attempts = 0
        max_scroll_attempts = 50
        
        while len(tweets_collected) < max_tweets and scroll_attempts < max_scroll_attempts:
            try:
                tweet_elements = self.driver.find_elements(
                    By.CSS_SELECTOR, 
                    '[data-testid="tweet"]'
                )
                for tweet_element in tweet_elements:
                    try:
                        text_element = tweet_element.find_element(
                            By.CSS_SELECTOR, 
                            '[data-testid="tweetText"]'
                        )
                        tweet_text = text_element.text
                        try:
                            time_element = tweet_element.find_element(By.TAG_NAME, "time")
                            tweet_date = time_element.get_attribute("datetime")
                        except NoSuchElementException:
                            tweet_date = datetime.now().isoformat()
                        try:
                            link_elements = tweet_element.find_elements(
                                By.CSS_SELECTOR, 
                                'a[href*="/status/"]'
                            )
                            tweet_url = link_elements[0].get_attribute("href") if link_elements else ""
                        except:
                            tweet_url = ""
                        stats = self.extract_tweet_stats(tweet_element)
                        tweet_id = ""
                        if tweet_url:
                            match = re.search(r'/status/(\d+)', tweet_url)
                            if match:
                                tweet_id = match.group(1)
                        tweet_data = {
                            'id': tweet_id,
                            'text': tweet_text,
                            'created_at': tweet_date,
                            'url': tweet_url,
                            'like_count': stats.get('likes', 0),
                            'retweet_count': stats.get('retweets', 0),
                            'reply_count': stats.get('replies', 0),
                            'quote_count': stats.get('quotes', 0)
                        }
                        if tweet_data not in tweets_collected:
                            tweets_collected.append(tweet_data)
                            if len(tweets_collected) % 10 == 0:
                                print(f"📊 {len(tweets_collected)} tweet toplandı...")
                    except Exception as e:
                        continue
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(scroll_pause)
                new_height = self.driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    scroll_attempts += 1
                else:
                    scroll_attempts = 0
                last_height = new_height
            except Exception as e:
                print(f"Scroll hatası: {str(e)}")
                break
        return tweets_collected[:max_tweets]
    
    def extract_tweet_stats(self, tweet_element):
        stats = {'likes': 0, 'retweets': 0, 'replies': 0, 'quotes': 0}
        try:
            like_elements = tweet_element.find_elements(
                By.CSS_SELECTOR, 
                '[data-testid="like"] span'
            )
            if like_elements:
                stats['likes'] = self.parse_count(like_elements[0].text)
            retweet_elements = tweet_element.find_elements(
                By.CSS_SELECTOR, 
                '[data-testid="retweet"] span'
            )
            if retweet_elements:
                stats['retweets'] = self.parse_count(retweet_elements[0].text)
            reply_elements = tweet_element.find_elements(
                By.CSS_SELECTOR, 
                '[data-testid="reply"] span'
            )
            if reply_elements:
                stats['replies'] = self.parse_count(reply_elements[0].text)
        except Exception:
            pass
        return stats
    
    def parse_count(self, count_text):
        if not count_text:
            return 0
        count_text = count_text.strip()
        if count_text.endswith('K'):
            return int(float(count_text[:-1]) * 1000)
        elif count_text.endswith('M'):
            return int(float(count_text[:-1]) * 1000000)
        else:
            try:
                return int(count_text.replace(',', ''))
            except:
                return 0
    
    def get_user_tweets(self, username, max_tweets=100):
        try:
            url = f"https://twitter.com/{username}"
            print(f"🌐 {url} adresine gidiliyor...")
            self.driver.get(url)
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, '[data-testid="tweet"]'))
            )
            print("📜 Tweet'ler toplanıyor...")
            tweets = self.scroll_and_collect_tweets(max_tweets)
            return tweets
        except TimeoutException:
            print("❌ Sayfa yüklenemedi veya tweet bulunamadı")
            return []
        except Exception as e:
            print(f"❌ Hata: {str(e)}")
            return []
    
    def search_tweets(self, query, max_tweets=100):
        try:
            search_url = f"https://twitter.com/search?q={query}&src=typed_query&f=live"
            print(f"🔍 Arama yapılıyor: {search_url}")
            self.driver.get(search_url)
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, '[data-testid="tweet"]'))
            )
            tweets = self.scroll_and_collect_tweets(max_tweets)
            return tweets
        except TimeoutException:
            print("❌ Arama sonuçları yüklenemedi")
            return []
        except Exception as e:
            print(f"❌ Arama hatası: {str(e)}")
            return []
    
    def save_to_text_file(self, tweets_data, filename, format_type='simple'):
        try:
            os.makedirs(os.path.dirname(filename) if os.path.dirname(filename) else '.', exist_ok=True)
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(f"# X (Twitter) Tweet'leri\n")
                f.write(f"# Oluşturma tarihi: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"# Toplam tweet sayısı: {len(tweets_data)}\n\n")
                if format_type == 'simple':
                    for i, tweet in enumerate(tweets_data, 1):
                        f.write(f"Tweet {i}:\n")
                        f.write(f"{tweet['text']}\n")
                        f.write("-" * 50 + "\n\n")
                elif format_type == 'detailed':
                    for i, tweet in enumerate(tweets_data, 1):
                        f.write(f"=== Tweet {i} ===\n")
                        f.write(f"ID: {tweet['id']}\n")
                        f.write(f"Tarih: {tweet['created_at']}\n")
                        f.write(f"URL: {tweet['url']}\n")
                        f.write(f"Beğeni: {tweet['like_count']} | Retweet: {tweet['retweet_count']} | Yanıt: {tweet['reply_count']}\n")
                        f.write(f"\nMetin:\n{tweet['text']}\n")
                        f.write("=" * 80 + "\n\n")
            print(f"✅ {len(tweets_data)} tweet {filename} dosyasına kaydedildi")
        except Exception as e:
            print(f"❌ Dosya kaydetme hatası: {str(e)}")
    
    def close(self):
        if hasattr(self, 'driver'):
            self.driver.quit()
            print("🔌 WebDriver kapatıldı")

def main():
    print("🐦 X (Twitter) Tweet Çekici (Selenium)")
    print("=" * 50)
    scraper = None
    try:
        scraper = TwitterScraperSelenium(headless=True)
        print("1. Kullanıcı tweet'lerini çek")
        print("2. Anahtar kelime ile ara")
        choice = input("\nSeçiminizi yapın (1 veya 2): ")
        if choice == "1":
            username = input("X kullanıcı adını girin (@ olmadan): ")
            max_tweets = int(input("Maksimum tweet sayısı (varsayılan 50): ") or 50)
            tweets = scraper.get_user_tweets(username, max_tweets)
            file_prefix = f"tweets_{username}"
        elif choice == "2":
            query = input("Arama terimi girin: ")
            max_tweets = int(input("Maksimum tweet sayısı (varsayılan 50): ") or 50)
            tweets = scraper.search_tweets(query, max_tweets)
            safe_query = "".join(c for c in query if c.isalnum() or c in (' ', '-', '_')).rstrip()
            file_prefix = f"search_{safe_query.replace(' ', '_')}"
        else:
            print("❌ Geçersiz seçim!")
            return
        if tweets:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            os.makedirs("twitter_data", exist_ok=True)
            simple_file = f"twitter_data/{file_prefix}_{timestamp}_simple.txt"
            detailed_file = f"twitter_data/{file_prefix}_{timestamp}_detailed.txt"
            json_file = f"twitter_data/{file_prefix}_{timestamp}.json"
            scraper.save_to_text_file(tweets, simple_file, 'simple')
            scraper.save_to_text_file(tweets, detailed_file, 'detailed')
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump(tweets, f, indent=2, ensure_ascii=False)
            print(f"\n✅ İşlem tamamlandı!")
            print(f"📁 {len(tweets)} tweet kaydedildi:")
            print(f"   - {simple_file}")
            print(f"   - {detailed_file}")
            print(f"   - {json_file}")
        else:
            print("❌ Hiç tweet bulunamadı")
    except KeyboardInterrupt:
        print("\n⏹️  İşlem kullanıcı tarafından durduruldu")
    except Exception as e:
        print(f"❌ Genel hata: {str(e)}")
    finally:
        if scraper:
            scraper.close()

if __name__ == "__main__":
    main()
