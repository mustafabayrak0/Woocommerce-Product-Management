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
        version="wc/v3",
        timeout=80,
    )
    return wcapi


def manipulate_xml(products_in_xml, vat_rate):
    undefined_categories = []
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
        x = parent_category
        y = child_category
        # category manipulation
        categories = {"Alt Giyim": 83, "Etek": 68, "Pantolon": 69, "Dış Giyim": 76, "Ferace": 79, "Giy-Çık": 78,
                      "İ-Kap": 67, "Kaban": 80, "Mont": 81, "Trenç": 77, "Yelek": 82, "Kap": 15, "Üst Giyim": 84,
                      "Abaya": 72, "Bluz": 74, "Elbise": 75, "İkili Takım": 70, "Tulum": 73, "Tunik": 71, "Ceket": 85}
        try:
            a = categories[parent_category]
            i["category_path"] = [{"id": categories[parent_category]}, {"id": categories[child_category]}]
        except Exception as ex:
            if [parent_category,child_category] not in undefined_categories:
                undefined_categories.append([parent_category,child_category])
            i["category_path"] = [{"id": 76}]

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
    for i in undefined_categories:
        print(f"Tanımlanmamış kategori: {i[0]} & {i[1]}")
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


def woocommerce_create_products(wcapi, selected_product):
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
    visibility = "visible"

    if stock_quantity == 0 or not images:
        visibility = "search"
    if stock_quantity != 0:
        stock_quantity = 1 * len(options)

    if len(options) == 0:
        type_of_product = "simple"
    else:
        type_of_product = "variable"

    data = {
        "name": f"{name}",
        "sku": f"{sku}",
        "description": f"{description}",
        "type": type_of_product,
        "tax_status": "none",
        "images": images,
        "categories": category,
        "regular_price": normal_price,
        "sale_price": sale_price,
        "stock_quantity": stock_quantity,
        "catalog_visibility": visibility,
        "stock_status": stock_status,
        "manage_stock": True,
        "attributes": [
            {"name": "Size", "visible": True, "variation": True, "options": options},
        ],
    }
    for attempt in range(3):
        try:
            start = time.time()
            wcapi.post("products", data).json()
            print('(Create) Time Taken:', time.strftime("%H:%M:%S", time.gmtime(time.time() - start)))
        except requests.exceptions.ConnectionError as ex:
            print('(Create Error) Time Taken:', time.strftime("%H:%M:%S", time.gmtime(time.time() - start)))
            print(ex)
            break
        except requests.exceptions.ReadTimeout as ex:
            print('(Create Error) Time Taken:', time.strftime("%H:%M:%S", time.gmtime(time.time() - start)))
            print(ex)
            time.sleep(5 + (5 * attempt))
        except Exception as ex:
            print('(Create Error) Time Taken:', time.strftime("%H:%M:%S", time.gmtime(time.time() - start)))
            print(ex)
            time.sleep(5 + (5 * attempt))
        else:
            print('(Create) No Error')
            break


def woocommerce_update_products(wcapi, selected_product, product_id):
    i = selected_product
    name = i["name"]
    description = i["detail"]
    images = i["images"]
    category = i["category_path"]
    normal_price = i["price_list"]
    sale_price = i["price_special_vat_included"]
    stock_quantity = len(i["cat1name"])
    stock_status = i["unit"]
    options = i["cat1name"]
    visibility = "visible"
    if stock_quantity == 0 or not images:
        visibility = "search"
    if stock_quantity != 0:
        stock_quantity = 1 * len(options)

    if len(options) == 0:
        type_of_product = "simple"
    else:
        type_of_product = "variable"

    data = {
        "id": product_id,
        "name": f"{name}",
        "description": f"{description}",
        "catalog_visibility": visibility,
        "stock_quantity": stock_quantity,
        "images": images,
        "type": type_of_product,
        "categories": category,
        "regular_price": normal_price,
        "sale_price": sale_price,
        "stock_status": stock_status,
        "attributes": [
            {"name": "Size", "visible": True, "variation": True, "options": options},
        ],
    }
    for attempt in range(3):
        try:
            start = time.time()
            wcapi.put(f"products/{product_id}", data).json()
            print('(Update) Time Taken:', time.strftime("%H:%M:%S", time.gmtime(time.time() - start)))
        except requests.exceptions.ConnectionError as ex:
            print('(Update Error) Time Taken:', time.strftime("%H:%M:%S", time.gmtime(time.time() - start)))
            print(ex)
            break
        except requests.exceptions.ReadTimeout as ex:
            print('(Update Error) Time Taken:', time.strftime("%H:%M:%S", time.gmtime(time.time() - start)))
            print(ex)
            wcapi_new = woocommerce_api_connection(consumerKey, consumerSecret, storeUrl)
            wcapi = wcapi_new
            time.sleep(5 + (5 * attempt))
        except Exception as ex:
            print('(Update Error) Time Taken:', time.strftime("%H:%M:%S", time.gmtime(time.time() - start)))
            print(ex)
            time.sleep(5 + (5 * attempt))
        else:
            print('(Update) No Error')
            break


def woocommerce_delete_products(wcapi, product_id):
    for attempt in range(3):
        try:
            start = time.time()
            wcapi.delete(f"products/{product_id}", params={"force": True}).json()
            print('(Delete) Time Taken:', time.strftime("%H:%M:%S", time.gmtime(time.time() - start)))
        except requests.exceptions.ConnectionError as ex:
            print('(Delete Error) Time Taken:', time.strftime("%H:%M:%S", time.gmtime(time.time() - start)))
            print(ex)
            break
        except requests.exceptions.ReadTimeout as ex:
            print('(Delete Error) Time Taken:', time.strftime("%H:%M:%S", time.gmtime(time.time() - start)))
            print(ex)
            time.sleep(5 + (5 * attempt))
        except Exception as ex:
            print('(Delete Error) Time Taken:', time.strftime("%H:%M:%S", time.gmtime(time.time() - start)))
            print(ex)
            time.sleep(5 + (5 * attempt))
        else:
            print('(Delete) No Error')
            break


# def batch_operations_products(wcapi, data):
#     request_count = 0
#     for attempt in range(3):
#         try:
#             time.sleep(2)
#             request_count += 1
#             start = time.time()
#             wcapi.post("products/batch", data).json()
#             print('Time Taken:', time.strftime("%H:%M:%S", time.gmtime(time.time() - start)))
#         except requests.exceptions.ConnectionError as ex:
#             print('(error)Time Taken:', time.strftime("%H:%M:%S", time.gmtime(time.time() - start)))
#             print(ex)
#             break
#         # except ConnectionResetError as ex:
#         #     print(ex)
#         #     break
#         except requests.exceptions.ReadTimeout as ex:
#             print('(error)Time Taken:', time.strftime("%H:%M:%S", time.gmtime(time.time() - start)))
#             print(ex)
#             wcapi_new = woocommerce_api_connection(consumerKey, consumerSecret, storeUrl)
#             wcapi = wcapi_new
#             time.sleep(5 + (5 * attempt))
#         except Exception as ex:
#             print('(error)Time Taken:', time.strftime("%H:%M:%S", time.gmtime(time.time() - start)))
#             print(ex)
#             time.sleep(5 + (5 * attempt))
#         else:
#             print('no error')
#             break


def woocommerce_list_variations(wcapi, product_id):
    variation_in_limante = wcapi.get(f"products/{product_id}/variations").json()
    if len(variation_in_limante) != 0:
        return variation_in_limante


def woocommerce_create_variations(wcapi, product_id, property, regular_price, sale_price):
    data = {
        "regular_price": regular_price,
        "sale_price": sale_price,
        "stock_quantity": 1,
        "attributes": [
            {
                "name": "Size",
                "option": property
            }
        ]
    }
    for attempt in range(3):
        try:
            start = time.time()
            wcapi.post(f"products/{product_id}/variations", data).json()
            print('(Create Variation) Time Taken:', time.strftime("%H:%M:%S", time.gmtime(time.time() - start)))
        except requests.exceptions.ConnectionError as ex:
            print('(Create Variation Error) Time Taken:', time.strftime("%H:%M:%S", time.gmtime(time.time() - start)))
            print(ex)
            break
        except requests.exceptions.ReadTimeout as ex:
            print('(Create Variation Error) Time Taken:', time.strftime("%H:%M:%S", time.gmtime(time.time() - start)))
            print(ex)
            time.sleep(5 + (5 * attempt))
        except Exception as ex:
            print('(Create Variation Error) Time Taken:', time.strftime("%H:%M:%S", time.gmtime(time.time() - start)))
            print(ex)
            time.sleep(5 + (5 * attempt))
        else:
            print('(Create Variation) No Error')
            break


def woocommerce_update_variations(wcapi, product_id, variation_id, regular_price, sale_price):
    data = {
        "regular_price": regular_price,
        "sale_price": sale_price,
        "stock_quantity": 1,
    }
    for attempt in range(3):
        try:
            start = time.time()
            wcapi.put(f"products/{product_id}/variations/{variation_id}", data).json()
            print('(Update Variation) Time Taken:', time.strftime("%H:%M:%S", time.gmtime(time.time() - start)))
        except requests.exceptions.ConnectionError as ex:
            print('(Update Variation Error) Time Taken:', time.strftime("%H:%M:%S", time.gmtime(time.time() - start)))
            print(ex)
            break
        except requests.exceptions.ReadTimeout as ex:
            print('(Update Variation Error) Time Taken:', time.strftime("%H:%M:%S", time.gmtime(time.time() - start)))
            print(ex)
            wcapi_new = woocommerce_api_connection(consumerKey, consumerSecret, storeUrl)
            wcapi = wcapi_new
            time.sleep(5 + (5 * attempt))
        except Exception as ex:
            print('(Update Variation Error) Time Taken:', time.strftime("%H:%M:%S", time.gmtime(time.time() - start)))
            print(ex)
            time.sleep(5 + (5 * attempt))
        else:
            print('(Update Variation) No Error')
            break


def woocommerce_delete_variations(wcapi, product_id, variation_id):
    for attempt in range(3):
        try:
            start = time.time()
            wcapi.delete(f"products/{product_id}/variations/{variation_id}", params={"force": True}).json()
            print('(Delete Variation) Time Taken:', time.strftime("%H:%M:%S", time.gmtime(time.time() - start)))
        except requests.exceptions.ConnectionError as ex:
            print('(Delete Variation Error) Time Taken:', time.strftime("%H:%M:%S", time.gmtime(time.time() - start)))
            print(ex)
            break
        except requests.exceptions.ReadTimeout as ex:
            print('(Delete Variation Error) Time Taken:', time.strftime("%H:%M:%S", time.gmtime(time.time() - start)))
            print(ex)
            time.sleep(5 + (5 * attempt))
        except Exception as ex:
            print('(Delete Variation Error) Time Taken:', time.strftime("%H:%M:%S", time.gmtime(time.time() - start)))
            print(ex)
            time.sleep(5 + (5 * attempt))
        else:
            print('(Delete Variation) No Error')
            break


# def string_formatter(string_to_format):
#     new_string = ""
#     for i in string_to_format:
#         if i.isdigit():
#             new_string += i
#     return new_string


def main(wcapi, products_in_xml, products_in_limante):
    sku_list_of_xml = []
    sku_list_of_limante = []
    sku_list_of_xml_for_delete = []
    sku_list_of_limante_with_ids = []
    sku_list_of_xml_for_variations = []
    created_products_count = 0
    updated_products_count = 0
    deleted_products_count = 0

    # Create sku lists
    for i in products_in_limante:
        for page in i:
            if type(page) is list:
                j = i[0]
            else:
                j = page
            try:
                sku_list_of_limante.append(j["sku"])
            except Exception as ex:
                print(ex)
    for i in products_in_limante:
        for page in i:
            if type(page) is list:
                j = i[0]
            else:
                j = page
            try:
                sku_list_of_limante_with_ids.append([j["sku"], j["id"]])
            except Exception as ex:
                print(ex)
    for j in products_in_xml:
        sku_list_of_xml.append([j["ws_code"], j])
        sku_list_of_xml_for_delete.append(j["ws_code"])
        sku_list_of_xml_for_variations.append([j["ws_code"], j["price_list"], j["price_special_vat_included"]])

    # Create and Update
    for product in sku_list_of_xml:
        selectedProduct = product[1]
        if product[0] not in sku_list_of_limante:
            if float(selectedProduct["price_special_vat_included"]) > 90:
                woocommerce_create_products(wcapi, selectedProduct)
                created_products_count += 1
        else:
            for id_product_list in sku_list_of_limante_with_ids:
                if id_product_list[0] == product[0]:
                    productId = id_product_list[1]
                    break
            j = 0
            check = True
            while j < len(productsInLimante) and check:
                for i in products_in_limante[j]:
                    if i["sku"] == selectedProduct["ws_code"]:
                        productInLimante = i
                        check = False
                        break
                j += 1
            stock_num = i["stock_quantity"]
            if i["stock_quantity"] is None:
                stock_num = "0"
            stock_xml = 1 * len(selectedProduct["cat1name"])
            img_lst = []
            try:
                for j in i["images"]:
                    img_lst.append(j["src"])
            except:
                pass
            img_xml = []
            try:
                for j in selectedProduct["images"]:
                    img_xml.append(j["src"])
            except:
                pass

            prod_limante_var = [i["name"], i["attributes"][0]["options"], i["price"], stock_num,
                                len(img_lst)]
            prod_xml_var = [selectedProduct["name"], selectedProduct["cat1name"],
                            selectedProduct["price_special_vat_included"], stock_xml, len(img_xml)]
            prod_limante_simple = [i["name"], i["attributes"][0]["options"], i["regular_price"], i["price"], stock_num,
                                   len(img_lst)]
            prod_xml_simple = [selectedProduct["name"], selectedProduct["cat1name"], selectedProduct["price_list"],
                               selectedProduct["price_special_vat_included"], stock_xml, len(img_xml)]
            if i["type"] == "variable":
                if prod_limante_var != prod_xml_var:
                    woocommerce_update_products(wcapi, selectedProduct, productId)
                    updated_products_count += 1
            elif i["type"] == "simple":
                if prod_limante_simple != prod_xml_simple:
                    woocommerce_update_products(wcapi, selectedProduct, productId)
                    updated_products_count += 1

    # Delete
    for i in range(len(sku_list_of_limante_with_ids)):
        if sku_list_of_limante_with_ids[i][0] not in sku_list_of_xml_for_delete:
            prod_id = sku_list_of_limante_with_ids[i][1]
            woocommerce_delete_products(wcapi, prod_id)
            deleted_products_count += 1

    print(
        f"{len(sku_list_of_xml)} products in xml\n{len(sku_list_of_limante)} products in limante\n{created_products_count}"
        f" products created\n{updated_products_count} products updated\n{deleted_products_count} products deleted")

    products_in_limante = woocommerce_list_products(wcapi, storeUrl, consumerKey, perPage, pageNumberRange)
    prod_list_of_limante_with_ids = []
    for i in products_in_limante:
        for page in i:
            if type(page) is list:
                j = i[0]
            else:
                j = page
            try:
                prod_list_of_limante_with_ids.append([j, j["id"]])
            except Exception as ex:
                print(ex)

    for prod in prod_list_of_limante_with_ids:
        variations_in_limante = woocommerce_list_variations(wcapi, prod[1])
        props_of_variation = []
        props_of_variation_with_ids = []
        variations_of_product = prod[0]["attributes"][0]["options"]  # HATA!
        product_id = prod[1]
        for i in sku_list_of_xml_for_variations:
            if i[0] == prod[0]["sku"]:
                regular_price_of_product = i[1]
                sale_price_of_product = i[2]
        if variations_in_limante:
            for i in variations_in_limante:
                if len(i["attributes"]) == 0:
                    break
                props_of_variation.append(i["attributes"][0]["option"])
                props_of_variation_with_ids.append([i["id"], i["attributes"][0]["option"]])
            regular_price_of_variation = i["regular_price"]
            sale_price_of_variation = i["sale_price"]
            for i in props_of_variation_with_ids:
                variation_id = i[0]
                if i[1] in variations_of_product:
                    if [regular_price_of_variation, sale_price_of_variation] != \
                            [regular_price_of_product, sale_price_of_product]:
                        woocommerce_update_variations(wcapi, product_id, variation_id, regular_price_of_product,
                                                      sale_price_of_product)
                else:
                    woocommerce_delete_variations(wcapi, product_id, variation_id, regular_price_of_product,
                                                  sale_price_of_product)
        for i in variations_of_product:
            if i not in props_of_variation:
                variation_prop = i
                woocommerce_create_variations(wcapi, product_id, variation_prop, regular_price_of_product,
                                              sale_price_of_product)


if __name__ == '__main__':
    import requests
    import xmltodict
    from woocommerce import API
    import requests
    import json
    import time
    import math

    # urls
    xmlUrl = "https://www.orhanstore.com/xml/?R=791&K=6e71&Imgs=1&AltUrun=1&TamLink&Dislink"
    storeUrl = "https://limante.com.tr"

    # keys
    consumerKey = "ck_ca601ed7ac90662e94741985aee84c3df7c34dc1"
    consumerSecret = "cs_aff11ea841ded6082c35d3a3285c560fbb29c3b5"

    # parametric values
    parseXmlFirstParameter = "products"
    parseXmlSecondParameter = "product"
    perPage = 100
    pageNumberRange = 40
    vatRate = 8

    # program flow
    start_time = time.time()
    productsInXml = parse_xml(xmlUrl, parseXmlFirstParameter, parseXmlSecondParameter)
    wcapi = woocommerce_api_connection(consumerKey, consumerSecret, storeUrl)
    productsInLimante = woocommerce_list_products(wcapi, storeUrl, consumerKey, perPage, pageNumberRange)
    productsInXml = manipulate_xml(productsInXml, vatRate)
    main(wcapi, productsInXml, productsInLimante)
    seconds = time.time() - start_time
    print('Total Time:', time.strftime("%H:%M:%S", time.gmtime(seconds)))
