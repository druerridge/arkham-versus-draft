from flask import Flask, render_template, request, redirect, url_for
import requests
import json
import os
from datetime import datetime, timedelta

app = Flask(__name__)

# Cache configuration
PACKS_CACHE_FILE = 'arkham_packs_cache.json'
CARDS_CACHE_FILE = 'arkham_cards_cache.json'
CACHE_DURATION_HOURS = 24  # Cache for 24 hours
PACKS_API_URL = 'https://arkhamdb.com/api/public/packs/'
CARDS_API_URL = 'https://arkhamdb.com/api/public/cards/'
ARKHAMDB_BASE_URL = 'https://arkhamdb.com'

# Faction to Magic color mapping
FACTION_COLOR_MAP = {
    'guardian': ['W'], 
    'seeker': ['U'],   
    'rogue': ['B'],    
    'mystic': ['R'],   
    'survivor': ['G'], 
    'neutral': [],     
}

# Type code to Magic type mapping
TYPE_CODE_MAP = {
    'investigator': 'Creature',
    'asset': 'Artifact',
    'event': 'Instant',
    'skill': 'Sorcery', 
    'treachery': 'Enchantment',
}

def format_image_url(image_src):
    """Format image URL by prepending ArkhamDB base URL if needed."""
    if not image_src:
        return ''
    if image_src.startswith('http'):
        return image_src  # Already a full URL
    return ARKHAMDB_BASE_URL + image_src

def is_cache_valid(cache_file):
    """Check if the cache file exists and is still valid."""
    if not os.path.exists(cache_file):
        return False
    
    # Check if cache is older than CACHE_DURATION_HOURS
    cache_time = datetime.fromtimestamp(os.path.getmtime(cache_file))
    expiry_time = cache_time + timedelta(hours=CACHE_DURATION_HOURS)
    return datetime.now() < expiry_time

def fetch_and_cache_packs():
    """Fetch packs from API and cache them locally."""
    try:
        print(f"Fetching packs from {PACKS_API_URL}")
        response = requests.get(PACKS_API_URL, timeout=10)
        response.raise_for_status()
        
        packs_data = response.json()
        
        # Cache the data
        with open(PACKS_CACHE_FILE, 'w', encoding='utf-8') as f:
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
        with open(PACKS_CACHE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading cache: {e}")
        return None

def fetch_and_cache_cards():
    """Fetch cards from API and cache them locally."""
    try:
        print(f"Fetching cards from {CARDS_API_URL}")
        response = requests.get(CARDS_API_URL, timeout=30)  # Longer timeout for cards
        response.raise_for_status()
        
        cards_data = response.json()
        
        # Cache the data
        with open(CARDS_CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(cards_data, f, indent=2, ensure_ascii=False)
        
        print(f"Successfully cached {len(cards_data)} cards")
        return cards_data
    
    except requests.RequestException as e:
        print(f"Error fetching cards from API: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON response: {e}")
        return None

def load_cached_cards():
    """Load cards from cache file."""
    try:
        with open(CARDS_CACHE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading cards cache: {e}")
        return None

def get_arkham_cards():
    """Get Arkham Horror cards, either from cache or API."""
    # Check if we have a valid cache
    if is_cache_valid(CARDS_CACHE_FILE):
        print("Using cached cards data")
        cards_data = load_cached_cards()
        if cards_data:
            return cards_data
    
    # Cache is invalid or doesn't exist, fetch from API
    cards_data = fetch_and_cache_cards()
    if cards_data:
        return cards_data
    
    # If API fails, try to use stale cache
    print("API failed, attempting to use stale cards cache")
    cards_data = load_cached_cards()
    if cards_data:
        return cards_data
    
    print("Unable to load cards data")
    return []

def convert_to_draftmancer_format(arkham_cards, selected_pack_names):
    """Convert Arkham cards to Draftmancer custom card list format."""
    # Get pack data to map pack names to pack codes
    packs_data = load_cached_packs()
    if not packs_data:
        packs_data = fetch_and_cache_packs()
    
    if not packs_data:
        return {"error": "Unable to load pack data"}
    
    # Create a mapping from pack name to pack code
    pack_name_to_code = {pack['name']: pack['code'] for pack in packs_data}
    
    # Get pack codes for selected packs
    selected_pack_codes = set()
    for pack_name in selected_pack_names:
        pack_code = pack_name_to_code.get(pack_name)
        if pack_code:
            selected_pack_codes.add(pack_code)
    
    # Filter cards from selected packs and exclude cards with XP > 0
    filtered_cards = []
    for card in arkham_cards:
        if card.get('pack_code') in selected_pack_codes:
            # Filter out cards with XP > 0
            xp = card.get('xp', 0)
            if xp is None or xp <= 0:
                # Skip cards with 'b' suffix that are linked backs of other cards
                code = card.get('code', '')
                if code.endswith('b'):
                    # Check if there's a corresponding front card that links to this
                    base_code = code[:-1]
                    front_card_exists = any(
                        c.get('code') == base_code and c.get('linked_to_code') == code 
                        for c in arkham_cards if c.get('pack_code') in selected_pack_codes
                    )
                    if not front_card_exists:
                        # This 'b' card is not a linked back, include it
                        filtered_cards.append(card)
                    # If it is a linked back, skip it (it will be used as back image)
                else:
                    filtered_cards.append(card)
    
    # Create a lookup for linked back cards
    linked_back_lookup = {}
    for card in arkham_cards:
        if card.get('pack_code') in selected_pack_codes:
            linked_to = card.get('linked_to_code')
            if linked_to and linked_to.endswith('b'):
                # Find the linked back card
                back_card = next((c for c in arkham_cards if c.get('code') == linked_to), None)
                if back_card:
                    linked_back_lookup[card.get('code')] = back_card
    
    # Convert to Draftmancer format
    draftmancer_cards = []
    for card in filtered_cards:
        # Convert cost to string, handle special cases
        cost = card.get('cost')
        if cost == -2:
            mana_cost_str = "X"
        elif cost is not None:
            mana_cost_str = str(cost)
        else:
            mana_cost_str = "0"
        
        draftmancer_card = {
            "name": card.get('name', ''),
            "image": format_image_url(card.get('imagesrc', '')),
            "colors": FACTION_COLOR_MAP.get(card.get('faction_code', 'neutral'), []),
            "mana_cost": mana_cost_str,
            "type": TYPE_CODE_MAP.get(card.get('type_code'), 'Instant'),
            "rating": 0
        }
        
        # Add layout field and related_cards for investigator cards
        if card.get('type_code') == 'investigator':
            draftmancer_card["layout"] = "split_left"
            
            # Add related_cards based on deck_requirements
            related_cards = []
            deck_requirements = card.get('deck_requirements', {})
            if 'card' in deck_requirements:
                card_data = deck_requirements['card']
                if isinstance(card_data, dict):
                    # Get card codes from the keys of the card dictionary
                    related_card_codes = list(card_data.keys())
                    # Find the names of these cards
                    for code in related_card_codes:
                        related_card = next((c for c in arkham_cards if c.get('code') == code), None)
                        if related_card:
                            related_cards.append(related_card.get('name', ''))
            
            if related_cards:
                draftmancer_card["related_cards"] = related_cards
        
        # Handle back image - check for linked back card first, then backimagesrc
        card_code = card.get('code', '')
        if card_code in linked_back_lookup:
            # Use the linked back card's image
            back_card = linked_back_lookup[card_code]
            back_card_data = {
                "name": card.get('name', '') + " - back",
                "image": format_image_url(back_card.get('imagesrc', '')),
                "type": TYPE_CODE_MAP.get(card.get('type_code'), 'Instant')
            }
            # Add layout field for investigator back cards
            if card.get('type_code') == 'investigator':
                back_card_data["layout"] = "split_left"
            draftmancer_card["back"] = back_card_data
        elif card.get('backimagesrc'):
            # Use the standard backimagesrc
            back_card_data = {
                "name": card.get('name', '') + " - back",
                "image": format_image_url(card.get('backimagesrc', '')),
                "type": TYPE_CODE_MAP.get(card.get('type_code'), 'Instant')
            }
            # Add layout field for investigator back cards
            if card.get('type_code') == 'investigator':
                back_card_data["layout"] = "split_left"
            draftmancer_card["back"] = back_card_data
        
        draftmancer_cards.append(draftmancer_card)
    
    return {
        "cards": draftmancer_cards,
        "count": len(draftmancer_cards),
        "selected_packs": selected_pack_names
    }

def get_arkham_sets():
    """Get Arkham Horror sets, either from cache or API."""
    # Check if we have a valid cache
    if is_cache_valid(PACKS_CACHE_FILE):
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
    
    if not selected_sets:
        return render_template('draft_result.html', selected_sets=[], error="No sets selected")
    
    # Get all cards and convert to Draftmancer format
    print(f"Generating Draftmancer format for {len(selected_sets)} selected sets")
    arkham_cards = get_arkham_cards()
    
    if not arkham_cards:
        return render_template('draft_result.html', selected_sets=selected_sets, 
                             error="Unable to load card data")
    
    draftmancer_data = convert_to_draftmancer_format(arkham_cards, selected_sets)
    
    if "error" in draftmancer_data:
        return render_template('draft_result.html', selected_sets=selected_sets, 
                             error=draftmancer_data["error"])
    
    # Generate filename with timestamp
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"arkham_draft_{timestamp}.json"
    filepath = os.path.join(os.getcwd(), filename)
    
    # Save Draftmancer format file
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(draftmancer_data["cards"], f, indent=2, ensure_ascii=False)
        
        print(f"Generated Draftmancer file: {filename} with {draftmancer_data['count']} cards")
        
        return render_template('draft_result.html', 
                             selected_sets=selected_sets,
                             card_count=draftmancer_data['count'],
                             filename=filename,
                             filepath=filepath)
    
    except Exception as e:
        print(f"Error saving Draftmancer file: {e}")
        return render_template('draft_result.html', selected_sets=selected_sets, 
                             error=f"Error saving draft file: {str(e)}")

@app.route('/refresh-cache')
def refresh_cache():
    """Manually refresh the packs cache."""
    # Remove existing cache file if it exists
    if os.path.exists(PACKS_CACHE_FILE):
        os.remove(PACKS_CACHE_FILE)
    
    # Fetch fresh data
    packs_data = fetch_and_cache_packs()
    if packs_data:
        return f"Cache refreshed successfully! Found {len(packs_data)} packs.", 200
    else:
        return "Failed to refresh cache. Check console for errors.", 500

@app.route('/refresh-cards-cache')
def refresh_cards_cache():
    """Manually refresh the cards cache."""
    # Remove existing cache file if it exists
    if os.path.exists(CARDS_CACHE_FILE):
        os.remove(CARDS_CACHE_FILE)
    
    # Fetch fresh data
    cards_data = fetch_and_cache_cards()
    if cards_data:
        return f"Cards cache refreshed successfully! Found {len(cards_data)} cards.", 200
    else:
        return "Failed to refresh cards cache. Check console for errors.", 500

@app.route('/download/<filename>')
def download_file(filename):
    """Download a generated draft file."""
    # Security check - only allow arkham_draft files
    if not filename.startswith('arkham_draft_') or not filename.endswith('.json'):
        return "File not found", 404
    
    filepath = os.path.join(os.getcwd(), filename)
    if not os.path.exists(filepath):
        return "File not found", 404
    
    from flask import send_file
    return send_file(filepath, as_attachment=True, download_name=filename)

if __name__ == '__main__':
    app.run(debug=True)