#!/usr/bin/env python3
"""
Test script to verify CNN URL content extraction
"""

import requests
from bs4 import BeautifulSoup

def test_cnn_extraction():
    url = "https://www.cnn.com/us/live-news/nyc-manhattan-shooting-shane-tamura-07-29-25"
    
    try:
        print(f"Testing URL: {url}")
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        print(f"✅ Successfully fetched page (status: {response.status_code})")
        print(f"✅ Content length: {len(response.text)} characters")
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Remove unwanted elements
        for element in soup(['script', 'style', 'nav', 'footer', 'header', 'aside', 'noscript', 'iframe']):
            element.decompose()
        
        # Try to find main content
        main_content = (
            soup.find('main') or 
            soup.find('article') or 
            soup.find('div', class_=lambda x: x and ('content' in x or 'article' in x or 'post' in x)) or
            soup.find('div', {'id': lambda x: x and 'content' in x})
        )
        
        if main_content:
            content_text = main_content.get_text(separator=' ', strip=True)
            print(f"✅ Found main content section")
        else:
            content_text = soup.get_text(separator=' ', strip=True)
            print(f"⚠️  Using full page content (no main section found)")
        
        # Clean content
        content_text = ' '.join(content_text.split())
        
        print(f"✅ Extracted text length: {len(content_text)} characters")
        print(f"✅ First 500 characters:")
        print("-" * 50)
        print(content_text[:500])
        print("-" * 50)
        
        # Check if it contains relevant content
        relevant_keywords = ['shooting', 'manhattan', 'tamura', 'nypd', 'victims']
        found_keywords = [kw for kw in relevant_keywords if kw.lower() in content_text.lower()]
        
        print(f"✅ Found relevant keywords: {found_keywords}")
        
        if len(content_text) > 1000 and found_keywords:
            print("🎉 SUCCESS: Content extraction is working properly!")
            return True
        else:
            print("❌ ISSUE: Content seems incomplete or irrelevant")
            return False
            
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return False

if __name__ == "__main__":
    test_cnn_extraction() 