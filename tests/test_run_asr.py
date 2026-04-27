from evaluation.run_asr import get_audio_source, is_url, normalize_language


def test_get_audio_source_accepts_camel_case_path() -> None:
    assert get_audio_source({"id": "en-001", "audioPath": "./vocals.m4a"}) == "./vocals.m4a"


def test_is_url_detects_presigned_url() -> None:
    assert is_url("https://bucket.example.com/vocals.m4a?X-Amz-Signature=abc")
    assert not is_url("./datasets/benchmark/en-001/vocals.m4a")


def test_normalize_language() -> None:
    assert normalize_language(" JP ") == "jp"
