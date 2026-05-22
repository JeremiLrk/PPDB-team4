import server.app as app_module


def _stub_app_setup(monkeypatch, seed_calls):
    monkeypatch.setattr(app_module, "_register_blueprints", lambda flask_app: None)
    monkeypatch.setattr(app_module, "_register_cli_commands", lambda flask_app: None)
    monkeypatch.setattr(app_module, "init_db", lambda flask_app: None)
    monkeypatch.setattr(
        app_module,
        "seed_db",
        lambda flask_app, verbose=True: seed_calls.append((flask_app, verbose)),
    )


def test_startup_seed_is_skipped_without_seed_flag(monkeypatch):
    seed_calls = []

    monkeypatch.delenv("SEED_ON_STARTUP", raising=False)
    monkeypatch.delenv("PPDB_SEEDED_ON_STARTUP", raising=False)
    _stub_app_setup(monkeypatch, seed_calls)

    app_module.create_app()

    assert seed_calls == []


def test_startup_seed_runs_when_enabled(monkeypatch):
    seed_calls = []

    monkeypatch.setenv("SEED_ON_STARTUP", "1")
    monkeypatch.delenv("PPDB_SEEDED_ON_STARTUP", raising=False)
    _stub_app_setup(monkeypatch, seed_calls)

    app_module.create_app()

    assert len(seed_calls) == 1
    assert seed_calls[0][1] is True
    assert app_module.os.environ["PPDB_SEEDED_ON_STARTUP"] == "1"


def test_startup_seed_respects_verbose_flag(monkeypatch):
    seed_calls = []

    monkeypatch.setenv("SEED_ON_STARTUP", "1")
    monkeypatch.setenv("SEED_VERBOSE", "0")
    monkeypatch.delenv("PPDB_SEEDED_ON_STARTUP", raising=False)
    _stub_app_setup(monkeypatch, seed_calls)

    app_module.create_app()

    assert len(seed_calls) == 1
    assert seed_calls[0][1] is False


def test_startup_seed_is_skipped_after_launch_already_seeded(monkeypatch):
    seed_calls = []

    monkeypatch.setenv("SEED_ON_STARTUP", "1")
    monkeypatch.setenv("PPDB_SEEDED_ON_STARTUP", "1")
    _stub_app_setup(monkeypatch, seed_calls)

    app_module.create_app()

    assert seed_calls == []
