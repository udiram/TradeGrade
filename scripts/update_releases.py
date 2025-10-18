#!/usr/bin/env python3
"""
Script to update releases data after git commits
This can be run manually or as a git hook
"""

import os
import sys
import json
from datetime import datetime

# Add the project root to the Python path
project_root = os.path.join(os.path.dirname(__file__), '..')
sys.path.insert(0, project_root)

def update_releases_cache():
    """Update the releases cache file"""
    try:
        from app.services.releases import get_latest_releases
        
        # Get latest releases
        releases = get_latest_releases(50)
        
        # Convert to serializable format
        releases_data = []
        for release in releases:
            releases_data.append({
                'version': release.version,
                'date': release.date,
                'type': release.type,
                'summary': release.summary,
                'features': release.features,
                'improvements': release.improvements,
                'fixes': release.fixes,
                'technical': release.technical
            })
        
        # Save to cache file
        cache_file = os.path.join(os.path.dirname(__file__), '..', 'app', 'static', 'releases_cache.json')
        with open(cache_file, 'w') as f:
            json.dump({
                'last_updated': datetime.now().isoformat(),
                'releases': releases_data
            }, f, indent=2)
        
        print(f"✅ Updated releases cache with {len(releases_data)} releases")
        return True
        
    except Exception as e:
        print(f"❌ Failed to update releases cache: {e}")
        return False

if __name__ == "__main__":
    success = update_releases_cache()
    sys.exit(0 if success else 1)
