# Woffu bot

A script written in python to automatically check-in and check-out in woffu.
The script contains some constants used to define the time to check-in and
check-out, and the variance (check-in/out times are randomized with a variance
to offer plausible deniability to using a bot).

You can also define your vacation days so that the script will not check-in
that day.  The script looks for a file called `holidays.txt` where each line is
a date in ISO 8601 format.  Example:
```
2021-01-01
```
