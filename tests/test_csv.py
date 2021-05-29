from activesoup import Driver


def test_can_download_csv(tmp_path, requests_mock):
    d = Driver()
    output_path = tmp_path / "output.csv"

    requests_mock.get(
        "http://remote.test/csv",
        headers={"Content-Type": "text/csv"},
        text="Col1,Col2\nVal1,Val2",
    )

    page = d.get("http://remote.test/csv")
    page.save(output_path)

    assert output_path.exists()
    assert output_path.read_text() == "Col1,Col2\nVal1,Val2"
