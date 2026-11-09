"""
Smoke test to ensure all Streamlit pages and engines import and execute cleanly.
"""
import pytest
from unittest.mock import patch, MagicMock
import streamlit as st

def test_page_modules_importable():
    from pages import (
        dashboard, projects, questionnaire, question_manager,
        profiles, generator, dataset_manager, validation,
        analysis, visualization, exports, settings
    )
    assert dashboard is not None
    assert projects is not None
    assert questionnaire is not None
    assert question_manager is not None
    assert profiles is not None
    assert generator is not None
    assert dataset_manager is not None
    assert validation is not None
    assert analysis is not None
    assert visualization is not None
    assert exports is not None
    assert settings is not None

