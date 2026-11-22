// Capstone project - Roll number 2501010091, K=91
// Black rectangle: starts at screen row 91, 20 rows high, 64 pixels wide.
// 64 pixels = 4 screen words per row. Screen rows contain 32 words.
// Hold any key to draw; release all keys to clear.

(LOOP)
    @KBD
    D=M
    @DRAW
    D;JGT

    // No key: set COLOR to white (0) to clear the rectangle.
    @0
    D=A
    @COLOR
    M=D
    @FILL
    0;JMP

(DRAW)
    // Key pressed: set COLOR to black (-1).
    @0
    D=A
    D=!D
    @COLOR
    M=D

(FILL)
    // Start at SCREEN + 32*91 = SCREEN + 2912 words.
    @2912
    D=A
    @SCREEN
    D=D+A
    @PTR
    M=D

    @20
    D=A
    @ROWS
    M=D

(ROW)
    // Write four consecutive 16-pixel words = 64 pixels.
    @4
    D=A
    @COLS
    M=D

(COL)
    @COLOR
    D=M
    @PTR
    A=M
    M=D

    @PTR
    M=M+1
    @COLS
    M=M-1
    D=M
    @COL
    D;JGT

    // Skip the remaining 28 words to reach the same columns next row.
    @28
    D=A
    @PTR
    M=D+M

    @ROWS
    M=M-1
    D=M
    @ROW
    D;JGT

    @LOOP
    0;JMP
