import os
import pandas as pd
from nltk import sent_tokenize, word_tokenize
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer
from textblob import TextBlob
import requests
from urllib.parse import urlparse
from bs4 import BeautifulSoup

import nltk
nltk.download('punkt')
nltk.download('stopwords')

def download_text_from_url(url, output_folder, url_id):
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')

        # Extract the article title
        title = soup.title.string.strip()

        # Extract paragraphs that likely contain the article text
        paragraphs = soup.find_all('p')

        # Extract text content from paragraphs
        body_paragraphs = [paragraph.get_text() for paragraph in paragraphs]

        # Combine the title and body paragraphs into a single paragraph
        article_text = f"{title}\n\n{' '.join(body_paragraphs)}"

        # Extract filename from the URL
        filename = os.path.join(output_folder, f"{url_id}.txt")

        # Save the text content to a separate file
        with open(filename, 'w', encoding='utf-8') as file:
            file.write(article_text)

        return filename
    except Exception as e:
        print(f"Failed to download content from {url}: {str(e)}")
        return None

def calculate_text_metrics(words, sentences):
    avg_sentence_length = sum(len(sent.split()) for sent in sentences) / len(sentences) if len(sentences) > 0 else 0

    stop_words = set(stopwords.words('english'))
    words = [word.lower() for word in words if word.isalpha() and word.lower() not in stop_words]

    ps = PorterStemmer()
    complex_words = [ps.stem(word) for word in words]
    percentage_complex_words = (len(complex_words) / len(words)) * 100 if len(words) > 0 else 0

    fog_index = 0.4 * (avg_sentence_length + percentage_complex_words)

    avg_words_per_sentence = len(words) / len(sentences) if len(sentences) > 0 else 0

    syllable_count = sum([syllable_count_word(word) for word in words])
    syllable_per_word = syllable_count / len(words) if len(words) > 0 else 0

    personal_pronouns = sum(1 for word in words if word.lower() in ['i', 'me', 'my', 'mine', 'myself'])

    avg_word_length = sum(len(word) for word in words) / len(words) if len(words) > 0 else 0

    return avg_sentence_length, percentage_complex_words, fog_index, avg_words_per_sentence, syllable_per_word, personal_pronouns, avg_word_length

def syllable_count_word(word):
    word = word.lower()
    vowels = 'aeiouy'
    count = sum(1 for i in range(1, len(word)) if word[i] in vowels and word[i - 1] not in vowels) + (1 if word[0] in vowels else 0)
    count -= 1 if word.endswith('e') else 0
    return max(1, count)

def extract_and_analyze_text(url, file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            article_text = file.read()
            sentences = sent_tokenize(article_text)
            words = word_tokenize(article_text)

        # Perform sentiment analysis using TextBlob
        blob = TextBlob(article_text)
        polarity_score = blob.sentiment.polarity
        subjectivity_score = blob.sentiment.subjectivity

        # Calculate other text metrics
        avg_sentence_length, percentage_complex_words, fog_index, avg_words_per_sentence, syllable_per_word, personal_pronouns, avg_word_length = calculate_text_metrics(words, sentences)

        # Extract filename from the path
        filename = os.path.basename(file_path)

        result_dict = {
            'URL_ID': filename,
            'URL': url,
            'POSITIVE SCORE': max(0, polarity_score),
            'NEGATIVE SCORE': max(0, -polarity_score),
            'POLARITY SCORE': polarity_score,
            'SUBJECTIVITY SCORE': subjectivity_score,
            'AVG SENTENCE LENGTH': avg_sentence_length,
            'PERCENTAGE OF COMPLEX WORDS': percentage_complex_words,
            'FOG INDEX': fog_index,
            'AVG NUMBER OF WORDS PER SENTENCE': avg_words_per_sentence,
            'COMPLEX WORD COUNT': int(percentage_complex_words * len(words) / 100),
            'WORD COUNT': len(words),
            'SYLLABLE PER WORD': syllable_per_word,
            'PERSONAL PRONOUNS': personal_pronouns,
            'AVG WORD LENGTH': avg_word_length
        }

        return result_dict

    except Exception as e:
        print(f"Analysis failed for {file_path}: {str(e)}")
        return None

def analyze_all_text_files(input_df, output_folder):
    results = []

    for index, row in input_df.iterrows():
        url = row['URL']
        url_id = row['URL_ID']
        file_path = download_text_from_url(url, output_folder, url_id)
        
        if file_path is not None:
            result = extract_and_analyze_text(url, file_path)
            if result is not None:
                results.append(result)

    return results

def main():
    input_file = "Input.xlsx"
    output_folder = "Extracted_text"

    # Ensure the output folder exists or create it
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    input_df = pd.read_excel(input_file)
    results = analyze_all_text_files(input_df, output_folder)

    df_results = pd.DataFrame(results)

    output_csv = "output_analysis.csv"
    df_results.to_csv(output_csv, index=False)

if __name__ == "__main__":
    main()