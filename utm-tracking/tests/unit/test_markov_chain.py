"""
Unit tests для Markov Chain модели.
"""

import pytest
from utils.markov_chain import MarkovChainPredictor


class TestMarkovChainPredictor:
    """Тесты для MarkovChainPredictor."""

    def test_predict_cvr_exact_match(self, db_session, test_user, sample_pattern_performance):
        """Тест предсказания CVR при точном совпадении паттерна."""

        predictor = MarkovChainPredictor(
            db=db_session,
            user_id=test_user.id,
            product_category="lootbox"
        )

        # Паттерн существует в БД
        result = predictor.predict_cvr(
            hook_type="wait",
            emotion="excitement",
            pacing="fast",
            cta_type="urgency"
        )

        # Проверки
        assert result["prediction_method"] == "exact_match"
        assert result["predicted_cvr"] == 0.12  # 12%
        assert result["predicted_cvr_percent"] == 12.0
        assert result["sample_size"] == 10
        assert result["confidence_score"] > 0
        assert isinstance(result["confidence_interval"], tuple)
        assert result["confidence_interval"][0] < result["predicted_cvr"] < result["confidence_interval"][1]

    def test_predict_cvr_partial_match(self, db_session, test_user, sample_creatives):
        """Тест предсказания CVR при частичном совпадении паттерна."""

        predictor = MarkovChainPredictor(
            db=db_session,
            user_id=test_user.id,
            product_category="lootbox"
        )

        # Паттерн не существует точно, но есть частичные совпадения
        result = predictor.predict_cvr(
            hook_type="wait",
            emotion="excitement",
            pacing="slow",  # Изменили pacing
            cta_type="none"
        )

        # Проверки
        assert result["prediction_method"] in ["partial_match", "bayesian_estimate"]
        assert result["predicted_cvr"] > 0
        assert result["sample_size"] >= 0

    def test_predict_cvr_bayesian_estimate(self, db_session, test_user, sample_creatives):
        """Тест байесовской оценки для неизвестных паттернов."""

        predictor = MarkovChainPredictor(
            db=db_session,
            user_id=test_user.id,
            product_category="lootbox"
        )

        # Совершенно новый паттерн
        result = predictor.predict_cvr(
            hook_type="unknown_hook",
            emotion="unknown_emotion",
            pacing="unknown_pacing",
            cta_type="unknown_cta"
        )

        # Проверки
        assert result["prediction_method"] == "bayesian_estimate"
        assert result["predicted_cvr"] > 0  # Должен использовать prior
        assert result["confidence_score"] < 0.7  # Низкая уверенность

    def test_predict_cvr_no_data(self, db_session, test_user):
        """Тест предсказания когда нет данных вообще."""

        predictor = MarkovChainPredictor(
            db=db_session,
            user_id=test_user.id,
            product_category="new_product"  # Нет данных для этой категории
        )

        result = predictor.predict_cvr(
            hook_type="wait",
            emotion="excitement",
            pacing="fast"
        )

        # Проверки
        assert result["prediction_method"] == "bayesian_estimate"
        assert result["predicted_cvr"] == 0.05  # Базовый CVR
        assert result["sample_size"] == 0
        assert result["confidence_interval"] == (0.02, 0.10)

    def test_update_pattern_performance(self, db_session, test_user, sample_creatives):
        """Тест обновления паттернов производительности из креативов."""

        predictor = MarkovChainPredictor(
            db=db_session,
            user_id=test_user.id,
            product_category="lootbox"
        )

        result = predictor.update_pattern_performance()

        # Проверки
        assert result["pattern_groups_updated"] > 0
        assert result["total_creatives_processed"] == len(sample_creatives)

        # Проверим что паттерны созданы
        from database.models import PatternPerformance

        patterns = db_session.query(PatternPerformance).filter(
            PatternPerformance.user_id == test_user.id,
            PatternPerformance.product_category == "lootbox"
        ).all()

        assert len(patterns) > 0

        # Проверим что метрики корректны
        for pattern in patterns:
            assert pattern.sample_size > 0
            assert pattern.total_clicks > 0
            assert pattern.total_conversions > 0
            assert pattern.avg_cvr > 0

    def test_get_best_patterns(self, db_session, test_user, sample_pattern_performance):
        """Тест получения топ паттернов."""

        predictor = MarkovChainPredictor(
            db=db_session,
            user_id=test_user.id,
            product_category="lootbox"
        )

        # Топ по CVR
        top_cvr = predictor.get_best_patterns(metric="cvr", top_n=5)

        assert len(top_cvr) > 0
        assert top_cvr[0]["avg_cvr"] >= top_cvr[-1]["avg_cvr"]  # Отсортировано по убыванию

        # Топ по ROAS
        top_roas = predictor.get_best_patterns(metric="roas", top_n=5)

        assert len(top_roas) > 0

    def test_confidence_interval_calculation(self, db_session, test_user):
        """Тест расчета доверительного интервала."""

        predictor = MarkovChainPredictor(
            db=db_session,
            user_id=test_user.id,
            product_category="lootbox"
        )

        # Тест 1: Много данных → узкий CI
        ci_lower, ci_upper = predictor._calculate_confidence_interval(
            conversions=1000,
            clicks=10000
        )

        assert 0 <= ci_lower < 0.10 < ci_upper <= 1
        assert (ci_upper - ci_lower) < 0.02  # Узкий интервал

        # Тест 2: Мало данных → широкий CI
        ci_lower, ci_upper = predictor._calculate_confidence_interval(
            conversions=5,
            clicks=50
        )

        assert 0 <= ci_lower < 0.10 < ci_upper <= 1
        assert (ci_upper - ci_lower) > 0.05  # Широкий интервал

        # Тест 3: Нет данных
        ci_lower, ci_upper = predictor._calculate_confidence_interval(
            conversions=0,
            clicks=0
        )

        assert ci_lower == 0.0
        assert ci_upper == 0.0

    def test_min_sample_size_threshold(self, db_session, test_user):
        """Тест порога минимального размера выборки."""

        predictor = MarkovChainPredictor(
            db=db_session,
            user_id=test_user.id,
            product_category="lootbox"
        )

        # Создать паттерн с малым sample size
        from database.models import PatternPerformance

        small_pattern = PatternPerformance(
            user_id=test_user.id,
            product_category="lootbox",
            hook_type="test_hook",
            emotion="test_emotion",
            pacing="test_pacing",
            cta_type="test_cta",
            sample_size=3,  # Меньше min_sample_size (10)
            total_clicks=30,
            total_conversions=3,
            avg_cvr=1000
        )

        db_session.add(small_pattern)
        db_session.commit()

        # Предсказание должно использовать partial_match или bayesian_estimate
        result = predictor.predict_cvr(
            hook_type="test_hook",
            emotion="test_emotion",
            pacing="test_pacing",
            cta_type="test_cta"
        )

        # Не должен использовать exact_match из-за малого sample size
        assert result["prediction_method"] in ["partial_match", "bayesian_estimate"]

    def test_laplace_smoothing(self, db_session, test_user):
        """Тест Laplace smoothing для новых паттернов."""

        predictor = MarkovChainPredictor(
            db=db_session,
            user_id=test_user.id,
            product_category="lootbox"
        )

        # Alpha параметр для сглаживания
        assert predictor.alpha == 1.0

        # Создать минимальные тестовые данные
        from database.models import Creative

        creative = Creative(
            user_id=test_user.id,
            name="Test Creative",
            creative_type="ugc",
            product_category="lootbox",
            hook_type="new_hook",
            emotion="new_emotion",
            pacing="new_pacing",
            clicks=10,
            conversions=1,
            status="testing"
        )

        db_session.add(creative)
        db_session.commit()

        # Предсказание должно использовать smoothing
        result = predictor.predict_cvr(
            hook_type="new_hook",
            emotion="new_emotion",
            pacing="new_pacing"
        )

        # Проверка что предсказание разумно
        assert 0 < result["predicted_cvr"] < 1


class TestPatternAggregation:
    """Тесты агрегации паттернов."""

    def test_pattern_grouping(self, db_session, test_user, sample_creatives):
        """Тест группировки креативов по паттернам."""

        predictor = MarkovChainPredictor(
            db=db_session,
            user_id=test_user.id,
            product_category="lootbox"
        )

        result = predictor.update_pattern_performance()

        # Должно быть 3 группы (wait+excitement+fast, question+curiosity+medium, bold_claim+greed+fast)
        assert result["pattern_groups_updated"] == 3

    def test_pattern_metrics_calculation(self, db_session, test_user):
        """Тест расчета метрик паттернов."""

        from database.models import Creative

        # Создать 5 креативов с одним паттерном
        for i in range(5):
            creative = Creative(
                user_id=test_user.id,
                name=f"Test {i}",
                creative_type="ugc",
                product_category="lootbox",
                hook_type="same_hook",
                emotion="same_emotion",
                pacing="same_pacing",
                cta_type="same_cta",
                impressions=1000,
                clicks=100,
                conversions=10,
                revenue=5000,
                media_spend=1000,
                status="testing"
            )

            db_session.add(creative)

        db_session.commit()

        # Обновить паттерны
        predictor = MarkovChainPredictor(
            db=db_session,
            user_id=test_user.id,
            product_category="lootbox"
        )

        predictor.update_pattern_performance()

        # Проверить агрегированные метрики
        from database.models import PatternPerformance

        pattern = db_session.query(PatternPerformance).filter(
            PatternPerformance.user_id == test_user.id,
            PatternPerformance.hook_type == "same_hook"
        ).first()

        assert pattern is not None
        assert pattern.sample_size == 5
        assert pattern.total_impressions == 5000
        assert pattern.total_clicks == 500
        assert pattern.total_conversions == 50
        assert pattern.avg_cvr == 1000  # 10% CVR
