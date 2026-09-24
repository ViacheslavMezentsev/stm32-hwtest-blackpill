"""Read-only macro-expression demonstration for the current F411 application.

Uses the standard runner for flashing/boot/recovery. Not part of coverage counts.
"""
from pathlib import Path


def macro_expressions(t):
    import gdb

    t.reach("loop")
    expressions = [
        ("__HAL_RCC_GPIOC_IS_CLK_ENABLED()", 1),
        ("__HAL_RCC_ADC1_IS_CLK_ENABLED()", 1),
        ("__HAL_RCC_SPI1_IS_CLK_ENABLED()", 0),
        ("(RCC->AHB1ENR & RCC_AHB1ENR_GPIOCEN) != 0", 1),
    ]
    t.report["macro_context"] = "loop / User/Src/program.cpp"
    evidence = t.report["macro_expressions"] = []
    for expression, expected in expressions:
        expansion = gdb.execute("macro expand " + expression, to_string=True)
        actual = t.value(expression)
        evidence.append(dict(expression=expression, expansion=expansion, value=actual))
        t.check(expression, actual, expected)
    # A missing macro is a compatibility error, not a silently false predicate.
    missing_rejected = False
    try:
        gdb.parse_and_eval("__STM32_GDBTEST_INTENTIONALLY_MISSING_MACRO__()")
    except gdb.error:
        missing_rejected = True
    t.check("missing macro rejected", missing_rejected, True)


if __name__ == "__main__":
    import argparse
    import json
    import sys

    root = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(root))
    from stm32_gdbtest.runner import run

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stand", type=Path, required=True)
    args = parser.parse_args()
    session = json.loads((root / "build/f411ce-debug-hwtest/hwtest/session.json").read_text())
    session["out"] = str(root / "build/f411ce-macros/runs")
    test = dict(id="HW_MACRO_SMOKE", path=str(Path(__file__).resolve()),
                function="macro_expressions", timeout_s=20, contracts=[])
    raise SystemExit(run(session, test, args.stand, identity_policy="strict"))
