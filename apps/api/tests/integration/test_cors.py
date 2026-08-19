import importlib


def test_cors_origins_use_environment_override(monkeypatch) -> None:
    monkeypatch.setenv("CORS_ORIGINS", "https://evelyn.vercel.app, https://preview.vercel.app")

    import app.main

    main = importlib.reload(app.main)

    assert main.CORS_ORIGINS == ["https://evelyn.vercel.app", "https://preview.vercel.app"]

    monkeypatch.delenv("CORS_ORIGINS")
    main = importlib.reload(main)

    assert "http://127.0.0.1:3100" in main.CORS_ORIGINS
