import database
from app import app


def setup_db(monkeypatch, tmp_path):
    monkeypatch.setenv('DATABASE_URL', f"sqlite:///{tmp_path / 'favorites.db'}")
    app.config['TESTING'] = True


def test_favorites_persist_are_unique_and_private(monkeypatch, tmp_path):
    setup_db(monkeypatch, tmp_path)
    with app.test_client() as client:
        assert client.post('/favorites', data={'word': 'starving', 'action': 'add'}).status_code == 303
        client.post('/favorites', data={'word': 'starving', 'action': 'add'})
        page = client.get('/favorites').data.decode()
        assert 'starving' in page and '餓到不行' in page
        with client.session_transaction() as session:
            uid = session['user_id']
        assert database.fetch_favorites(uid) == ['starving']
        database._build_engine.cache_clear()
        database._initialized_database_urls.clear()
        assert database.fetch_favorites(uid) == ['starving']
        assert not database.fetch_vocabulary(uid)
        database.apply_battle_result(uid, 'starving', True, 0, 0)
        assert '★ 已收藏' in client.get('/vocabulary').data.decode()
        with app.test_client() as other:
            assert 'starving' not in other.get('/favorites').data.decode()
        client.post('/favorites', data={'word': 'starving', 'action': 'remove'})
        assert not database.fetch_favorites(uid)
        assert '還沒有收藏' in client.get('/favorites').data.decode()


def test_invalid_favorite_and_safe_return(monkeypatch, tmp_path):
    setup_db(monkeypatch, tmp_path)
    with app.test_client() as client:
        assert client.post('/favorites', data={'word': '<script>', 'action': 'add'}).status_code == 400
        assert client.post('/favorites', data={'word': 'starving', 'action': 'bad'}).status_code == 400
        response = client.post('/favorites', data={'word': 'starving', 'action': 'add', 'next': 'https://example.com'})
        assert response.location.endswith('/favorites')
        assert '★ 已收藏' in client.get('/study').data.decode()


def test_guest_favorites_merge_on_login(monkeypatch, tmp_path):
    setup_db(monkeypatch, tmp_path)
    guest = database.ensure_guest_profile()
    account = database.ensure_auth_profile('auth-favorites', 'Reader')
    database.set_favorite(guest['id'], 'starving', True)
    database.set_favorite(account['id'], 'starving', True)
    database.set_favorite(account['id'], 'tired', True)
    database.ensure_auth_profile('auth-favorites', 'Reader', guest['id'])
    assert set(database.fetch_favorites(account['id'])) == {'starving', 'tired'}
    assert not database.fetch_favorites(guest['id'])
