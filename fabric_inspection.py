"""Fabric Inspection System using the textile 4-Point System.

This module supports:
1) Predefined sample input for quick testing.
2) Interactive/manual input for real inspection use.

It is intentionally designed as a small, extendable foundation for future
integration with AI pipelines (e.g., computer vision defect detection).
"""

from collections import Counter
from typing import Any, Dict, List, Optional, Tuple, Union

# -----------------------------
# Configurable decision limits
# -----------------------------
ACCEPT_LIMIT = 40.0
SECOND_QUALITY_LIMIT = 60.0


DefectInput = Union[float, int, Dict[str, Any]]


def get_points(size: float) -> int:
    """Assign 4-Point-System score for a single defect size in inches.

    Rules:
    - 0 < size <= 3   -> 1 point
    - 3 < size <= 6   -> 2 points
    - 6 < size <= 9   -> 3 points
    - size > 9        -> 4 points
    """
    if size <= 0:
        raise ValueError("Defect size must be a positive value in inches.")

    if size <= 3:
        return 1
    if size <= 6:
        return 2
    if size <= 9:
        return 3
    return 4


def _normalize_defects(defects: List[DefectInput]) -> List[Dict[str, Any]]:
    """Normalize defect inputs to a standard structure.

    Output format:
    [{"type": Optional[str], "size": float}, ...]
    """
    normalized: List[Dict[str, Any]] = []

    for item in defects:
        if isinstance(item, (int, float)):
            size = float(item)
            if size <= 0:
                raise ValueError(f"Invalid defect size: {item}. Size must be positive.")
            normalized.append({"type": None, "size": size})

        elif isinstance(item, dict):
            if "size" not in item:
                raise ValueError(f"Invalid defect entry {item}. Missing 'size'.")

            size = float(item["size"])
            if size <= 0:
                raise ValueError(f"Invalid defect size: {size}. Size must be positive.")

            defect_type = item.get("type")
            normalized.append({"type": defect_type, "size": size})

        else:
            raise ValueError(
                "Defect format must be either a number or a dict with keys 'size' and optional 'type'."
            )

    return normalized


def calculate_total_points(defects: List[DefectInput]) -> int:
    """Calculate total points for all defects.

    Returns 0 for an empty defect list.
    """
    if not defects:
        return 0

    normalized = _normalize_defects(defects)
    return sum(get_points(defect["size"]) for defect in normalized)


def calculate_points_per_100(total_points: int, length: float, width: float) -> float:
    """Compute points per 100 square yards.

    Formula:
    (Total Points * 36 * 100) / (Length * Width)

    where length is in yards, width is in inches.
    """
    if length <= 0 or width <= 0:
        raise ValueError("Fabric length and width must be greater than zero.")

    return (total_points * 36 * 100) / (length * width)


def classify_fabric(score: float) -> str:
    """Classify fabric quality based on configurable thresholds."""
    if score <= ACCEPT_LIMIT:
        return "ACCEPT"
    if score <= SECOND_QUALITY_LIMIT:
        return "SECOND QUALITY"
    return "REJECT"


def _validate_fabric_inputs(gsm: float, weight: float, length: float, width: float) -> None:
    """Validate top-level fabric inputs with user-friendly messages."""
    if gsm <= 0:
        raise ValueError("GSM must be greater than zero.")
    if weight <= 0:
        raise ValueError("Roll weight must be greater than zero.")
    if length <= 0:
        raise ValueError("Fabric length must be greater than zero.")
    if width <= 0:
        raise ValueError("Fabric width must be greater than zero.")


def inspect_fabric(
    gsm: float,
    weight: float,
    length: float,
    width: float,
    defects: List[DefectInput],
) -> Dict[str, Any]:
    """Run complete inspection and return structured report data."""
    _validate_fabric_inputs(gsm, weight, length, width)

    normalized = _normalize_defects(defects)
    total_points = calculate_total_points(defects)
    score = calculate_points_per_100(total_points, length, width)
    decision = classify_fabric(score)

    detailed_rows: List[Dict[str, Any]] = []
    points_histogram = Counter()
    defect_type_counter = Counter()

    for idx, defect in enumerate(normalized, start=1):
        points = get_points(defect["size"])
        points_histogram[points] += 1

        if defect["type"]:
            defect_type_counter[str(defect["type"])] += 1

        detailed_rows.append(
            {
                "index": idx,
                "type": defect["type"],
                "size": defect["size"],
                "points": points,
            }
        )

    return {
        "gsm": gsm,
        "weight": weight,
        "length": length,
        "width": width,
        "total_defects": len(normalized),
        "total_points": total_points,
        "points_per_100": score,
        "decision": decision,
        "details": detailed_rows,
        "points_histogram": dict(sorted(points_histogram.items())),
        "defect_type_count": dict(sorted(defect_type_counter.items())),
    }


def print_report(report: Dict[str, Any]) -> None:
    """Print a clean, industry-style inspection report."""
    print("\n" + "-" * 40)
    print("FABRIC INSPECTION REPORT")
    print("-" * 40)

    print("\nFabric Details:")
    print(f"- GSM: {report['gsm']}")
    print(f"- Roll Weight: {report['weight']} kg")
    print(f"- Length: {report['length']} yards")
    print(f"- Width: {report['width']} inches")

    print("\nDefect Summary:")
    print(f"- Total Defects: {report['total_defects']}")
    print(f"- Total Points: {report['total_points']}")

    print("\nDetailed Breakdown:")
    if not report["details"]:
        print("No defects recorded.")
    else:
        for row in report["details"]:
            line = (
                f"Defect {row['index']} -> Size: {row['size']} inch -> Points: {row['points']}"
            )
            if row["type"]:
                line += f" -> Type: {row['type']}"
            print(line)

    print("\nHistogram Summary:")
    for point in [1, 2, 3, 4]:
        count = report["points_histogram"].get(point, 0)
        print(f"- {point}-point defects: {count}")

    if report["defect_type_count"]:
        print("\nDefect Type Count:")
        for defect_type, count in report["defect_type_count"].items():
            print(f"- {defect_type}: {count}")

    print("\nFinal Calculation:")
    print(f"- Points per 100 sq yards: {report['points_per_100']:.2f}")

    print("\nDecision:")
    print(f"- {report['decision']}")


def _read_positive_float(prompt: str) -> float:
    """Read a positive float from console, retrying on invalid input."""
    while True:
        raw = input(prompt).strip()
        try:
            value = float(raw)
            if value <= 0:
                print("Please enter a number greater than zero.")
                continue
            return value
        except ValueError:
            print("Invalid number. Please try again.")


def _read_defects_interactively() -> List[DefectInput]:
    """Read defects one-by-one until user types 'done'."""
    defects: List[DefectInput] = []
    print("\nEnter defects one by one. Type 'done' when finished.")
    print("You may enter only size (e.g., 4.5) or type,size (e.g., hole,2.5)")

    while True:
        raw = input("Defect entry: ").strip()
        if raw.lower() == "done":
            break

        if not raw:
            print("Entry cannot be empty.")
            continue

        try:
            if "," in raw:
                defect_type, size_str = [part.strip() for part in raw.split(",", 1)]
                size = float(size_str)
                defects.append({"type": defect_type or None, "size": size})
            else:
                size = float(raw)
                defects.append(size)
        except ValueError:
            print("Invalid format. Use size or type,size (example: stain,5).")

    return defects


def run_sample_case() -> None:
    """Run the mandatory sample test case from the specification."""
    sample_gsm = 200
    sample_weight = 110
    sample_length = 26.4
    sample_width = 66
    sample_defects = [2.5, 5, 8, 10]

    print("\nRunning sample test case...")
    report = inspect_fabric(
        gsm=sample_gsm,
        weight=sample_weight,
        length=sample_length,
        width=sample_width,
        defects=sample_defects,
    )
    print_report(report)


def run_interactive_mode() -> None:
    """Run manual user input workflow."""
    print("\nInteractive Fabric Inspection")
    gsm = _read_positive_float("Enter Fabric GSM: ")
    weight = _read_positive_float("Enter Roll Weight (kg): ")
    length = _read_positive_float("Enter Fabric Length (yards): ")
    width = _read_positive_float("Enter Fabric Width (inches): ")
    defects = _read_defects_interactively()

    try:
        report = inspect_fabric(gsm, weight, length, width, defects)
        print_report(report)
    except ValueError as exc:
        print(f"Input error: {exc}")


def main() -> None:
    """Entry point for command-line use and Google Colab execution."""
    print("Fabric Inspection System (4-Point System)")
    print("1) Run sample test case")
    print("2) Run interactive mode")

    choice = input("Select option (1/2): ").strip()
    if choice == "1":
        run_sample_case()
    elif choice == "2":
        run_interactive_mode()
    else:
        print("Invalid option. Running sample test case by default.")
        run_sample_case()


if __name__ == "__main__":
    try:
        main()
    except ValueError as exc:
        # Top-level guard for clean user-facing errors.
        print(f"Error: {exc}")
    except ZeroDivisionError:
        # Defensive fallback in case formula is called directly with bad values.
        print("Error: Cannot divide by zero. Please verify length and width inputs.")
