from scripts.compare_controlled_judge import compare_judge_rows


def test_compare_judge_rows_uses_paired_images_and_reports_direction() -> None:
    legacy = [
        _row("a.jpg", overall=2.0, clarity=3.0),
        _row("b.jpg", overall=3.0, clarity=4.0),
    ]
    constrained = [
        _row("a.jpg", overall=4.0, clarity=4.0),
        _row("b.jpg", overall=4.0, clarity=5.0),
    ]

    result = compare_judge_rows(
        legacy,
        constrained,
        metrics=("overall_mean", "clarity_mean"),
        bootstrap_samples=500,
        seed=7,
    )

    assert [row["metric"] for row in result] == ["overall_mean", "clarity_mean"]
    assert result[0]["paired_images"] == 2
    assert result[0]["legacy_mean"] == 2.5
    assert result[0]["constrained_mean"] == 4.0
    assert result[0]["mean_difference"] == 1.5
    assert result[0]["wins"] == 2
    assert result[0]["ties"] == 0
    assert result[0]["losses"] == 0
    assert result[0]["snapshot_direction"] == "constrained_higher"


def test_compare_judge_rows_rejects_unpaired_images() -> None:
    legacy = [_row("a.jpg", overall=3.0, clarity=3.0)]
    constrained = [_row("b.jpg", overall=3.0, clarity=3.0)]

    try:
        compare_judge_rows(legacy, constrained)
    except ValueError as error:
        assert "paired image sets differ" in str(error)
    else:
        raise AssertionError("unpaired judge files must be rejected")


def _row(image_name: str, *, overall: float, clarity: float) -> dict[str, str]:
    return {
        "image_name": image_name,
        "semantic_correctness_mean": str(overall),
        "spatial_accuracy_mean": str(overall),
        "groundedness_mean": str(overall),
        "clarity_mean": str(clarity),
        "overall_mean": str(overall),
    }
