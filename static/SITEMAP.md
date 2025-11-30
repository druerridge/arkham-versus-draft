# Arkham Versus Draft - Sitemap

## Web Application Routes

### Public Pages (GET)

#### `/` - Main Application
- **Description**: Primary interface for Arkham Horror LCG versus draft setup
- **Features**: 
  - Pack selection from ArkhamDB with default selections (Revised Core Set, Dunwich Legacy, Path to Carcosa, Starter Decks)
  - Advanced options panel with collapsible Instructions section
  - Cards to Include/Exclude functionality
  - "Full Cube" support for custom card lists
  - Hybrid Draft/Download button with bot/human draft modes
  - Beta status indicator
- **Templates**: `templates/index.html`
- **Methods**: GET
- **Priority**: High
- **Recent Updates**: 
  - Added Beta tag to title (Nov 2025)
  - Moved draft controls to top of page (Nov 2025)
  - Added default pack selections (Nov 2025)
  - Fixed parallel investigator required card inclusion (Nov 2025)

#### `/deck-exporter` - Deck Export Tool
- **Description**: Utility for exporting decks to various formats
- **Features**: Deck format conversion and export capabilities
- **Templates**: `templates/deck_exporter.html` 
- **Methods**: GET
- **Priority**: Medium
- **Recent Updates**: Added Beta tag to header (Nov 2025)

#### `/sitemap.xml` - XML Sitemap
- **Description**: Machine-readable sitemap for search engines
- **Location**: `static/sitemap.xml`
- **Methods**: GET
- **Last Modified**: 2025-11-30

### API Endpoints (POST)

#### `/draft` - Generate Draft File
- **Description**: Creates downloadable Draftmancer-compatible draft file
- **Input**: Form data with pack selections, options, and custom cards
- **Output**: Draft result page with download link
- **Templates**: `templates/draft_result.html`
- **Methods**: POST
- **Features**:
  - Supports pack-based drafting
  - Custom card inclusion via "Cards to Include"
  - Three-sheet draft structure (Investigators, BasicWeaknesses, PlayerCards)
  - Quantity configuration per pack

#### `/get-draft-content` - Generate Draft Content
- **Description**: Returns draft file content as JSON for client-side download
- **Input**: Form data with pack selections, options, and custom cards
- **Output**: JSON with filename and file content
- **Methods**: POST
- **Features**:
  - Client-side file generation (no server files created)
  - Same logic as `/draft` route but returns content instead of template
  - Supports pack-based and Cards to Include workflows
  - Improved parallel investigator handling with required card inclusion

#### `/draft-now` - Live Draft Session
- **Description**: Initiates immediate live draft session via Socket.IO
- **Input**: Form data with pack selections and options, draft mode (bot/human)
- **Output**: JSON response for Socket.IO integration
- **Methods**: POST
- **Features**:
  - Real-time drafting with Draftmancer
  - Bot vs Human draft mode selection
  - Popup window integration
  - WebSocket communication
  - Automatic team draft configuration for human drafts

### Static Assets

#### `/favicon.ico` - Site Icon
- **Description**: Serves application favicon
- **Location**: `static/favicon.ico`
- **Methods**: GET

#### Additional Static Files (served by Flask automatically)
- `static/apple-touch-icon.png` - Apple device icon
- `static/favicon-96x96.png` - High-resolution favicon
- `static/favicon.svg` - Vector favicon
- `static/web-app-manifest-*.png` - PWA manifest icons
- `static/site.webmanifest` - Web app manifest
- `static/draftmancer-connect.js` - Socket.IO integration script (ES6 module)
- `static/sitemap.xml` - XML sitemap for search engines
- `static/SITEMAP.md` - Human-readable sitemap documentation

## File Structure

### Templates
- `templates/index.html` - Main application interface with options panel
- `templates/draft_result.html` - Draft generation results and download
- `templates/deck_exporter.html` - Deck export utility interface

### Cache Files
- `arkham_packs_cache.json` - Cached ArkhamDB pack data
- `arkham_cards_cache.json` - Cached ArkhamDB card data  
- `pack_cards_cache/` - Directory for individual pack card caches

### Generated Files
- `arkham_draft_*.draftmancer.txt` - Generated draft files with timestamps

## Key Features

### Pack Selection
- Grouped by campaign cycles
- Quantity configuration per pack
- Pack validation and caching

### Advanced Options
- Layout customization (investigators per pack, basic weaknesses per pack, player cards per pack)
- Card inclusion/exclusion lists
- Custom card support via "Cards to Include"
- "Full Cube" functionality for pack-independent drafting

### Draft Generation
- Three-sheet structure for organized drafting
- Draftmancer format compatibility
- Related card inclusion (bonded cards, deck requirements for parallel investigators)
- Proper card type categorization
- Investigator uniqueness by name+set (except Core/Revised Core treated as same)
- Special handling for rotated parallel investigator images (Daisy, Roland, Skids)
- Required cards automatically included from unselected packs when needed

### Live Drafting
- Socket.IO integration with Draftmancer
- Real-time draft session management
- Popup window coordination

### Export Capabilities
- Draftmancer .txt file format
- Direct download functionality
- Deck conversion utilities