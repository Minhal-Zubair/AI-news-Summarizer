from flask import Flask, request, render_template, flash, redirect, url_for
import nltk
from textblob import TextBlob
from newspaper import Article
from urllib.parse import urlparse
import validators
import requests

try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Set your secret key here

def get_website_name(url):
    # Extract the website name from the URL
    parsed_url = urlparse(url)
    domain = parsed_url.netloc
    if domain.startswith("www."):
        domain = domain[4:]
    return domain

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        url = request.form.get('url', '').strip()
        summary_length = request.form.get('summary_length', 'medium')

        if not validators.url(url):
            flash('Please enter a valid URL.')
            return redirect(url_for('index'))

        try:
            response = requests.get(url)
            response.raise_for_status()
        except requests.RequestException:
            flash('Failed to download the content of the URL.')
            return redirect(url_for('index'))

        article = Article(url)
        article.download()
        article.parse()

        title = article.title or "No Title Found"
        authors = ', '.join(article.authors) if article.authors else get_website_name(url)
        publish_date = article.publish_date.strftime('%B %d, %Y') if article.publish_date else "N/A"

        # Determine max sentences based on summary length
        if summary_length == 'short':
            max_summarized_sentences = 3
        elif summary_length == 'medium':
            max_summarized_sentences = 5
        else:  # detailed
            max_summarized_sentences = 10

        sentences = [s.strip() for s in article.text.split('.') if s.strip()]
        summary_sentences = sentences[:max_summarized_sentences]
        summary = '. '.join(summary_sentences)
        if summary and not summary.endswith('.'):
            summary += '.'

        if not summary:
            flash('Could not generate a summary. Please try a different URL.')
            return redirect(url_for('index'))

        analysis = TextBlob(article.text)
        polarity = analysis.sentiment.polarity

        if polarity > 0:
           sentiment = 'positive 🙂'
        elif polarity < 0:
           sentiment = 'negative 😟'
        else:
           sentiment = 'neutral 😐'

        top_image = article.top_image or url_for('static', filename='default-image.png')

        return render_template('index.html',
                               title=title,
                               authors=authors,
                               publish_date=publish_date,
                               summary=summary,
                               top_image=top_image,
                               sentiment=sentiment)

    return render_template('index.html')


if __name__ == '__main__':
    app.run(debug=True)
