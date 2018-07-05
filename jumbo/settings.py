# -*- coding: utf-8 -*-

BOT_NAME = 'jumbo'

SPIDER_MODULES = ['jumbo.spiders']
NEWSPIDER_MODULE = 'jumbo.spiders'

ITEM_PIPELINES = {
    'jumbo.pipelines.SKUPipeline': 300
}
