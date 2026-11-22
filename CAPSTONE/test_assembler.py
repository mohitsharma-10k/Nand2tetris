import tempfile
from pathlib import Path
from assembler import assemble, AssemblyError

def main():
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "Tiny.asm"
        p.write_text("@2\nD=A\n@LOOP\n0;JMP\n(LOOP)\n@value\nM=D\n", encoding="utf-8")
        out, count = assemble(p)
        lines = out.read_text().splitlines()
        assert count == 6
        assert lines[0] == "0000000000000010"
        assert lines[1] == "1110110000010000"
        assert lines[2] == "0000000000000100"
        assert lines[3] == "1110101010000111"
        assert lines[4] == "0000000000010000"
        assert lines[5] == "1110001100001000"
        bad = Path(td) / "Bad.asm"
        bad.write_text("@2\nD=Q\n", encoding="utf-8")
        try:
            assemble(bad)
        except AssemblyError as e:
            assert "Line 2:" in str(e)
        else:
            raise AssertionError("Invalid instruction was not rejected")
    print("Assembler self-test: PASS")

if __name__ == "__main__":
    main()
