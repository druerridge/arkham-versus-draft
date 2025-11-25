from flask import Flask, render_template, request, redirect, url_for
import requests
import json
import os
from datetime import datetime, timedelta

app = Flask(__name__)

# Cache configuration
PACKS_CACHE_FILE = 'arkham_packs_cache.json'
CARDS_CACHE_FILE = 'arkham_cards_cache.json'
PACK_CARDS_CACHE_DIR = 'pack_cards_cache'
CACHE_DURATION_HOURS = 168  # Cache for a week
PACKS_API_URL = 'https://arkhamdb.com/api/public/packs/'
CARDS_API_URL = 'https://arkhamdb.com/api/public/cards/'
ARKHAMDB_BASE_URL = 'https://arkhamdb.com'

# Faction to Magic color mapping
FACTION_COLOR_MAP = {
    'guardian': ['U'], 
    'seeker': ['W'],   
    'rogue': ['G'],    
    'mystic': ['B'],   
    'survivor': ['R'], 
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

def get_pack_cards_cache_path(pack_code):
    """Get the cache file path for a specific pack."""
    if not os.path.exists(PACK_CARDS_CACHE_DIR):
        os.makedirs(PACK_CARDS_CACHE_DIR)
    return os.path.join(PACK_CARDS_CACHE_DIR, f'{pack_code}_cards.json')

def fetch_and_cache_pack_cards(pack_code):
    """Fetch cards from a specific pack and cache them."""
    try:
        pack_cards_url = f'{CARDS_API_URL}{pack_code}'
        print(f"Fetching cards from pack {pack_code}: {pack_cards_url}")
        response = requests.get(pack_cards_url, timeout=30)
        response.raise_for_status()
        
        pack_cards_data = response.json()
        
        # Cache the data
        cache_path = get_pack_cards_cache_path(pack_code)
        with open(cache_path, 'w', encoding='utf-8') as f:
            json.dump(pack_cards_data, f, indent=2, ensure_ascii=False)
        
        print(f"Successfully cached {len(pack_cards_data)} cards from pack {pack_code}")
        return pack_cards_data
    
    except requests.RequestException as e:
        print(f"Error fetching pack {pack_code} cards from API: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON response for pack {pack_code}: {e}")
        return None

def load_cached_pack_cards(pack_code):
    """Load cached cards for a specific pack."""
    cache_path = get_pack_cards_cache_path(pack_code)
    try:
        with open(cache_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading pack {pack_code} cache: {e}")
        return None

def get_pack_cards(pack_code):
    """Get cards for a specific pack, either from cache or API."""
    cache_path = get_pack_cards_cache_path(pack_code)
    
    # Check if we have a valid cache for this pack
    if is_cache_valid(cache_path):
        print(f"Using cached data for pack {pack_code}")
        pack_cards_data = load_cached_pack_cards(pack_code)
        if pack_cards_data:
            return pack_cards_data
    
    # Cache is invalid or doesn't exist, fetch from API
    pack_cards_data = fetch_and_cache_pack_cards(pack_code)
    if pack_cards_data:
        return pack_cards_data
    
    # If API fails, try to use stale cache
    print(f"API failed for pack {pack_code}, attempting to use stale cache")
    pack_cards_data = load_cached_pack_cards(pack_code)
    if pack_cards_data:
        return pack_cards_data
    
    print(f"Unable to load cards data for pack {pack_code}")
    return []

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
                # Skip cards that are bonded to other cards
                if card.get('bonded_to'):
                    continue
                
                # Skip cards with 'b' suffix that are linked backs of other cards
                code = card.get('code', '')
                if code.endswith('b'):
                    # Check if there's any card that links to this 'b' card
                    front_card_exists = any(
                        c.get('linked_to_code') == code 
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
    
    # Convert  to Draftmancer format for CustomCards section
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
            "set": f"AH{card.get('pack_code', '').upper()}",
            "collector_number": str(card.get('code', '')),
            "rating": 0
        }

        if card.get('type_code') == 'investigator':
            draftmancer_card["draft_effects"] = ["FaceUp"]

        # Add layout field and related_cards for investigator cards
        if card.get('type_code') == 'investigator':
            draftmancer_card["layout"] = "split_left"
            
            # Add related_cards based on deck_requirements and bonded_cards
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
            
            # Add bonded cards to related_cards
            bonded_cards = card.get('bonded_cards', [])
            if bonded_cards:
                for bonded_card_info in bonded_cards:
                    bonded_code = bonded_card_info.get('code')
                    if bonded_code:
                        bonded_card = next((c for c in arkham_cards if c.get('code') == bonded_code), None)
                        if bonded_card:
                            related_cards.append(bonded_card.get('name', ''))
            
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
        "selected_packs": selected_pack_names,
        "selected_pack_codes": selected_pack_codes,
        "filtered_cards": filtered_cards  # Include filtered cards for MainSlot generation
    }

def generate_player_cards(selected_pack_codes, pack_quantities=None):
    """Generate the PlayerCards section with actual card quantities from pack data, separated by set."""
    # Dictionary to track card quantities by (card_name, pack_code, collector_number) tuples
    card_set_quantities = {}
    
    # Get the main cards cache to verify which cards are player cards
    main_cards = get_arkham_cards()
    player_card_codes = set(card.get('code') for card in main_cards if card.get('code'))
    
    # Create pack code to name mapping for quantity lookup
    packs_data = load_cached_packs()
    pack_code_to_name = {pack['code']: pack['name'] for pack in packs_data} if packs_data else {}
    
    # Fetch pack-specific card data for each selected pack
    for pack_code in selected_pack_codes:
        pack_cards = get_pack_cards(pack_code)
        
        # Get the multiplier for this pack (default to 1 if not specified)
        pack_name = pack_code_to_name.get(pack_code, pack_code)
        pack_multiplier = pack_quantities.get(pack_name, 1) if pack_quantities else 1
        
        for card in pack_cards:
            # Only include cards that exist in the main cards cache (player cards)
            card_code = card.get('code', '')
            if card_code not in player_card_codes:
                continue
                
            # Skip cards that are bonded to other cards
            if card.get('bonded_to'):
                continue
            # Skip investigators and cards with restrictions field
            if card.get('type_code') == 'investigator':
                continue
            if 'restrictions' in card and card['restrictions']:
                continue
            # Skip basic weakness cards
            if card.get('subtype_code') == 'basicweakness':
                continue
            # Skip cards with XP > 0
            xp = card.get('xp', 0)
            if xp is not None and xp > 0:
                continue
            
            card_name = card.get('name', '')
            collector_number = str(card.get('code', ''))
            base_quantity = card.get('quantity', 0)
            final_quantity = base_quantity * pack_multiplier
            
            if card_name and final_quantity > 0:
                # Create a key combining card name, pack code, and collector number
                card_set_key = (card_name, pack_code, collector_number)
                
                if card_set_key in card_set_quantities:
                    card_set_quantities[card_set_key] += final_quantity
                else:
                    card_set_quantities[card_set_key] = final_quantity
    
    # Generate player cards lines with actual quantities, separated by set
    card_entries = []
    for (card_name, pack_code, collector_number), total_quantity in card_set_quantities.items():
        card_entries.append(f"{total_quantity} {card_name} (AH{pack_code.upper()}) {collector_number}")
    
    # Sort the entries by card name (ignoring quantity and set)
    card_entries.sort(key=lambda x: x.split(' ', 1)[1].split(' (AH')[0])
    
    return card_entries

def generate_investigators_cards(selected_pack_codes, pack_quantities=None):
    """Generate the Investigators section with unique cards by name, prioritizing revised core then most recent."""
    # Dictionary to track best card by name: card_name -> (card_data, pack_data)
    best_cards_by_name = {}
    
    # Get the main cards cache to verify which cards are player cards
    main_cards = get_arkham_cards()
    player_card_codes = set(card.get('code') for card in main_cards if card.get('code'))
    
    # Get pack data for priority logic
    packs_data = load_cached_packs()
    pack_code_to_pack = {pack['code']: pack for pack in packs_data} if packs_data else {}
    pack_code_to_name = {pack['code']: pack['name'] for pack in packs_data} if packs_data else {}
    
    # Fetch pack-specific card data for each selected pack
    for pack_code in selected_pack_codes:
        pack_cards = get_pack_cards(pack_code)
        pack_data = pack_code_to_pack.get(pack_code, {})
        
        for card in pack_cards:
            # Only include cards that exist in the main cards cache (player cards)
            card_code = card.get('code', '')
            if card_code not in player_card_codes:
                continue
                
            # Skip cards that are bonded to other cards
            if card.get('bonded_to'):
                continue
            # Only include investigators
            if card.get('type_code') != 'investigator':
                continue
            
            card_name = card.get('name', '')
            if not card_name:
                continue
            
            # Check if this is a better version than what we have
            if card_name not in best_cards_by_name:
                best_cards_by_name[card_name] = (card, pack_data)
            else:
                current_card, current_pack = best_cards_by_name[card_name]
                
                # Priority logic:
                # 1. Revised core set (pack_code == 'rcore') wins
                # 2. Otherwise, highest cycle_position wins
                # 3. If cycle_position is tied, highest position wins
                
                if pack_code == 'rcore' and current_pack.get('code') != 'rcore':
                    # New card is from revised core, current is not
                    best_cards_by_name[card_name] = (card, pack_data)
                elif current_pack.get('code') == 'rcore' and pack_code != 'rcore':
                    # Current card is from revised core, new is not - keep current
                    pass
                else:
                    # Neither or both are revised core, compare by cycle_position and position
                    current_cycle = current_pack.get('cycle_position', 0)
                    current_pos = current_pack.get('position', 0)
                    new_cycle = pack_data.get('cycle_position', 0)
                    new_pos = pack_data.get('position', 0)
                    
                    if (new_cycle > current_cycle) or (new_cycle == current_cycle and new_pos > current_pos):
                        best_cards_by_name[card_name] = (card, pack_data)
    
    # Generate investigators lines (no quantities, just unique cards)
    card_entries = []
    for card_name, (card, pack_data) in best_cards_by_name.items():
        collector_number = str(card.get('code', ''))
        pack_code = card.get('pack_code', '')
        card_entries.append(f"1 {card_name} (AH{pack_code.upper()}) {collector_number}")
    
    # Sort the entries by card name
    card_entries.sort(key=lambda x: x.split(' ', 1)[1].split(' (AH')[0])
    
    return card_entries

def generate_basic_weaknesses_cards(selected_pack_codes, pack_quantities=None):
    """Generate the BasicWeaknesses section with unique cards by name, prioritizing revised core then most recent."""
    # Dictionary to track best card by name: card_name -> (card_data, pack_data)
    best_cards_by_name = {}
    
    # Get the main cards cache to verify which cards are player cards
    main_cards = get_arkham_cards()
    player_card_codes = set(card.get('code') for card in main_cards if card.get('code'))
    
    # Get pack data for priority logic
    packs_data = load_cached_packs()
    pack_code_to_pack = {pack['code']: pack for pack in packs_data} if packs_data else {}
    pack_code_to_name = {pack['code']: pack['name'] for pack in packs_data} if packs_data else {}
    
    # Fetch pack-specific card data for each selected pack
    for pack_code in selected_pack_codes:
        pack_cards = get_pack_cards(pack_code)
        pack_data = pack_code_to_pack.get(pack_code, {})
        
        for card in pack_cards:
            # Only include cards that exist in the main cards cache (player cards)
            card_code = card.get('code', '')
            if card_code not in player_card_codes:
                continue
                
            # Skip cards that are bonded to other cards
            if card.get('bonded_to'):
                continue
            # Only include basic weakness cards
            if card.get('subtype_code') != 'basicweakness':
                continue
            
            card_name = card.get('name', '')
            if not card_name:
                continue
            
            # Check if this is a better version than what we have
            if card_name not in best_cards_by_name:
                best_cards_by_name[card_name] = (card, pack_data)
            else:
                current_card, current_pack = best_cards_by_name[card_name]
                
                # Priority logic:
                # 1. Revised core set (pack_code == 'rcore') wins
                # 2. Otherwise, highest cycle_position wins
                # 3. If cycle_position is tied, highest position wins
                
                if pack_code == 'rcore' and current_pack.get('code') != 'rcore':
                    # New card is from revised core, current is not
                    best_cards_by_name[card_name] = (card, pack_data)
                elif current_pack.get('code') == 'rcore' and pack_code != 'rcore':
                    # Current card is from revised core, new is not - keep current
                    pass
                else:
                    # Neither or both are revised core, compare by cycle_position and position
                    current_cycle = current_pack.get('cycle_position', 0)
                    current_pos = current_pack.get('position', 0)
                    new_cycle = pack_data.get('cycle_position', 0)
                    new_pos = pack_data.get('position', 0)
                    
                    if (new_cycle > current_cycle) or (new_cycle == current_cycle and new_pos > current_pos):
                        best_cards_by_name[card_name] = (card, pack_data)
    
    # Generate basic weaknesses lines (no quantities, just unique cards)
    card_entries = []
    for card_name, (card, pack_data) in best_cards_by_name.items():
        collector_number = str(card.get('code', ''))
        pack_code = card.get('pack_code', '')
        card_entries.append(f"1 {card_name} (AH{pack_code.upper()}) {collector_number}")
    
    # Sort the entries by card name
    card_entries.sort(key=lambda x: x.split(' ', 1)[1].split(' (AH')[0])
    
    return card_entries

def generate_draftmancer_file_content(cards, investigators_cards, basic_weaknesses_cards, player_cards, selected_pack_names):
    """Generate the complete Draftmancer file content in .txt format."""
    lines = []
    
    # CustomCards section
    lines.append("[CustomCards]")
    import json
    lines.append(json.dumps(cards, indent=2, ensure_ascii=False))
    
    # Settings section  
    lines.append("[Settings]")
    settings = {
        "name": "AH LCG - Draft",
        "cardBack": "https://images.steamusercontent.com/ugc/786371626459887968/96D099C4BBCD944EF3935E613FDF5706E46CA25A/?imw=5000&imh=5000&ima=fit&impolicy=Letterbox&imcolor=%23000000&letterbox=false",
        "layouts": {
            "Investigators": {
                "weight": 1,
                "slots": {
                    "Investigators": 3
                }
            },
            "BasicWeaknesses": {
                "weight": 1,
                "slots": {
                    "BasicWeaknesses": 3
                }
            },
            "PlayerCards": {
                "weight": 1,
                "slots": {
                    "PlayerCards": 15
                }
            }
        },
        "predeterminedLayouts": ["Investigators", "BasicWeaknesses", "PlayerCards", "PlayerCards", "PlayerCards"],
        "withReplacement": False
    }
    lines.append(json.dumps(settings, indent=4))
    
    # Investigators section
    lines.append("[Investigators]")
    lines.extend(investigators_cards)
    
    # BasicWeaknesses section
    lines.append("[BasicWeaknesses]")
    lines.extend(basic_weaknesses_cards)
    
    # PlayerCards section
    lines.append("[PlayerCards]")
    lines.extend(player_cards)
    
    return "\n".join(lines)

def get_arkham_sets_grouped():
    """Get Arkham Horror sets grouped by cycle."""
    # Check if we have a valid cache
    if is_cache_valid(PACKS_CACHE_FILE):
        print("Using cached packs data")
        packs_data = load_cached_packs()
        if packs_data:
            # Sort packs by cycle_position first, then by position
            sorted_packs = sorted(packs_data, key=lambda pack: (pack.get('cycle_position', 99), pack.get('position', 99)))
            return group_packs_by_cycle(sorted_packs)
    
    # Cache is invalid or doesn't exist, fetch from API
    packs_data = fetch_and_cache_packs()
    if packs_data:
        # Sort packs by cycle_position first, then by position
        sorted_packs = sorted(packs_data, key=lambda pack: (pack.get('cycle_position', 99), pack.get('position', 99)))
        return group_packs_by_cycle(sorted_packs)
    
    # If API fails, try to use stale cache
    print("API failed, attempting to use stale cache")
    packs_data = load_cached_packs()
    if packs_data:
        # Sort packs by cycle_position first, then by position
        sorted_packs = sorted(packs_data, key=lambda pack: (pack.get('cycle_position', 99), pack.get('position', 99)))
        return group_packs_by_cycle(sorted_packs)
    
    # All methods failed
    print("All methods failed, unable to load pack data")
    return None

def group_packs_by_cycle(packs_data):
    """Group packs by cycle_position and return structured data."""
    cycles = {}
    
    for pack in packs_data:
        cycle_pos = pack.get('cycle_position', 99)
        if cycle_pos not in cycles:
            # Special case for cycle_position 60 (Starter Decks)
            if cycle_pos == 60:
                cycle_name = "Starter Decks"
            # Special case for cycle_position 70 (Side Stories)
            elif cycle_pos == 70:
                cycle_name = "Side Stories"
            # Special case for cycle_position 80 (Promotional)
            elif cycle_pos == 80:
                cycle_name = "Promotional"
            # Special case for cycle_position 90 (Parallel)
            elif cycle_pos == 90:
                cycle_name = "Parallel"
            else:
                cycle_name = pack['name']  # First pack in cycle becomes the cycle name
            
            cycles[cycle_pos] = {
                'cycle_name': cycle_name,
                'packs': []
            }
        cycles[cycle_pos]['packs'].append(pack['name'])
    
    # Convert to sorted list
    return [{'cycle_position': pos, **data} for pos, data in sorted(cycles.items())]

def get_arkham_sets():
    """Get Arkham Horror sets, either from cache or API."""
    # Check if we have a valid cache
    if is_cache_valid(PACKS_CACHE_FILE):
        print("Using cached packs data")
        packs_data = load_cached_packs()
        if packs_data:
            # Sort packs by cycle_position first, then by position
            sorted_packs = sorted(packs_data, key=lambda pack: (pack.get('cycle_position', 99), pack.get('position', 99)))
            return [pack['name'] for pack in sorted_packs]
    
    # Cache is invalid or doesn't exist, fetch from API
    packs_data = fetch_and_cache_packs()
    if packs_data:
        # Sort packs by cycle_position first, then by position
        sorted_packs = sorted(packs_data, key=lambda pack: (pack.get('cycle_position', 99), pack.get('position', 99)))
        return [pack['name'] for pack in sorted_packs]
    
    # If API fails, try to use stale cache
    print("API failed, attempting to use stale cards cache")
    packs_data = load_cached_packs()
    if packs_data:
        # Sort packs by cycle_position first, then by position
        sorted_packs = sorted(packs_data, key=lambda pack: (pack.get('cycle_position', 99), pack.get('position', 99)))
        return [pack['name'] for pack in sorted_packs]
    
    # All methods failed
    print("All methods failed, unable to load pack data")
    return []

@app.route('/')
def index():
    arkham_sets_grouped = get_arkham_sets_grouped()
    if arkham_sets_grouped is None:
        return render_template('index.html', cycles=[], error="Unable to load pack data from ArkhamDB. Please try again later or check your internet connection.")
    return render_template('index.html', cycles=arkham_sets_grouped)

@app.route('/draft', methods=['POST'])
def draft():
    selected_sets = request.form.getlist('sets')
    
    if not selected_sets:
        return render_template('draft_result.html', selected_sets=[], error="No sets selected")
    
    # Process pack quantities - get quantities for each selected pack
    pack_quantities = {}
    for pack_name in selected_sets:
        quantity_key = f'quantity_{pack_name}'
        quantity = int(request.form.get(quantity_key, 1))  # Default to 1 if not specified
        pack_quantities[pack_name] = quantity
    
    # Get all cards and convert to Draftmancer format
    print(f"Generating Draftmancer format for {len(selected_sets)} selected sets with quantities: {pack_quantities}")
    arkham_cards = get_arkham_cards()
    
    if not arkham_cards:
        return render_template('draft_result.html', selected_sets=selected_sets, 
                             error="Unable to load card data")
    
    draftmancer_data = convert_to_draftmancer_format(arkham_cards, selected_sets)
    
    if "error" in draftmancer_data:
        return render_template('draft_result.html', selected_sets=selected_sets, 
                             error=draftmancer_data["error"])
    
    # Generate cards for all three sheets with actual quantities and pack multipliers
    investigators_cards = generate_investigators_cards(draftmancer_data["selected_pack_codes"], pack_quantities)
    basic_weaknesses_cards = generate_basic_weaknesses_cards(draftmancer_data["selected_pack_codes"], pack_quantities)
    player_cards = generate_player_cards(draftmancer_data["selected_pack_codes"], pack_quantities)
    
    # Generate complete Draftmancer file content
    file_content = generate_draftmancer_file_content(
        draftmancer_data["cards"],
        investigators_cards,
        basic_weaknesses_cards,
        player_cards,
        selected_sets
    )
    
    # Generate filename with timestamp and new extension
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"arkham_draft_{timestamp}.draftmancer.txt"
    filepath = os.path.join(os.getcwd(), filename)
    
    # Save Draftmancer format file
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(file_content)
        
        investigator_count = draftmancer_data['count']
        investigators_count = len(investigators_cards)
        basic_weaknesses_count = len(basic_weaknesses_cards)
        player_cards_count = len(player_cards)
        print(f"Generated Draftmancer file: {filename} with {investigator_count} custom cards, {investigators_count} investigators, {basic_weaknesses_count} basic weaknesses, and {player_cards_count} player cards")
        
        return render_template('draft_result.html', 
                             selected_sets=selected_sets,
                             card_count=investigator_count,
                             investigators_count=investigators_count,
                             basic_weaknesses_count=basic_weaknesses_count,
                             player_cards_count=player_cards_count,
                             filename=filename,
                             filepath=filepath)
    
    except Exception as e:
        print(f"Error saving Draftmancer file: {e}")
        return render_template('draft_result.html', selected_sets=selected_sets, 
                             error=f"Error saving draft file: {str(e)}")

@app.route('/draft-now', methods=['POST'])
def draft_now():
    from flask import jsonify
    
    selected_sets = request.form.getlist('sets')
    
    if not selected_sets:
        return jsonify({"error": "No sets selected"}), 400
    
    # Process pack quantities - get quantities for each selected pack
    pack_quantities = {}
    for pack_name in selected_sets:
        quantity_key = f'quantity_{pack_name}'
        quantity = int(request.form.get(quantity_key, 1))  # Default to 1 if not specified
        pack_quantities[pack_name] = quantity
    
    # Get all cards and convert to Draftmancer format
    print(f"Generating Draftmancer format for immediate draft with {len(selected_sets)} selected sets and quantities: {pack_quantities}")
    arkham_cards = get_arkham_cards()
    
    if not arkham_cards:
        return jsonify({"error": "Unable to load card data"}), 500
    
    draftmancer_data = convert_to_draftmancer_format(arkham_cards, selected_sets)
    
    if "error" in draftmancer_data:
        return jsonify({"error": draftmancer_data["error"]}), 500
    
    # Generate cards for all three sheets with actual quantities and pack multipliers
    investigators_cards = generate_investigators_cards(draftmancer_data["selected_pack_codes"], pack_quantities)
    basic_weaknesses_cards = generate_basic_weaknesses_cards(draftmancer_data["selected_pack_codes"], pack_quantities)
    player_cards = generate_player_cards(draftmancer_data["selected_pack_codes"], pack_quantities)
    
    # Generate complete Draftmancer file content
    file_content = generate_draftmancer_file_content(
        draftmancer_data["cards"],
        investigators_cards,
        basic_weaknesses_cards,
        player_cards,
        selected_sets
    )
    
    # Return JSON data for immediate drafting
    investigators_count = len(investigators_cards)
    basic_weaknesses_count = len(basic_weaknesses_cards)
    player_cards_count = len(player_cards)
    
    print(f"Generated Draftmancer content for immediate draft with {draftmancer_data['count']} custom cards, {investigators_count} investigators, {basic_weaknesses_count} basic weaknesses, and {player_cards_count} player cards")
    
    return jsonify({
        "cubeFile": file_content,
        "metadata": {
            "cardCount": draftmancer_data['count'],
            "investigatorsCount": investigators_count,
            "basicWeaknessesCount": basic_weaknesses_count,
            "playerCardsCount": player_cards_count,
            "selectedSets": selected_sets
        }
    })

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
    if not filename.startswith('arkham_draft_') or not filename.endswith('.draftmancer.txt'):
        return "File not found", 404
    
    filepath = os.path.join(os.getcwd(), filename)
    if not os.path.exists(filepath):
        return "File not found", 404
    
    from flask import send_file
    return send_file(filepath, as_attachment=True, download_name=filename)

if __name__ == '__main__':
    app.run(debug=True)