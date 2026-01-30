# Contributing to git-auto-pro

First off, thank you for considering contributing to git-auto-pro! It's people like you that make git-auto-pro such a great tool.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [How Can I Contribute?](#how-can-i-contribute)
- [Development Setup](#development-setup)
- [Coding Standards](#coding-standards)
- [Commit Guidelines](#commit-guidelines)
- [Pull Request Process](#pull-request-process)
- [Reporting Bugs](#reporting-bugs)
- [Suggesting Enhancements](#suggesting-enhancements)
- [Community](#community)

## Code of Conduct

This project and everyone participating in it is governed by our Code of Conduct. By participating, you are expected to uphold this code. Please report unacceptable behavior to the project maintainers.

### Our Standards

- **Be respectful**: Treat everyone with respect and kindness
- **Be collaborative**: Work together towards the common goal
- **Be inclusive**: Welcome diverse perspectives and backgrounds
- **Be patient**: Remember that everyone has different skill levels
- **Be constructive**: Provide helpful feedback and suggestions

## Getting Started

### Prerequisites

Before you begin, ensure you have:
- Git installed on your system
- A GitHub account
- Basic understanding of version control concepts
- Familiarity with the command line

### First Time Setup

1. **Fork the repository**: Click the 'Fork' button at the top right of the repository page
2. **Clone your fork**:
   ```bash
   git clone https://github.com/YOUR-USERNAME/git-auto-pro.git
   cd git-auto-pro
   ```
3. **Add upstream remote**:
   ```bash
   git remote add upstream https://github.com/HimanshuSingh-966/git-auto-pro.git
   ```
4. **Verify remotes**:
   ```bash
   git remote -v
   ```

## How Can I Contribute?

### Types of Contributions

We welcome various types of contributions:

- **Code contributions**: Bug fixes, new features, performance improvements
- **Documentation**: Improve README, add examples, write tutorials
- **Testing**: Write tests, report bugs, verify fixes
- **Design**: UI/UX improvements, logo design, graphics
- **Community**: Answer questions, help others, spread the word

### Good First Issues

Look for issues labeled `good first issue` or `help wanted`. These are great starting points for new contributors.

## Development Setup

### Installation

1. **Install dependencies** (if applicable):
   ```bash
   # Add installation commands specific to your project
   npm install
   # or
   pip install -r requirements.txt
   ```

2. **Configure development environment**:
   ```bash
   # Add any environment setup commands
   cp .env.example .env
   ```

3. **Run tests** to ensure everything is working:
   ```bash
   # Add test commands
   npm test
   # or
   pytest
   ```

### Building the Project

```bash
# Add build commands
npm run build
# or
python setup.py build
```

## Coding Standards

### General Guidelines

- Write clear, readable, and maintainable code
- Follow the existing code style and patterns
- Comment complex logic and non-obvious solutions
- Keep functions small and focused on a single task
- Use meaningful variable and function names

### Language-Specific Standards

**Python**:
- Follow PEP 8 style guide
- Use type hints where appropriate
- Write docstrings for functions and classes

**JavaScript**:
- Use ES6+ features
- Follow Airbnb style guide
- Use async/await for asynchronous operations

### Code Formatting

We use automated formatters to maintain consistent code style:

```bash
# Python
black .
flake8

# JavaScript
npm run lint
npm run format
```

## Commit Guidelines

We follow the [Conventional Commits](https://www.conventionalcommits.org/) specification for commit messages.

### Commit Message Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types

- `feat`: A new feature
- `fix`: A bug fix
- `docs`: Documentation only changes
- `style`: Changes that don't affect code meaning (formatting, etc.)
- `refactor`: Code changes that neither fix bugs nor add features
- `perf`: Performance improvements
- `test`: Adding or updating tests
- `chore`: Changes to build process or auxiliary tools

### Examples

```bash
feat(cli): add support for auto-commit scheduling

Implemented a new scheduling feature that allows users to
configure automatic commits at specified intervals.

Closes #123
```

```bash
fix(auth): resolve token expiration issue

Fixed a bug where authentication tokens would expire
prematurely, causing users to be logged out unexpectedly.

Fixes #456
```

### Commit Best Practices

- Use the imperative mood ("Add feature" not "Added feature")
- Keep the subject line under 50 characters
- Wrap the body at 72 characters
- Reference issues and pull requests in the footer
- Separate subject from body with a blank line

## Pull Request Process

### Before Submitting

1. **Update your fork**:
   ```bash
   git fetch upstream
   git checkout main
   git merge upstream/main
   ```

2. **Create a feature branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Make your changes**:
   - Write code
   - Add tests
   - Update documentation
   - Ensure all tests pass

4. **Commit your changes**:
   ```bash
   git add .
   git commit -m "feat: your feature description"
   ```

5. **Push to your fork**:
   ```bash
   git push origin feature/your-feature-name
   ```

### Submitting a Pull Request

1. Go to the original repository on GitHub
2. Click "New Pull Request"
3. Select your fork and branch
4. Fill out the PR template with:
   - Clear description of changes
   - Related issue numbers
   - Screenshots (if applicable)
   - Testing steps

### PR Guidelines

- **One feature per PR**: Keep PRs focused on a single feature or fix
- **Update documentation**: Ensure docs reflect your changes
- **Write tests**: Add tests for new features and bug fixes
- **Follow code style**: Maintain consistent formatting
- **Resolve conflicts**: Rebase if your branch is behind main
- **Be responsive**: Address review comments promptly

### PR Review Process

1. Maintainers will review your PR within a few days
2. Address any requested changes
3. Once approved, a maintainer will merge your PR
4. Celebrate! 🎉 You're now a contributor!

### After Your PR is Merged

- Delete your feature branch:
  ```bash
  git branch -d feature/your-feature-name
  git push origin --delete feature/your-feature-name
  ```
- Update your local main branch:
  ```bash
  git checkout main
  git pull upstream main
  ```

## Reporting Bugs

### Before Submitting a Bug Report

- Check the [existing issues](https://github.com/HimanshuSingh-966/git-auto-pro/issues) to avoid duplicates
- Verify you're using the latest version
- Try to reproduce the issue with minimal configuration
- Collect relevant information (logs, screenshots, error messages)

### How to Submit a Bug Report

Create an issue with the following information:

**Title**: Clear, descriptive summary

**Description**:
- Expected behavior
- Actual behavior
- Steps to reproduce
- System information (OS, version, etc.)
- Screenshots or error logs (if applicable)

**Example**:

```markdown
**Environment:**
- OS: Ubuntu 22.04
- Version: v1.2.3
- Git version: 2.39.0

**Steps to Reproduce:**
1. Run `git-auto-pro init`
2. Configure with X settings
3. Execute command Y

**Expected Behavior:**
The tool should automatically commit changes

**Actual Behavior:**
Error: "Unable to detect changes"

**Error Log:**
[Paste error log here]
```

## Suggesting Enhancements

### Before Submitting an Enhancement

- Check if the feature already exists
- Review open feature requests
- Ensure it aligns with project goals
- Consider if it would benefit most users

### How to Submit an Enhancement

Create an issue with:

- **Clear title**: Describe the enhancement concisely
- **Problem statement**: What problem does this solve?
- **Proposed solution**: How should it work?
- **Alternatives**: Other solutions you've considered
- **Benefits**: Why is this valuable?
- **Implementation ideas**: (Optional) Technical approach

## Testing

### Running Tests

```bash
# Run all tests
npm test

# Run specific test suite
npm test -- --grep "authentication"

# Run with coverage
npm run test:coverage
```

### Writing Tests

- Write tests for all new features
- Ensure tests are deterministic and isolated
- Use descriptive test names
- Follow the AAA pattern: Arrange, Act, Assert

Example:
```javascript
describe('AutoCommit', () => {
  it('should commit changes when file is modified', async () => {
    // Arrange
    const autoCommit = new AutoCommit();
    const testFile = 'test.txt';
    
    // Act
    await autoCommit.watch(testFile);
    fs.writeFileSync(testFile, 'new content');
    
    // Assert
    const commits = await getLatestCommit();
    expect(commits).toContain('Auto-commit: test.txt modified');
  });
});
```

## Documentation

### Documentation Guidelines

- Write clear, concise explanations
- Include code examples
- Update README when adding features
- Use proper Markdown formatting
- Add diagrams for complex concepts

### Documentation Structure

```
docs/
├── README.md          # Main documentation
├── CONTRIBUTING.md    # This file
├── INSTALLATION.md    # Setup instructions
├── USAGE.md          # How to use the tool
├── API.md            # API reference
└── TROUBLESHOOTING.md # Common issues
```

## Community

### Getting Help

- **Issues**: For bug reports and feature requests
- **Discussions**: For questions and general discussion
- **Discord/Slack**: (If applicable) Real-time chat with community
- **Email**: Contact maintainers directly for sensitive issues

### Stay Updated

- Watch the repository for updates
- Star the repo to show support
- Follow the maintainers on GitHub
- Check the changelog for new releases

## Recognition

Contributors are recognized in several ways:

- Listed in CONTRIBUTORS.md
- Mentioned in release notes
- GitHub contributor badge
- Our eternal gratitude! 💙

## License

By contributing to git-auto-pro, you agree that your contributions will be licensed under the same license as the project (see LICENSE file).

## Questions?

Don't hesitate to ask questions! We're here to help:

- Open an issue with the `question` label
- Reach out to maintainers
- Join our community discussions

**Thank you for contributing to git-auto-pro!** 🚀

Your contributions help make this project better for everyone. We appreciate your time and effort!

---

**Maintainers:**
- [@HimanshuSingh-966](https://github.com/HimanshuSingh-966)

**Last Updated:** January 2026
