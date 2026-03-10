"""Tests for release command."""

import pytest
import git
from pathlib import Path
from unittest.mock import patch, MagicMock
from git_auto_pro.commands.release import (
    _bump_version,
    _read_current_version,
    _generate_changelog,
    _update_version_files,
)


class TestVersionBumping:
    """Test version bumping logic."""
    
    def test_bump_patch(self):
        assert _bump_version("1.0.0", "patch") == "1.0.1"
    
    def test_bump_minor(self):
        assert _bump_version("1.0.0", "minor") == "1.1.0"
    
    def test_bump_major(self):
        assert _bump_version("1.0.0", "major") == "2.0.0"
    
    def test_bump_patch_from_nonzero(self):
        assert _bump_version("2.3.4", "patch") == "2.3.5"
    
    def test_bump_minor_resets_patch(self):
        assert _bump_version("1.2.3", "minor") == "1.3.0"
    
    def test_bump_major_resets_all(self):
        assert _bump_version("1.2.3", "major") == "2.0.0"
    
    def test_invalid_version_format(self):
        with pytest.raises(ValueError):
            _bump_version("invalid", "patch")
    
    def test_invalid_bump_type(self):
        with pytest.raises(ValueError):
            _bump_version("1.0.0", "invalid")


class TestVersionReading:
    """Test reading version from files."""
    
    def test_read_from_pyproject(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text('[project]\nname = "test"\nversion = "1.2.3"\n')
        
        version = _read_current_version()
        assert version == "1.2.3"
    
    def test_read_fallback_to_init(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        
        # No pyproject.toml, but __init__.py exists
        init_dir = tmp_path / "git_auto_pro"
        init_dir.mkdir()
        init_file = init_dir / "__init__.py"
        init_file.write_text('__version__ = "4.5.6"\n')
        
        version = _read_current_version()
        assert version == "4.5.6"


class TestChangelogGeneration:
    """Test changelog generation from commits."""
    
    def test_generate_changelog(self, temp_repo):
        """Test changelog with conventional commits."""
        # Create some commits
        test_file = Path(temp_repo.working_dir) / "test.txt"
        
        test_file.write_text("v1")
        temp_repo.index.add(["test.txt"])
        temp_repo.index.commit("feat: add new feature")
        
        test_file.write_text("v2")
        temp_repo.index.add(["test.txt"])
        temp_repo.index.commit("fix: resolve bug")
        
        test_file.write_text("v3")
        temp_repo.index.add(["test.txt"])
        temp_repo.index.commit("docs: update readme")
        
        changelog = _generate_changelog(temp_repo)
        
        assert "Features" in changelog
        assert "Bug Fixes" in changelog
        assert "Documentation" in changelog
    
    def test_generate_changelog_no_commits(self, temp_repo):
        """Test changelog with no commits."""
        changelog = _generate_changelog(temp_repo)
        assert changelog  # Should return something, not crash


class TestVersionFileUpdate:
    """Test updating version in files."""
    
    def test_update_pyproject(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text('[project]\nversion = "1.0.0"\n')
        
        _update_version_files("2.0.0")
        
        content = pyproject.read_text()
        assert '2.0.0' in content
    
    def test_update_init_file(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        
        # Create pyproject
        pyproject = tmp_path / "pyproject.toml"
        pyproject.write_text('[project]\nversion = "1.0.0"\n')
        
        # Create __init__.py
        init_dir = tmp_path / "git_auto_pro"
        init_dir.mkdir()
        init_file = init_dir / "__init__.py"
        init_file.write_text('__version__ = "1.0.0"\n')
        
        _update_version_files("2.0.0")
        
        content = init_file.read_text()
        assert '2.0.0' in content
