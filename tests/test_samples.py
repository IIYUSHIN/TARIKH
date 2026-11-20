from PIL import Image

from app.models import DocType
from tools.make_samples import make_all


def test_make_all_writes_three_readable_images(tmp_path):
    paths = make_all(tmp_path)
    assert set(paths) == set(DocType)
    for doc_type, p in paths.items():
        assert p.exists(), doc_type
        assert Image.open(p).width >= 1200


def test_every_sample_is_marked_fictional_in_metadata(tmp_path):
    for p in make_all(tmp_path).values():
        assert Image.open(p).info.get("tarikh-sample") == "fictional"


def test_photo_variant_is_a_different_jpeg_of_each_paper(tmp_path):
    clean = make_all(tmp_path / "clean")
    photo = make_all(tmp_path / "photo", photo=True)
    for t in DocType:
        assert photo[t].suffix == ".jpg" and clean[t].suffix == ".png"
        assert photo[t].read_bytes() != clean[t].read_bytes()
