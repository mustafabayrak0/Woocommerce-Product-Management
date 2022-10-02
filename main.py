def parse_xml(xml_url, parse_xml_first_parameter, parse_xml_second_parameter):
    response = (requests.get(xml_url))
    data = xmltodict.parse(response.content)
    return data[parse_xml_first_parameter][parse_xml_second_parameter]


def group_variations(products_in_xml):
    index_list = []
    codes_list = []
    for i in range(len(products_in_xml)):
        temp_list = []
        if products_in_xml[i]["ws_code"] not in index_list:
            index_list.append(products_in_xml[i]["code"])
            temp_list.append(products_in_xml[i]["code"])
            new_string_1 = string_formatter(products_in_xml[i]["ws_code"])
            for j in range(i + 1, len(products_in_xml)):
                new_string_2 = string_formatter(products_in_xml[j]["ws_code"])
                if new_string_1 == new_string_2:
                    temp_list.append(products_in_xml[j]["code"])
                    index_list.append(products_in_xml[j]["code"])
            codes_list.append(temp_list)
    return codes_list


def manipulate_xml(products_in_xml, variation_groups_list, vat_rate):
    for i in products_in_xml:

        # price manipulation
        i["price_list"] = str(math.floor(float(i["price_list"]) * ((100 + vat_rate) / 100)) + 0.99)
        i["price_special_vat_included"] = str(math.floor(float(i["price_special_vat_included"])) + 0.99)

        # images list manipulation
        images = []
        try:
            for j in i["images"]["img_item"]:
                images.append({"src": f"{j}"})
            parent_category = i["cat2name"]
            child_category = i["cat3name"]
        except KeyError:
            pass
        i["images"] = images

        # stock status manipulation
        if i["stock"] == "0":
            i["unit"] = "outofstock"
        else:
            i["unit"] = "instock"

        # category manipulation
        i["category_path"] = [{"name": f"{parent_category}"}, {"name": f"{child_category}"}]

        # type manipulation
        for group_list in variation_groups_list:
            if len(group_list) == 1:
                for product_id in group_list:
                    for product in products_in_xml:
                        if product["code"] == f"{product_id}":
                            product["model"] = "simple"
            else:
                for product_ids in group_list:
                    for product in products_in_xml:
                        if product["code"] == f"{product_id}":
                            product["model"] = "variable"

        # variation manipulation

    return products_in_xml


def woocommerce_api_connection(consumer_key, consumer_secret, store_url):
    wcapi = API(
        url=store_url,
        consumer_key=consumer_key,
        consumer_secret=consumer_secret,
        wp_api=True,
        version="wc/v3"
    )
    return wcapi


def woocommerce_list_products(wcapi, store_url, consumer_key, per_page, page_number_range):
    payload = json.dumps({
        "id": "test_id",
        "name": "test_name",
        "sku": "test_sku",
        "type": "simple",
        "regular_price": "2229",
        "description": "test_description",
        "tags": "test_tag",
        "sale_price": "test_sale_price",
        "stock_quantity": "test_stock_quantity",
        "categories": [
            {
                "name": "test_category"
            },
            {
                "name": "test_category"
            }
        ],
        "images": [
            {
                "src": "https://demo.woothemes.com/woocommerce/wp-content/uploads/sites/56/2013/06/T_2_front.jpg"
            },
            {
                "src": "https://demo.woothemes.com/woocommerce/wp-content/uploads/sites/56/2013/06/T_2_back.jpg"
            }
        ]
    })
    headers = {
        'Content-Type': 'application/json',
        'Authorization': 'Basic Y2tfY2E2MDFlZDdhYzkwNjYyZTk0NzQxOTg1YWVlODRjM2RmN2MzNGRjMTpjc19hZmYxMWVhODQxZGVkNjA4MmMzNWQzYTMyODVjNTYwZmJiMjljM2I1"'
    }

    products_in_limante = []
    for page_number in range(1, page_number_range):
        url = f"{store_url}/wp-json/wc/v3/products?{per_page}=100&page={page_number}"
        response = requests.request("GET", url, headers=headers, data=payload)
        if len(response.json()) != 0:
            products_in_limante.append(response.json())

    return products_in_limante


def woocommerce_create_products(wcapi, products_in_xml):
    for i in products_in_xml:
        name = i["name"]
        product_id = i["code"]
        sku = i["ws_code"]
        description = i["detail"]
        images = i["images"]
        category = i["category_path"]
        normal_price = i["price_list"]
        sale_price = i["price_special_vat_included"]
        tag = i["brand"]
        stock_quantity = i["stock"]
        stock_status = i["unit"]
        data = {
            "id": f"{product_id}",
            "name": f"{name}",
            "sku": f"{sku}",
            "description": f"{description}",
            "catalog_visibility": "visible",
            "type": "variable",
            "tax_status": "none",
            "stock_quantity": stock_quantity,
            "location": "0",
            "published": "1",
            "variation": "",
            "images": images,
            "categories": category,
            "tags": tag,
            "regular_price": normal_price,
            "sale_price": sale_price,
            "purchasable": True,
            "stock_status": stock_status,
            "attributes": [
                {"name": "Size", "visible": True, "variation": True, "options": [
                    "Black",
                    "Green"
                ]},
            ],
        }
        wcapi.post("products", data).json()


def woocommerce_update_products(wcapi, products_in_limante, products_in_xml):
    data = {
        "regular_price": "24.54"
    }
    wcapi.put(f"products/{data}", data).json()


def woocommerce_delete_products(wcapi, product_id):
    try:
        wcapi.delete(f"products/{product_id}", params={"force": True})
    except requests.exceptions.ReadTimeout:
        time.sleep(5)


def string_formatter(string_to_format):
    new_string = ""
    for i in string_to_format:
        if i.isdigit():
            new_string += i
    return new_string


def program_flow(wcapi, products_in_xml, products_in_limante):
    id_list_of_xml = []
    id_list_of_limante = []
    created_products_count = 0
    updated_products_count = 0
    deleted_products_count = 0
    for i in products_in_limante:
        id_list_of_limante.append(i["code"]),
    for j in products_in_xml:
        id_list_of_xml.append(j["code"])
    for i in id_list_of_limante:
        if i["code"] not in id_list_of_xml:
            woocommerce_delete_products(wcapi, i["code"])
            deleted_products_count += 1

    for j in id_list_of_xml:
        if j not in id_list_of_limante:
            woocommerce_create_products(wcapi, products_in_xml)
            created_products_count += 1
        else:
            woocommerce_update_products(wcapi, products_in_limante, products_in_xml)
            updated_products_count += 1
    print(
        f"{len(id_list_of_xml)} products in xml\n{len(id_list_of_limante)}products in limante\n{created_products_count}"
        f"products created\n{updated_products_count}products updated\n{deleted_products_count}products deleted")


if __name__ == '__main__':
    import requests
    import xmltodict
    from woocommerce import API
    import requests
    import json
    import time
    import math

    # urls
    xmlUrl = "YourXmlUrl"
    storeUrl = "YourStoreUrl"

    # keys
    consumerKey = "YourConsumerKey"
    consumerSecret = "YourConsumerSecret"

    # parametric values
    parseXmlFirstParameter = "products"
    parseXmlSecondParameter = "product"
    perPage = 100
    pageNumberRange = 40
    vatRate = 8

    # program flow
    productsInXml = parse_xml(xmlUrl, parseXmlFirstParameter, parseXmlSecondParameter)
    variationGroupsList = group_variations(productsInXml)
    wcapi = woocommerce_api_connection(consumerKey, consumerSecret, storeUrl)
    productsInLimante = woocommerce_list_products(wcapi, storeUrl, consumerKey, perPage, pageNumberRange)
    productsInXml = manipulate_xml(productsInXml, variationGroupsList, vatRate)
    # program_flow(wcapi, productsInXml, productsInLimante)
