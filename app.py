from flask import Flask, request, jsonify, send_from_directory
from bs4 import BeautifulSoup
import requests
from urllib.parse import urlparse
import re

app = Flask(__name__)

@app.route('/')
def serve_index():
    return send_from_directory('.', 'index.html')

@app.route('/extract', methods=['POST'])
def extract_content():
    try:
        data = request.get_json()
        
        if not data or 'url' not in data or 'tags' not in data:
            return jsonify({'error': 'Missing required parameters: url and tags'}), 400
            
        url = data['url'].strip()
        tags = data['tags']
        
        # Validate URL format
        try:
            result = urlparse(url)
            if not all([result.scheme, result.netloc]):
                return jsonify({'error': 'Invalid URL format'}), 400
        except:
            return jsonify({'error': 'Invalid URL format'}), 400
        
        # Validate tags
        if not tags or not isinstance(tags, list) or len(tags) == 0:
            return jsonify({'error': 'No tags specified'}), 400
            
        # Clean tags - remove empty strings and duplicates
        clean_tags = []
        for tag in tags:
            cleaned = tag.strip()
            if cleaned and re.match(r'^[a-zA-Z0-9\s\.,#-_]+$', cleaned):
                clean_tags.append(cleaned)
        
        if not clean_tags:
            return jsonify({'error': 'No valid tags provided'}), 400
            
        # Fetch the webpage content
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            return jsonify({'error': f'Failed to fetch URL: {str(e)}'}), 400
        
        # Parse with BeautifulSoup
        soup = BeautifulSoup(response.text, 'html.parser')
        
        results = []
        for tag in clean_tags:
            try:
                # Handle both simple tags and CSS selectors
                if re.match(r'^[a-zA-Z0-9]+$', tag):  # Simple tag name
                    elements = soup.find_all(tag)
                else:  # CSS selector
                    elements = soup.select(tag)
                
                for element in elements:
                    results.append({
                        'tag': tag,
                        'content': str(element)
                    })
            except Exception as e:
                # Skip invalid selectors but continue processing others
                continue
        
        return jsonify({
            'results': results,
            'count': len(results)
        })
    
    except Exception as e:
        return jsonify({'error': f'Server error: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)