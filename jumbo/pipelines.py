# create table skus (sku varchar(20) PRIMARY KEY);
# create table product(sku varchar(20) PRIMARY KEY, name varchar(255), price FLOAT, weight int(11), cal int(11), fats float, carbs float, prots float, scrape DATETIME);
import MySQLdb

class SKUPipeline(object):
    def __init__(self):
        self.dbhost = "localhost"
        self.dbname = ""
        self.dbuser = ""
        self.dbpass = ""

    def open_spider(self, spider):
        self.db = MySQLdb.connect(host=self.dbhost, user=self.dbuser, passwd=self.dbpass, db=self.dbname)
        self.cur = self.db.cursor()

    def close_spider(self, spider):
        self.db.close()

    def process_item(self, item, spider):
        #query = "INSERT INTO skus VALUES('%s')" % (item['sku'])
        query = "INSERT INTO product VALUES('%s', '%s', '%f', '%d', '%d', '%f', '%f', '%f', now())" % (item["sku"], item["name"], item["price"], item["weight"], item["cal"], item["fat"], item["carb"], item["prot"])
        self.cur.execute(query)
        self.db.commit()
        return item
