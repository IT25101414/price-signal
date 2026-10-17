"""Repository-owned unit tests for the PDF extraction helpers.

The end-to-end checks against original CBSL PDFs remain in
``validate_extract_prices_real.py`` and are run explicitly with local source
reports. These tests require no private or externally hosted fixture files, so
they run identically in a fresh clone and in CI.
"""

import pytest

from extract_prices import check_consistency, clean_name, group_rows, parse_cell


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("1,250.00(a)", (1250.0, "ok")),
        ("n.a.", (None, "n.a.")),
        ("", (None, "")),
        (" 75 ", (75.0, "ok")),
    ],
)
def test_parse_cell_handles_report_values(raw, expected):
    assert parse_cell(raw) == expected


def test_parse_cell_rejects_unknown_text():
    with pytest.raises(ValueError, match="unparseable cell"):
        parse_cell("market closed")


def test_group_rows_uses_vertical_tolerance_and_horizontal_order():
    words = [
        {"text": "Today", "top": 10.8, "x0": 90},
        {"text": "Beans", "top": 10.0, "x0": 10},
        {"text": "Carrot", "top": 20.0, "x0": 10},
    ]

    rows = group_rows(words)

    assert [[word["text"] for word in row] for row in rows] == [
        ["Beans", "Today"],
        ["Carrot"],
    ]


@pytest.mark.parametrize(
    ("raw", "expected"),
    [("Pettah*", "Pettah"), ("Dambulla:", "Dambulla"), ("  Negombo  ", "Negombo")],
)
def test_clean_name_removes_report_markers(raw, expected):
    assert clean_name(raw) == expected


def _row(report_date, price_prior, price_today, prior_date=""):
    return {
        "report_date": report_date,
        "section": "VEGETABLES",
        "item": "Beans",
        "price_type": "retail",
        "market": "Pettah",
        "price_prior": price_prior,
        "price_today": price_today,
        "prior_date": prior_date,
    }


def test_check_consistency_accepts_matching_previous_price():
    rows = [
        _row("2026-10-01", 90.0, 100.0),
        _row("2026-10-02", 100.0, 110.0, "2026-10-01"),
    ]

    compared, mismatches, no_reference = check_consistency(rows)

    assert compared == 1
    assert mismatches == []
    assert no_reference == 1


def test_check_consistency_reports_mismatch_without_guessing():
    rows = [
        _row("2026-10-01", 90.0, 100.0),
        _row("2026-10-02", 105.0, 110.0, "2026-10-01"),
    ]

    compared, mismatches, no_reference = check_consistency(rows)

    assert compared == 1
    assert len(mismatches) == 1
    assert mismatches[0][-2:] == (100.0, 105.0)
    assert no_reference == 1
