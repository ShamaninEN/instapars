# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html
import scrapy
from scrapy.pipelines.images import ImagesPipeline
import os
from urllib.parse import urlparse
from pymongo import MongoClient


# class ItemInstaPhotosPipeline(ImagesPipeline):
#     def get_media_requests(self, item, info):
#         if item['profile_pic_url']:
#             try:
#                 yield scrapy.Request(item['profile_pic_url'], meta=item)
#             except Exception as err:
#                 print(err)
#
#     def file_path(self, request, response=None, info=None, ):
#         item = request.meta
#         return 'files/' + item['name'] + '/' + os.path.basename(urlparse(request.url).path)
#
#     def item_completed(self, results, item, info):
#         if results:
#             item['photos'] = [itm[1] for itm in results if itm[0]]
#         return item
class DataBasePipeline:
    def __init__(self):
        client = MongoClient('mongodb://localhost:27017/')
        self.mongo_base = client.gbscrapy

    def process_item(self, item, spider):
        collection = self.mongo_base['instausers']
        collection.update_one(item, {'$set': item}, upsert=True)
        return item

