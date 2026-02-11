"""Tests for the approve_trusted_hospitals CLI command."""

from unittest.mock import MagicMock, patch

from waittime.cli.approve_trusted_hospitals import TRUSTED_SOURCE_IDS, main


def _make_hospital(hospital_id: str, is_verified: bool, is_visible: bool) -> MagicMock:
    h = MagicMock()
    h.id = hospital_id
    h.name = f"Hospital {hospital_id}"
    h.is_verified = is_verified
    h.is_visible = is_visible
    return h


class TestTrustedSourceList:
    def test_all_four_provinces_present(self):
        assert "alberta-ahs" in TRUSTED_SOURCE_IDS
        assert "bc-phsa" in TRUSTED_SOURCE_IDS
        assert "ontario-health" in TRUSTED_SOURCE_IDS
        assert "quebec-msss" in TRUSTED_SOURCE_IDS


class TestApproveTrustedHospitals:
    @patch("waittime.cli.approve_trusted_hospitals.DatabaseService")
    def test_dry_run_does_not_modify(self, mock_db_cls):
        db = mock_db_cls.return_value
        db.get_hospitals_by_source.return_value = [
            _make_hospital("h1", is_verified=False, is_visible=False),
        ]

        with patch("sys.argv", ["cmd", "--dry-run"]):
            result = main()

        assert result == 0
        db.verify_hospital.assert_not_called()

    @patch("waittime.cli.approve_trusted_hospitals.DatabaseService")
    def test_approves_unapproved_hospitals(self, mock_db_cls):
        db = mock_db_cls.return_value
        unapproved = _make_hospital("h1", is_verified=False, is_visible=False)
        db.get_hospitals_by_source.return_value = [unapproved]

        with patch("sys.argv", ["cmd"]):
            result = main()

        assert result == 0
        db.verify_hospital.assert_any_call("h1", make_visible=True)

    @patch("waittime.cli.approve_trusted_hospitals.DatabaseService")
    def test_skips_already_approved(self, mock_db_cls):
        db = mock_db_cls.return_value
        approved = _make_hospital("h1", is_verified=True, is_visible=True)
        db.get_hospitals_by_source.return_value = [approved]

        with patch("sys.argv", ["cmd"]):
            result = main()

        assert result == 0
        db.verify_hospital.assert_not_called()

    @patch("waittime.cli.approve_trusted_hospitals.DatabaseService")
    def test_mixed_approval_states(self, mock_db_cls):
        db = mock_db_cls.return_value
        hospitals = [
            _make_hospital("h1", is_verified=True, is_visible=True),
            _make_hospital("h2", is_verified=False, is_visible=False),
            _make_hospital("h3", is_verified=True, is_visible=False),
        ]
        db.get_hospitals_by_source.return_value = hospitals

        with patch("sys.argv", ["cmd"]):
            result = main()

        assert result == 0
        # h2 needs both, h3 needs is_visible
        assert db.verify_hospital.call_count >= 2

    @patch("waittime.cli.approve_trusted_hospitals.DatabaseService")
    def test_queries_all_trusted_sources(self, mock_db_cls):
        db = mock_db_cls.return_value
        db.get_hospitals_by_source.return_value = []

        with patch("sys.argv", ["cmd"]):
            main()

        called_sources = [
            call.args[0] for call in db.get_hospitals_by_source.call_args_list
        ]
        for source_id in TRUSTED_SOURCE_IDS:
            assert source_id in called_sources

    @patch("waittime.cli.approve_trusted_hospitals.DatabaseService")
    def test_returns_error_on_db_failure(self, mock_db_cls):
        mock_db_cls.side_effect = ValueError("No DATABASE_URL")

        with patch("sys.argv", ["cmd"]):
            result = main()

        assert result == 1
