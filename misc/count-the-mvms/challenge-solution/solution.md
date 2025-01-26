# count-the-mvms

First, extract the images:
`pdfimages -all certificate_SAMPLE_TEAM.pdf`

Open the resulting image and save an MVM pattern in `mvm_pattern.png`.

Run the solve script to find all of the matches for the pattern.

Add 3 to the number ("x3CTF x MVM" + MVM logo + "mvm organizer") + any additional mvms in team name.

You should get 9336.

Get the MD2 of "9336" and bake the flag: `x3c{th3r3_4re_9336_MVMs_1n_my_c3rtif1cat3_2931355ee608d35463f2ef7847474858}`