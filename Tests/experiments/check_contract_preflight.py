"""Offline regression against real GDB/ELF, including intentionally wrong contracts."""
import argparse
from copy import deepcopy
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from hwtest.build_manifest import digest, load_verified
from hwtest.contracts import select_contracts

parser = argparse.ArgumentParser()
parser.add_argument("--session", type=Path, required=True)
args = parser.parse_args()
session = json.loads(args.session.read_text())
elf = Path(session["elf"])
manifest = load_verified(session["build_manifest"], digest(elf), session["profile"])
registry = Path(session["profile"]).parent / "Tests/contracts.json"
names = list(json.loads(registry.read_text())["contracts"])
selected = select_contracts(registry, names, manifest)
out = ROOT / "build/contract-validation" / Path(session["profile"]).parent.name
out.mkdir(parents=True, exist_ok=True)
variants = {"positive": selected}
for name in ("missing_symbol", "return_type", "arity", "argument_name", "field_type", "enum_value", "pointee_const"):
    data = deepcopy(selected)
    contracts = data["contracts"]
    function = contracts["rcc_error"]["functions"]["HAL_RCC_OscConfig"]
    if name == "missing_symbol":
        contracts["rcc_error"]["functions"]["HAL_Missing_Contract_Function"] = function
    elif name == "return_type":
        function["returns"] = "void"
    elif name == "arity":
        function["arguments"] = []
    elif name == "argument_name":
        function["arguments"] = [{"name": "wrong_name", "type": function["arguments"][0]["type"]}]
    elif name == "pointee_const":
        argument = function["arguments"][0]
        typename = argument["type"]
        argument["type"] = typename[6:] if typename.startswith("const ") else "const " + typename
    elif name == "field_type":
        contracts["gpio_arguments"]["fields"]["GPIO_InitTypeDef"]["Pin"] = "uint16_t"
    else:
        contracts["rcc_error"]["enums"]["HAL_StatusTypeDef"]["HAL_ERROR"] = 99
    variants[name] = data
for name in ("missing_macro", "missing_macro_context", "wrong_macro_scope", "unexpanded_macro"):
    data = deepcopy(selected)
    macros = data["contracts"]["clock_macros"]["macros"]
    if name == "missing_macro":
        macros["expressions"].append("__HWTEST_MISSING_MACRO__()")
    elif name == "missing_macro_context":
        macros["context"] = "HWTEST_MISSING_CONTEXT"
    elif name == "wrong_macro_scope":
        macros["context"] = ("adc_convert_typical" if "f103c8" in session["profile"]
                             else "adc_convert_factory")
    else:
        # Function-like definition exists, but without parentheses no expansion occurs.
        macros["expressions"] = ["__HAL_RCC_ADC1_IS_CLK_ENABLED"]
    variants[name] = data
for name, data in variants.items():
    result = out / (name + "-result.json")
    result.unlink(missing_ok=True)
    request = out / (name + "-request.json")
    request.write_text(json.dumps(dict(elf=str(elf), result=str(result), selected=data)))
    env = os.environ.copy()
    env.update(HWTEST_CONTRACT_REQUEST=str(request), PYTHONDONTWRITEBYTECODE="1", TEMP=str(out), TMP=str(out))
    env.pop("PYTHONHOME", None)
    env.pop("PYTHONPATH", None)
    with (out / (name + ".log")).open("wb") as log:
        proc = subprocess.run([session["gdb"], "-nx", "-q", "-batch", "-iex", "set auto-load off",
            str(elf), "-x", str(ROOT / "hwtest/contract_preflight.py")], timeout=15, env=env,
            stdout=log, stderr=subprocess.STDOUT, creationflags=subprocess.CREATE_NO_WINDOW)
    report = json.loads(result.read_text())
    expected = "PASS" if name == "positive" else "ERROR"
    assert report["status"] == expected and proc.returncode == (0 if expected == "PASS" else 2), report
    assert report["connection_attempted"] is False
    assert report["elf_sha256"] == digest(elf)
    print(name + ": " + expected + " (no target connection)")
