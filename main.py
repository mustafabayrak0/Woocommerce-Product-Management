def parse_xml(xml_url, parse_xml_first_parameter, parse_xml_second_parameter):
    response = (requests.get(xml_url))
    data = xmltodict.parse(response.content)
    return data[parse_xml_first_parameter][parse_xml_second_parameter]


def woocommerce_api_connection(consumer_key, consumer_secret, store_url):
    wcapi = API(
        url=store_url,
        consumer_key=consumer_key,
        consumer_secret=consumer_secret,
        wp_api=True,
        version="wc/v3"
    )
    return wcapi


def manipulate_xml(products_in_xml, vat_rate):
    for i in products_in_xml:

        # price manipulation
        i["price_list"] = str(math.floor(float(i["price_list"]) * ((100 + vat_rate) / 100)) + 0.99)
        i["price_special_vat_included"] = str(math.floor(float(i["price_special_vat_included"])) + 0.99)

        # images and categories manipulation
        images = []
        try:
            for j in i["images"]["img_item"]:
                if type(j) is list:
                    for image_list in j:
                        for image in image_list:
                            images.append({"src": f"{image}"})
                elif type(j) is str:
                    k = i["images"]["img_item"]
                    images.append({"src": f"{j}"})
            parent_category = i["cat2name"]
            child_category = i["cat3name"]
        except KeyError:
            pass
        except Exception as ex:
            print(ex)
        i["images"] = images

        # stock status manipulation
        if i["stock"] == "0":
            i["unit"] = "outofstock"
        else:
            i["unit"] = "instock"

        # category manipulation
        i["category_path"] = [{"name": f"{parent_category}"}, {"name": f"{child_category}"}]

        # attributes manipulation
        options = []
        try:
            for j in (i["subproducts"]["subproduct"]):
                try:
                    options.append(j["type2"])
                except:
                    pass

        except:
            pass
        i["cat1name"] = options
        # variation manipulation
    return products_in_xml


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
        url = f"{store_url}/wp-json/wc/v3/products?per_page={per_page}&page={page_number}"
        response = requests.request("GET", url, headers=headers, data=payload)
        if len(response.json()) != 0:
            products_in_limante.append(response.json())

    return products_in_limante


def woocommerce_create_products(wcapi, products_in_xml, selected_product):
    i = selected_product
    name = i["name"]
    sku = i["ws_code"]
    description = i["detail"]
    images = i["images"]
    category = i["category_path"]
    normal_price = i["price_list"]
    sale_price = i["price_special_vat_included"]
    stock_quantity = int(i["stock"])
    stock_status = i["unit"]
    options = i["cat1name"]
    data = {
        "name": f"{name}",
        "sku": f"{sku}",
        "description": f"{description}",
        "type": "variable",
        "tax_status": "none",
        "images": images,
        "categories": category,
        "regular_price": normal_price,
        "sale_price": sale_price,
        "stock_quantity": stock_quantity,
        "stock_status": stock_status,
        "attributes": [
            {"name": "Size", "visible": True, "variation": False, "options": options},
        ],
    }
    for attempt in range(3):
        try:
            wcapi.post("products", data).json()
        except requests.exceptions.ReadTimeout:
            time.sleep(5)
        except Exception as ex:
            print(ex)
        else:
            break


def woocommerce_update_products(wcapi, products_in_xml, selected_product):
    i = selected_product
    name = i["name"]
    description = i["detail"]
    images = i["images"]
    category = i["category_path"]
    normal_price = i["price_list"]
    sale_price = i["price_special_vat_included"]
    stock_quantity = int(i["stock"])
    stock_status = i["unit"]
    options = i["cat1name"]
    data = {
        "name": f"{name}",
        "description": f"{description}",
        "catalog_visibility": "visible",
        "type": "simple",
        "tax_status": "none",
        "stock_quantity": stock_quantity,
        "images": images,
        "categories": category,
        "regular_price": normal_price,
        "sale_price": sale_price,
        "purchasable": True,
        "stock_status": stock_status,
        "stock_quantity": stock_quantity,
        "attributes": [
            {"name": "Size", "visible": True, "variation": False, "options": options},
        ],
    }
    for attempt in range(3):
        try:
            wcapi.put(f"products/{data}", data).json()
        except requests.exceptions.ReadTimeout:

            time.sleep(5)
        else:
            break


def woocommerce_delete_products(wcapi, product_id):
    for attempt in range(3):
        try:
            wcapi.delete(f"products/{product_id}", params={"force": True})
        except requests.exceptions.ReadTimeout:
            time.sleep(5+(5*attempt))
        else:
            break


def woocommerce_create_variations(wcapi, products_in_Limante):
    for i in products_in_Limante:
        for j in i:
            for option in attributes[0]["options"]:
                try:
                    variations = [{"name": "Size", "option": option}]
                    attributes = j["attributes"]
                    id = j["id"]
                    regular_price = j["regular_price"]
                except:
                    pass
                data = {
                    "regular_price": regular_price,
                    "sale_price": sale_price,
                    "attributes": variations,
                    "stock_quantity": "1",
                    "stock_status": "1",
                }
                wcapi.post(f"products/{j}/variations", data).json()


def string_formatter(string_to_format):
    new_string = ""
    for i in string_to_format:
        if i.isdigit():
            new_string += i
    return new_string


def program_flow(wcapi, products_in_xml, products_in_limante):
    sku_list_of_xml = []
    sku_list_of_limante = []
    sku_list_of_xml_for_delete = []
    created_products_count = 0
    updated_products_count = 0
    deleted_products_count = 0

    # Create sku lists
    for i in products_in_limante:
        if type(i) is list:
            j = i[0]
        else:
            j = i
        try:
            sku_list_of_limante.append(j["sku"])
        except Exception as ex:
            print(ex)
    for j in products_in_xml:
        sku_list_of_xml.append([j["ws_code"], j])
        sku_list_of_xml_for_delete.append(j["ws_code"])

    # Do operations
    for product in sku_list_of_xml:
        selectedProduct = product[1]
        if product[0] not in sku_list_of_limante:
            woocommerce_create_products(wcapi, products_in_xml, selectedProduct)
            created_products_count += 1
        else:
            woocommerce_update_products(wcapi, products_in_limante, selectedProduct)
            updated_products_count += 1

    for product in sku_list_of_limante:
        if product not in sku_list_of_xml_for_delete:
            woocommerce_delete_products(wcapi, i["code"])
            deleted_products_count += 1

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
    xmlUrl = "XmlUrl"
    storeUrl = "https://limante.com.tr"

    # keys
    consumerKey = "consumerKey"
    consumerSecret = "consumerSecret"

    # parametric values
    parseXmlFirstParameter = "products"
    parseXmlSecondParameter = "product"
    perPage = 100
    pageNumberRange = 40
    vatRate = 8

    # program flow
    productsInXml = parse_xml(xmlUrl, parseXmlFirstParameter, parseXmlSecondParameter)
    wcapi = woocommerce_api_connection(consumerKey, consumerSecret, storeUrl)
    productsInLimante = woocommerce_list_products(wcapi, storeUrl, consumerKey, perPage, pageNumberRange)
    productsInXml = manipulate_xml(productsInXml, vatRate)
    program_flow(wcapi, productsInXml, productsInLimante)
