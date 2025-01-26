# kittyconvert

A php webapp has been set up to convert PNG files to ICO. Converted PNG files get the .ico extension and are stored in the `/uploads/` directory. The flag is placed at `/flag.txt`.

An executable php file can be created by bypassing the regex (`preg_replace("/^(.+)\\..+$/", "$1.ico", ...)`) - this can be done with a filename such as `.php`. When such a file is uploaded it'll not get the `.ico` extension and can be executed by visiting `/uploads/.php`.

The ICO file format is pretty simple and can be controlled trivially by creating an image with the corresponding BGRA values. However, the alpha values will have the LSB cut off, so only characters where `ord(c) % 2 == 0` can be used.

An example payload that works within the constraints is `<?php    echo(exec($_GET["c"])) ; ?>`. The flag can be retrieved by first uploading a PNG with the name `.php` and the above payload encoded, and then visiting `/uploads/.php?c=cat+/flag.txt`.

A python solve script is included. It requires Pillow and requests, and the `TARGET_URI` variable should be changed to point to the challenge.
