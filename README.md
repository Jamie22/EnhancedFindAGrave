## Enhanced Find A Grave Search

This program scrapes data off of Find a Grave using scrapy in order to perform a better search on birth and death years. The built in search functionality on Find A Grave has several issues. First, most graves in the database have an unknown birth year. If you search with a filter on birth year, these unknown birth graves can dissappear from the search results, even though Find A Grave doesn't know these graves fall on the wrong side of the filter. The same issue applies to death year, but graves with an unknown death year are uncommon. Furthermore, for birth and death year, it is possible to search before OR after a certain year, but not both. You cannot give a range of years to search.

This tool allows you to narrow down your search results futher by giving a range (minimum and maximum year) for birth and death. Furthermore, if the birth year is unknown, the scraper will go to the grave's description page to see if the age at death is given, and use that to calculate an estimated birth year. Graves will not get excluded from the results for having an unknown birth or death year.

### Usage

Set the search parameters in searchparameters.py. In command prompt, run scrapy runspider GraveSpider.py
An html file will be generated listing the graves that were found with links to their pages. Graves that have a grave photo are marked with an asterisk