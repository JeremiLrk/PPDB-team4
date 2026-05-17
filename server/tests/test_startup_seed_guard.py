import server.app as app_module


# Verifies startup seed is skipped without reloader child.
def test_startup_seed_is_skipped_without_reloader_child(monkeypatch):
    seed_calls = []

    monkeypatch.setenv("SEED_ON_STARTUP", "1")
    monkeypatch.delenv("WERKZEUG_RUN_MAIN", raising=False)

    monkeypatch.setattr(app_module, "_register_blueprints", lambda flask_app: None)
    monkeypatch.setattr(app_module, "_register_cli_commands", lambda flask_app: None)
    monkeypatch.setattr(app_module, "init_db", lambda flask_app: None)
    monkeypatch.setattr(app_module, "seed_db", lambda flask_app, verbose=True: seed_calls.append((flask_app, verbose)))

    app_module.create_app()

    assert seed_calls == []


# Verifies startup seed runs in reloader child.
def test_startup_seed_runs_in_reloader_child(monkeypatch):
    seed_calls = []

    monkeypatch.setenv("SEED_ON_STARTUP", "1")
    monkeypatch.setenv("WERKZEUG_RUN_MAIN", "true")

    monkeypatch.setattr(app_module, "_register_blueprints", lambda flask_app: None)
    monkeypatch.setattr(app_module, "_register_cli_commands", lambda flask_app: None)
    monkeypatch.setattr(app_module, "init_db", lambda flask_app: None)
    monkeypatch.setattr(app_module, "seed_db", lambda flask_app, verbose=True: seed_calls.append((flask_app, verbose)))

    app_module.create_app()

    assert len(seed_calls) == 1
