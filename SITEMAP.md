# Arkham Horror Team Draft - Sitemap

## Web Application Routes

### Public Pages (GET)

#### `/` - Main Application
- **Description**: Primary interface for Arkham Horror LCG team draft setup
- **Features**: 
  - Pack selection from ArkhamDB
  - Advanced options panel with layout customization
  - Cards to Include/Exclude functionality
  - "Full Cube" support for custom card lists
- **Templates**: `templates/index.html`
- **Methods**: GET
- **Priority**: High

#### `/deck-exporter` - Deck Export Tool
- **Description**: Utility for exporting decks to various formats
- **Features**: Deck format conversion and export capabilities
- **Templates**: `templates/deck_exporter.html` 
- **Methods**: GET
- **Priority**: Medium

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

#### `/draft-now` - Live Draft Session
- **Description**: Returns draft file content as JSON for client-side download
- **Input**: Form data with pack selections, options, and custom cards
- **Output**: JSON with filename and file content
- **Methods**: POST
- **Features**:
  - Client-side file generation (no server files created)
  - Same logic as `/draft` route but returns content instead of template
  - Supports pack-based and Cards to Include workflows
- **Description**: Initiates immediate live draft session via Socket.IO
- **Input**: Form data with pack selections and options
- **Output**: JSON response for Socket.IO integration
- **Methods**: POST
- **Features**:
  - Real-time drafting with Draftmancer
  - Popup window integration
  - WebSocket communication

### Utility Endpoints

#### `/refresh-cache` - Refresh Pack Cache
- **Description**: Manually refreshes ArkhamDB pack data cache
- **Output**: Cache refresh status message
- **Methods**: GET
- **Usage**: Administrative/debugging

#### `/refresh-cards-cache` - Refresh Cards Cache  
- **Description**: Manually refreshes ArkhamDB card data cache
- **Output**: Cache refresh status message
- **Methods**: GET
- **Usage**: Administrative/debugging

#### `/download/<filename>` - File Download (DEPRECATED)
- **Description**: ~~Secure download endpoint for generated draft files~~
- **Status**: Removed - replaced with client-side download functionality
- **Note**: Files are no longer saved on server; content is generated and downloaded client-side

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
- `static/draftmancer-connect.js` - Socket.IO integration script

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
- Related card inclusion (bonded cards, alternate art, etc.)
- Proper card type categorization

### Live Drafting
- Socket.IO integration with Draftmancer
- Real-time draft session management
- Popup window coordination

### Export Capabilities
- Draftmancer .txt file format
- Direct download functionality
- Deck conversion utilities