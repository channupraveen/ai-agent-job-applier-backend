#!/usr/bin/env python3
"""
Quick test of Indeed RSS - Run this to verify it works
"""

import requests
import feedparser
import sys
sys.path.append('C:/Users/pk055/Desktop/ai-agent-job-applier/src')

def test_indeed_rss():
    """Test Indeed RSS directly"""
    rss_url = "https://in.indeed.com/rss?q=python+developer&l=Delhi&radius=25&limit=10"
    
    print(f"🔍 Testing Indeed RSS: {rss_url}")
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(rss_url, headers=headers, timeout=30)
        print(f"📡 Response status: {response.status_code}")
        
        if response.status_code == 200:
            feed = feedparser.parse(response.text)
            print(f"✅ Found {len(feed.entries)} job entries")
            
            for i, entry in enumerate(feed.entries[:3], 1):
                title = entry.get('title', 'No title')
                link = entry.get('link', 'No link')
                print(f"   {i}. {title}")
                print(f"      URL: {link[:60]}...")
                
            return True
        else:
            print(f"❌ Failed with status {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    test_indeed_rss()
