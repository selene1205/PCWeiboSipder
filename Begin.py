from scrapy import cmdline

# cmdline.execute("scrapy crawl jiedaibao -s JOBDIR=crawls/jiedaibao".split())
# cmdline.execute("scrapy crawl ezubao -s JOBDIR=crawls/ezubao".split())
cmdline.execute("scrapy crawl qianbaowang -s JOBDIR=crawls/qianbaowang".split())
cmdline.execute("scrapy crawl xiaoyuandai -s JOBDIR=crawls/xioayuandai".split())
# cmdline.execute("scrapy crawl weibo -s JOBDIR=crawls/ezubao".split())
