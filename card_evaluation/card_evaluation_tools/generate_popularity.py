import csv
import os
import hashlib
import json
from pathlib import Path
from collections import defaultdict

def load_decklists_data():
    """
    Load decklists data from CSV file into a dictionary keyed by 'id'.
    
    Returns:
        dict: Dictionary with decklist IDs as keys and decklist data as values
    """
    decklists = {}
    
    # Get the path to the CSV file
    current_dir = Path(__file__).parent
    csv_path = current_dir.parent / "card_evaluation_inputs" / "decklists.csv"
    
    try:
        with open(csv_path, 'r', encoding='utf-8') as file:
            csv_reader = csv.DictReader(file)
            for row in csv_reader:
                decklist_id = row['id']
                decklists[decklist_id] = row
        
        print(f"Loaded {len(decklists)} decklists from {csv_path}")
        
    except FileNotFoundError:
        print(f"Error: Could not find decklists.csv at {csv_path}")
    except Exception as e:
        print(f"Error loading decklists data: {e}")
    
    return decklists

def load_decklist_stats_data():
    """
    Load decklist stats data from CSV file into a dictionary keyed by 'decklist_id'.
    
    Returns:
        dict: Dictionary with decklist IDs as keys and stats data as values
    """
    decklist_stats = {}
    
    # Get the path to the CSV file
    current_dir = Path(__file__).parent
    csv_path = current_dir.parent / "card_evaluation_inputs" / "decklist_stats.csv"
    
    try:
        with open(csv_path, 'r', encoding='utf-8') as file:
            csv_reader = csv.DictReader(file)
            for row in csv_reader:
                decklist_id = row['decklist_id']
                decklist_stats[decklist_id] = row
        
        print(f"Loaded {len(decklist_stats)} decklist stats from {csv_path}")
        
    except FileNotFoundError:
        print(f"Error: Could not find decklist_stats.csv at {csv_path}")
    except Exception as e:
        print(f"Error loading decklist stats data: {e}")
    
    return decklist_stats

def load_popularity_data():
    """
    Load both decklists and decklist stats data.
    
    Returns:
        tuple: (decklists_dict, decklist_stats_dict)
    """
    print("Loading popularity data...")
    
    decklists = load_decklists_data()
    decklist_stats = load_decklist_stats_data()
    
    print(f"Successfully loaded data for {len(decklists)} decklists and {len(decklist_stats)} decklist stats")
    
    return decklists, decklist_stats

def load_arkham_cards_cache():
    """
    Load arkham cards cache data from JSON file into a dictionary keyed by 'code'.
    
    Returns:
        dict: Dictionary with card codes as keys and card data as values
    """
    arkham_cards = {}
    
    # Get the path to the JSON file
    current_dir = Path(__file__).parent
    json_path = current_dir.parent.parent / "arkham_cards_cache.json"
    
    try:
        with open(json_path, 'r', encoding='utf-8') as file:
            cards_list = json.load(file)
            for card in cards_list:
                code = card.get('code')
                if code:
                    arkham_cards[code] = card
        
        print(f"Loaded {len(arkham_cards)} cards from arkham_cards_cache.json")
        
    except FileNotFoundError:
        print(f"Error: Could not find arkham_cards_cache.json at {json_path}")
    except Exception as e:
        print(f"Error loading arkham cards cache: {e}")
    
    return arkham_cards

def generate_investigator_occurrence_csv(decklists, arkham_cards, arkham_packs, output_path="investigator_occurrences.csv"):
    """
    Generate a CSV file with investigator occurrence statistics.
    
    Args:
        decklists (dict): Dictionary of filtered decklists keyed by 'id'.
        arkham_cards (dict): Dictionary of card data keyed by 'code'.
        arkham_packs (dict): Dictionary of pack data keyed by 'code'.
        output_path (str): Path where the CSV file should be saved.
    """
    # Count investigator occurrences
    investigator_counts = defaultdict(int)
    investigator_info = {}
    
    processed_decks = 0
    skipped_decks = 0
    
    for decklist_id, decklist in decklists.items():
        try:
            investigator_code = decklist.get('investigator_code', '').strip()
            investigator_name = decklist.get('investigator_name', '').strip()
            
            if investigator_code and investigator_name:
                investigator_counts[investigator_name] += 1
                
                # Store investigator info (use first encountered)
                if investigator_name not in investigator_info:
                    # Get investigator card info to find pack_code
                    card_info = arkham_cards.get(investigator_code, {})
                    pack_code = card_info.get('pack_code', '')
                    
                    # Get release date from pack info
                    pack_info = arkham_packs.get(pack_code, {})
                    date_released = pack_info.get('available', 'Unknown')
                    
                    investigator_info[investigator_name] = {
                        'investigator_code': investigator_code,
                        'pack_code': pack_code,
                        'date_released': date_released
                    }
            
            processed_decks += 1
            
        except Exception as e:
            print(f"Error processing investigator for decklist {decklist_id}: {e}")
            skipped_decks += 1
    
    # Write results to CSV
    try:
        with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['investigator_name', 'occurances', 'date_released']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            
            # Sort investigators by occurrence count (descending)
            sorted_investigators = sorted(
                investigator_counts.items(), 
                key=lambda x: x[1], 
                reverse=True
            )
            
            for investigator_name, count in sorted_investigators:
                info = investigator_info.get(investigator_name, {})
                writer.writerow({
                    'investigator_name': investigator_name,
                    'occurances': count,
                    'date_released': info.get('date_released', 'Unknown')
                })
        
        print(f"Generated investigator occurrence CSV with {len(investigator_counts)} investigators")
        print(f"Processed {processed_decks} decklists, skipped {skipped_decks} due to errors")
        print(f"Output saved to: {output_path}")
        
    except Exception as e:
        print(f"Error writing investigator CSV file: {e}")

def remove_low_value_decklists(decklists, decklist_stats, min_likes):
    """
    Remove decklists that have fewer than min_likes, have previous_deck/next_deck values,
    or have duplicate slots from both decklists and decklist_stats.
    
    Args:
        decklists (dict): Dictionary of decklists keyed by 'id'.
        decklist_stats (dict): Dictionary of decklist stats keyed by 'decklist_id'.
        min_likes (int): Minimum number of likes required to keep a decklist.
    """
    to_remove = []
    removed_for_likes = 0
    removed_for_previous_next = 0
    removed_for_duplicate_slots = 0
    seen_slots_hashes = set()
    
    for decklist_id, stats in decklist_stats.items():
        should_remove = False
        
        # Check if likes are below minimum
        try:
            likes = int(stats.get('likes', 0))
            if likes < min_likes:
                should_remove = True
                removed_for_likes += 1
        except ValueError:
            print(f"Warning: Invalid likes value for decklist_id {decklist_id}: {stats.get('likes')}")
        
        # Check if decklist has previous_deck or next_deck values
        if decklist_id in decklists:
            decklist = decklists[decklist_id]
            previous_deck = decklist.get('previous_deck', '').strip()
            next_deck = decklist.get('next_deck', '').strip()
            
            if previous_deck or next_deck:
                should_remove = True
                removed_for_previous_next += 1
            
            # Check for duplicate slots
            if not should_remove:  # Only check if not already marked for removal
                slots = decklist.get('slots', '').strip()
                if slots:
                    # Create hash of the slots field
                    slots_hash = hashlib.md5(slots.encode('utf-8')).hexdigest()
                    
                    if slots_hash in seen_slots_hashes:
                        should_remove = True
                        removed_for_duplicate_slots += 1
                    else:
                        seen_slots_hashes.add(slots_hash)
        
        if should_remove:
            to_remove.append(decklist_id)
    
    for decklist_id in to_remove:
        if decklist_id in decklists:
            del decklists[decklist_id]
        if decklist_id in decklist_stats:
            del decklist_stats[decklist_id]
    
    print(f"Removed {len(to_remove)} decklists:")
    print(f"  - {removed_for_likes} with fewer than {min_likes} likes")
    print(f"  - {removed_for_previous_next} with previous_deck or next_deck values")
    print(f"  - {removed_for_duplicate_slots} with duplicate slots")

def load_arkham_packs_cache():
    """
    Load arkham packs cache data from JSON file into a dictionary keyed by 'code'.
    
    Returns:
        dict: Dictionary with pack codes as keys and pack data as values
    """
    arkham_packs = {}
    
    # Get the path to the JSON file
    current_dir = Path(__file__).parent
    json_path = current_dir.parent.parent / "arkham_packs_cache.json"
    
    try:
        with open(json_path, 'r', encoding='utf-8') as file:
            packs_list = json.load(file)
            for pack in packs_list:
                code = pack.get('code')
                if code:
                    arkham_packs[code] = pack
        
        print(f"Loaded {len(arkham_packs)} packs from arkham_packs_cache.json")
        
    except FileNotFoundError:
        print(f"Error: Could not find arkham_packs_cache.json at {json_path}")
    except Exception as e:
        print(f"Error loading arkham packs cache: {e}")
    
    return arkham_packs

def remove_low_value_decklists(decklists, decklist_stats, min_likes):
    """
    Remove decklists that have fewer than min_likes, have previous_deck/next_deck values,
    or have duplicate slots from both decklists and decklist_stats.
    
    Args:
        decklists (dict): Dictionary of decklists keyed by 'id'.
        decklist_stats (dict): Dictionary of decklist stats keyed by 'decklist_id'.
        min_likes (int): Minimum number of likes required to keep a decklist.
    """
    to_remove = []
    removed_for_likes = 0
    removed_for_previous_next = 0
    removed_for_duplicate_slots = 0
    seen_slots_hashes = set()
    
    for decklist_id, stats in decklist_stats.items():
        should_remove = False
        
        # Check if likes are below minimum
        try:
            likes = int(stats.get('likes', 0))
            if likes < min_likes:
                should_remove = True
                removed_for_likes += 1
        except ValueError:
            print(f"Warning: Invalid likes value for decklist_id {decklist_id}: {stats.get('likes')}")
        
        # Check if decklist has previous_deck or next_deck values
        if decklist_id in decklists:
            decklist = decklists[decklist_id]
            previous_deck = decklist.get('previous_deck', '').strip()
            next_deck = decklist.get('next_deck', '').strip()
            
            if previous_deck or next_deck:
                should_remove = True
                removed_for_previous_next += 1
            
            # Check for duplicate slots
            if not should_remove:  # Only check if not already marked for removal
                slots = decklist.get('slots', '').strip()
                if slots:
                    # Create hash of the slots field
                    slots_hash = hashlib.md5(slots.encode('utf-8')).hexdigest()
                    
                    if slots_hash in seen_slots_hashes:
                        should_remove = True
                        removed_for_duplicate_slots += 1
                    else:
                        seen_slots_hashes.add(slots_hash)
        
        if should_remove:
            to_remove.append(decklist_id)
    
    for decklist_id in to_remove:
        if decklist_id in decklists:
            del decklists[decklist_id]
        if decklist_id in decklist_stats:
            del decklist_stats[decklist_id]
    
    print(f"Removed {len(to_remove)} decklists:")
    print(f"  - {removed_for_likes} with fewer than {min_likes} likes")
    print(f"  - {removed_for_previous_next} with previous_deck or next_deck values")
    print(f"  - {removed_for_duplicate_slots} with duplicate slots")

def generate_card_popularity_csv(decklists, arkham_cards, arkham_packs, output_path="card_popularity.csv"):
    """
    Generate a CSV file with card popularity statistics.
    
    Args:
        decklists (dict): Dictionary of filtered decklists keyed by 'id'.
        arkham_cards (dict): Dictionary of card data keyed by 'code'.
        arkham_packs (dict): Dictionary of pack data keyed by 'code'.
        output_path (str): Path where the CSV file should be saved.
    """
    # Initialize counters for each card (by name instead of code)
    card_stats_by_name = defaultdict(lambda: {
        'main_decks_including_once': 0,
        'main_deck_occurances': 0,
        'side_decks_including_once': 0,
        'side_deck_occurances': 0,
        'card_codes': [],
        'faction_code': '',
        'xp': 0,
        'date_released': ''
    })
    
    processed_decks = 0
    skipped_decks = 0
    
    for decklist_id, decklist in decklists.items():
        try:
            # Process main deck slots
            slots_str = decklist.get('slots', '').strip()
            if slots_str:
                try:
                    slots = json.loads(slots_str)
                    for card_code, quantity in slots.items():
                        quantity = int(quantity)
                        # Get card info to determine name
                        card_info = arkham_cards.get(card_code, {})
                        card_name = card_info.get('name', f'Unknown_{card_code}')
                        
                        # Append XP cost to name if xp > 0
                        xp = card_info.get('xp', 0)
                        if xp > 0:
                            card_name = f"{card_name} ({xp})"
                        
                        card_stats_by_name[card_name]['main_decks_including_once'] += 1
                        card_stats_by_name[card_name]['main_deck_occurances'] += quantity
                        card_stats_by_name[card_name]['card_codes'].append(card_code)
                        
                        # Store faction, xp, and date info (use first encountered)
                        if not card_stats_by_name[card_name]['faction_code']:
                            pack_code = card_info.get('pack_code', '')
                            pack_info = arkham_packs.get(pack_code, {})
                            date_released = pack_info.get('available', 'Unknown')
                            
                            card_stats_by_name[card_name]['faction_code'] = card_info.get('faction_code', 'Unknown')
                            card_stats_by_name[card_name]['xp'] = xp
                            card_stats_by_name[card_name]['date_released'] = date_released
                            
                except (json.JSONDecodeError, ValueError) as e:
                    print(f"Warning: Could not parse slots for decklist {decklist_id}: {e}")
            
            # Process side deck slots
            side_slots_str = decklist.get('sideSlots', '').strip()
            if side_slots_str:
                try:
                    side_slots = json.loads(side_slots_str)
                    for card_code, quantity in side_slots.items():
                        quantity = int(quantity)
                        # Get card info to determine name
                        card_info = arkham_cards.get(card_code, {})
                        card_name = card_info.get('name', f'Unknown_{card_code}')
                        
                        # Append XP cost to name if xp > 0
                        xp = card_info.get('xp', 0)
                        if xp > 0:
                            card_name = f"{card_name} ({xp})"
                        
                        card_stats_by_name[card_name]['side_decks_including_once'] += 1
                        card_stats_by_name[card_name]['side_deck_occurances'] += quantity
                        card_stats_by_name[card_name]['card_codes'].append(card_code)
                        
                        # Store faction, xp, and date info (use first encountered)
                        if not card_stats_by_name[card_name]['faction_code']:
                            pack_code = card_info.get('pack_code', '')
                            pack_info = arkham_packs.get(pack_code, {})
                            date_released = pack_info.get('available', 'Unknown')
                            
                            card_stats_by_name[card_name]['faction_code'] = card_info.get('faction_code', 'Unknown')
                            card_stats_by_name[card_name]['xp'] = xp
                            card_stats_by_name[card_name]['date_released'] = date_released
                            
                except (json.JSONDecodeError, ValueError) as e:
                    print(f"Warning: Could not parse sideSlots for decklist {decklist_id}: {e}")
            
            processed_decks += 1
            
        except Exception as e:
            print(f"Error processing decklist {decklist_id}: {e}")
            skipped_decks += 1
    
    # Write results to CSV
    try:
        with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = [
                'name',
                'faction_code',
                'xp',
                'date_released',
                'main_decks_including_once', 
                'main_deck_occurances', 
                'side_decks_including_once', 
                'side_deck_occurances'
            ]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            
            # Sort cards by total occurrences (main + side) for consistent output
            sorted_cards = sorted(
                card_stats_by_name.items(), 
                key=lambda x: x[1]['main_deck_occurances'] + x[1]['side_deck_occurances'], 
                reverse=True
            )
            
            # Filter out weakness cards, investigator-restricted cards, and investigator cards before writing
            filtered_cards = []
            weakness_count = 0
            investigator_restricted_count = 0
            investigator_count = 0
            for card_name, stats in sorted_cards:
                should_filter = False
                
                # Check all card codes for this name to see if any should be filtered
                for card_code in stats['card_codes']:
                    card_info = arkham_cards.get(card_code, {})
                    subtype_code = card_info.get('subtype_code', '')
                    type_code = card_info.get('type_code', '')
                    restrictions = card_info.get('restrictions', {})
                    
                    # Filter weakness cards
                    if subtype_code in ['weakness', 'basicweakness']:
                        weakness_count += 1
                        should_filter = True
                        break
                    
                    # Filter investigator-restricted cards
                    elif 'investigator' in restrictions:
                        investigator_restricted_count += 1
                        should_filter = True
                        break
                    
                    # Filter investigator cards
                    elif type_code == 'investigator':
                        investigator_count += 1
                        should_filter = True
                        break
                
                if not should_filter:
                    filtered_cards.append((card_name, stats))
            
            print(f"Filtered out {weakness_count} weakness cards, {investigator_restricted_count} investigator-restricted cards, and {investigator_count} investigator cards")
            
            for card_name, stats in filtered_cards:
                writer.writerow({
                    'name': card_name,
                    'faction_code': stats['faction_code'],
                    'xp': stats['xp'],
                    'date_released': stats['date_released'],
                    'main_decks_including_once': stats['main_decks_including_once'],
                    'main_deck_occurances': stats['main_deck_occurances'],
                    'side_decks_including_once': stats['side_decks_including_once'],
                    'side_deck_occurances': stats['side_deck_occurances']
                })
        
        print(f"Generated card popularity CSV with {len(filtered_cards)} cards (filtered out {weakness_count} weakness cards, {investigator_restricted_count} investigator-restricted cards, and {investigator_count} investigator cards)")
        print(f"Processed {processed_decks} decklists, skipped {skipped_decks} due to errors")
        print(f"Output saved to: {output_path}")
        
    except Exception as e:
        print(f"Error writing CSV file: {e}")

def main():
    """
    Main function to test the data loading functionality.
    """
    decklists, decklist_stats = load_popularity_data()
    arkham_cards = load_arkham_cards_cache()
    arkham_packs = load_arkham_packs_cache()

    remove_low_value_decklists(decklists, decklist_stats, min_likes=1)
    
    # Generate card popularity CSV
    output_path = Path(__file__).parent.parent / "card_evaluations" / "card_popularity.csv"
    generate_card_popularity_csv(decklists, arkham_cards, arkham_packs, str(output_path))
    
    # Generate investigator occurrence CSV
    investigator_output_path = Path(__file__).parent.parent / "card_evaluations" / "investigator_occurrences.csv"
    generate_investigator_occurrence_csv(decklists, arkham_cards, arkham_packs, str(investigator_output_path))

    # Print some sample data to verify loading
    if decklists:
        print(f"\nRemaining decklists after filtering: {len(decklists)}")
        print("\nSample decklist:")
        sample_id = next(iter(decklists))
        sample_decklist = decklists[sample_id]
        print(f"ID: {sample_id}")
        print(f"Name: {sample_decklist.get('name', 'N/A')}")
        print(f"Investigator: {sample_decklist.get('investigator_name', 'N/A')}")
        print(f"slots: {sample_decklist.get('slots', 'N/A')}")
        print(f"sideSlots: {sample_decklist.get('sideSlots', 'N/A')}")
    
    if decklist_stats:
        print("\nSample decklist stats:")
        sample_id = next(iter(decklist_stats))
        sample_stats = decklist_stats[sample_id]
        print(f"Decklist ID: {sample_id}")
        print(f"Favorites: {sample_stats.get('favorites', 'N/A')}")
        print(f"Likes: {sample_stats.get('likes', 'N/A')}")
        print(f"Comments: {sample_stats.get('comments', 'N/A')}")

if __name__ == "__main__":
    main()
