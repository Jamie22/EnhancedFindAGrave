import datetime

import scrapy
from dateutil.parser import parse
from collections import Counter

from EnhancedFindAGrave import searchparameters as param
from EnhancedFindAGrave.items import GraveItem


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

    search_url = 'https://www.findagrave.com/memorial/search?firstname=' + param.first_name + '&middlename=' \
                 + param.middle_name + '&lastname=' + param.last_name + '&birthyearfilter=' + url_birth_rel \
                 + '&birthyear=' + url_birth_year + '&deathyearfilter=' + url_death_rel + '&deathyear=' \
                 + url_death_year + '&locationId=' + param.location_id + '&datefilter=' + param.date_filter \
                 + '&orderby=' + param.order + '&photofilter=' + param.photo_filter

    if param.include_nickname:
        search_url += '&includeNickName=true'

    if param.include_maiden:
        search_url += '&includeMaidenName=true'

    if param.partial_name:
        search_url += '&partialLastName=true'

    if param.memorial_type == 'famous':
        search_url += '&famous=true'

    if param.memorial_type == 'sponsored':
        search_url += '&sponsored=true'

    if param.has_flowers:
        search_url += '&flowers=true'

    return [search_url]


class GraveSpider(scrapy.Spider):
        name = "grave_spider"
        start_urls = generate_search_url()
        page = 1

        def parse(self, response):
            for grave in response.css('.memorial-list-data .memorial-item'):

                birth_death = grave.css('.birthDeathDates::text').extract_first().split(' – ')
                birth = birth_death[0]

                try:
                    death = birth_death[1]
                except IndexError:
                    death = ''

                grave_id = grave.css('a::attr(id)').extract_first().split('-')[1]

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

                thumbnail = grave.css('.pic-wrapper img::attr(src)').extract_first()
                full_name = ''.join(grave.css('.name-grave').xpath('i/text()').extract()).rsplit(' ', 1)
                name_first = full_name[0].strip()
                name_last = full_name[1].strip()
                name_maiden = grave.css('.name-grave i i::text').extract_first()
                has_grave_photo = 'No grave photo' not in grave.extract()
                has_flowers = bool(grave.css('.icon-flowers').extract_first())
                is_famous = bool(grave.css('.icon-famous').extract_first())
                is_sponsored = bool(grave.css('.sponsored').extract_first())
                cemetery = grave.css('.memorial-item---cemet form button::text').extract_first()
                location = ' '.join(grave.css('.addr-cemet::text').extract_first().split())

                item = GraveItem()
                item['thumbnail'] = thumbnail
                item['name_first'] = name_first
                item['name_last'] = name_last
                item['name_maiden'] = name_maiden
                item['has_grave_photo'] = has_grave_photo
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
                    request = scrapy.Request("https://www.findagrave.com/memorial/" + grave_id,
                                             callback=self.parse_grave)
                    request.meta['item'] = item
                    yield request
                else:
                    yield item

            if len(response.css('.memorial-list-data .memorial-item')) > 0:
                self.page += 1

                yield scrapy.Request(
                    self.start_urls[0] + '&page=' + str(self.page),
                    callback=self.parse
                )

        # This method is called when the birth is unknown. This will check if the age at death is given on the grave's
        # page, and use it to calculate an estimated birth year
        def parse_grave(self, response):
            item = response.request.meta['item']
            death_year = item['death_year']
            bio = ' '.join(response.css('#fullBio::text').extract())
            inscription = ' '.join(response.css('#inscriptionValue::text').extract())
            grave_details = ' '.join(response.css('#gravesite-details::text').extract())
            description = 'beg ' + (bio or '') + ' ins ' + (inscription or '') + ' gs ' + (grave_details or '') + ' end'
            description = description.replace(':', ' ').replace('-', ' ').replace('.', ' ').lower()
            words_description = description.split()
            word_count = Counter(words_description)
            age = ''

            # Try to parse the age at death if description does not state multiple ages
            if word_count['years'] == 1:
                age = words_description[words_description.index('years') - 1]
            elif word_count['year'] == 1:
                age = words_description[words_description.index('year') - 1]
            elif word_count['age'] == 1:
                age = words_description[words_description.index('age') + 1]
            elif word_count['aged'] == 1:
                age = words_description[words_description.index('aged') + 1]

            if age and 'month' in words_description[words_description.index(age) + 1]:
                age = '0'
            else:
                age = ''.join(c for c in age if c.isdigit())

            # If age is found, use it to calculate estimated birth year
            if age:
                birth_year = death_year - int(age)

                # Skip this grave entry if birth year is outside the given range
                if (param.min_birth_year != 0 and birth_year < param.min_birth_year) or \
                        (param.max_birth_year != 0 and birth_year > param.max_birth_year):
                    return

                item['birth_year'] = birth_year
                item['birth'] = 'Est. ' + str(birth_year)

            yield item
