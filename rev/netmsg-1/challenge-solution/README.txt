1. rev the binary to figure out the binary protocol in use
2. notice that `x3c/common.Msg` uses all types from 1 to 14 besides 8 (note: client command output orders the removed "get flag" option between "view message box" (types 6 and 7) and "read message" (types 9 and 10))
3a. mess around with a debugger to trigger the exchange
3b. implement your own client (provided as main.py here)
