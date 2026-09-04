from core.factory import describe, repository_from_url
from core.json_repository import JsonRepository
from core.sqlite_repository import SqliteRepository


def test_a_bare_path_is_sqlite(tmp_path):
    repository = repository_from_url(str(tmp_path / "x.db"))
    assert isinstance(repository, SqliteRepository)
    repository.close()


def test_sqlite_url_scheme(tmp_path):
    repository = repository_from_url(f"sqlite:///{tmp_path / 'x.db'}")
    assert isinstance(repository, SqliteRepository)
    assert repository.path.name == "x.db"
    repository.close()


def test_a_directory_is_the_json_store(tmp_path):
    repository = repository_from_url(str(tmp_path))
    assert isinstance(repository, JsonRepository)
    repository.close()


def test_json_url_scheme(tmp_path):
    repository = repository_from_url(f"json://{tmp_path}")
    assert isinstance(repository, JsonRepository)
    repository.close()


def test_describe_masks_a_password():
    assert describe("postgresql://user:secret@db:5432/evertrack") == \
        "postgresql://user:***@db:5432/evertrack"


def test_describe_leaves_a_passwordless_url_alone():
    assert describe("postgresql://user@db:5432/evertrack") == "postgresql://user@db:5432/evertrack"


def test_describe_leaves_a_file_path_alone():
    assert describe("evertrack.db") == "evertrack.db"
