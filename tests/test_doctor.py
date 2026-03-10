"""Tests for doctor diagnostics."""

import pytest
from unittest.mock import patch, MagicMock
from git_auto_pro.commands.doctor import run_diagnostics


class TestDoctor:
    """Test doctor command."""
    
    @patch('git_auto_pro.commands.doctor.git')
    @patch('git_auto_pro.commands.doctor.shutil')
    def test_doctor_runs_without_crash(self, mock_shutil, mock_git):
        """Test that doctor runs without crashing."""
        mock_shutil.which.return_value = "/usr/bin/git"
        
        # Mock repo
        mock_repo = MagicMock()
        mock_repo.remotes = []
        mock_repo.active_branch = "main"
        mock_repo.untracked_files = []
        mock_repo.index.diff.return_value = []
        mock_git.Repo.return_value = mock_repo
        mock_git.InvalidGitRepositoryError = Exception
        
        with patch('git_auto_pro.commands.doctor.load_config', return_value={"default_branch": "main", "safe_mode": False}), \
             patch('git_auto_pro.github.get_stored_token', return_value=None), \
             patch('git_auto_pro.github.check_api_connectivity', return_value=True), \
             patch('git_auto_pro.commands.doctor.subprocess') as mock_sub:
            mock_sub.run.return_value = MagicMock(stdout="git version 2.43.0")
            # Should not raise
            run_diagnostics()
    
    @patch('git_auto_pro.commands.doctor.git')
    @patch('git_auto_pro.commands.doctor.shutil')
    def test_doctor_no_git(self, mock_shutil, mock_git):
        """Test doctor when git is not installed."""
        mock_shutil.which.return_value = None
        mock_git.Repo.side_effect = Exception("Not a repo")
        mock_git.InvalidGitRepositoryError = Exception
        
        with patch('git_auto_pro.commands.doctor.load_config', return_value={"safe_mode": False}), \
             patch('git_auto_pro.github.get_stored_token', return_value=None), \
             patch('git_auto_pro.github.check_api_connectivity', return_value=False):
            # Should not raise
            run_diagnostics()
    
    @patch('git_auto_pro.commands.doctor.git')
    @patch('git_auto_pro.commands.doctor.shutil')
    def test_doctor_with_token(self, mock_shutil, mock_git):
        """Test doctor when GitHub token is configured."""
        mock_shutil.which.return_value = "/usr/bin/git"
        mock_git.InvalidGitRepositoryError = Exception
        
        mock_repo = MagicMock()
        # Use MagicMock for remotes so .origin.url works
        mock_remotes = MagicMock()
        mock_remotes.origin.url = "https://github.com/user/repo.git"
        mock_remotes.__bool__ = lambda self: True
        mock_repo.remotes = mock_remotes
        mock_repo.active_branch = "main"
        mock_repo.untracked_files = ["file1.txt"]
        mock_repo.index.diff.return_value = []
        mock_git.Repo.return_value = mock_repo
        
        with patch('git_auto_pro.commands.doctor.load_config', return_value={"default_branch": "main", "safe_mode": True}), \
             patch('git_auto_pro.github.get_stored_token', return_value="test_token"), \
             patch('git_auto_pro.github.check_api_connectivity', return_value=True), \
             patch('git_auto_pro.commands.doctor.subprocess') as mock_sub, \
             patch('git_auto_pro.commands.doctor.requests') as mock_requests:
            mock_sub.run.return_value = MagicMock(stdout="git version 2.43.0")
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"login": "testuser"}
            mock_requests.get.return_value = mock_response
            
            run_diagnostics()
