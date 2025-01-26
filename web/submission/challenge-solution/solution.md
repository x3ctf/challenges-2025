# submissions

A php web server has been set up to accept challenge submissions and the flag file is already present at `/uploads/flag.txt`. Said flag cannot be accessed due to filesystem permissions, and neither can any uploads (sans a race-condition) due to `chmod 000 *` being run every time a file is uploaded.

The solution is to abuse the wildcard to inject an argument into the chmod command. By first uploading a file called `--reference=foo.txt` and then a file called `foo.txt`, the chmod command will end up copying the permissions from the `foo.txt` file instead of using 000, and so the flag becomes readable.

The flag can simply be retrieved from `/uploads/flag.txt` once the permissions have been changed.
