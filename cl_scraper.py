import argparse
import re
import sys
try:
    import bs4
    import requests
except ImportError:
    sys.stderr.write("Please make sure you have both beautiful soup and "
        "requests installed on this machine.")
    sys.exit(1)

# The GET query to go back a few pages
PAGE_QUERY="?s={}&"

# Map a section title to it's name in the craigslist url
SECTION_MAP= {
    "antiques" : "ata",
    "appliances" : "ppa",
    "arts+crafts" : "ara",
    "atv/utv/sno" : "sna",
    "auto parts" : "pta",
    "baby+kid" : "baa",
    "barter" : "bar",
    "beauty+hlth" : "haa",
    "bikes" : ["bia", "bip"],
    "boats" : ["boo", "bpa"],
    "books" : "bka",
    "business" : "bfa",
    "cars+trucks" : "cta",
    "cds/dvds/vhs" : "ema",
    "cell phones" : "moa",
    "clothes+acc" : "cla",
    "collectibles" : "cba",
    "computers" : ["sya", "syp"],
    "electronics" : "ela",
    "farm+garden" : "gra",
    "free" : "zip",
    "furniture" : "fua",
    "garage sale" : "gms",
    "general" : "foa",
    "heavy equip" : "hva",
    "household" : "hsa",
    "jewelry" : "jwa",
    "materials" : "maa",
    "motorcycles" : ["mca", "mpa"],
    "music instr" : "msa",
    "photo+video" : "pha",
    "rvs+camp" : "rva",
    "sporting" : "sga",
    "tickets" : "tia",
    "tools" : "tla",
    "toys+games" : "taa",
    "video gaming" : "vga",
    "wanted" : "waa"
}

def build_url(city, section):
    return "http://{}.craigslist.org/search/{}".format(city, section)

def get_page_text(url):
    # Will raise if it can't get the urn
    return requests.get(url).text

def get_postings(page_text):
    cl_soup = bs4.BeautifulSoup(page_text)
    return cl_soup.find_all("a", {"class" : "hdrlnk"})

def search_listings_page(url, pattern, search_body=False):
    postings = get_postings(get_page_text(url))

    matches = []

    for posting in postings:
        if pattern.match(posting.text):
            matches.append(posting)
        elif search_body:
            body_url = get_body_url(url, pattern)

            if search_posting_body(body_url, pattern):
                matches.append(posting)

    return matches

def search_posting_body(url, pattern):
    # TODO
    pass

def get_body_url(base_url, posting):
    base = base_url[:base_url.index("search")]
    return "{}{}".format(base, posting["href"])

def search_pages(base_url, pattern, depth=0, search_body=False):

    # Get the first page
    matches = search_listings_page(base_url, pattern)

    # Traverse down depth pages
    for i in xrange(depth):
        page_string = PAGE_QUERY.format(i * 100)
        page_url = "{}{}".format(base_url, page_string)

        matches.extend(search_listings_page(page_url, pattern, search_body))

    return matches

def format_results(base_url, results):
    result_strs = []
    for res in results:
        result_url = get_body_url(base_url, res)
        result_strs.append("\"{}\" -- {}".format(res.text, result_url))

    return '\n'.join(result_strs)

def parse_args(args):
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "pattern",
        type=str,
        help="The regular expression which you wish to scrape for.")

    parser.add_argument(
        "-c",
        "--city",
        type=str,
        nargs=1,
        default="seattle",
        help="The city in which you wish to search for {pattern}")

    # NOTE could add multiple sections
    parser.add_argument(
        "-s",
        "--section",
        type=str,
        default="free",
        help='The section of craigslist you wish to search. The special '
             'section "all" can be given to search the entire for sale section '
             'of craigslist.')

    parser.add_argument(
        "-b",
        "--search-body",
        action="store_true",
        help="Whether or not to search the body of each posting. By default, "
             "only the titles of each posting will be searched.")

    parser.add_argument(
        "-p",
        "--pages",
        type=int,
        default=5,
        help="The number of pages to search through, at 100 results per page.")

    return parser.parse_args()


def main():
    args = parse_args(sys.argv[1:])

    # Right now only one doesthe first page
    assert args.section in SECTION_MAP, "{} isn't a valid section".format(args.section)
    base_url = build_url(args.city, SECTION_MAP[args.section])

    pattern = re.compile(args.pattern)

    results = search_pages(base_url, pattern, depth=args.pages)

    result_str = format_results(base_url, results)

    # TODO output options: flat file, stdout, email
    print("Here are the results in {} on {} for {}"
            .format(args.city, args.section, args.pattern))
    print(result_str)

if __name__ == "__main__":
    main()
