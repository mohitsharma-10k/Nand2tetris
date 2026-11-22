#!/usr/bin/env python3
"""Two-pass Hack assembler for the Nand2Tetris Capstone (K=91).

Usage:
    python assembler.py Box.asm
    python assembler.py Add.asm --symbols
Invalid instructions are reported with their original source line number.
"""
from __future__ import annotations
import argparse
import re
import sys
from itertools import permutations
from pathlib import Path

PREDEFINED = {
    "SP": 0, "LCL": 1, "ARG": 2, "THIS": 3, "THAT": 4,
    **{f"R{i}": i for i in range(16)},
    "SCREEN": 16384, "KBD": 24576,
}
DEST = {
    "": "000", "M": "001", "D": "010", "MD": "011",
    "A": "100", "AM": "101", "AD": "110", "AMD": "111",
}
# The official course files sometimes write a destination in another order
# (Rect.asm and Pong.asm use "DM=..."), so accept every ordering of A, D, M.
for _key, _bits in list(DEST.items()):
    for _order in permutations(_key):
        DEST.setdefault("".join(_order), _bits)
JUMP = {
    "": "000", "JGT": "001", "JEQ": "010", "JGE": "011",
    "JLT": "100", "JNE": "101", "JLE": "110", "JMP": "111",
}
COMP = {
    "0": "0101010", "1": "0111111", "-1": "0111010",
    "D": "0001100", "A": "0110000", "M": "1110000",
    "!D": "0001101", "!A": "0110001", "!M": "1110001",
    "-D": "0001111", "-A": "0110011", "-M": "1110011",
    "D+1": "0011111", "A+1": "0110111", "M+1": "1110111",
    "D-1": "0001110", "A-1": "0110010", "M-1": "1110010",
    "D+A": "0000010", "D+M": "1000010",
    "D-A": "0010011", "D-M": "1010011",
    "A-D": "0000111", "M-D": "1000111",
    "D&A": "0000000", "D&M": "1000000",
    "D|A": "0010101", "D|M": "1010101",
}
SYMBOL_RE = re.compile(r"^[A-Za-z_.$:][A-Za-z0-9_.$:]*$")

class AssemblyError(Exception):
    pass

def clean_source(path: Path):
    """Return (original_line_number, cleaned_instruction) pairs."""
    lines = []
    try:
        raw_lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        raise AssemblyError(f"Cannot read {path}: {exc}") from exc
    for number, raw in enumerate(raw_lines, 1):
        line = raw.split("//", 1)[0].strip()
        line = re.sub(r"\s+", "", line)
        if line:
            lines.append((number, line))
    return lines

def assemble(source_path: Path, write_symbols: bool = False):
    lines = clean_source(source_path)
    symbols = dict(PREDEFINED)
    rom = 0

    # Pass 1: record labels and their ROM addresses.
    for line_no, line in lines:
        if line.startswith("("):
            if not line.endswith(")") or line.count("(") != 1 or line.count(")") != 1:
                raise AssemblyError(f"Line {line_no}: invalid label declaration")
            label = line[1:-1]
            if not SYMBOL_RE.match(label):
                raise AssemblyError(f"Line {line_no}: invalid label name '{label}'")
            if label in symbols:
                raise AssemblyError(f"Line {line_no}: duplicate or reserved label '{label}'")
            symbols[label] = rom
        else:
            rom += 1

    # Pass 2: translate instructions and allocate variables from RAM[16].
    next_variable = 16
    machine_code = []
    for line_no, line in lines:
        if line.startswith("("):
            continue
        if line.startswith("@"):
            value = line[1:]
            if not value:
                raise AssemblyError(f"Line {line_no}: missing A-instruction value")
            if value.isdigit():
                address = int(value)
            else:
                if not SYMBOL_RE.match(value):
                    raise AssemblyError(f"Line {line_no}: invalid symbol '{value}'")
                if value not in symbols:
                    if next_variable > 16383:
                        raise AssemblyError(f"Line {line_no}: ran out of variable RAM addresses")
                    symbols[value] = next_variable
                    next_variable += 1
                address = symbols[value]
            if not 0 <= address <= 32767:
                raise AssemblyError(f"Line {line_no}: A-instruction value must be 0..32767")
            machine_code.append(f"{address:016b}")
            continue

        if line.count(";") > 1 or line.count("=") > 1:
            raise AssemblyError(f"Line {line_no}: invalid instruction")
        if "=" in line:
            dest, remainder = line.split("=", 1)
        else:
            dest, remainder = "", line
        if ";" in remainder:
            comp, jump = remainder.split(";", 1)
        else:
            comp, jump = remainder, ""
        if dest not in DEST:
            raise AssemblyError(f"Line {line_no}: invalid instruction (unknown destination '{dest}')")
        if comp not in COMP:
            raise AssemblyError(f"Line {line_no}: invalid instruction (unknown computation '{comp}')")
        if jump not in JUMP:
            raise AssemblyError(f"Line {line_no}: invalid instruction (unknown jump '{jump}')")
        machine_code.append("111" + COMP[comp] + DEST[dest] + JUMP[jump])

    output_path = source_path.with_suffix(".hack")
    output_path.write_text("\n".join(machine_code) + ("\n" if machine_code else ""), encoding="utf-8")
    if write_symbols:
        symbols_path = source_path.parent / "symbols.txt"
        symbols_path.write_text(
            "\n".join(f"{name}={address}" for name, address in sorted(symbols.items())) + "\n",
            encoding="utf-8"
        )
    return output_path, len(machine_code)

def main():
    parser = argparse.ArgumentParser(description="Assemble Hack .asm source into .hack machine code.")
    parser.add_argument("source", type=Path, help="input .asm file")
    parser.add_argument("--symbols", action="store_true", help="also write symbols.txt (optional)")
    args = parser.parse_args()
    try:
        output, count = assemble(args.source, args.symbols)
        print(f"Success: wrote {output} ({count} instructions).")
    except AssemblyError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
