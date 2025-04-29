from flask import Flask, request, jsonify, render_template
from bs4 import BeautifulSoup
import requests
import google.generativeai as genai
from groq import Groq
import os
from dotenv import load_dotenv
import re
import urllib.parse
import json
import time

load_dotenv('.env.local')

app = Flask(__name__)

# Configure APIs
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
groq_client = Groq(api_key=os.getenv('GROQ_API_KEY'))

# Token limits
GROQ_TOKEN_LIMIT = 4000  # Set below the 5000 limit to be safe

@app.route('/')
def home():
    return render_template('index.html')

def scrape_webpage(url):
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()  # Raise exception for 4XX/5XX responses
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract domain name for source attribution
        domain = urllib.parse.urlparse(url).netloc
        # Convert www.example.com to "Example" with proper capitalization
        site_name = ' '.join(word.capitalize() for word in domain.split('.')[-2].split('-'))
        
        # Enhanced scraping to preserve more structure
        content = {
            'title': soup.title.string if soup.title else '',
            'headings': [{'level': h.name, 'text': h.text.strip()} for h in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']) if h.text.strip()],
            'paragraphs': [p.text.strip() for p in soup.find_all('p') if p.text.strip()],
            'lists': [{'type': ul.name, 'items': [li.text.strip() for li in ul.find_all('li') if li.text.strip()]} for ul in soup.find_all(['ul', 'ol'])],
            'url': url,
            'domain': domain,
            'site_name': site_name
        }
        
        return content
    except Exception as e:
        return {'error': f"Failed to scrape webpage: {str(e)}"}

# Custom search implementation instead of using the GoogleSearch class
def search_for_urls(query, num_results=3):
    try:
        # Encode the query for URL
        encoded_query = urllib.parse.quote_plus(query)
        
        # Use a direct request to search engine
        search_url = f"https://www.google.com/search?q={encoded_query}"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Referer': 'https://www.google.com/'
        }
        
        response = requests.get(search_url, headers=headers, timeout=10)
        response.raise_for_status()
        
        # Parse the HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # More robust URL extraction
        results = []
        
        # Method 1: Extract from '/url?' links (typical Google format)
        for link in soup.select('a[href^="/url?"]'):
            href = link.get('href')
            if href.startswith('/url?'):
                # Extract actual URL from Google redirect
                url_param = href.split('?')[1].split('&')
                for param in url_param:
                    if param.startswith('q='):
                        url = urllib.parse.unquote(param[2:])
                        # Skip Google-specific and common unwanted domains
                        if not any(domain in url for domain in [
                            'google.com', 'youtube.com', 'googleusercontent.com', 
                            'accounts.google', 'support.google'
                        ]):
                            if url not in results:  # Avoid duplicates
                                results.append(url)
                                if len(results) >= num_results:
                                    return results
        
        # Method 2: Try to find links in search results with specific patterns
        for div in soup.select('div.g, div.yuRUbf, div[data-hveid]'):
            links = div.select('a[href^="http"]')
            for link in links:
                url = link.get('href')
                if url and not any(domain in url for domain in [
                    'google.com', 'youtube.com', 'googleusercontent.com', 
                    'accounts.google', 'support.google'
                ]):
                    if url not in results:  # Avoid duplicates
                        results.append(url)
                        if len(results) >= num_results:
                            return results
        
        # Method 3: Last resort - get all external links
        if not results:
            for link in soup.find_all('a'):
                href = link.get('href')
                if href and href.startswith('http') and not any(domain in href for domain in [
                    'google.com', 'youtube.com', 'googleusercontent.com', 
                    'accounts.google', 'support.google'
                ]):
                    if href not in results:  # Avoid duplicates
                        results.append(href)
                        if len(results) >= num_results:
                            return results
        
        # If we got any results at all, return them even if fewer than requested
        if results:
            return results
            
        # Try a different search engine as fallback
        return search_with_fallback_engine(query, num_results)
    
    except Exception as e:
        print(f"Search error: {str(e)}")
        return search_with_fallback_engine(query, num_results)

def search_with_fallback_engine(query, num_results=3):
    """Try alternative search engines when Google fails"""
    try:
        # Try Bing as fallback
        encoded_query = urllib.parse.quote_plus(query)
        search_url = f"https://www.bing.com/search?q={encoded_query}"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        }
        
        response = requests.get(search_url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        results = []
        for link in soup.select('a[href^="http"]'):
            url = link.get('href')
            if url and not any(domain in url for domain in ['bing.com', 'microsoft.com', 'msn.com']):
                if url not in results:
                    results.append(url)
                    if len(results) >= num_results:
                        return results
                        
        if results:
            return results
            
        # If all fails, return diverse fallbacks (not just Wikipedia)
        fallbacks = [
            f"https://en.wikipedia.org/wiki/{query.replace(' ', '_')}",
            f"https://www.britannica.com/search?query={query.replace(' ', '+')}",
            f"https://duckduckgo.com/?q={query.replace(' ', '+')}"
        ]
        return fallbacks[:num_results]
        
    except Exception as e:
        print(f"Fallback search error: {str(e)}")
        # Ultimate fallback with diverse sources
        return [
            f"https://en.wikipedia.org/wiki/{query.replace(' ', '_')}",
            f"https://www.britannica.com/search?query={query.replace(' ', '+')}"
        ]

def search_for_topic(topic):
    try:
        search_results = search_for_urls(topic, num_results=3)
        
        if not search_results:
            return {'error': 'No results found for this topic'}
        
        # Try first URL, then fall back to others if needed    
        for url in search_results:
            content = scrape_webpage(url)
            if 'error' not in content:
                return content
                
        # If all URLs failed, return last error
        return {'error': 'Failed to scrape any of the search results'}
    except Exception as e:
        return {'error': f"Search error: {str(e)}"}

def estimate_token_count(text):
    # Very rough estimation: 1 token ≈ 4 characters for English text
    return len(text) // 4

def truncate_text_to_token_limit(text, token_limit):
    # Rough truncation based on estimated token count
    estimated_tokens = estimate_token_count(text)
    
    if estimated_tokens <= token_limit:
        return text
    
    # Calculate rough character limit
    char_limit = token_limit * 4
    
    # Try to truncate at paragraph boundaries
    paragraphs = text.split('\n\n')
    result = ""
    
    for para in paragraphs:
        if estimate_token_count(result + para + "\n\n") > token_limit:
            break
        result += para + "\n\n"
    
    # Add indication that content was truncated
    if result != text:
        result += "\n\n[Content truncated due to token limits...]"
    
    return result

def process_with_llm(content, model_choice):
    # Create a structured text that preserves the headings hierarchy
    site_attribution = ""
    if 'site_name' in content and 'domain' in content:
        site_attribution = f"Source: {content['site_name']} ({content['domain']})"
    
    combined_text = f"Title: {content['title']}\n\n"
    
    # Add the source attribution prominently
    if site_attribution:
        combined_text += f"{site_attribution}\n\n"
    
    # Add the URL for reference
    if 'url' in content:
        combined_text += f"Source URL: {content['url']}\n\n"
    
    # Rest of the function remains the same...
    
    prompt = (
        f"Create a concise summary of this content and format it using proper markdown "
        f"with headings, subheadings, bold text for important points, and bullet points where appropriate. "
        f"Start the summary with '# Summary from {content.get('site_name', 'Web Source')}' as the main heading. "
        f"Focus on the main topics and key points, keeping your response brief and well-structured: \n\n{combined_text}"
    )
    
    # Continue with the rest of the function...
    
    # Truncate prompt if needed
    if model_choice == 'groq':
        prompt = truncate_text_to_token_limit(prompt, GROQ_TOKEN_LIMIT)
    
    if model_choice == 'gemini':
        try:
            # Try using the new model name format (as of March 2025)
            model = genai.GenerativeModel('gemini-1.5-pro')
            response = model.generate_content(prompt)
            return response.text
        except Exception as e1:
            try:
                # Fallback to newer model if available
                model = genai.GenerativeModel('gemini-1.0-pro')
                response = model.generate_content(prompt)
                return response.text
            except Exception as e2:
                # If all else fails, try listing available models
                try:
                    available_models = [m.name for m in genai.list_models()]
                    gemini_models = [m for m in available_models if 'gemini' in m.lower()]
                    
                    if gemini_models:
                        # Use the first available Gemini model
                        model = genai.GenerativeModel(gemini_models[0])
                        response = model.generate_content(prompt)
                        return response.text
                    else:
                        # Fall back to Groq if no Gemini models are available
                        return f"Error with Gemini: No available Gemini models found. Falling back to Groq.\n\n{process_with_groq(prompt)}"
                except Exception as e3:
                    # Ultimate fallback to Groq
                    return f"Error with Gemini: {str(e1)}\n\nFalling back to Groq.\n\n{process_with_groq(prompt)}"
    else:  # groq
        return process_with_groq(prompt)

def process_with_groq(prompt):
    try:
        # Ensure the prompt is within token limits
        prompt = truncate_text_to_token_limit(prompt, GROQ_TOKEN_LIMIT)
        
        completion = groq_client.chat.completions.create(
            model="mixtral-8x7b-32768",
            messages=[{
                "role": "user",
                "content": prompt
            }]
        )
        return completion.choices[0].message.content
    except Exception as e:
        return f"Error with Groq: {str(e)}"

@app.route('/scrape', methods=['POST'])
def scrape():
    data = request.json
    url = data.get('url')
    topic = data.get('topic')
    model_choice = data.get('model', 'gemini')
    
    if url:
        content = scrape_webpage(url)
    elif topic:
        content = search_for_topic(topic)
    else:
        return jsonify({'error': 'Please provide either a URL or a topic'})
        
    if 'error' in content:
        return jsonify(content)
        
    summary = process_with_llm(content, model_choice)
    return jsonify({
        'raw_content': content,
        'summary': summary,
        'model_used': model_choice
    })

@app.route('/search', methods=['POST'])
def search_route():
    data = request.json
    query = data.get('query')
    model_choice = data.get('model', 'gemini')
    
    if not query:
        return jsonify({'error': 'Please provide a search query'})
    
    try:
        # Get search results using our custom function
        search_results = search_for_urls(query, num_results=3)
        
        if not search_results:
            # Fallback for testing - create a Wikipedia URL from the search query
            fallback_url = "https://en.wikipedia.org/wiki/" + query.replace(" ", "_")
            search_results = [fallback_url]
            
        # Try to scrape the first result, then fall back to others if needed
        content = None
        last_error = None
        
        for url in search_results:
            print(f"Attempting to scrape: {url}")  # Debug logging
            scraped_content = scrape_webpage(url)
            if 'error' not in scraped_content:
                content = scraped_content
                break
            else:
                last_error = scraped_content['error']
                print(f"Scraping error: {last_error}")  # Debug logging
        
        if not content:
            # Ultimate fallback - create a minimal content structure with search info
            content = {
                'title': f"Search results for: {query}",
                'headings': [{'level': 'h1', 'text': f"Search Query: {query}"}],
                'paragraphs': [f"The search for '{query}' was performed but content could not be retrieved. Please try another query or directly enter a URL."],
                'lists': [],
                'url': "N/A - Search fallback"
            }
            
            summary = (
                f"# Search Results for: {query}\n\n"
                f"Unfortunately, we couldn't retrieve detailed content for this search query. "
                f"This could be due to:\n\n"
                f"- Limited access to search results\n"
                f"- Website access restrictions\n"
                f"- Complex webpage structures\n\n"
                f"**Last error:** {last_error}\n\n"
                f"Please try:\n"
                f"- A more specific search query\n"
                f"- Directly entering a URL to scrape\n"
                f"- A different topic"
            )
            
            return jsonify({
                'raw_content': content,
                'summary': summary,
                'model_used': model_choice
            })
        
        # Process the content with the selected LLM
        summary = process_with_llm(content, model_choice)
        
        return jsonify({
            'raw_content': content,
            'summary': summary,
            'model_used': model_choice
        })
        
    except Exception as e:
        # Comprehensive error handling with detailed information
        error_message = str(e)
        print(f"Search route error: {error_message}")  # Debug logging
        
        fallback_summary = (
            f"# Search Error\n\n"
            f"There was an error processing your search for '{query}'.\n\n"
            f"**Error details:** {error_message}\n\n"
            f"Please try:\n"
            f"- A different search query\n"
            f"- Using the URL scraping feature directly\n"
            f"- Checking your network connection"
        )
        
        return jsonify({
            'raw_content': {'title': 'Search Error', 'error': error_message},
            'summary': fallback_summary,
            'model_used': model_choice
        })

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    question = data.get('question')
    context = data.get('context')
    model_choice = data.get('model', 'gemini')
    
    # Use a more concise prompt to reduce token count
    prompt = f"Context: {context}\n\nQuestion: {question}\n\nProvide a concise answer focusing only on relevant information."
    
    # Truncate for Groq if needed
    if model_choice == 'groq':
        prompt = truncate_text_to_token_limit(prompt, GROQ_TOKEN_LIMIT)
    
    if model_choice == 'gemini':
        try:
            # Try using the new model name format
            model = genai.GenerativeModel('gemini-1.5-pro')
            response = model.generate_content(prompt)
            answer = response.text
        except Exception:
            try:
                # Fallback to alternate model
                model = genai.GenerativeModel('gemini-1.0-pro')
                response = model.generate_content(prompt)
                answer = response.text
            except Exception as e:
                # If Gemini fails, use Groq as fallback with truncated prompt
                truncated_prompt = truncate_text_to_token_limit(prompt, GROQ_TOKEN_LIMIT)
                completion = groq_client.chat.completions.create(
                    model="mixtral-8x7b-32768",
                    messages=[{"role": "user", "content": truncated_prompt}]
                )
                answer = f"(Gemini failed, using Groq as fallback) {completion.choices[0].message.content}"
    else:
        # Ensure the prompt is within token limits for Groq
        truncated_prompt = truncate_text_to_token_limit(prompt, GROQ_TOKEN_LIMIT)
        completion = groq_client.chat.completions.create(
            model="mixtral-8x7b-32768",
            messages=[{"role": "user", "content": truncated_prompt}]
        )
        answer = completion.choices[0].message.content
    
    return jsonify({
        'answer': answer,
        'model_used': model_choice
    })

@app.route('/check-models')
def check_models():
    try:
        models = genai.list_models()
        return jsonify({
            'available_models': [m.name for m in models],
            'gemini_models': [m.name for m in models if 'gemini' in m.name.lower()]
        })
    except Exception as e:
        return jsonify({'error': str(e)})

if __name__ == '__main__':
    app.run(debug=True)