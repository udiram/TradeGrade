# Contributing to TradeGrade

Thank you for your interest in contributing to TradeGrade! This document provides guidelines and information for contributors.

## 🚀 Getting Started

### Prerequisites
- Python 3.13+
- Git
- Basic knowledge of Flask, SQLAlchemy, and web development

### Development Setup

1. **Fork and clone the repository:**
   ```bash
   git clone https://github.com/yourusername/TradeGrade.git
   cd TradeGrade
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

5. **Initialize the database:**
   ```bash
   flask db init
   flask db migrate -m "Initial migration"
   flask db upgrade
   ```

6. **Run the application:**
   ```bash
   python run.py
   ```

## 📋 How to Contribute

### Reporting Issues

Before creating an issue, please:
1. Check if the issue already exists
2. Use the issue templates
3. Provide detailed information about the problem
4. Include steps to reproduce the issue

### Suggesting Features

We welcome feature suggestions! Please:
1. Check if the feature is already requested
2. Provide a clear description of the feature
3. Explain the use case and benefits
4. Consider implementation complexity

### Code Contributions

1. **Create a feature branch:**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes:**
   - Follow the coding standards
   - Add tests for new functionality
   - Update documentation as needed

3. **Test your changes:**
   ```bash
   python -m pytest
   ```

4. **Commit your changes:**
   ```bash
   git commit -m "Add: brief description of changes"
   ```

5. **Push to your fork:**
   ```bash
   git push origin feature/your-feature-name
   ```

6. **Create a Pull Request:**
   - Use the PR template
   - Provide a clear description
   - Link any related issues

## 📝 Coding Standards

### Python Code Style
- Follow PEP 8 guidelines
- Use type hints where appropriate
- Write docstrings for functions and classes
- Keep functions small and focused

### Example:
```python
def analyze_trade(offered_players: List[Player], 
                 requested_players: List[Player]) -> Dict[str, Any]:
    """
    Analyze a fantasy football trade proposal.
    
    Args:
        offered_players: List of players being offered
        requested_players: List of players being requested
        
    Returns:
        Dictionary containing analysis results
    """
    # Implementation here
    pass
```

### HTML/CSS/JavaScript
- Use semantic HTML
- Follow BEM methodology for CSS
- Use modern JavaScript (ES6+)
- Ensure responsive design

### Database
- Use descriptive model names
- Add proper indexes
- Include foreign key constraints
- Write migration scripts for schema changes

## 🧪 Testing

### Writing Tests
- Write tests for all new functionality
- Aim for high test coverage
- Use descriptive test names
- Test both success and failure cases

### Test Structure
```python
def test_trade_analysis_success():
    """Test successful trade analysis."""
    # Arrange
    offered = [create_test_player()]
    requested = [create_test_player()]
    
    # Act
    result = analyze_trade(offered, requested)
    
    # Assert
    assert result['success'] is True
    assert 'recommendation' in result
```

### Running Tests
```bash
# Run all tests
python -m pytest

# Run with coverage
python -m pytest --cov=app

# Run specific test file
python -m pytest tests/test_analysis.py

# Run with verbose output
python -m pytest -v
```

## 📚 Documentation

### Code Documentation
- Write clear docstrings
- Include type hints
- Add inline comments for complex logic
- Update README for new features

### API Documentation
- Document all new endpoints
- Include request/response examples
- Specify authentication requirements
- Add error response codes

## 🔄 Pull Request Process

### Before Submitting
1. Ensure all tests pass
2. Update documentation
3. Check code style
4. Test on different browsers/devices

### PR Description Template
```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Tests pass locally
- [ ] Manual testing completed
- [ ] Cross-browser testing (if applicable)

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] No breaking changes (or documented)
```

## 🏷️ Commit Message Format

Use conventional commit messages:

```
type(scope): description

[optional body]

[optional footer]
```

### Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

### Examples:
```
feat(analysis): add team depth analysis
fix(roster): resolve AJAX toggle issue
docs(readme): update installation instructions
```

## 🐛 Bug Reports

When reporting bugs, please include:

1. **Environment Information:**
   - OS and version
   - Python version
   - Browser and version (if applicable)

2. **Steps to Reproduce:**
   - Clear, numbered steps
   - Expected vs actual behavior
   - Screenshots or error messages

3. **Additional Context:**
   - Related issues
   - Workarounds (if any)
   - Impact on functionality

## 💡 Feature Requests

For feature requests, please provide:

1. **Problem Description:**
   - What problem does this solve?
   - Who would benefit from this feature?

2. **Proposed Solution:**
   - How should this work?
   - Any design considerations?

3. **Alternatives Considered:**
   - Other ways to solve the problem
   - Why this approach is preferred

## 🤝 Community Guidelines

### Be Respectful
- Use welcoming and inclusive language
- Be respectful of differing viewpoints
- Focus on what is best for the community

### Be Constructive
- Provide helpful feedback
- Suggest improvements
- Share knowledge and resources

### Be Patient
- Remember that maintainers are volunteers
- Allow time for review and discussion
- Be understanding of different time zones

## 📞 Getting Help

- **GitHub Issues**: For bugs and feature requests
- **GitHub Discussions**: For questions and general discussion
- **Email**: support@tradegrade.com for private matters

## 🎉 Recognition

Contributors will be recognized in:
- README.md contributors section
- Release notes
- Project documentation

Thank you for contributing to TradeGrade! 🏈
