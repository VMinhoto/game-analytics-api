"""
Unit tests for the anomaly detection module.
"""

from app.utils.anomaly import compute_z_scores


class TestComputeZScores:

    def test_empty_list_returns_empty(self):
        assert compute_z_scores([]) == []

    def test_single_value_not_flagged(self):
        results = compute_z_scores([100])
        assert len(results) == 1
        assert results[0].is_anomaly is False

    def test_uniform_values_no_anomalies(self):
        """Identical values → std_dev=0 → no anomalies."""
        results = compute_z_scores([100, 100, 100, 100])
        assert all(not r.is_anomaly for r in results)
        assert all(r.z_score == 0.0 for r in results)

    def test_obvious_outlier_is_flagged(self):
        values = [100, 102, 98, 101, 99, 100, 10000]
        results = compute_z_scores(values, threshold=2.0)
        assert results[-1].is_anomaly is True
        assert results[-1].z_score > 2.0
        assert "above" in results[-1].reason

    def test_low_outlier_flagged(self):
        values = [10000, 10200, 9800, 10100, 9900, 100]
        results = compute_z_scores(values, threshold=2.0)
        assert results[-1].is_anomaly is True
        assert results[-1].z_score < -2.0
        assert "below" in results[-1].reason

    def test_normal_values_not_flagged(self):
        values = [100, 102, 98, 101, 99, 100, 10000]
        results = compute_z_scores(values, threshold=2.0)
        assert all(not r.is_anomaly for r in results[:-1])

    def test_higher_threshold_fewer_anomalies(self):
        values = [100, 102, 98, 101, 99, 100, 200]
        loose = compute_z_scores(values, threshold=3.0)
        strict = compute_z_scores(values, threshold=1.0)
        assert sum(r.is_anomaly for r in strict) >= sum(r.is_anomaly for r in loose)

    def test_result_fields_populated(self):
        results = compute_z_scores([10, 20, 30])
        for r in results:
            assert isinstance(r.value, int)
            assert isinstance(r.mean, float)
            assert isinstance(r.std_dev, float)
            assert isinstance(r.z_score, float)
            assert isinstance(r.is_anomaly, bool)
            assert isinstance(r.reason, str)