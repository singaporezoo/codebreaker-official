# Codebreaker

This is the official Github repository for Codebreaker, an automated platform that allows for easy and quick grading of Informatics Olympiad solutions, created by "Singapore Zoo" in 2020 (due to the gradual discontinuation of [Dunjudge](https://dunjudge.me/)).

## Reference Links

Refer to the following links:

- [Current WIP](https://docs.google.com/document/d/1NN-bjnTUQeKOiVLaZO7ytHM4ChqOTPbR7cxBSR6tTyo/edit)
- [Documentation](https://docs.google.com/document/d/11_kzvH0YCCwvcKx3kSb16qmEVznQcYf9dj8B5gsicts/edit)
- [Analytics Github](https://github.com/dvdg6566/codebreaker-analytics)
- [Compiler Github](https://github.com/singaporezoo/codebreaker-compiler/)

### Checker Documentation

##### without `testlib.h`

If you are not using `testlib.h`, checker is called with $3$ arguments in this order:

- input file (`argv[1]`)
- participant output file (`argv[2]`)
- jury output file (`argv[3]`)

The checker should output a real number between $0$ and $1$. The score will be multiplied by the subtask score.

##### with `testlib.h`

If you are using `testlib.h`, the following is behaviour of the modified `testlib.h` (modification is in `InStream::quit` function starting at line 2596)

- `_ok`: prints 1
- `_wa`: prints 0
- `_pe`: prints 0
- `_fail`: prints nothing (checker fail)
- `_dirt`: prints 0
- `_points`: prints custom error message that you specified. Example use is `quitf(_points,"%.2f\n",0.69420);` to give $69.42\%$ of the subtask score
- `__unexpected_eof`: prints 0
