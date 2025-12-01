"""
Pytest fixtures для тестов.
"""

import pytest
import os
import sys
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import Mock

# Добавить корневую папку в PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from database.base import Base
from database.models import User, Creative, PatternPerformance, TrafficSource


@pytest.fixture(scope="session")
def engine():
    """Создать in-memory SQLite для тестов."""
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    return engine


@pytest.fixture(scope="function")
def db_session(engine):
    """Создать сессию БД для каждого теста."""
    Session = sessionmaker(bind=engine)
    session = Session()

    yield session

    session.rollback()
    session.close()


@pytest.fixture
def test_user(db_session):
    """Создать тестового пользователя."""
    user = User(
        id="test-user-123",
        username="testuser",
        telegram_id=123456789,
        created_at=datetime.utcnow()
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def sample_creatives(db_session, test_user):
    """
    Создать набор креативов для тестирования.

    Включает разные паттерны:
    - 3 креатива с hook="wait", emotion="excitement", pacing="fast" (CVR 12%)
    - 2 креатива с hook="question", emotion="curiosity", pacing="medium" (CVR 8%)
    - 1 креатив с hook="bold_claim", emotion="greed", pacing="fast" (CVR 15%)
    """

    creatives = []

    # Группа 1: wait + excitement + fast (хороший CVR)
    for i in range(3):
        creative = Creative(
            user_id=test_user.id,
            name=f"Wait Creative {i+1}",
            creative_type="ugc",
            product_category="lootbox",
            hook_type="wait",
            emotion="excitement",
            pacing="fast",
            cta_type="urgency",
            impressions=1000,
            clicks=100,
            conversions=12,
            revenue=6000,  # $60 revenue
            media_spend=1000,  # $10 spent
            status="testing",
            created_at=datetime.utcnow() - timedelta(days=7)
        )

        # Рассчитать метрики
        creative.ctr = int((creative.clicks / creative.impressions) * 10000)  # 10%
        creative.cvr = int((creative.conversions / creative.clicks) * 10000)  # 12%
        creative.roas = int((creative.revenue / creative.media_spend) * 100)  # 6x

        db_session.add(creative)
        creatives.append(creative)

    # Группа 2: question + curiosity + medium (средний CVR)
    for i in range(2):
        creative = Creative(
            user_id=test_user.id,
            name=f"Question Creative {i+1}",
            creative_type="ugc",
            product_category="lootbox",
            hook_type="question",
            emotion="curiosity",
            pacing="medium",
            cta_type="soft",
            impressions=1000,
            clicks=80,
            conversions=6,
            revenue=3000,  # $30
            media_spend=1000,  # $10
            status="testing",
            created_at=datetime.utcnow() - timedelta(days=7)
        )

        creative.ctr = int((creative.clicks / creative.impressions) * 10000)
        creative.cvr = int((creative.conversions / creative.clicks) * 10000)  # 7.5%
        creative.roas = int((creative.revenue / creative.media_spend) * 100)

        db_session.add(creative)
        creatives.append(creative)

    # Группа 3: bold_claim + greed + fast (лучший CVR)
    creative = Creative(
        user_id=test_user.id,
        name="Bold Claim Creative",
        creative_type="ugc",
        product_category="lootbox",
        hook_type="bold_claim",
        emotion="greed",
        pacing="fast",
        cta_type="urgency",
        impressions=1000,
        clicks=120,
        conversions=18,
        revenue=9000,  # $90
        media_spend=1000,  # $10
        status="testing",
        created_at=datetime.utcnow() - timedelta(days=7)
    )

    creative.ctr = int((creative.clicks / creative.impressions) * 10000)
    creative.cvr = int((creative.conversions / creative.clicks) * 10000)  # 15%
    creative.roas = int((creative.revenue / creative.media_spend) * 100)

    db_session.add(creative)
    creatives.append(creative)

    db_session.commit()

    for creative in creatives:
        db_session.refresh(creative)

    return creatives


@pytest.fixture
def sample_pattern_performance(db_session, test_user):
    """Создать паттерны производительности."""

    patterns = [
        PatternPerformance(
            user_id=test_user.id,
            product_category="lootbox",
            hook_type="wait",
            emotion="excitement",
            pacing="fast",
            cta_type="urgency",
            sample_size=10,
            total_impressions=10000,
            total_clicks=1000,
            total_conversions=120,
            total_revenue=60000,
            avg_ctr=1000,  # 10%
            avg_cvr=1200,  # 12%
            avg_roas=600,  # 6x
            confidence_interval_lower=900,  # 9%
            confidence_interval_upper=1500,  # 15%
            transition_probability=1200  # 12%
        ),
        PatternPerformance(
            user_id=test_user.id,
            product_category="lootbox",
            hook_type="question",
            emotion="curiosity",
            pacing="medium",
            cta_type="soft",
            sample_size=5,
            total_impressions=5000,
            total_clicks=400,
            total_conversions=30,
            total_revenue=15000,
            avg_ctr=800,  # 8%
            avg_cvr=750,  # 7.5%
            avg_roas=300,  # 3x
            confidence_interval_lower=500,
            confidence_interval_upper=1000,
            transition_probability=750
        )
    ]

    for pattern in patterns:
        db_session.add(pattern)

    db_session.commit()

    return patterns


@pytest.fixture
def sample_traffic_sources(db_session, test_user):
    """Создать трафик для тестов."""

    sources = []

    for i in range(5):
        source = TrafficSource(
            user_id=test_user.id,
            utm_source="tiktok",
            utm_medium="video",
            utm_campaign=f"test_campaign_{i}",
            utm_content=f"creative_{i}",
            clicks=100 + i * 10,
            conversions=10 + i * 2,
            revenue=(10 + i * 2) * 500,  # $5 per conversion
            first_click=datetime.utcnow() - timedelta(days=i),
            last_click=datetime.utcnow(),
            device_type="mobile"
        )

        db_session.add(source)
        sources.append(source)

    db_session.commit()

    return sources


@pytest.fixture
def mock_anthropic_client():
    """Mock Anthropic API client."""

    mock = Mock()

    # Mock response
    mock_response = Mock()
    mock_response.content = [Mock(text='''{
        "hook_type": "wait",
        "emotion": "excitement",
        "pacing": "fast",
        "cta_type": "urgency",
        "has_text_overlay": true,
        "has_voiceover": true,
        "features": {
            "has_face": true,
            "num_scenes": 3,
            "dominant_colors": ["red", "gold"],
            "visual_complexity": "high",
            "audio_energy": "high"
        },
        "confidence": 0.85,
        "reasoning": "Test analysis"
    }''')]

    mock.messages.create.return_value = mock_response

    return mock
