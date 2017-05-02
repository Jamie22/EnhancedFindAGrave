import scrapy
import datetime
from string import Template
from dateutil.parser import parse
import searchparameters as param

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
            <a href="https://findagrave.com/cgi-bin/fg.cgi?page=gr&GRid=$graveID">$lastName, $firstName</a> $gravePhoto
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


# Generate the URL to start scraping from based on the given search parameters
def generate_search_url():
    url_birth_rel = 'all'
    url_birth_year = ''

    if param.max_death_year == 0:
        url_death_rel = 'all'
        url_death_year = ''
    else:
        url_death_rel = 'before'
        url_death_year = str(param.max_death_year + 1)

    search_url = 'https://findagrave.com/cgi-bin/fg.cgi?page=gsr&GSfn=' + param.first_name + '&GSmn=' \
                 + param.middle_name + '&GSln=' + param.last_name + '&GSbyrel=' + url_birth_rel + '&GSby=' \
                 + url_birth_year + '&GSdyrel=' + url_death_rel + '&GSdy=' + url_death_year + '&GScntry=' \
                 + str(param.country_id) + '&GSst=' + str(param.state_id) + '&GSgrid=&df=' + param.date_filter \
                 + '&GSob=' + param.order

    if param.include_maiden:
        search_url += '&GSiman=1'

    if param.partial_name:
        search_url += '&GSpartial=1'

    return [search_url]


def write_html_entry(file, item):
    html_entry = html_template \
        .substitute(graveID=item['grave_id'], lastName=item['name_last'], firstName=item['name_first'],
                    gravePhoto='*' if item['has_grave_photo'] else '', birth=item['birth'], death=item['death'],
                    cemetery=item['cemetery'], location=item['location'])

    file.write(html_entry)


class GraveItem(scrapy.Item):
    name_first = scrapy.Field()
    name_last = scrapy.Field()
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


class GraveSpider(scrapy.Spider):
        name = "grave_spider"
        start_urls = generate_search_url()

        def __init__(self, *a, **kw):
            super(GraveSpider, self).__init__(*a, **kw)
            file = open('searchresults.html', 'w')
            file.write(html_header)

        def parse(self, response):
            file = open('searchresults.html', 'a')

            GRAVE_SELECTOR = '//tr[@bgcolor="DCD0CF"]'

            for grave in response.xpath(GRAVE_SELECTOR):

                birth_death = grave.xpath('td[@align="LEFT"]/font[@class="minus1"]/text()').extract_first()
                birth = birth_death.partition('b.')[-1].rpartition('d.')[0].strip()
                death = birth_death.partition('d.')[-1].strip()
                grave_id = grave.xpath('td[@align="LEFT"]/font[@color="DCD0CF"]/text()').extract_first().strip()

                # Parse birth and death years. 1 means unknown
                birth_year = 1
                death_year = 1

                try:
                    birth_year = parse(birth, default=datetime.date(1,1,1), fuzzy=True).year
                except:
                    pass

                try:
                    death_year = parse(death, default=datetime.date(1,1,1), fuzzy=True).year
                except:
                    pass

                # Skip this grave entry if the birth or death year is known and is outside the given range
                if birth_year != 1 and ((param.min_birth_year != 0 and birth_year < param.min_birth_year)
                                        or (param.max_birth_year != 0 and birth_year > param.max_birth_year)):
                    continue

                if death_year != 1 and ((param.min_death_year != 0 and death_year < param.min_death_year)
                                        or (param.max_death_year != 0 and death_year > param.max_death_year)):
                    continue

                full_name = grave.xpath('td[@align="LEFT"]/a/text()').extract_first().split(', ')
                name_first = full_name[1]
                name_last = full_name[0]
                has_grave_photo = bool(grave.xpath('td[@align="LEFT"]/a/img[contains(@src, "headstone.gif")]')
                                       .extract_first())
                has_person_photo = bool(grave.xpath('td[@align="LEFT"]/a/img[contains(@src, "photo.gif")]')
                                        .extract_first())
                has_flowers = bool(grave.xpath('td[@align="LEFT"]/a/img[contains(@src, "flowers.gif")]')
                                   .extract_first())
                is_famous = bool(grave.xpath('td[@align="LEFT"]/a/img[contains(@src, "famousStar.png")]')
                                 .extract_first())
                is_sponsored = bool(grave.xpath('td[@align="LEFT"]/a/img[contains(@src, "heart.gif")]').extract_first())
                cemetery = grave.xpath('td[@align="RIGHT"]/font[@class="minus1"]/a/text()').extract_first()
                list_location = grave.xpath('td[@align="RIGHT"]/font[@class="minus1"]/text()').extract()
                list_location = list(filter(lambda x: not x.isspace(), list_location))
                location = ', '.join(list_location)

                item = GraveItem()
                item['name_first'] = name_first
                item['name_last'] = name_last
                item['has_grave_photo'] = has_grave_photo
                item['has_person_photo'] = has_person_photo
                item['has_flowers'] = has_flowers
                item['is_famous'] = is_famous
                item['is_sponsored'] = is_sponsored
                item['birth'] = birth
                item['death'] = death
                item['birth_year'] = birth_year
                item['death_year'] = death_year
                item['grave_id'] = grave_id
                item['cemetery'] = cemetery
                item['location'] = location

                # If birth year is not known but death year is, parse the grave's page in case it has the age at death
                if birth_year == 1 and death_year != 1:
                    request = scrapy.Request("https://findagrave.com/cgi-bin/fg.cgi?page=gr&GRid=" + grave_id,
                                             callback=self.parse_grave)
                    request.meta['item'] = item
                    yield request
                else:
                    write_html_entry(file, item)
                    yield item

            NEXT_PAGE_SELECTOR = '//td[@align="RIGHT"]/a[contains(text(), "Records ")]/@href'
            next_page = response.xpath(NEXT_PAGE_SELECTOR).extract_first()
            if next_page:
                yield scrapy.Request(
                    response.urljoin(next_page),
                    callback=self.parse
                )

        # This method is called when the birth is unknown. This will check if the age at death is given on the grave's
        # page, and use it to calculate an estimated birth year
        def parse_grave(self, response):
            item = response.request.meta['item']
            death_year = item['death_year']
            lines_description = response.xpath('//td[@valign="top"][@colspan="2"]/text()').extract()
            description = ' '.join(lines_description)
            description = description.replace(':', '').replace('-', '').lower()
            words_description = description.split()
            age = ''

            # Try to parse the age at death
            try:
                age = words_description[words_description.index('age') + 1]
            except:
                try:
                    age = words_description[words_description.index('aged') + 1]
                except:
                    try:
                        age = words_description[words_description.index('years') - 1]
                    except:
                        pass

            # If age is found, use it to calculate estimated birth year
            if age:
                age = ''.join(c for c in age if c.isdigit())
                birth_year = death_year - int(age)

                # Skip this grave entry if birth year is outside the given range
                if (param.min_birth_year != 0 and birth_year < param.min_birth_year) or \
                        (param.max_birth_year != 0 and birth_year > param.max_birth_year):
                    return

                item['birth_year'] = birth_year
                item['birth'] = 'Est. ' + str(birth_year)

            file = open('searchresults.html', 'a')
            write_html_entry(file, item)

            yield item

        def closed(self, reason):
            file = open('searchresults.html', 'a')
            file.write(html_footer)