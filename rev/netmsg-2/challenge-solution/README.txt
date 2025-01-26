1. rev the binary to figure out the super-secure 32-bit RSA encryption used to secure the session key and extract the static AES key
2. decrypt the traffic to get the username and password
3. connect to the service yourself with them and get the message with the ident "flag" for the flag

the regular client can be used, but the solve script from netmsg-1 is reused here as a quickly runnable proof of concept
