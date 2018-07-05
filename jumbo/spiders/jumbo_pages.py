# -*- coding: utf-8 -*-

import os
import json
import sys
reload(sys)
sys.setdefaultencoding('utf-8')
import scrapy
import MySQLdb

class JumboSpider(scrapy.Spider):
    name = 'jumbo'
    curr_page = 0
    list_url = "https://www.jumbo.com/producten?SortingAttribute=ALPHABETICAL_ASCENDING"
    product_url = "https://www.jumbo.com/f/"

    def __init__(self, maxpages=0, recheck=0, delay=1.0, *args, **kwargs):
        super(JumboSpider, self).__init__(*args, **kwargs)
        self.maxpages = int(maxpages)
        self.download_delay = float(delay);
        if (recheck == "0"):
            self.recheck = 0
            self.dbhost = "localhost"
            self.dbname = "jumbo"
            self.dbuser = "jumbousr"
            self.dbpass = "jumbopass"
            self.db = MySQLdb.connect(host=self.dbhost, user=self.dbuser, passwd=self.dbpass, db=self.dbname)
            self.cur = self.db.cursor()
        else:
            self.recheck = 1

    def check_existing(self, sku):
        query = "SELECT COUNT(1) FROM product WHERE sku = '%s'" % sku
        self.cur.execute(query)
        if self.cur.fetchone()[0]:
            return True
        else:
            return False

    def start_requests(self):
        for i in range(self.maxpages):
            print "------ SCRAPING: %s?PageNumber=%d" % (self.list_url, i)
            yield scrapy.Request("%s&PageNumber=%d" % (self.list_url, i), callback=self.parse)

    def parse(self, response):
        skus = response.xpath('//li["data-product-sku"]/@data-product-sku').extract()
        for sku in skus:
            #yield {'sku': k}
            if (self.recheck == 1):
                yield scrapy.Request("%s%s" % (self.product_url, sku),  meta={'sku': sku}, callback=self.parse_product)
            else:
                if (not self.check_existing(sku)):
                    yield scrapy.Request("%s%s" % (self.product_url, sku),  meta={'sku': sku}, callback=self.parse_product)
                else:
                    print "SKU %s already checked" % sku

    def parse_product(self, response):
        sku = response.meta['sku']
        name = response.xpath('//div[@class="jum-column-main "]//h1//text()').extract()[0].replace("'"," ")
        price_text = response.xpath('//div[@class="jum-add-product"]//span[@class="jum-price-format"]//text()').extract()
        price = 0
        if (len(price_text) > 1):
            price = int(price_text[0]) + float(price_text[1])/100
        else:
            price = float(price_text[0])
        weight ="0"
        if (len(response.xpath('//div[@class="jum-add-product"]//span[@class="jum-pack-size"]//text()').extract()) > 0):
            weight = response.xpath('//div[@class="jum-add-product"]//span[@class="jum-pack-size"]//text()').extract()[0]
        if ("x" in weight):
            weight = float(0)
        elif ("ml" in weight):
            weight = float(weight.replace("ml","").strip().replace(",","."))
        elif ("liter" in weight):
            weight = float(weight.replace("liter","").strip().replace(",","."))*1000
        elif ("Kg" in weight):
            weight = float(weight.replace("Kg","").strip().replace(",","."))*1000
        elif ("KG" in weight):
            weight = float(weight.replace("KG","").strip().replace(",","."))*1000
        elif ("kg" in weight):
            weight = float(weight.replace("kg","").strip().replace(",","."))*1000
        elif ("gram" in weight):
            weight = float(weight.replace("gram","").strip().replace(",","."))
        elif ("g." in weight):
            weight = float(weight.replace("g.","").strip().replace(",","."))
        elif ("g" in weight):
            weight = float(weight.replace("g","").strip().replace(",","."))
        ## solve liter, l, cl, and 4 x 50, etc
        else:
            weight = float(0)
        cal = 0
        fat = 0
        carb = 0
        prot = 0

        # get some idea about the nutrition table
        columns = len(response.xpath('//th[@class="jum-nutiriton-heading"]'))
        if columns > 0:
            index = 1
            if columns > 1:
                for i in range(1, columns+1):
                    heading = response.xpath('//th[@class="jum-nutiriton-heading"][%d]//text()' % i).extract()
                    if len(heading) > 0:
                        if '100' in heading[0]:
                            index = i
                            break
            #print "INDEX :: %d" % index

            # extract nutrition data - calories
            cal = float(0)
            energie_sel_text = "none"
            if (len(response.xpath('//tr/th[text() = "energie"]')) > 0):
                energie_sel_text = "energie"
            if (len(response.xpath('//tr/th[text() = "Energie"]')) > 0):
                energie_sel_text = "Energie"
            if (len(response.xpath('//tr/th[text() = "Energie (kcal)"]')) > 0):
                energie_sel_text = "Energie (kcal)"
            if (len(response.xpath('//tr/th[text() = "-Energie"]')) > 0):
                energie_sel_text = "-Energie"
            if (len(response.xpath('//tr/th[text() = "Energie:"]')) > 0):
                energie_sel_text = "Energie:"
            if (len(response.xpath('//tr/th[text() = "Energie (kJ / kcal)"]')) > 0):
                energie_sel_text = "Energie (kJ / kcal)"
            if (energie_sel_text != "none"):
                if ((energie_sel_text == "Energie (kcal)") | (energie_sel_text == "Energie (kJ / kcal)")):
                    cal = response.xpath('//tr/th[text() = "%s"]/following-sibling::td[%d]//text()' % (energie_sel_text, index)).extract()[0].replace(",",".").replace("kcal","").replace("(","").replace(")","")
                    if "/" in cal:
                        cal = float(cal.split("/")[1])
                    else:
                        cal = float(cal)
                elif len(response.xpath('//tr/th[text() = "%s"]/following-sibling::td[%d]//text()' % (energie_sel_text, index))) > 0:
                    if ('kcal' in response.xpath('//tr/th[text() = "%s"]/following-sibling::td[%d]//text()' % (energie_sel_text, index)).extract()[0]):
                        cal_arr = response.xpath('//tr/th[text() = "%s"]/following-sibling::td[%d]//text()' % (energie_sel_text, index)).extract()[0].replace("kcal"," kcal").split()
                        cal_index = 0
                        cal_i = 0
                        for txt in cal_arr:
                            if 'kcal' in txt:
                                cal_index = cal_i
                            cal_i += 1
                        cal = cal_arr[cal_index-1].replace(",",".").replace("kcal","").replace("(","").replace(")","")
                        if "/" in cal:
                            cal = float(cal.split("/")[1])
                        else:
                            cal = float(cal)
                else:
                    cal_selector = '//tr/th[text() = "%s"]/parent::tr/following-sibling::tr[1]/td[%d]/text()' % (energie_sel_text, index)
                    cal_text = response.xpath(cal_selector).extract()
                    if 'kcal' in cal_text[0]:
                        cal = cal_text[0].split()[0].replace("kcal","").replace(",",".").replace("(","").replace(")","")
                        if "/" in cal:
                            cal = float(cal.split("/")[1])
                        else:
                            cal = float(cal)
            else:
                print "---- [WARN] sku %s no fat found" % sku

            # extract nutrition data - fats
            fat_sel_text = "none"
            if (len(response.xpath('//tr/th[text() = "vetten"]')) > 0):
                fat_sel_text = "vetten"
            if (len(response.xpath('//tr/th[text() = "Vet"]')) > 0):
                fat_sel_text = "Vet"
            if (len(response.xpath('//tr/th[text() = "Vet:"]')) > 0):
                fat_sel_text = "Vet:"
            if (len(response.xpath('//tr/th[text() = "Vetten"]')) > 0):
                fat_sel_text = "Vetten"
            if (len(response.xpath('//tr/th[text() = "-Vetten"]')) > 0):
                fat_sel_text = "-Vetten"
            if (len(response.xpath('//tr/th[text() = "Vetten:"]')) > 0):
                fat_sel_text = "Vetten:"
            if (len(response.xpath('//tr/th[text() = "Vetten (g)"]')) > 0):
                fat_sel_text = "Vetten (g)"
            if fat_sel_text != "none":
                fat_selector = '//tr/th[text() = "%s"]/following-sibling::td[%d]//text()' % (fat_sel_text, index)
                fat_text = response.xpath(fat_selector).extract()
                fat = fat_text[0]
                if 'g' in fat_text[0]:
                    fat_arr = fat_text[0].split()
                    fat_index = 0
                    for txt in fat_arr:
                        if txt == 'g':
                            break
                        else:
                            fat_index += 1
                    fat = float(fat_arr[fat_index-1].replace("<","").replace(">","").replace("g","").replace(",","."))
                else:
                    fat = float(fat.replace(",","."))
            else:
                print "---- [WARN] sku %s no fat found" % sku

            # extract nutrition data - carbs
            carb_sel_text = "none"
            if (len(response.xpath('//tr/th[text() = "koolhydraten"]')) > 0):
                carb_sel_text = "koolhydraten"
            if (len(response.xpath('//tr/th[text() = "Koolhydraten"]')) > 0):
                carb_sel_text = "Koolhydraten"
            if (len(response.xpath('//tr/th[text() = "-Koolhydraten"]')) > 0):
                carb_sel_text = "-Koolhydraten"
            if (len(response.xpath('//tr/th[text() = "Koolhydraten:"]')) > 0):
                    carb_sel_text = "Koolhydraten:"
            if (len(response.xpath('//tr/th[text() = "Koolhydraten (g)"]')) > 0):
                carb_sel_text = "Koolhydraten (g)"
            if carb_sel_text != "none":
                carb_selector = '//tr/th[text() = "%s"]/following-sibling::td[%d]//text()' % (carb_sel_text, index)
                carb_text = response.xpath(carb_selector).extract()
                carb = carb_text[0]
                if 'g' in carb_text[0]:
                    carb_arr = carb_text[0].split()
                    carb_index = 0
                    for txt in carb_arr:
                        if txt == 'g':
                            break
                        else:
                            carb_index += 1
                    carb = float(carb_arr[carb_index-1].replace("<","").replace("g","").replace(",","."))
                else:
                    carb = float(carb.replace(",","."))
            else:
                print "---- [WARN] sku %s no carbs found" % sku


            # extract nutrition data - proteins
            prot_sel_text = "none"
            if (len(response.xpath('//tr/th[text() = "eiwitten"]')) > 0):
                prot_sel_text = "eiwitten"
            if (len(response.xpath('//tr/th[text() = "Eiwit"]')) > 0):
                prot_sel_text = "Eiwit"
            if (len(response.xpath('//tr/th[text() = "Eiwit:"]')) > 0):
                prot_sel_text = "Eiwit:"
            if (len(response.xpath('//tr/th[text() = "Eiwitten"]')) > 0):
                prot_sel_text = "Eiwitten"
            if (len(response.xpath('//tr/th[text() = "Eiwitten:"]')) > 0):
                prot_sel_text = "Eiwitten:"
            if (len(response.xpath('//tr/th[text() = "-Eiwitten"]')) > 0):
                prot_sel_text = "-Eiwitten"
            if (len(response.xpath('//tr/th[text() = "Eiwitten (g)"]')) > 0):
                prot_sel_text = "Eiwitten (g)"
            if prot_sel_text != "none":
                prot_selector = '//tr/th[text() = "%s"]/following-sibling::td[%d]//text()' % (prot_sel_text, index)
                prot_text = response.xpath(prot_selector).extract()
                prot = prot_text[0]
                if 'g' in prot_text[0]:
                    prot_arr = prot_text[0].split()
                    prot_index = 0
                    for txt in prot_arr:
                        if txt == 'g':
                            break
                        else:
                            prot_index += 1
                    prot = float(prot_arr[prot_index-1].replace("<","").replace("g","").replace(",","."))
                else:
                    prot = float(prot.replace(",","."))
            else:
                print "---- [WARN] sku %s no prot found" % sku

        # test
        if (1 == 1):
            print "--------------------------------"
            print "SKU: %s" % sku
            print "NAME: %s" % name
            print "PRICE: %f" % price
            print "WEIGHT: %s" % weight
            print "CAL: %s" % cal
            print "FAT: %s" % fat
            print "CARB: %s" % carb
            print "PROT: %s" % prot

        # add to db
        yield {
        'sku': sku,
        'name': name,
        'price': price,
        'weight': weight,
        'cal': cal,
        'fat': fat,
        'carb': carb,
        'prot': prot
        }
