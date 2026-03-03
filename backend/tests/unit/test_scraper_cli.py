from unittest.mock import MagicMock, patch

import pytest

from waittime.cli.scraper import SCRAPERS, hospital_id_to_name, main, run_scraper


def test_scrapers_registry_includes_bc():
    """Verify BC is registered for --all runs."""
    assert "bc-phsa" in SCRAPERS


def test_hospital_id_to_name():
    """Verify conversion of hospital IDs to readable names."""
    assert hospital_id_to_name("ca-on-cheo") == "Cheo"
    assert (
        hospital_id_to_name("ca-on-ottawa-hospital-the-civic-site")
        == "Ottawa Hospital The Civic Site"
    )
    assert hospital_id_to_name("random-id") == "Random Id"
    assert hospital_id_to_name("ca-qc-chu-sainte-justine") == "Chu Sainte Justine"


@patch("waittime.cli.scraper.SCRAPERS")
def test_run_scraper_unknown_source(mock_scrapers):
    """Verify that unknown sources return 0."""
    mock_scrapers.keys.return_value = ["valid-source"]
    assert run_scraper("unknown-source") == 0


@patch("waittime.cli.scraper.SCRAPERS")
def test_run_scraper_dry_run(mock_scrapers):
    """Verify dry run logic without database calls."""
    mock_scraper_class = MagicMock()
    mock_source_factory = MagicMock()
    mock_source = MagicMock(name="Test Source", province="ON")
    mock_source_factory.return_value = mock_source

    mock_scrapers.__contains__.return_value = True
    mock_scrapers.__getitem__.return_value = (mock_scraper_class, mock_source_factory)

    # Setup scraper instance and return measurements
    mock_scraper_instance = mock_scraper_class.return_value.__enter__.return_value
    mock_scraper_instance.run.return_value = [
        MagicMock(hospital_id="h1", value=10),
        MagicMock(hospital_id="h2", value=20),
    ]

    with patch("waittime.cli.scraper.DatabaseService") as mock_db:
        count = run_scraper("ontario-health", dry_run=True)
        assert count == 2
        mock_db.assert_not_called()


@patch("waittime.cli.scraper.SCRAPERS")
@patch("waittime.cli.scraper.DatabaseService")
@patch("waittime.cli.scraper.GeocodingService")
def test_run_scraper_success(mock_geocoder, mock_db, mock_scrapers):
    """Verify run_scraper uses BaseScraper.run pipeline with hospital upserts."""
    mock_scraper_class = MagicMock()
    mock_source_factory = MagicMock()
    mock_source = MagicMock(name="Test Source", province="ON")
    mock_source_factory.return_value = mock_source

    mock_scrapers.__contains__.return_value = True
    mock_scrapers.__getitem__.return_value = (mock_scraper_class, mock_source_factory)

    measurements = [MagicMock(hospital_id="ca-on-h1", value=10)]
    mock_scraper_instance = mock_scraper_class.return_value.__enter__.return_value

    def run_side_effect(*args, **kwargs):
        before_save = kwargs.get("before_save")
        if kwargs.get("save_to_db") and before_save:
            before_save(measurements)
        return measurements

    mock_scraper_instance.run.side_effect = run_side_effect

    mock_db_instance = mock_db.return_value
    mock_db_instance.get_hospital.return_value = None  # New hospital
    mock_geocoder_instance = mock_geocoder.return_value
    mock_geocoder_instance.geocode_hospital.return_value = MagicMock(
        city="Ottawa", latitude=45.0, longitude=-75.0, confidence=1.0
    )

    count = run_scraper("ontario-health", dry_run=False)

    assert count == 1
    mock_scraper_class.assert_called_once_with(mock_source, db=mock_db_instance)
    assert mock_scraper_instance.run.call_args.kwargs["save_to_db"] is True
    assert callable(mock_scraper_instance.run.call_args.kwargs["before_save"])
    mock_db_instance.upsert_hospital.assert_called_once()
    mock_db_instance.insert_measurements.assert_not_called()
    mock_db_instance.update_heartbeat.assert_not_called()


@patch("waittime.cli.scraper.SCRAPERS")
@patch("waittime.cli.scraper.DatabaseService")
@patch("waittime.cli.scraper.GeocodingService")
def test_run_scraper_manages_shared_connection_context(mock_geocoder, mock_db, mock_scrapers):
    """Verify shared connection context is entered and exited around scraper execution."""
    mock_scraper_class = MagicMock()
    mock_source_factory = MagicMock()
    mock_source = MagicMock(name="Test Source", province="ON")
    mock_source_factory.return_value = mock_source

    mock_scrapers.__contains__.return_value = True
    mock_scrapers.__getitem__.return_value = (mock_scraper_class, mock_source_factory)

    measurements = [MagicMock(hospital_id="ca-on-h1", value=10)]
    mock_scraper_instance = mock_scraper_class.return_value.__enter__.return_value

    def run_side_effect(*args, **kwargs):
        before_save = kwargs.get("before_save")
        if kwargs.get("save_to_db") and before_save:
            before_save(measurements)
        return measurements

    mock_scraper_instance.run.side_effect = run_side_effect

    connection_context = MagicMock()
    connection_context.__enter__.return_value = MagicMock()

    base_db_instance = MagicMock()
    base_db_instance.get_connection.return_value = connection_context

    scraper_db_instance = MagicMock()
    scraper_db_instance.get_hospital.return_value = None

    mock_db.side_effect = [base_db_instance, scraper_db_instance]

    mock_geocoder_instance = mock_geocoder.return_value
    mock_geocoder_instance.geocode_hospital.return_value = MagicMock(
        city="Ottawa", latitude=45.0, longitude=-75.0, confidence=1.0
    )

    count = run_scraper("ontario-health", dry_run=False)

    assert count == 1
    connection_context.__enter__.assert_called_once()
    connection_context.__exit__.assert_called_once_with(None, None, None)


def test_main_list_scrapers():
    """Verify that --list exits normally."""
    with patch("sys.argv", ["scraper.py", "--list"]):
        # Use a dict for SCRAPERS to satisfy argparse and the loop
        with patch("waittime.cli.scraper.SCRAPERS", {"s1": (MagicMock(), MagicMock())}):
            with pytest.raises(SystemExit) as excinfo:
                main()
            assert excinfo.value.code == 0


def test_main_all_scrapers():
    """Verify that --all iterates through scrapers."""
    with patch("sys.argv", ["scraper.py", "--all"]):
        with patch("waittime.cli.scraper.SCRAPERS", {"s1": (MagicMock(), MagicMock())}):
            with patch("waittime.cli.scraper.run_scraper", return_value=10) as mock_run:
                with pytest.raises(SystemExit) as excinfo:
                    main()
                assert excinfo.value.code == 0
                mock_run.assert_any_call("s1", dry_run=False)


def test_run_scraper_dry_run_many_measurements():
    """Verify dry run logging truncation with >5 items."""
    mock_scrapers_dict = {"s1": (MagicMock(), MagicMock())}
    mock_run = MagicMock(return_value=[MagicMock(hospital_id=f"h{i}", value=i) for i in range(10)])
    mock_scrapers_dict["s1"][0].return_value.__enter__.return_value.run = mock_run

    with patch("waittime.cli.scraper.SCRAPERS", mock_scrapers_dict):
        with patch("waittime.cli.scraper.DatabaseService"):
            count = run_scraper("s1", dry_run=True)
            assert count == 10


def test_run_scraper_skip_existing_hospital():
    """Verify that existing hospitals with coordinates are skipped."""
    mock_scraper_class = MagicMock()
    mock_source_factory = MagicMock()
    mock_source = MagicMock(name="Test Source", province="ON")
    mock_source_factory.return_value = mock_source

    measurements = [MagicMock(hospital_id="ca-on-h1", value=10)]
    mock_scraper_instance = mock_scraper_class.return_value.__enter__.return_value

    def run_side_effect(*args, **kwargs):
        before_save = kwargs.get("before_save")
        if kwargs.get("save_to_db") and before_save:
            before_save(measurements)
        return measurements

    mock_scraper_instance.run.side_effect = run_side_effect

    with patch("waittime.cli.scraper.SCRAPERS", {"s1": (mock_scraper_class, mock_source_factory)}):
        with patch("waittime.cli.scraper.DatabaseService") as mock_db:
            mock_db_instance = mock_db.return_value
            # Setup existing hospital with valid coords
            mock_db_instance.get_hospital.return_value = MagicMock(latitude=45.0, longitude=-75.0)

            with patch("waittime.cli.scraper.GeocodingService") as mock_geocoder:
                run_scraper("s1", dry_run=False)
                # Should NOT call geocode_hospital because it's skipped
                mock_geocoder.return_value.geocode_hospital.assert_not_called()


def test_run_scraper_handles_general_exception():
    """Verify that run_scraper handles and logs general exceptions."""
    mock_scraper_class = MagicMock()
    mock_source_factory = MagicMock()
    mock_source = MagicMock(name="Test Source", province="ON")
    mock_source_factory.return_value = mock_source

    mock_scrapers_dict = {"s1": (mock_scraper_class, mock_source_factory)}

    with patch("waittime.cli.scraper.SCRAPERS", mock_scrapers_dict):
        with patch("waittime.cli.scraper.DatabaseService") as mock_db:
            mock_scraper_instance = mock_scraper_class.return_value.__enter__.return_value
            mock_scraper_instance.run.side_effect = Exception("General Error")

            count = run_scraper("s1")
            assert count == 0
            mock_db.return_value.update_heartbeat.assert_not_called()


def test_main_single_source():
    """Verify that --source runs a single scraper."""
    with patch("sys.argv", ["scraper.py", "--source", "ontario-health"]):
        with patch("waittime.cli.scraper.run_scraper", return_value=5) as mock_run:
            with pytest.raises(SystemExit) as excinfo:
                main()
            assert excinfo.value.code == 0
            mock_run.assert_called_once_with("ontario-health", dry_run=False)


def test_main_no_args(capsys):
    """Verify that running without args prints help and exits with 1."""
    with patch("sys.argv", ["scraper.py"]):
        with pytest.raises(SystemExit) as excinfo:
            main()
        assert excinfo.value.code == 1
        captured = capsys.readouterr()
        assert "usage:" in captured.out


def test_run_scraper_geocoding_failure():
    """Verify that run_scraper uses placeholders when geocoding fails."""
    mock_scraper_class = MagicMock()
    mock_source_factory = MagicMock()
    mock_source = MagicMock(name="Test Source", province="ON")
    mock_source_factory.return_value = mock_source

    measurements = [MagicMock(hospital_id="ca-on-h1", value=10)]
    mock_scraper_instance = mock_scraper_class.return_value.__enter__.return_value

    def run_side_effect(*args, **kwargs):
        before_save = kwargs.get("before_save")
        if kwargs.get("save_to_db") and before_save:
            before_save(measurements)
        return measurements

    mock_scraper_instance.run.side_effect = run_side_effect

    with patch("waittime.cli.scraper.SCRAPERS", {"s1": (mock_scraper_class, mock_source_factory)}):
        with patch("waittime.cli.scraper.DatabaseService") as mock_db:
            mock_db_instance = mock_db.return_value
            mock_db_instance.get_hospital.return_value = None

            with patch("waittime.cli.scraper.GeocodingService") as mock_geocoder:
                # Mock geocoding failure
                mock_geocoder.return_value.geocode_hospital.return_value = None

                run_scraper("s1", dry_run=False)

                # Should call upsert_hospital with placeholders
                args, _ = mock_db_instance.upsert_hospital.call_args
                hospital = args[0]
                assert hospital.city == "Unknown"
                assert hospital.latitude == 0.0
                assert hospital.longitude == 0.0


def test_new_hospitals_are_auto_approved():
    """Verify hospitals from government sources are created as verified and visible."""
    mock_scraper_class = MagicMock()
    mock_source_factory = MagicMock()
    mock_source = MagicMock(name="Test Source", province="AB")
    mock_source_factory.return_value = mock_source

    measurements = [MagicMock(hospital_id="ca-ab-foothills", value=60)]
    mock_scraper_instance = mock_scraper_class.return_value.__enter__.return_value

    def run_side_effect(*args, **kwargs):
        before_save = kwargs.get("before_save")
        if kwargs.get("save_to_db") and before_save:
            before_save(measurements)
        return measurements

    mock_scraper_instance.run.side_effect = run_side_effect

    with patch("waittime.cli.scraper.SCRAPERS", {"s1": (mock_scraper_class, mock_source_factory)}):
        with patch("waittime.cli.scraper.DatabaseService") as mock_db:
            mock_db_instance = mock_db.return_value
            mock_db_instance.get_hospital.return_value = None

            with patch("waittime.cli.scraper.GeocodingService") as mock_geocoder:
                mock_geocoder.return_value.geocode_hospital.return_value = MagicMock(
                    city="Calgary", latitude=51.0, longitude=-114.0, confidence=0.9
                )

                run_scraper("s1", dry_run=False)

                args, _ = mock_db_instance.upsert_hospital.call_args
                hospital = args[0]
                assert hospital.is_verified is True
                assert hospital.is_visible is True
