"""
Unit tests для Early Signals Analyzer.
"""

import pytest
from datetime import datetime, timedelta
from utils.early_signals import EarlySignalsAnalyzer, bulk_analyze_24h


class TestEarlySignalsAnalyzer:
    """Тесты для EarlySignalsAnalyzer."""

    def test_strong_positive_signal(self):
        """Тест распознавания сильного позитивного сигнала."""

        analyzer = EarlySignalsAnalyzer()

        result = analyzer.analyze_24h_performance(
            impressions=500,
            clicks=20,        # CTR 4% (хороший)
            landing_views=18,
            landing_bounces=6,  # Bounce 33% (хороший)
            avg_time_on_page=6.5,  # Время 6.5s (хорошее)
            conversions=2,    # Ранние конверсии (бонус)
            created_at=datetime.utcnow() - timedelta(hours=24)
        )

        assert result["signal"] == "strong_positive"
        assert result["recommendation"] == "scale"
        assert result["confidence"] > 0.7
        assert result["predicted_final_cvr"] > 0
        assert "scale" in result["next_action"].lower()

    def test_strong_negative_signal(self):
        """Тест распознавания сильного негативного сигнала."""

        analyzer = EarlySignalsAnalyzer()

        result = analyzer.analyze_24h_performance(
            impressions=800,
            clicks=5,         # CTR 0.625% (плохой)
            landing_views=4,
            landing_bounces=3,  # Bounce 75% (плохой)
            avg_time_on_page=1.2,  # Время 1.2s (плохое)
            conversions=0,    # Нет конверсий
            created_at=datetime.utcnow() - timedelta(hours=24)
        )

        assert result["signal"] == "strong_negative"
        assert result["recommendation"] == "kill"
        assert result["confidence"] > 0.7
        assert result["predicted_final_cvr"] < 0.05
        assert "kill" in result["next_action"].lower() or "stop" in result["next_action"].lower()

    def test_neutral_signal(self):
        """Тест нейтрального сигнала."""

        analyzer = EarlySignalsAnalyzer()

        result = analyzer.analyze_24h_performance(
            impressions=500,
            clicks=10,        # CTR 2% (средний)
            landing_views=9,
            landing_bounces=4,  # Bounce 44% (средний)
            avg_time_on_page=3.5,  # Время 3.5s (среднее)
            conversions=0,
            created_at=datetime.utcnow() - timedelta(hours=24)
        )

        assert result["signal"] in ["neutral", "positive", "negative"]
        assert result["recommendation"] in ["continue", "pause"]

    def test_insufficient_data_time(self):
        """Тест недостаточного времени (меньше 6 часов)."""

        analyzer = EarlySignalsAnalyzer()

        result = analyzer.analyze_24h_performance(
            impressions=500,
            clicks=20,
            landing_views=18,
            landing_bounces=6,
            avg_time_on_page=6.5,
            conversions=2,
            created_at=datetime.utcnow() - timedelta(hours=3)  # Только 3 часа
        )

        assert result["signal"] == "insufficient_data"
        assert result["recommendation"] == "wait"
        assert result["confidence"] == 0.0

    def test_insufficient_data_volume(self):
        """Тест недостаточного объема данных."""

        analyzer = EarlySignalsAnalyzer()

        result = analyzer.analyze_24h_performance(
            impressions=50,   # Меньше 100
            clicks=2,         # Меньше 10
            landing_views=2,
            landing_bounces=1,
            avg_time_on_page=5.0,
            conversions=0,
            created_at=datetime.utcnow() - timedelta(hours=24)
        )

        assert result["signal"] == "insufficient_volume"
        assert result["recommendation"] == "wait"
        assert result["confidence"] == 0.0

    def test_positive_signals_counting(self):
        """Тест подсчета позитивных сигналов."""

        analyzer = EarlySignalsAnalyzer()

        result = analyzer.analyze_24h_performance(
            impressions=1000,
            clicks=35,        # CTR 3.5% (выше 3%) → +2
            landing_views=30,
            landing_bounces=10,  # Bounce 33% (ниже 40%) → +1
            avg_time_on_page=6.0,  # Время 6s (выше 5s) → +1
            conversions=1,    # Ранние конверсии → +1
            created_at=datetime.utcnow() - timedelta(hours=24)
        )

        # Должно быть 5 позитивных сигналов (2+1+1+1)
        assert result["signal"] == "strong_positive"
        assert "✅" in result["reasoning"]  # Позитивные сигналы отмечены

    def test_negative_signals_counting(self):
        """Тест подсчета негативных сигналов."""

        analyzer = EarlySignalsAnalyzer()

        result = analyzer.analyze_24h_performance(
            impressions=1000,
            clicks=8,         # CTR 0.8% (ниже 1%) → -2
            landing_views=7,
            landing_bounces=6,   # Bounce 85% (выше 70%) → -1
            avg_time_on_page=1.5,  # Время 1.5s (ниже 2s) → -1
            conversions=0,
            created_at=datetime.utcnow() - timedelta(hours=24)
        )

        # Должно быть 4 негативных сигнала (2+1+1)
        assert result["signal"] in ["strong_negative", "negative"]
        assert "❌" in result["reasoning"]  # Негативные сигналы отмечены

    def test_predicted_cvr_scaling(self):
        """Тест масштабирования предсказанного CVR."""

        analyzer = EarlySignalsAnalyzer()

        # Сильный позитивный сигнал
        result_positive = analyzer.analyze_24h_performance(
            impressions=500,
            clicks=20,
            landing_views=18,
            landing_bounces=5,
            avg_time_on_page=7.0,
            conversions=2,
            created_at=datetime.utcnow() - timedelta(hours=24)
        )

        # Сильный негативный сигнал
        result_negative = analyzer.analyze_24h_performance(
            impressions=500,
            clicks=5,
            landing_views=4,
            landing_bounces=3,
            avg_time_on_page=1.0,
            conversions=0,
            created_at=datetime.utcnow() - timedelta(hours=24)
        )

        # Позитивный CVR должен быть выше
        assert result_positive["predicted_final_cvr"] > result_negative["predicted_final_cvr"]

    def test_confidence_scores(self):
        """Тест уверенности предсказаний."""

        analyzer = EarlySignalsAnalyzer()

        # Четкий сигнал (много позитивных или негативных показателей)
        result_clear = analyzer.analyze_24h_performance(
            impressions=1000,
            clicks=40,  # Очень хороший CTR
            landing_views=35,
            landing_bounces=5,  # Отличный bounce
            avg_time_on_page=8.0,  # Отличное время
            conversions=3,
            created_at=datetime.utcnow() - timedelta(hours=24)
        )

        # Смешанный сигнал
        result_mixed = analyzer.analyze_24h_performance(
            impressions=500,
            clicks=15,  # CTR 3% (хороший)
            landing_views=13,
            landing_bounces=7,  # Bounce 54% (средний)
            avg_time_on_page=3.0,  # Время 3s (среднее)
            conversions=0,
            created_at=datetime.utcnow() - timedelta(hours=24)
        )

        # Четкий сигнал должен иметь более высокую уверенность
        assert result_clear["confidence"] >= result_mixed["confidence"]

    def test_metrics_output(self):
        """Тест корректности выходных метрик."""

        analyzer = EarlySignalsAnalyzer()

        result = analyzer.analyze_24h_performance(
            impressions=1000,
            clicks=30,
            landing_views=25,
            landing_bounces=10,
            avg_time_on_page=5.5,
            conversions=2,
            created_at=datetime.utcnow() - timedelta(hours=24)
        )

        # Проверка метрик
        assert "metrics" in result
        assert result["metrics"]["24h_ctr"] == 0.03  # 30/1000
        assert result["metrics"]["bounce_rate"] == 0.4  # 10/25
        assert result["metrics"]["avg_time_on_page"] == 5.5
        assert result["metrics"]["early_cvr"] == 0.0667  # 2/30 (округление)
        assert result["metrics"]["conversions"] == 2
        assert result["metrics"]["sample_size"] == 30


class TestBulkAnalysis:
    """Тесты массового анализа."""

    def test_bulk_analyze_24h(self):
        """Тест массового анализа 20 креативов."""

        creatives_data = []

        # 3 победителя
        for i in range(3):
            creatives_data.append({
                "id": f"winner-{i}",
                "name": f"Winner {i}",
                "impressions": 500,
                "clicks": 20,
                "landing_views": 18,
                "landing_bounces": 5,
                "avg_time_on_page": 6.5,
                "conversions": 2,
                "created_at": datetime.utcnow() - timedelta(hours=24)
            })

        # 10 потенциальных
        for i in range(10):
            creatives_data.append({
                "id": f"potential-{i}",
                "name": f"Potential {i}",
                "impressions": 500,
                "clicks": 12,
                "landing_views": 10,
                "landing_bounces": 4,
                "avg_time_on_page": 4.0,
                "conversions": 0,
                "created_at": datetime.utcnow() - timedelta(hours=24)
            })

        # 7 лузеров
        for i in range(7):
            creatives_data.append({
                "id": f"loser-{i}",
                "name": f"Loser {i}",
                "impressions": 800,
                "clicks": 5,
                "landing_views": 4,
                "landing_bounces": 3,
                "avg_time_on_page": 1.2,
                "conversions": 0,
                "created_at": datetime.utcnow() - timedelta(hours=24)
            })

        result = bulk_analyze_24h(creatives_data)

        # Проверки
        assert "winners" in result
        assert "potential" in result
        assert "losers" in result
        assert "summary" in result

        assert len(result["winners"]) > 0
        assert len(result["losers"]) > 0

        summary = result["summary"]
        assert summary["total_analyzed"] == 20
        assert summary["winners_count"] + summary["potential_count"] + summary["losers_count"] == 20
        assert summary["kill_rate"] >= 0
        assert summary["estimated_savings_usd"] > 0

    def test_bulk_savings_calculation(self):
        """Тест расчета экономии бюджета."""

        creatives_data = []

        # 10 лузеров
        for i in range(10):
            creatives_data.append({
                "id": f"loser-{i}",
                "name": f"Loser {i}",
                "impressions": 800,
                "clicks": 5,
                "landing_views": 4,
                "landing_bounces": 3,
                "avg_time_on_page": 1.0,
                "conversions": 0,
                "created_at": datetime.utcnow() - timedelta(hours=24)
            })

        result = bulk_analyze_24h(creatives_data)

        # Проверить экономию
        losers_count = len(result["losers"])
        expected_savings = losers_count * 40  # $40 на каждого

        assert result["summary"]["estimated_savings_usd"] == expected_savings

    def test_bulk_empty_list(self):
        """Тест пустого списка креативов."""

        result = bulk_analyze_24h([])

        assert result["summary"]["total_analyzed"] == 0
        assert len(result["winners"]) == 0
        assert len(result["potential"]) == 0
        assert len(result["losers"]) == 0


class TestThresholds:
    """Тесты пороговых значений."""

    def test_ctr_thresholds(self):
        """Тест пороговых значений CTR."""

        analyzer = EarlySignalsAnalyzer()

        assert analyzer.THRESHOLDS["ctr_good"] == 0.03
        assert analyzer.THRESHOLDS["ctr_bad"] == 0.01

    def test_bounce_thresholds(self):
        """Тест пороговых значений bounce rate."""

        analyzer = EarlySignalsAnalyzer()

        assert analyzer.THRESHOLDS["bounce_good"] == 0.40
        assert analyzer.THRESHOLDS["bounce_bad"] == 0.70

    def test_time_thresholds(self):
        """Тест пороговых значений времени на странице."""

        analyzer = EarlySignalsAnalyzer()

        assert analyzer.THRESHOLDS["time_good"] == 5.0
        assert analyzer.THRESHOLDS["time_bad"] == 2.0

    def test_threshold_boundary_values(self):
        """Тест граничных значений."""

        analyzer = EarlySignalsAnalyzer()

        # Граница хорошего CTR
        result_good = analyzer.analyze_24h_performance(
            impressions=1000,
            clicks=30,  # Ровно 3%
            landing_views=28,
            landing_bounces=10,
            avg_time_on_page=5.0,
            conversions=0,
            created_at=datetime.utcnow() - timedelta(hours=24)
        )

        # Граница плохого CTR
        result_bad = analyzer.analyze_24h_performance(
            impressions=1000,
            clicks=10,  # Ровно 1%
            landing_views=9,
            landing_bounces=5,
            avg_time_on_page=3.0,
            conversions=0,
            created_at=datetime.utcnow() - timedelta(hours=24)
        )

        # Хороший результат должен быть лучше
        assert result_good["predicted_final_cvr"] > result_bad["predicted_final_cvr"]


class TestEdgeCases:
    """Тесты граничных случаев."""

    def test_zero_clicks(self):
        """Тест с нулевыми кликами."""

        analyzer = EarlySignalsAnalyzer()

        result = analyzer.analyze_24h_performance(
            impressions=1000,
            clicks=0,
            landing_views=0,
            landing_bounces=0,
            avg_time_on_page=0,
            conversions=0,
            created_at=datetime.utcnow() - timedelta(hours=24)
        )

        # Должно вернуть insufficient_volume
        assert result["signal"] == "insufficient_volume"
        assert result["recommendation"] == "wait"

    def test_perfect_metrics(self):
        """Тест с идеальными метриками."""

        analyzer = EarlySignalsAnalyzer()

        result = analyzer.analyze_24h_performance(
            impressions=1000,
            clicks=100,  # CTR 10%
            landing_views=95,
            landing_bounces=5,  # Bounce 5%
            avg_time_on_page=15.0,  # 15 секунд
            conversions=10,  # CVR 10%
            created_at=datetime.utcnow() - timedelta(hours=24)
        )

        assert result["signal"] == "strong_positive"
        assert result["recommendation"] == "scale"
        assert result["confidence"] > 0.7

    def test_all_bounces(self):
        """Тест когда все посетители bounce."""

        analyzer = EarlySignalsAnalyzer()

        result = analyzer.analyze_24h_performance(
            impressions=1000,
            clicks=20,
            landing_views=20,
            landing_bounces=20,  # 100% bounce
            avg_time_on_page=0.5,
            conversions=0,
            created_at=datetime.utcnow() - timedelta(hours=24)
        )

        assert result["signal"] in ["strong_negative", "negative"]
        assert result["recommendation"] in ["kill", "pause"]
