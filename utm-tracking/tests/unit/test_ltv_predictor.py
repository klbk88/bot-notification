"""
Unit tests для LTV Predictor.
"""

import pytest
from utils.ltv_predictor import LTVPredictor, LTV_BENCHMARKS


class TestLTVPredictor:
    """Тесты для LTVPredictor."""

    def test_predict_ltv_language_learning(self, db_session):
        """Тест предсказания LTV для языкового обучения."""

        predictor = LTVPredictor(db=db_session)

        result = predictor.predict_ltv(
            day_7_sessions=10,
            day_7_time_in_app=60,  # 60 минут за 7 дней
            features_used=8,
            category="language_learning"
        )

        # Проверки
        assert "predicted_ltv_d30" in result
        assert "predicted_ltv_d90" in result
        assert "predicted_ltv_d180" in result
        assert "estimated_retention" in result
        assert "confidence" in result
        assert "user_segment" in result

        # LTV должен расти со временем
        assert result["predicted_ltv_d30"] < result["predicted_ltv_d90"]
        assert result["predicted_ltv_d90"] < result["predicted_ltv_d180"]

        # Проверка retention
        retention = result["estimated_retention"]
        assert retention["day_30"] > retention["day_90"] > retention["day_180"]

    def test_predict_ltv_coding(self, db_session):
        """Тест предсказания LTV для coding категории."""

        predictor = LTVPredictor(db=db_session)

        result = predictor.predict_ltv(
            day_7_sessions=12,
            day_7_time_in_app=90,
            features_used=10,
            category="coding"
        )

        # Coding должен иметь более высокий LTV чем language learning
        result_lang = predictor.predict_ltv(
            day_7_sessions=12,
            day_7_time_in_app=90,
            features_used=10,
            category="language_learning"
        )

        assert result["predicted_ltv_d180"] > result_lang["predicted_ltv_d180"]

    def test_predict_ltv_fitness(self, db_session):
        """Тест предсказания LTV для fitness категории."""

        predictor = LTVPredictor(db=db_session)

        result = predictor.predict_ltv(
            day_7_sessions=8,
            day_7_time_in_app=45,
            features_used=6,
            category="fitness"
        )

        # Fitness должен иметь более низкий LTV чем coding
        result_coding = predictor.predict_ltv(
            day_7_sessions=8,
            day_7_time_in_app=45,
            features_used=6,
            category="coding"
        )

        assert result["predicted_ltv_d180"] < result_coding["predicted_ltv_d180"]

    def test_user_segmentation_power_user(self, db_session):
        """Тест сегментации power user."""

        predictor = LTVPredictor(db=db_session)

        result = predictor.predict_ltv(
            day_7_sessions=15,  # Много сессий
            day_7_time_in_app=120,  # Много времени
            features_used=12,
            category="language_learning"
        )

        assert result["user_segment"] == "power_user"
        assert result["confidence"] > 0.5

    def test_user_segmentation_active_user(self, db_session):
        """Тест сегментации active user."""

        predictor = LTVPredictor(db=db_session)

        result = predictor.predict_ltv(
            day_7_sessions=7,  # Средние сессии
            day_7_time_in_app=50,  # Среднее время
            features_used=6,
            category="language_learning"
        )

        assert result["user_segment"] == "active_user"

    def test_user_segmentation_casual_user(self, db_session):
        """Тест сегментации casual user."""

        predictor = LTVPredictor(db=db_session)

        result = predictor.predict_ltv(
            day_7_sessions=3,  # Мало сессий
            day_7_time_in_app=20,  # Мало времени
            features_used=3,
            category="language_learning"
        )

        assert result["user_segment"] == "casual_user"

    def test_retention_estimation(self, db_session):
        """Тест оценки retention."""

        predictor = LTVPredictor(db=db_session)

        # Высокая активность → высокий retention
        high_sessions = predictor._estimate_retention(
            day_7_sessions=12,
            target_day=180
        )

        # Низкая активность → низкий retention
        low_sessions = predictor._estimate_retention(
            day_7_sessions=3,
            target_day=180
        )

        assert high_sessions > low_sessions

    def test_retention_decay_over_time(self, db_session):
        """Тест decay retention со временем."""

        predictor = LTVPredictor(db=db_session)

        retention_30 = predictor._estimate_retention(10, 30)
        retention_90 = predictor._estimate_retention(10, 90)
        retention_180 = predictor._estimate_retention(10, 180)

        # Retention должен падать со временем
        assert retention_30 > retention_90 > retention_180

    def test_confidence_calculation(self, db_session):
        """Тест расчета confidence."""

        predictor = LTVPredictor(db=db_session)

        # Много данных → высокая уверенность
        high_conf = predictor._calculate_confidence(
            sessions=10,
            time=80,
            features=8
        )

        # Мало данных → низкая уверенность
        low_conf = predictor._calculate_confidence(
            sessions=2,
            time=15,
            features=2
        )

        assert high_conf > low_conf
        assert 0 <= low_conf <= 1
        assert 0 <= high_conf <= 1

    def test_roas_calculation(self, db_session):
        """Тест расчета ROAS."""

        predictor = LTVPredictor(db=db_session)

        # Profitable case
        roas_profitable = predictor._calculate_roas(
            media_spend=1000,  # $10
            conversions=10,
            ltv=50.0  # $50 LTV
        )

        assert roas_profitable["roas"] > 1.5
        assert roas_profitable["status"] == "profitable"
        assert roas_profitable["total_ltv"] == 500.0  # 10 * $50

        # Break even case
        roas_breakeven = predictor._calculate_roas(
            media_spend=1000,  # $10
            conversions=10,
            ltv=10.0  # $10 LTV
        )

        assert 0.8 <= roas_breakeven["roas"] <= 1.2
        assert roas_breakeven["status"] in ["break_even", "losing"]

        # Losing case
        roas_losing = predictor._calculate_roas(
            media_spend=1000,  # $10
            conversions=10,
            ltv=5.0  # $5 LTV
        )

        assert roas_losing["roas"] < 0.8
        assert roas_losing["status"] == "losing"

    def test_roas_no_conversions(self, db_session):
        """Тест ROAS при отсутствии конверсий."""

        predictor = LTVPredictor(db=db_session)

        roas = predictor._calculate_roas(
            media_spend=1000,
            conversions=0,
            ltv=50.0
        )

        assert roas["roas"] == 0
        assert roas["status"] == "no_conversions"

    def test_predict_creative_ltv(self, db_session, test_user, sample_creatives):
        """Тест предсказания LTV для креатива."""

        predictor = LTVPredictor(db=db_session)

        creative = sample_creatives[0]

        # Mock user behavior cohort
        user_cohort = {
            "avg_sessions_d7": 8,
            "avg_time_in_app_d7": 55,
            "avg_features_used_d7": 7
        }

        result = predictor.predict_creative_ltv(
            creative_id=str(creative.id),
            user_behavior_cohort=user_cohort
        )

        # Проверки
        assert "creative_id" in result
        assert "creative_name" in result
        assert "ltv_prediction" in result
        assert "roas_projection" in result

        # Проверка LTV prediction
        ltv_pred = result["ltv_prediction"]
        assert "predicted_ltv_d180" in ltv_pred
        assert "user_segment" in ltv_pred

    def test_predict_creative_ltv_not_found(self, db_session):
        """Тест с несуществующим креативом."""

        predictor = LTVPredictor(db=db_session)

        result = predictor.predict_creative_ltv(
            creative_id="nonexistent-id",
            user_behavior_cohort={}
        )

        assert result == {}

    def test_benchmarks_exist(self):
        """Тест наличия бенчмарков."""

        assert "language_learning" in LTV_BENCHMARKS
        assert "coding" in LTV_BENCHMARKS
        assert "fitness" in LTV_BENCHMARKS

        # Проверка структуры
        for category, benchmarks in LTV_BENCHMARKS.items():
            assert "avg_ltv_d180" in benchmarks
            assert "top_10_percent" in benchmarks
            assert "power_user_ltv" in benchmarks

            # Power user LTV должен быть выше топ 10%
            assert benchmarks["power_user_ltv"] > benchmarks["top_10_percent"]
            # Топ 10% должен быть выше среднего
            assert benchmarks["top_10_percent"] > benchmarks["avg_ltv_d180"]


class TestEdgeCases:
    """Тесты граничных случаев."""

    def test_zero_sessions(self, db_session):
        """Тест с нулевыми сессиями."""

        predictor = LTVPredictor(db=db_session)

        result = predictor.predict_ltv(
            day_7_sessions=0,
            day_7_time_in_app=0,
            features_used=0,
            category="language_learning"
        )

        # Должен вернуть минимальный LTV
        assert result["predicted_ltv_d180"] > 0  # Все равно есть base_ltv
        assert result["user_segment"] == "casual_user"
        assert result["confidence"] == 0.5  # Базовая уверенность

    def test_extremely_high_engagement(self, db_session):
        """Тест с экстремально высокой активностью."""

        predictor = LTVPredictor(db=db_session)

        result = predictor.predict_ltv(
            day_7_sessions=50,  # Очень много
            day_7_time_in_app=500,  # 500 минут
            features_used=30,
            category="coding"
        )

        # Должен быть очень высокий LTV
        assert result["predicted_ltv_d180"] > 500
        assert result["user_segment"] == "power_user"
        assert result["confidence"] == 1.0  # Максимальная уверенность

    def test_retention_clamps(self, db_session):
        """Тест ограничения retention в пределах 5-60%."""

        predictor = LTVPredictor(db=db_session)

        # Очень высокие сессии
        retention_high = predictor._estimate_retention(
            day_7_sessions=100,
            target_day=30
        )

        # Очень низкие сессии
        retention_low = predictor._estimate_retention(
            day_7_sessions=1,
            target_day=180
        )

        # Проверка границ
        assert 0.05 <= retention_high <= 0.6
        assert 0.05 <= retention_low <= 0.6

    def test_unknown_category(self, db_session):
        """Тест с неизвестной категорией."""

        predictor = LTVPredictor(db=db_session)

        result = predictor.predict_ltv(
            day_7_sessions=8,
            day_7_time_in_app=50,
            features_used=7,
            category="unknown_category"
        )

        # Должен использовать дефолтные коэффициенты (language_learning)
        result_default = predictor.predict_ltv(
            day_7_sessions=8,
            day_7_time_in_app=50,
            features_used=7,
            category="language_learning"
        )

        assert result["predicted_ltv_d180"] == result_default["predicted_ltv_d180"]


class TestLTVComponents:
    """Тесты компонентов LTV модели."""

    def test_base_ltv_component(self, db_session):
        """Тест базового компонента LTV."""

        predictor = LTVPredictor(db=db_session)

        # Даже с нулевыми метриками есть base_ltv
        result = predictor.predict_ltv(
            day_7_sessions=0,
            day_7_time_in_app=0,
            features_used=0,
            category="coding"
        )

        # Базовый LTV для coding = 40
        assert result["predicted_ltv_d180"] >= 40

    def test_session_weight_impact(self, db_session):
        """Тест влияния сессий на LTV."""

        predictor = LTVPredictor(db=db_session)

        result_low = predictor.predict_ltv(
            day_7_sessions=2,
            day_7_time_in_app=30,
            features_used=5,
            category="language_learning"
        )

        result_high = predictor.predict_ltv(
            day_7_sessions=15,
            day_7_time_in_app=30,
            features_used=5,
            category="language_learning"
        )

        # Больше сессий → выше LTV
        assert result_high["predicted_ltv_d180"] > result_low["predicted_ltv_d180"]

    def test_time_weight_impact(self, db_session):
        """Тест влияния времени на LTV."""

        predictor = LTVPredictor(db=db_session)

        result_low = predictor.predict_ltv(
            day_7_sessions=8,
            day_7_time_in_app=20,
            features_used=5,
            category="language_learning"
        )

        result_high = predictor.predict_ltv(
            day_7_sessions=8,
            day_7_time_in_app=100,
            features_used=5,
            category="language_learning"
        )

        # Больше времени → выше LTV
        assert result_high["predicted_ltv_d180"] > result_low["predicted_ltv_d180"]

    def test_feature_weight_impact(self, db_session):
        """Тест влияния использования фич на LTV."""

        predictor = LTVPredictor(db=db_session)

        result_low = predictor.predict_ltv(
            day_7_sessions=8,
            day_7_time_in_app=50,
            features_used=2,
            category="language_learning"
        )

        result_high = predictor.predict_ltv(
            day_7_sessions=8,
            day_7_time_in_app=50,
            features_used=15,
            category="language_learning"
        )

        # Больше фич → выше LTV
        assert result_high["predicted_ltv_d180"] > result_low["predicted_ltv_d180"]
