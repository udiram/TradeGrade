# TradeGrade Releases

This document explains how the automatic releases system works in TradeGrade.

## Overview

The releases page automatically tracks all git commits and organizes them into meaningful release notes. Every time you commit, the system:

1. Parses your commit messages
2. Categorizes them (features, improvements, fixes, technical)
3. Groups them by date
4. Generates version numbers
5. Creates beautiful release notes

## How It Works

### Automatic Tracking

- **Git Hooks**: A post-commit hook automatically updates releases data after each commit
- **Smart Categorization**: Commit messages are analyzed to determine the type of change
- **Version Generation**: Versions are generated based on date (e.g., `2025.10.17.1`)

### Commit Message Categories

The system automatically categorizes commits based on keywords:

- **Features** (`✨ New Features`): `add`, `implement`, `create`, `new`, `feature`
- **Improvements** (`🚀 Improvements`): `improve`, `enhance`, `update`, `refactor`, `optimize`
- **Bug Fixes** (`🐛 Bug Fixes`): `fix`, `bug`, `error`, `issue`, `problem`
- **Technical** (`🔧 Technical Updates`): `migration`, `database`, `deploy`, `config`, `setup`

### Release Types

- **Major**: Significant new features or breaking changes
- **Minor**: New features or substantial improvements
- **Patch**: Bug fixes and small improvements
- **Hotfix**: Critical bug fixes

## Manual Updates

If you need to manually update the releases data:

```bash
python3 scripts/update_releases.py
```

## Customization

### Adding New Categories

Edit `app/services/releases.py` and modify the `categorize_commit()` function:

```python
def categorize_commit(message: str) -> tuple[str, str]:
    message_lower = message.lower()
    
    # Add your custom keywords
    if any(word in message_lower for word in ['your', 'custom', 'keywords']):
        commit_type = 'your_category'
    # ... rest of function
```

### Styling

The releases page styling is in `app/templates/releases.html`. You can customize:

- Colors and themes
- Layout and spacing
- Icons and badges
- Mobile responsiveness

## Best Practices

### Commit Messages

Write clear, descriptive commit messages for better categorization:

```bash
# Good examples
git commit -m "Add injury status tracking for players"
git commit -m "Fix mobile navigation menu positioning"
git commit -m "Improve dashboard empty state styling"
git commit -m "Configure Railway deployment for MySQL"

# Avoid
git commit -m "fix stuff"
git commit -m "updates"
```

### Release Frequency

- **Daily**: For active development
- **Weekly**: For regular feature releases
- **As needed**: For hotfixes and critical updates

## Files

- `app/templates/releases.html` - Releases page template
- `app/services/releases.py` - Release data generation service
- `scripts/update_releases.py` - Manual update script
- `.git/hooks/post-commit` - Automatic update hook

## Access

Visit `/releases` on your TradeGrade instance to see the latest release notes.
