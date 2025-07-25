import requests
from bs4 import BeautifulSoup

def scrape_meditations():
    url = "https://www.gutenberg.org/files/2680/2680-h/2680-h.htm"  # more stable version
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")

    content = soup.get_text(separator="\n")
    with open("meditations.txt", "w", encoding="utf-8") as f:
        f.write(content)
    print("Saved meditations.txt")

def scrape_daily_stoic_articles():
    base_url = "https://modernstoicism.com/articles/"
    response = requests.get(base_url)
    soup = BeautifulSoup(response.text, "html.parser")

    article_links = [
        a['href'] for a in soup.find_all('a', href=True)
        if "/articles/" in a['href']
    ][:7]


    articles = []
    for link in article_links:
        try:
            page = requests.get(link)
            page_soup = BeautifulSoup(page.text, "html.parser")
            text = page_soup.get_text(separator="\n")
            articles.append(text)
        except Exception as e:
            print(f"Failed to scrape {link}: {e}")

    with open("daily_stoic_articles.txt", "w", encoding="utf-8") as f:
        for article in articles:
            f.write(article + "\n\n")
   

if __name__ == "__main__":

    scrape_meditations()
    scrape_daily_stoic_articles()
    
