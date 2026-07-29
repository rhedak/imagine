from pathlib import Path

from imagine.reference import Reference, build_reference_legend, combine_prompt


def test_legend_empty_for_no_references():
    assert build_reference_legend([]) == ""


def test_legend_labels_by_position_both_conventions():
    refs = [
        Reference(Path("a.png"), "Style anchor."),
        Reference(Path("b.png"), "Character sheet."),
    ]
    legend = build_reference_legend(refs)
    assert "Image 1 (IMAGE_0): Style anchor." in legend
    assert "Image 2 (IMAGE_1): Character sheet." in legend


def test_legend_falls_back_to_generic_caption():
    refs = [Reference(Path("a.png"))]
    legend = build_reference_legend(refs)
    assert "Image 1 (IMAGE_0): Reference image 1." in legend


def test_combine_prompt_no_references_no_negative():
    assert combine_prompt("do the thing") == "do the thing"


def test_combine_prompt_includes_legend_and_negative():
    refs = [Reference(Path("a.png"), "Style anchor.")]
    combined = combine_prompt("do the thing", refs, negative="no watermarks")
    assert "Image 1 (IMAGE_0): Style anchor." in combined
    assert "do the thing" in combined
    assert "Do NOT include any of the following:\nno watermarks" in combined


def test_reference_path_is_coerced_to_path():
    ref = Reference("a.png", "caption")
    assert isinstance(ref.path, Path)
