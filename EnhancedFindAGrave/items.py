# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class GraveItem(scrapy.Item):
    name_first = scrapy.Field()
    name_last = scrapy.Field()
    name_maiden = scrapy.Field()
    has_grave_photo = scrapy.Field()
    has_person_photo = scrapy.Field()
    has_flowers = scrapy.Field()
    is_famous = scrapy.Field()
    is_sponsored = scrapy.Field()
    birth = scrapy.Field()
    death = scrapy.Field()
    birth_year = scrapy.Field()
    death_year = scrapy.Field()
    grave_id = scrapy.Field()
    cemetery = scrapy.Field()
    location = scrapy.Field()
