"""
Unit tests для Creative Analyzer.
"""

import pytest
from unittest.mock import Mock, patch
from utils.creative_analyzer import (
    CreativeAnalyzer,
    analyze_creative_quick,
    analyze_creative_hybrid
)


class TestTextPatternExtraction:
    """Тесты извлечения паттернов из текста."""

    def test_extract_wait_hook(self):
        """Тест определения hook типа 'wait'."""

        analyzer = CreativeAnalyzer()

        result = analyzer.extract_patterns_from_text(
            caption="Wait until the end! 🔥",
            hashtags=["fyp"]
        )

        assert result["hook_type"] == "wait"

    def test_extract_question_hook(self):
        """Тест определения hook типа 'question'."""

        analyzer = CreativeAnalyzer()

        result = analyzer.extract_patterns_from_text(
            caption="Do you know this secret?",
            hashtags=[]
        )

        assert result["hook_type"] == "question"

    def test_extract_bold_claim_hook(self):
        """Тест определения hook типа 'bold_claim'."""

        analyzer = CreativeAnalyzer()

        result = analyzer.extract_patterns_from_text(
            caption="You won't believe what happened!",
            hashtags=[]
        )

        assert result["hook_type"] == "bold_claim"

    def test_extract_curiosity_hook(self):
        """Тест определения hook типа 'curiosity'."""

        analyzer = CreativeAnalyzer()

        result = analyzer.extract_patterns_from_text(
            caption="The secret revealed",
            hashtags=["secret"]
        )

        assert result["hook_type"] == "curiosity"

    def test_extract_urgency_hook(self):
        """Тест определения hook типа 'urgency'."""

        analyzer = CreativeAnalyzer()

        result = analyzer.extract_patterns_from_text(
            caption="Today only! Last chance to win",
            hashtags=[]
        )

        assert result["hook_type"] == "urgency"

    def test_extract_excitement_emotion(self):
        """Тест определения emotion 'excitement'."""

        analyzer = CreativeAnalyzer()

        result = analyzer.extract_patterns_from_text(
            caption="This is insane! 🔥 Amazing results",
            hashtags=[]
        )

        assert result["emotion"] == "excitement"

    def test_extract_fear_emotion(self):
        """Тест определения emotion 'fear'."""

        analyzer = CreativeAnalyzer()

        result = analyzer.extract_patterns_from_text(
            caption="Don't miss out! Before it's gone",
            hashtags=["fomo"]
        )

        assert result["emotion"] == "fear"

    def test_extract_greed_emotion(self):
        """Тест определения emotion 'greed'."""

        analyzer = CreativeAnalyzer()

        result = analyzer.extract_patterns_from_text(
            caption="Win $1000! 💰 Money money money",
            hashtags=[]
        )

        assert result["emotion"] == "greed"

    def test_extract_curiosity_emotion(self):
        """Тест определения emotion 'curiosity'."""

        analyzer = CreativeAnalyzer()

        result = analyzer.extract_patterns_from_text(
            caption="What is this secret?",
            hashtags=[]
        )

        assert result["emotion"] == "curiosity"

    def test_extract_direct_cta(self):
        """Тест определения CTA 'direct'."""

        analyzer = CreativeAnalyzer()

        result = analyzer.extract_patterns_from_text(
            caption="Click here to join now!",
            hashtags=[]
        )

        assert result["cta_type"] == "direct"

    def test_extract_soft_cta(self):
        """Тест определения CTA 'soft'."""

        analyzer = CreativeAnalyzer()

        result = analyzer.extract_patterns_from_text(
            caption="Learn more about this",
            hashtags=[]
        )

        assert result["cta_type"] == "soft"

    def test_extract_urgency_cta(self):
        """Тест определения CTA 'urgency'."""

        analyzer = CreativeAnalyzer()

        result = analyzer.extract_patterns_from_text(
            caption="Limited time offer!",
            hashtags=[]
        )

        assert result["cta_type"] == "urgency"

    def test_extract_scarcity_cta(self):
        """Тест определения CTA 'scarcity'."""

        analyzer = CreativeAnalyzer()

        result = analyzer.extract_patterns_from_text(
            caption="Only 10 spots left! Exclusive offer",
            hashtags=[]
        )

        assert result["cta_type"] == "scarcity"

    def test_hashtags_included_in_analysis(self):
        """Тест что хештеги учитываются в анализе."""

        analyzer = CreativeAnalyzer()

        result = analyzer.extract_patterns_from_text(
            caption="Check this out",
            hashtags=["money", "win", "profit"]
        )

        # Должен определить greed из хештегов
        assert result["emotion"] == "greed"

    def test_confidence_lower_for_text_only(self):
        """Тест что confidence ниже для текст-only анализа."""

        analyzer = CreativeAnalyzer()

        result = analyzer.extract_patterns_from_text(
            caption="Wait until the end!",
            hashtags=[]
        )

        # Text-only анализ должен иметь низкую уверенность
        assert result["confidence"] == 0.5
        assert "text only" in result["reasoning"].lower()


class TestAnalyzerFallback:
    """Тесты fallback механизмов."""

    def test_fallback_without_api_key(self, monkeypatch):
        """Тест fallback когда нет API ключа."""

        # Убрать API ключ
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

        analyzer = CreativeAnalyzer()

        # Должен использовать fallback
        result = analyzer._fallback_analysis()

        assert result["hook_type"] == "unknown"
        assert result["emotion"] == "unknown"
        assert result["pacing"] == "medium"
        assert result["confidence"] == 0.0
        assert "not available" in result["reasoning"].lower()

    def test_analyze_video_without_frames(self, monkeypatch):
        """Тест анализа видео без извлечения фреймов."""

        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

        analyzer = CreativeAnalyzer()

        # Должен упасть в fallback
        result = analyzer._analyze_with_claude([])

        assert result["hook_type"] == "unknown"
        assert result["confidence"] == 0.0


class TestSimilarity:
    """Тесты similarity функций."""

    def test_cosine_similarity(self):
        """Тест расчета cosine similarity."""

        analyzer = CreativeAnalyzer()

        # Идентичные векторы
        vec1 = [1.0, 0.5, 0.3]
        vec2 = [1.0, 0.5, 0.3]

        similarity = analyzer.calculate_similarity(vec1, vec2)
        assert similarity == pytest.approx(1.0, abs=0.01)

        # Ортогональные векторы
        vec3 = [1.0, 0.0, 0.0]
        vec4 = [0.0, 1.0, 0.0]

        similarity_ortho = analyzer.calculate_similarity(vec3, vec4)
        assert similarity_ortho == pytest.approx(0.0, abs=0.01)

        # Похожие векторы
        vec5 = [1.0, 0.5, 0.2]
        vec6 = [0.9, 0.6, 0.3]

        similarity_similar = analyzer.calculate_similarity(vec5, vec6)
        assert 0.9 < similarity_similar < 1.0


class TestHelperFunctions:
    """Тесты вспомогательных функций."""

    def test_analyze_creative_quick_with_caption(self):
        """Тест быстрого анализа с caption."""

        result = analyze_creative_quick(
            caption="Wait until the end! 🔥",
            hashtags=["fyp", "viral"]
        )

        assert result["hook_type"] == "wait"
        assert result["emotion"] == "excitement"

    def test_analyze_creative_quick_no_input(self):
        """Тест быстрого анализа без входных данных."""

        with pytest.raises(ValueError, match="Must provide either video or caption"):
            analyze_creative_quick()

    @patch('utils.creative_analyzer.VideoAnalyzer')
    def test_analyze_creative_hybrid(self, mock_video_analyzer):
        """Тест гибридного анализа."""

        # Mock VideoAnalyzer
        mock_analyzer_instance = Mock()
        mock_analyzer_instance.analyze.return_value = {
            "pacing": "fast",
            "has_face": True,
            "num_scenes": 8,
            "audio_energy": "high",
            "has_voiceover": True,
            "duration_seconds": 15,
            "tempo_bpm": 128,
            "scenes_per_second": 0.5
        }

        mock_video_analyzer.return_value = mock_analyzer_instance

        result = analyze_creative_hybrid(
            video_path="/tmp/test_video.mp4",
            caption="Wait until the end! 🔥",
            hashtags=["fyp"]
        )

        # Проверки
        assert result["hook_type"] == "wait"  # Из caption
        assert result["emotion"] == "excitement"  # Из caption
        assert result["pacing"] == "fast"  # Из видео
        assert result["has_face"] is True  # Из видео
        assert result["has_voiceover"] is True  # Из аудио
        assert result["confidence"] == 0.75  # Гибридный анализ
        assert "hybrid" in result["analysis_method"]


class TestEdgeCases:
    """Тесты граничных случаев."""

    def test_empty_caption(self):
        """Тест с пустым caption."""

        analyzer = CreativeAnalyzer()

        result = analyzer.extract_patterns_from_text(
            caption="",
            hashtags=[]
        )

        # Должен вернуть дефолтные значения
        assert result["hook_type"] in ["other", "unknown"]
        assert result["cta_type"] in ["none", "unknown"]

    def test_only_emoji_caption(self):
        """Тест с caption из только эмодзи."""

        analyzer = CreativeAnalyzer()

        result = analyzer.extract_patterns_from_text(
            caption="🔥💰⚡",
            hashtags=[]
        )

        # Должен обработать эмодзи
        # 🔥 → excitement, 💰 → greed
        assert result["emotion"] in ["excitement", "greed"]

    def test_mixed_signals(self):
        """Тест с противоречивыми сигналами."""

        analyzer = CreativeAnalyzer()

        result = analyzer.extract_patterns_from_text(
            caption="Wait for it... Learn more now! Click here",
            hashtags=[]
        )

        # Должен выбрать один из сигналов
        # Первый hook обычно побеждает
        assert result["hook_type"] == "wait"
        # Первый CTA
        assert result["cta_type"] in ["soft", "direct"]

    def test_very_long_caption(self):
        """Тест с очень длинным caption."""

        analyzer = CreativeAnalyzer()

        long_caption = "Wait " * 1000  # Очень длинный текст

        result = analyzer.extract_patterns_from_text(
            caption=long_caption,
            hashtags=[]
        )

        # Должен корректно обработать
        assert result["hook_type"] == "wait"

    def test_special_characters(self):
        """Тест со специальными символами."""

        analyzer = CreativeAnalyzer()

        result = analyzer.extract_patterns_from_text(
            caption="Wait!!! #@$%^&* Don't miss!!!",
            hashtags=[]
        )

        # Должен игнорировать спецсимволы
        assert result["hook_type"] == "wait"

    def test_multiple_languages(self):
        """Тест с текстом на разных языках."""

        analyzer = CreativeAnalyzer()

        # Английский + эмодзи
        result = analyzer.extract_patterns_from_text(
            caption="Подожди до конца! Wait until the end!",
            hashtags=[]
        )

        # Должен найти английские паттерны
        assert result["hook_type"] == "wait"

    def test_clip_embedding_not_implemented(self):
        """Тест CLIP embedding когда не реализовано."""

        analyzer = CreativeAnalyzer()

        embedding = analyzer.get_clip_embedding("/tmp/test_image.jpg")

        # Должен вернуть None
        assert embedding is None
