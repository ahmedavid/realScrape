import requests
import re
import random
import time
from bs4 import BeautifulSoup
from pymongo import MongoClient

client = MongoClient('mongodb://localhost:27017/')
db = client.emlakaz
items_collection = db.items

base_url = "https://emlak.az/"

def parseParams(parameters):
  params = {}
  for param in parameters:
      if len(param) == 1:
          continue
      res = re.search(r"<dd><span class=\"label\">(.+)<\/span>(.+)<\/dd>",str(param))
      params[res.group(1)] = res.group(2)
      
  return params


def scrapeProperty(base_url,item_id):
  uri = str(item_id) + "-.html"
  item = {
      "item_id": item_id
  }
  try:
    url = base_url + uri 
    response = requests.get(url)
    soup = BeautifulSoup(response.text,"html.parser")

    title_obj = soup.select_one(".panel > h1.title")
    if title_obj is None:
      raise ValueError("Item doesn't exist:", item_id)
    title = title_obj.getText()
    item["title"] = title
    item["isRent"] = title[0] != "S"
    item["date"] = soup.select_one(".box-panel > .date > strong").getText()
    item["price"] = int("".join(soup.select_one(".left-bar > .price > .m").getText().split(" ")))
    item["address"] = soup.select_one(".map-address > h4").getText().split(": ")[1]
    phone_obj = soup.select_one(".silver-box > .phone")
    item["phone"] = phone_obj.getText() if phone_obj else None
    
    # coords (lat,lng)
    coords = soup.select_one("#google_map")["value"].strip("()").split(", ")
    item["lat"] = float(coords[0]) 
    item["lng"] = float(coords[1]) 
    
    # params
    params = parseParams(soup.select_one(".technical-characteristics"))
    item["params"] = params
    
    item["description"] = soup.select_one(".desc > p").getText()
    print("Scraping: ", item_id)
    return item
  except BaseException as error:
    print("Error: ", error)



if __name__ == "__main__":
  start_point = 800000
  end_point   = 800100
  step        = 10

  items = []

  for batch_start in range(start_point,end_point,step):
    print("Batch:", batch_start,batch_start+step)
    for i in range(batch_start,batch_start+step):
      item = scrapeProperty(base_url,i)
      if item:
        items.append(item)

    if len(items) > 0:
      items_collection.insert_many(items)
      print("Items saved")
    else:
      print("Nothing to save")
    items = []
    sleep_time = random.randint(5,10)
    print(f"Pausing for {sleep_time}...")
    time.sleep(sleep_time)

  # for item in items_collection.find({},{"_id": False}):
  #   print(item)