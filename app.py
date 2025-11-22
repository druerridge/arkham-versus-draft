from flask import Flask, render_template, request, redirect, url_for
import requests
import json
import os
from datetime import datetime, timedelta

app = Flask(__name__)

# Cache configuration
CACHE_FILE = 'arkham_packs_cache.json'
CACHE_DURATION_HOURS = 24  # Cache for 24 hours
API_URL = 'https://arkhamdb.com/api/public/packs/'

def is_cache_valid():
    """Check if the cache file exists and is still valid."""
    if not os.path.exists(CACHE_FILE):
        return False
    
    # Check if cache is older than CACHE_DURATION_HOURS
    cache_time = datetime.fromtimestamp(os.path.getmtime(CACHE_FILE))
    expiry_time = cache_time + timedelta(hours=CACHE_DURATION_HOURS)
    return datetime.now() < expiry_time

def fetch_and_cache_packs():
    """Fetch packs from API and cache them locally."""
    try:
        print(f"Fetching packs from {API_URL}")
        response = requests.get(API_URL, timeout=10)
        response.raise_for_status()
        
        packs_data = response.json()
        
        # Cache the data
        with open(CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(packs_data, f, indent=2, ensure_ascii=False)
        
        print(f"Successfully cached {len(packs_data)} packs")
        return packs_data
    
    except requests.RequestException as e:
        print(f"Error fetching packs from API: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON response: {e}")
        return None

def load_cached_packs():
    """Load packs from cache file."""
    try:
        with open(CACHE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading cache: {e}")
        return None

def get_arkham_sets():
    """Get Arkham Horror sets, either from cache or API."""
    # Check if we have a valid cache
    if is_cache_valid():
        print("Using cached packs data")
        packs_data = load_cached_packs()
        if packs_data:
            return [pack['name'] for pack in packs_data]
    
    # Cache is invalid or doesn't exist, fetch from API
    packs_data = fetch_and_cache_packs()
    if packs_data:
        return [pack['name'] for pack in packs_data]
    
    # If API fails, try to use stale cache
    print("API failed, attempting to use stale cache")
    packs_data = load_cached_packs()
    if packs_data:
        return [pack['name'] for pack in packs_data]
    
    # Fallback to hardcoded list if everything fails
    print("All methods failed, using fallback hardcoded list")
    return [
        "Core Set",
        "The Dunwich Legacy",
        "The Path to Carcosa", 
        "The Forgotten Age",
        "The Circle Undone",
        "The Dream-Eaters",
        "The Innsmouth Conspiracy",
        "Edge of the Earth",
        "The Scarlet Keys",
        "The Feast of Hemlock Vale"
    ]

@app.route('/')
def index():
    arkham_sets = get_arkham_sets()
    return render_template('index.html', sets=arkham_sets)

@app.route('/draft', methods=['POST'])
def draft():
    selected_sets = request.form.getlist('sets')
    # For now, just redirect back with a simple response
    # In a real implementation, you'd handle the draft logic here
    return render_template('draft_result.html', selected_sets=selected_sets)

@app.route('/refresh-cache')
def refresh_cache():
    """Manually refresh the packs cache."""
    # Remove existing cache file if it exists
    if os.path.exists(CACHE_FILE):
        os.remove(CACHE_FILE)
    
    # Fetch fresh data
    packs_data = fetch_and_cache_packs()
    if packs_data:
        return f"Cache refreshed successfully! Found {len(packs_data)} packs.", 200
    else:
        return "Failed to refresh cache. Check console for errors.", 500

if __name__ == '__main__':
    app.run(debug=True)