#!/usr/bin/env python3
"""
Test the enhanced content extraction similar to what the API does
"""

import requests
from bs4 import BeautifulSoup

def test_enhanced_extraction():
    url = "https://www.cnn.com/us/live-news/nyc-manhattan-shooting-shane-tamura-07-29-25"
    
    try:
        print(f"Testing enhanced extraction for: {url}")
        
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Remove unwanted elements
        for element in soup(['script', 'style', 'nav', 'footer', 'header', 'aside', 'noscript', 'iframe']):
            element.decompose()
        
        # Extract main content with multiple strategies
        content_text = ""
        
        # Strategy 1: Look for main content areas
        main_content = (
            soup.find('main') or 
            soup.find('article') or 
            soup.find('div', class_=lambda x: x and ('content' in x or 'article' in x or 'post' in x))
        )
        
        if main_content:
            content_text = main_content.get_text(separator=' ', strip=True)
            print(f"✅ Found main content section: {len(content_text)} chars")
        
        # Strategy 2: If content is too short, look for specific news content patterns
        if len(content_text) < 1500:
            print("🔍 Content too short, looking for additional elements...")
            # Look for paragraphs, list items, and divs that might contain news content
            content_elements = soup.find_all(['p', 'li', 'div'], text=True)
            additional_content = []
            
            for elem in content_elements:
                text = elem.get_text(strip=True)
                # Skip very short text or common navigation elements
                if (len(text) > 50 and 
                    not any(skip in text.lower() for skip in ['cookie', 'subscribe', 'sign in', 'menu', 'navigation', 'advertisement'])):
                    additional_content.append(text)
            
            if additional_content:
                content_text += " " + " ".join(additional_content[:10])  # Take first 10 relevant elements
                print(f"✅ Added additional content elements: {len(additional_content)} found")
        
        # Strategy 3: If still too short, get all text but filter more carefully
        if len(content_text) < 1000:
            print("🔍 Still too short, using filtered sentences...")
            all_text = soup.get_text(separator=' ', strip=True)
            # Split into sentences and filter
            sentences = [s.strip() for s in all_text.split('.') if len(s.strip()) > 30]
            relevant_sentences = [s for s in sentences[:20] if not any(skip in s.lower() for skip in 
                                ['cookie', 'subscribe', 'sign in', 'menu', 'follow us', 'advertisement', 'newsletter'])]
            content_text = '. '.join(relevant_sentences[:15]) + '.'
            print(f"✅ Using filtered sentences approach: {len(relevant_sentences)} sentences")
        
        # Clean and limit content
        content_text = ' '.join(content_text.split())  # Remove extra whitespace
        content_text = content_text[:5000]  # Increased limit for better content
        
        print(f"📊 Final content length: {len(content_text)} characters")
        print(f"📄 First 800 characters:")
        print("-" * 80)
        print(content_text[:800])
        print("-" * 80)
        
        # Check for relevant keywords
        relevant_keywords = ['shooting', 'manhattan', 'tamura', 'nypd', 'victims', 'police', 'killed']
        found_keywords = [kw for kw in relevant_keywords if kw.lower() in content_text.lower()]
        print(f"🎯 Found relevant keywords: {found_keywords}")
        
        if len(content_text) > 1500 and len(found_keywords) >= 3:
            print("🎉 SUCCESS: Enhanced extraction is working!")
            return content_text
        else:
            print(f"⚠️  PARTIAL SUCCESS: Content length={len(content_text)}, keywords={len(found_keywords)}")
            return content_text
            
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return None

if __name__ == "__main__":
    result = test_enhanced_extraction()
    if result:
        print(f"\n🎤 Would generate podcast with {len(result)} characters of content")
    else:
        print("\n❌ Would fall back to generic content") 