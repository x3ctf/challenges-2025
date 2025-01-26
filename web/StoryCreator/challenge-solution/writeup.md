# Story Creator

Story Creator is a web application that lets users create images based on a
background image, title, and call-to-action. It is implemented using Go and 
gqlgen on the backend, Vite, React and Apollo GraphQL on the frontend, and the
images are rendered using Rod to control a headless browser.

The application segments users data by generating a UUID cookie for each user
and adding it to each user's request data.

## Setting

There is a GraphQL API with a root query field `flag`. It returns the value of
the cookie `flag` received from the browser.

The Rod headless browser has this cookie set to the real flag.

## Vulnerability - Automated Persistent Queries cache poisoning

The application uses Automated Persistent Queries to reduce the size of the
GraphQL requests. However, the query cache is susceptible to hash collisions,
this is illustrated by artificially shrinking the hashes to a limited keyspace.

This is due to gqlgen always setting the cache key when the query and APQ hash
were sent together, and not checking if the cache key was already set.

In addition, there is a functionality to include variables in the story text,
such as `{{ foo }}`. These variables are taken from the GraphQL response data,
therefore the user can load the flag using cache pollution and then render the
flag using this templating system.

## Solution

1. Upload an image using the GraphQL API 

This can be done using the `createImage` mutation. This can also be done once
in advance using the browser, and the ID reused.

2. Create a story using the GraphQL API 

This can be done using the `createStory` mutation. The text should contain the 
templated variable `{{ flag }}`.

3. Create an export using the GraphQL API 

This triggers the bot to render the image.

4. Pollute the cache

This can be done by
(1) reading the `/render/X` page code, to discover the query
    and appropriate SHA hash
(2) discovering the APQ cache artifically reduced key size and calculating the 
    key for that query 
(3) creating another query that maps to the same artificially reduced key
(4) sending the query to the server - with valid SHA256 hash - that evaluates to
    the same reduced key.

For example, adding `#` letters to the end of the GraphQL query until the reduced
key matches.

5. Wait for the export to complete

The exporter runs every 30 seconds. Polling `{ export(id:$id) { ready } }` field
can be useful.

6. Retrieve exported image

Getting the URL `/export/X` will return the image.

7. Extract the flag from the image

OCR or just looking at the image will reveal the flag.
