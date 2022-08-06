import csv
import sys
import time
import json
import requests
from datetime import datetime
from bs4 import BeautifulSoup
import re
import random
from concurrent.futures import ThreadPoolExecutor,as_completed

base_url = "https://bina.az/items/"
cont_error = 0

month_map = {
    1: "Yanvar",
    2: "Fevral",
    3: "Mart",
    4: "Aprel",
    5: "May",
    6: "İyun",
    7: "İyul",
    8: "Avqust",
    9: "Sentyabr",
    10: "Oktyabr",
    11: "Noyabr",
    12: "Dekabr",
}
today_arr = [
    str(f"{datetime.now().day:02}"),
    str(month_map[datetime.now().month]),
    str(datetime.now().year)
]

today_str = " ".join(today_arr)

def parsePrice(priceStr):
    priceArr = priceStr.split(" ")
    return int("".join(priceArr))

def parseParams(parameters):
    params = {}
    for param in parameters.children:
        res = re.search(r"<tr><td>(.+)<\/td><td>(.+)<\/td><\/tr>",str(param))
        params[res.group(1)] = res.group(2)
        
    return params

def scrapeUrl(base_url,item_id):
  global cont_error
  # print(base_url,item_id)
  item = {
      "id": item_id
  }
  url = base_url + str(item_id)
  try:
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    item_page = soup.select_one(".price-val")
    if(item_page is None):
      cont_error += 1
      if(cont_error > 10):
        print("Too many back to back errors, exiting ...")
        sys.exit(2)
      raise ValueError("Item deleted: "+str(item_id))
    else:
      cont_error = 0

    coords = soup.select_one("#item_map")
    item["lng"] = coords["data-lng"]
    item["lat"] = coords["data-lat"]
    item["price"] = parsePrice(item_page.getText())
    item["isRent"] = True if soup.select_one(".price_header > .price > p > .price-per") else False
    item["title"] = soup.select_one(".services-container > h1").getText()
    item["address"] = soup.select_one(".map_address").text[7:]
    item["parameters"] = parseParams(soup.select_one(".parameters"))
    item["description"] = soup.select_one("article").getText()
    raw_date_arr = soup.select_one(".item_info").select_one(":last-child").get_text().split(":")[1].strip().split(" ")
    item["date"] = " ".join(raw_date_arr) if len(raw_date_arr) == 3 else toda
    return item
  except BaseException as error:
    print('An exception occurred: {}'.format(error))

def process_batch(fn,start,batch_size):
  results = []
  with ThreadPoolExecutor(max_workers=8) as executor:
    futures = {executor.submit(fn,base_url,x) : x for x in range(start,start+batch_size)}

    for future in as_completed(futures):
        res = future.result()
        if res:
          results.append(res)
    return results

if __name__ == "__main__":
  start_point = 2000000
  end_point = 2010000
  step = 1000

  # start_time = time.time()
  for batch_start in range(start_point,end_point,step):
    batch_results = process_batch(scrapeUrl,batch_start,step)
    filename = f"data/{batch_start}-{batch_start+step}-result.json"
    print("Writing batch: ", filename)
    with open(filename,"a",encoding="utf-8") as json_file:
        json.dump(batch_results,json_file,ensure_ascii=False)
        pause_time = random.randint(20,30)
        print(f"Sleeping for {pause_time}")
        time.sleep(pause_time)

  # seconds = time.time() - start_time

  # print(f"Job took {seconds} secs")
      