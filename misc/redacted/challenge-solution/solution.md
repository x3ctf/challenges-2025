# redacted

A screenshot has been censored with the default ShareX pen, which draws a solid red anti-aliased line with a black shadow underneath. Many characters of the flag are almost entirely covered with the pen, so it is pretty difficult to read out the flag.

There is no one single correct way to solve the challenge, but the approach I as the challenge creator took was first covering up the profile pop-up and reverting its shadow in an image editing program. This is what the `corrected.png` file is.

Then I took the Discord font from Discord itself and wrote a page that used the font on a canvas for a brute-ish attack. Iterating through all the possible 3-charater combinations the script on the page tries to ignore the red parts of the image and attempts to find the closest possible match to the censored image. Eventually, the entire flag can be revealed this way.

The version of the solve script included here has an autosolve button which looks at the flag and simulates what the user would've had to press to solve the chall manually.

This solve script works in Chromium both on Windows and Linux (I tried Manjaro Xfce in a VM). The font rendering on Linux is a little different, so this challenge may be a bit harder to solve. On both operating systems, the `l` in `w0uldv3` is not guessed correctly due to how narrow `ldv` is. This could easily be solved by writing a better script than mine. On Linux, the `u` in `b3c4u5e` is not guessed correctly by the script, but this is fairly guessable both visually and due to it being a common english word.
