"""Tests for safe commit flow."""

import pytest
import git
from pathlib import Path
from unittest.mock import patch, MagicMock
from git_auto_pro.commands.safe_flow import safe_push


class TestSafePush:
    """Test safe push flow."""
    
    def test_safe_push_creates_test_branch(self, temp_repo, monkeypatch):
        """Test that safe push creates a test branch."""
        monkeypatch.chdir(temp_repo.working_dir)
        
        # Create initial commit on main
        test_file = Path(temp_repo.working_dir) / "initial.txt"
        test_file.write_text("initial")
        temp_repo.index.add(["initial.txt"])
        temp_repo.index.commit("Initial commit")
        
        # Rename branch to main
        temp_repo.active_branch.rename("main")
        
        # Create a change
        change_file = Path(temp_repo.working_dir) / "change.txt"
        change_file.write_text("change")
        
        # Mock the PR creation to avoid real API calls
        with patch('git_auto_pro.commands.safe_flow.create_pull_request') as mock_pr, \
             patch('git_auto_pro.commands.safe_flow.load_config', return_value={
                 "test_branch_prefix": "test",
                 "pr_base_branch": "main",
                 "auto_create_pr": False,
             }):
            safe_push("Test safe push")
        
        # Should have created a test branch
        branches = [str(b) for b in temp_repo.branches]
        assert any(b.startswith("test/") for b in branches)
    
    def test_safe_push_nothing_staged(self, temp_repo, monkeypatch):
        """Test safe push with nothing to commit."""
        monkeypatch.chdir(temp_repo.working_dir)
        
        # Create initial commit
        test_file = Path(temp_repo.working_dir) / "initial.txt"
        test_file.write_text("initial")
        temp_repo.index.add(["initial.txt"])
        temp_repo.index.commit("Initial commit")
        temp_repo.active_branch.rename("main")
        
        with patch('git_auto_pro.commands.safe_flow.load_config', return_value={
                "test_branch_prefix": "test",
                "pr_base_branch": "main",
                "auto_create_pr": False,
             }):
            # Should not crash — nothing to commit
            safe_push("Empty push")
    
    def test_safe_push_custom_feature_name(self, temp_repo, monkeypatch):
        """Test safe push with custom feature name."""
        monkeypatch.chdir(temp_repo.working_dir)
        
        # Setup
        test_file = Path(temp_repo.working_dir) / "initial.txt"
        test_file.write_text("initial")
        temp_repo.index.add(["initial.txt"])
        temp_repo.index.commit("Initial commit")
        temp_repo.active_branch.rename("main")
        
        # Create change
        change_file = Path(temp_repo.working_dir) / "feature.txt"
        change_file.write_text("feature")
        
        with patch('git_auto_pro.commands.safe_flow.create_pull_request'), \
             patch('git_auto_pro.commands.safe_flow.load_config', return_value={
                 "test_branch_prefix": "test",
                 "pr_base_branch": "main",
                 "auto_create_pr": False,
             }):
            safe_push("Add feature", feature_name="login-page")
        
        branches = [str(b) for b in temp_repo.branches]
        assert "test/login-page" in branches
    
    def test_safe_push_not_a_repo(self, tmp_path, monkeypatch):
        """Test safe push outside a git repo."""
        monkeypatch.chdir(tmp_path)
        
        # Should not crash
        safe_push("Test")
