# Solution for SpellCheckers Inc.

To solve this challenge, players must first overwrite one of the default magic database files to configure a json
file to be detected as an image. After this, players must craft and upload a json file, read by a custom templating
engine to read the flag. Both these files must be specifically crafted polyglots to exploit parser differentials.

## Overwriting the mime database

To get the flag, players must upload a json file and pass it to `rebuild/index.php`. Players can furthermore upload new
magicians using `administration.php`. What stops players from uploading json files directly is a mime check in
`administration.php` enforcing the uploaded files to be jpeg. This check is performed using the `file` utility. PHP json
parsing is quite strict in what is allows as a json and will not parse files where data is appended or prepended.

When a magician is uploaded ".magic" is appended to the chosen magician name. The name is not sanitized however, so
players can add files ending in ".magic" to the system by naming a magician `../../../and/so/on`. One such file is
`/home/app/.magic`. The easiest way of finding that this path is checked for magic is by `strace`ing the `file` utility
- documentation on which files are checked is somewhat incomplete - like this: `strace --trace file file /etc/hosts`.

### magical polyglot #1

The magic itself can look like this:

```
0	string  {	jpeg
!:mime  image/jpeg
```

However, the magic must also pass the mime check for being and image when uploading magicians and be a valid magic file
(see man 5 file). Thus, a second polyglot must be constructed.

```
if (!preg_match('\w{1,5} image.*', $mime)) {
    echo "<p>Invalid upload!</p>";
    exit();
}
```

One such polyglot can be created using XBM images. XBM images are based solely on printable characters. Furthermore,
the XBM checks performed by `file` allow every line to be prefixed by a `#`. Since `#` is used by libmagic for comments,
the XBM image will not cause `file` to error out during mime checks.

### Overwriting the magic

With the polyglot constructed, players can upload the polyglot magic as a new magician with the name
`../../../../../home/app/`. This will overwrite `/home/app/.magic`.

## Uploading the template

This removes the first obstacle from uploading a custom template and exfiltrating the flag that way. However, due to an
undocumented behaviour, `file` will not apply the new magic to a standard json file. json and a few other file types
are implemented in a different way in magic and thus ignore the magic database. Before players can exfiltrate the flag,
they must construct another polyglot. This time a json file that can be parsed by PHP, while not being detected as json
by `file`. 

```json
{"num": "\x56","sections":[{"type":"link","tag":"h1","value":"/flag.txt"}]}
```

One such polyglot can be constructed by adding special backslash characters to one of the json strings. This will result
in `file` not recognizing the file as json but will be stripped by the *sanitization* in PHP.

## Getting the flag

Finally, users render the custom template by navigating to `/rebuild.php?site=../magicians/NAME.json`.

# tl;dr

1. Navigate to `administration.php`.
2. Upload `magic.xbm` with the name `../../../../home/app/`.
3. Upload `exfil.json` with the name `exfil`.
4. Navigate to `rebuild/?page=../magicians/exfil.magic`
