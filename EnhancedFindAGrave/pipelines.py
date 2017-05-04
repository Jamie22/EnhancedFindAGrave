from string import Template

# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html

html_header = """<!DOCTYPE html>
<html>
    <head>
        <title>Enhanced Find A Grave search results</title>
        <style>
            .graveListing
            {
                padding-bottom:20px;
            }
        </style>
    </head>
    <body>"""

html_template = Template("""
        <div class="graveListing">
            <a href="https://findagrave.com/cgi-bin/fg.cgi?page=gr&GRid=$graveID">$lastName, $firstName 
            <i>$maidenName</i></a> $gravePhoto
            <br/>
            $birth – $death
            <br/>
            $cemetery
            <br/>
            $location
        </div>
""")

html_footer = """
    </body>
</html>"""


class HtmlWriterPipeline(object):
    def open_spider(self, spider):
        self.file = open('searchresults.html', 'w')
        self.file.write(html_header)

    def close_spider(self, spider):
        self.file.write(html_footer)
        self.file.close()

    def process_item(self, item, spider):
        html_entry = html_template \
            .substitute(graveID=item['grave_id'], lastName=item['name_last'], firstName=item['name_first'],
                        maidenName=item['name_maiden'] or '', gravePhoto='*' if item['has_grave_photo'] else '',
                        birth=item['birth'], death=item['death'], cemetery=item['cemetery'], location=item['location'])

        self.file.write(html_entry)
        return item
