# Contributing to Arepy 🎮

Thank you for your interest in contributing to **Arepy**! We welcome contributions from everyone, whether you're fixing bugs, adding features, improving documentation, or helping with testing.

## 📋 Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Making Changes](#making-changes)
- [Testing](#testing)
- [Code Style](#code-style)
- [Submitting Changes](#submitting-changes)
- [Types of Contributions](#types-of-contributions)
- [Community](#community)

## 🤝 Code of Conduct

This project adheres to a Code of Conduct that we expect all contributors to follow:

- **Be respectful** and inclusive in your language and actions
- **Be collaborative** and help others learn and grow
- **Be constructive** when giving feedback
- **Focus on what's best** for the community and the project

## 🚀 Getting Started

### Prerequisites

- Python 3.10 or higher
- Git
- Basic knowledge of Python and game development concepts
- Familiarity with ECS (Entity Component System) architecture is helpful

### Areas Where We Need Help

- 🐛 **Bug fixes** - Help us squash those pesky bugs
- ✨ **New features** - Implement items from our roadmap
- 📚 **Documentation** - Improve guides, API docs, and examples
- 🧪 **Testing** - Write tests and improve coverage
- 🎨 **Examples** - Create games and demos using Arepy
- 🔧 **Performance** - Optimize the ECS engine
- 🎮 **Game bundles** - Add more built-in components and systems

## 💻 Development Setup

### 1. Fork and Clone

```bash
# Fork the repository on GitHub, then clone your fork
git clone https://github.com/YOUR_USERNAME/arepy.git
cd arepy

# Add the original repository as upstream
git remote add upstream https://github.com/Scr44gr/arepy.git
```

### 2. Set Up Development Environment

```bash
# Install uv (if you don't have it)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies with testing extras
uv sync --extra testing

# Activate the virtual environment
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

### 3. Verify Installation

```bash
# Run tests to make sure everything works
uv run pytest

# Run a simple example
uv run python examples/bunnymark.py
```

## 🔧 Making Changes

### 1. Create a Branch

```bash
# Update your main branch
git checkout main
git pull upstream main

# Create a new branch for your feature
git checkout -b feature/awesome-feature
# or for bug fixes:
git checkout -b fix/issue-description
```

### 2. Development Guidelines

#### **ECS Architecture**
- Keep components as **pure data** containers
- Put logic in **systems**, not components
- Use **queries** to filter entities efficiently
- Follow the **single responsibility principle**

#### **Code Organization**
```
arepy/
├── ecs/             # Core ECS implementation
│   ├── components.py    # Component base classes
│   ├── entities.py      # Entity management
│   ├── registry.py      # ECS registry
│   ├── query/          # Query system
│   └── systems.py      # System pipeline
├── bundle/          # Built-in components and systems
│   ├── components/     # Common game components
│   └── systems/        # Common game systems
└── engine/          # Engine integration (Raylib, etc.)
```

#### **Component Example**
```python
from arepy.ecs import Component

class Velocity(Component):
    """Component representing velocity in 2D space."""
    
    def __init__(self, x: float = 0.0, y: float = 0.0):
        super().__init__()
        self.x = x
        self.y = y
```

#### **System Example**
```python
from arepy.ecs import Query, Entity, With

def movement_system(query: Query[Entity, With[Transform, Velocity]]):
    """System that applies velocity to transform positions."""
    for entity in query.get_entities():
        transform = entity.get_component(Transform)
        velocity = entity.get_component(Velocity)
        
        transform.position.x += velocity.x
        transform.position.y += velocity.y
```

## 🧪 Testing

### Running Tests

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=arepy --cov-report=html

# Run specific test file
uv run pytest tests/test_registry.py -v

# Run tests for specific functionality
uv run pytest -k "test_query" -v
```

### Writing Tests

- **Write tests for all new features**
- **Add tests for bug fixes** to prevent regressions
- **Use descriptive test names** that explain what is being tested
- **Follow pytest conventions**

#### Test Example
```python
import pytest
from arepy.ecs import Registry, Entity
from arepy.bundle.components import Transform

def test_entity_component_operations():
    """Test adding, getting, and removing components from entities."""
    registry = Registry()
    entity = registry.create_entity()
    transform = Transform(x=10.0, y=20.0)
    
    # Add component
    entity.add_component(transform)
    assert entity.has_component(Transform)
    
    # Get component
    retrieved = entity.get_component(Transform)
    assert retrieved.x == 10.0
    assert retrieved.y == 20.0
    
    # Remove component
    entity.remove_component(Transform)
    assert not entity.has_component(Transform)
```

### Coverage Requirements

- **New code should have at least 80% test coverage**
- **Critical ECS functionality should have 90%+ coverage**
- **Bug fixes must include tests**

## 🎨 Code Style

### Python Style Guide

We follow **PEP 8** with some project-specific conventions:

```bash
# Format code with black (if you have it installed)
black arepy/ tests/

# Sort imports with isort (if you have it installed)
isort arepy/ tests/
```

### Conventions

- **Use type hints** for all function parameters and return values
- **Write docstrings** for all public classes and functions
- **Use descriptive variable names**
- **Keep functions small and focused**

#### Docstring Example
```python
def create_entity(self) -> Entity:
    """Create a new entity in the registry.
    
    Returns:
        Entity: A new entity with a unique ID.
        
    Example:
        >>> registry = Registry()
        >>> entity = registry.create_entity()
        >>> print(entity.get_id())
        1
    """
```

## 📤 Submitting Changes

### 1. Commit Your Changes

```bash
# Stage your changes
git add .

# Commit with a descriptive message
git commit -m "Add velocity component for 2D movement

- Implement Velocity component with x/y fields
- Add movement system that applies velocity to transforms
- Include comprehensive tests for velocity operations
- Update documentation with movement examples"
```

### 2. Push and Create Pull Request

```bash
# Push your branch
git push origin feature/awesome-feature

# Go to GitHub and create a Pull Request
```

### 3. Pull Request Guidelines

#### **PR Title Format**
- `feat: add velocity component for 2D movement`
- `fix: resolve entity cleanup memory leak`
- `docs: improve ECS architecture guide`
- `test: add comprehensive query system tests`

#### **PR Description Template**
```markdown
## Description
Brief description of the changes.

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Documentation update
- [ ] Performance improvement
- [ ] Test improvement

## Testing
- [ ] All existing tests pass
- [ ] New tests added for new functionality
- [ ] Manual testing completed

## Checklist
- [ ] Code follows project style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] Tests added/updated
```

## 📚 Types of Contributions

### 🐛 Bug Reports

When reporting bugs, please include:

- **Arepy version**
- **Python version**
- **Operating system**
- **Steps to reproduce**
- **Expected behavior**
- **Actual behavior**
- **Code example** (if applicable)

### ✨ Feature Requests

When requesting features:

- **Describe the problem** you're trying to solve
- **Explain your proposed solution**
- **Consider alternative solutions**
- **Provide use cases** and examples

### 📖 Documentation

Help improve our documentation:

- **API documentation** - Document classes and functions
- **Tutorials** - Create step-by-step guides
- **Examples** - Build demo games and snippets
- **README improvements** - Keep our main docs up-to-date

### 🎮 Examples and Demos

Create example projects that showcase Arepy:

- **Simple games** - Pong, Snake, Breakout
- **Tech demos** - Particle systems, UI examples
- **Performance benchmarks** - Stress tests and optimization examples

## 🏷️ Issue Labels

We use labels to categorize issues:

- `bug` - Something isn't working
- `enhancement` - New feature or request
- `documentation` - Improvements to docs
- `good first issue` - Good for newcomers
- `help wanted` - Extra attention needed
- `priority: high` - Critical issues
- `ecs` - Core ECS system related
- `graphics` - Raylib/rendering related
- `performance` - Performance improvements

## 💬 Community

### Getting Help

- **GitHub Discussions** - Ask questions and share ideas
- **GitHub Issues** - Report bugs and request features
- **Discord** - Real-time community chat (coming soon!)

### Stay Updated

- **Watch the repository** for notifications
- **Follow the project** for updates
- **Star the repo** if you find it useful!

## 🙏 Recognition

Contributors will be:

- **Listed in our Contributors section**
- **Credited in release notes** for significant contributions
- **Given appropriate GitHub repository permissions** for regular contributors

---

Thank you for contributing to Arepy! Together we're building an awesome Python game engine! 🎮✨

**Questions?** Feel free to reach out by opening an issue or starting a discussion.
