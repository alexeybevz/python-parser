import re
import pyodbc
from geoip import geolite2
from datetime import datetime

def main():
    load_data()
    get_report1()
    get_report2()
    get_report3()
    get_report4()
    get_report5()
    get_report6()
    get_report7()

def load_data():
    main_site = "https://all_to_the_bottom.com/"
    lines = read_log_file('logs.txt')
    unique_ip_addresses = get_unique_ip_addresses(lines)

    added_goods = []
    added_carts = []

    for ip_address in unique_ip_addresses:

        i = 0
        user_id = 0
        actions = []
        goods = []
        carts_payed = []

        filtered = get_lines_by(lines, ip_address)

        for row in filtered:
            actionDate = extract_substr(r'\d{1,4}\-\d{1,2}\-\d{1,2} \d{1,2}\:\d{1,2}\:\d{1,4}', row)
            guid = extract_substr(r'\[\w{1,8}\]', row)[1:-1]
            pages = row.split(main_site)[1]

            if pages == "":
                actions.append( action("Посещение главной страницы", actionDate) )
            else:
                resultSplit = pages.split("/")
                category = resultSplit[0]

                if len(resultSplit) == 1:
                    if "cart?" in category:
                        actions.append( action("Добавление товара в корзину " + category, actionDate) )
                        goods_id = extract_substr('goods_id=\d+', category).split("=")[1]
                        goods_name = filtered[i-1].split(main_site)[1].split("/")[1]
                        category_prev = filtered[i-1].split(main_site)[1].split("/")[0]
                        amount = extract_substr('amount=\d+', category).split("=")[1]
                        cart_id = extract_substr('cart_id=\d+', category).split("=")[1]
                        goods.append( good(goods_id, goods_name if not goods_name is None else "", category_prev if not category_prev is None else "", amount, cart_id) )
                    if "pay?" in category:
                        actions.append( action("Начало оплаты корзины " + category, actionDate) )
                        user_id = extract_substr('user_id=\d+', category).split("=")[1]

                else:
                    good_name = resultSplit[1]

                    if "success_pay" in category:
                        actions.append( action("Успешная оплата корзины {}".format(category), actionDate))
                        carts_payed.append( cart(extract_substr(r'\d+', category), actionDate) )
                    elif good_name == "":
                        actions.append( action("Посещение категории {}".format(category), actionDate))
                    else:
                        actions.append( action("Посещение товара {}/{}".format(category, good_name), actionDate) )
            i = i + 1

        conn = create_conn_to_db()

        db_user_id = insert_user(conn, [user_id, ip_address, get_country(ip_address)])

        for act in actions:
            insert_user_action(conn, [db_user_id, act.get_descr(), act.get_date()])

        for g in goods:
            if not g.get_good_id() in added_goods:
                insert_good(conn, [g.get_good_id(), g.get_good_name(), g.get_category()])
                added_goods.append(g.get_good_id())

            if not g.get_cart_id() in added_carts:
                fltr = list(filter(lambda x: x.get_cart_id() == g.get_cart_id(), carts_payed))
                payDate = None
                if len(fltr) > 0:
                    payDate = fltr[0].get_pay_date()

                insert_cart(conn, [g.get_cart_id(), db_user_id, payDate])
                added_carts.append(g.get_cart_id())

            insert_cart_item(conn, [g.get_cart_id(), g.get_good_id(), g.get_amount()])

        conn.close()
    return "Выполнен парсинг файла. Данные загружены в базу данных"

# Functions

def create_conn_to_db():
    conn = pyodbc.connect("Driver={SQL Server Native Client 11.0};"
                          "Server=localhost;"
                          "Database=Parser;"
                          "Trusted_Connection=yes;")
    return conn

def insert_user(conn, parms):
    cursor = conn.cursor()
    cmd = 'INSERT INTO Users (userIdLog, ipAddress, country) VALUES (?,?,?)'
    cursor.execute(cmd, parms)
    db_user_id = cursor.execute('SELECT @@IDENTITY AS id;').fetchone()[0]
    cursor.commit()
    return db_user_id

def insert_user_action(conn, parms):
    cursor = conn.cursor()
    cmd = 'INSERT INTO UserAction (userId, action, actionDate) VALUES (?,?,?)'
    cursor.execute(cmd, parms)
    cursor.commit()
    return

def insert_good(conn, parms):
    cursor = conn.cursor()
    cmd = 'INSERT INTO Good (id, name, category) VALUES (?,?,?)'
    cursor.execute(cmd, parms)
    cursor.commit()
    return

def insert_cart(conn, parms):
    cursor = conn.cursor()
    cmd = 'INSERT INTO Cart (id, userId, payDate) VALUES (?,?,?)'
    cursor.execute(cmd, parms)
    cursor.commit()
    return

def insert_cart_item(conn, parms):
    cursor = conn.cursor()
    cmd = 'INSERT INTO CartItem (cartId, goodId, amount) VALUES (?,?,?)'    
    cursor.execute(cmd, parms)
    cursor.commit()
    return
    

def read_log_file(pathToFile):
    with open(pathToFile) as f:
        return [line.rstrip() for line in f]

def get_country(ip_address):
    match = geolite2.lookup(ip_address)
    if match is not None:
        return match.country
    return "-"

def get_unique_ip_addresses(lines):
    distinct = []
    seen = set()
    for x in lines:
        ip_address = extract_substr(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', x)
        if not ip_address in seen:
            seen.add(ip_address)
            distinct.append(ip_address)
    return distinct

def extract_substr(pattern, source):
    return re.search(pattern, source).group()

def get_lines_by(lines, ip_address):
    return list(filter(lambda x: ip_address in x, lines))

# Domain

class cart:
    def __init__(self, cartId, payDate):
        self.cartId = cartId
        self.payDate = payDate

    def get_cart_id(self):
        return self.cartId

    def get_pay_date(self):
        return datetime.strptime(self.payDate, '%Y-%m-%d %H:%M:%S')

class action:
    def __init__(self, actionDescr, actionDate):
        self.actionDescr = actionDescr
        self.actionDate = actionDate

    def get_descr(self):
        return self.actionDescr

    def get_date(self):
        return datetime.strptime(self.actionDate, '%Y-%m-%d %H:%M:%S')

    def show(self):
        print( self.actionDescr + " " + self.actionDate )

class good:
    def __init__(self, goods_id, goods_name, category, amount, cart_id):
        self.goods_id = goods_id
        self.goods_name = goods_name
        self.category = category
        self.amount = amount
        self.cart_id = cart_id

    def get_good_id(self):
        return self.goods_id

    def get_good_name(self):
        return self.goods_name

    def get_category(self):
        return self.category

    def get_amount(self):
        return self.amount

    def get_cart_id(self):
        return self.cart_id

    def show(self):
        print( self.goods_id   + " " +
               self.goods_name + " " +
               self.category   + " " +
               self.amount     + " " +
               self.cart_id )

# Report 1
def get_report1():
    print('1. Посетители из какой страны совершают больше всего действий на сайте?')
    print_report(
        '''
        SELECT TOP 10 u.country, COUNT(ua.id) AS count_actions
        FROM Users u
        INNER JOIN UserAction ua ON ua.userId = u.id
        GROUP BY u.country
        ORDER BY COUNT(ua.id) desc
        ''')

def get_report2():
    print('2. Посетители из какой страны чаще всего интересуются товарами из категории “fresh_fish”?')
    print_report(
        '''
        SELECT TOP 10 ISNULL(u.country, '-') AS country, COUNT(ua.id) AS count_fresh_fish_actions
        FROM Users u
        INNER JOIN UserAction ua ON ua.userId = u.id
        WHERE ua.action LIKE '%fresh_fish%'
        GROUP BY ISNULL(u.country, '-')
        ORDER BY COUNT(ua.id) desc
        ''')

def get_report3():
    print('3. В какое время суток чаще всего просматривают категорию “frozen_fish”?')
    print_report(
        '''
        ;WITH pre AS (
            SELECT
            CASE
                when cast(actionDate as time) between '00:00:01' and '06:00:00' then 'Ночь'
                when cast(actionDate as time) between '06:00:00' and '12:00:00' then 'Утро'
                when cast(actionDate as time) between '12:00:00' and '18:00:00' then 'День'
                when cast(actionDate as time) between '18:00:00' and '23:59:59' then 'Вечер'
            END AS dt
            FROM UserAction
            WHERE action LIKE '%frozen_fish%'
        )
        SELECT dt, COUNT(dt) AS count
        FROM pre
        GROUP BY dt
        ORDER BY COUNT(dt) DESC
        ''')    

def get_report4():
    print('4. Какое максимальное число запросов на сайт за астрономический час (c 00 минут 00 секунд до 59 минут 59 секунд)?')
    print_report(
        '''
        SELECT TOP 1 CAST(actionDate AS DATE), DATEPART(Hour, actionDate) acad_hour, COUNT(actionDate) AS count
        FROM UserAction
        GROUP BY CAST(actionDate AS date), DATEPART(Hour, actionDate)
        ORDER BY COUNT(actionDate) DESC
        ''')

def get_report5():
    print('5. Товары из какой категории чаще всего покупают совместно с товаром из категории “semi_manufactures”?')
    print_report(
        '''
        ;WITH cart_with_semi_manufactures AS (
            SELECT distinct c.cartId
            FROM CartItem c
            INNER JOIN Good g ON g.id = c.goodId
            WHERE g.category = 'semi_manufactures'
        )
        SELECT g.category, COUNT(c.cartId) AS count
        FROM cart_with_semi_manufactures csm
        INNER JOIN CartItem c ON c.cartId = csm.cartId
        INNER JOIN Good g ON g.id = c.goodId
        WHERE g.category <> 'semi_manufactures'
        GROUP BY g.category
        ORDER BY count(c.cartId) DESC
        ''')

def get_report6():
    print('6. Сколько брошенных (не оплаченных) корзин имеется?')
    print_report(
        '''
        SELECT COUNT(DISTINCT id) AS count
        FROM Cart
        WHERE payDate IS NULL
        ''')

def get_report7():
    print('7. Какое количество пользователей совершали повторные покупки?')
    print_report(
        '''
        WITH pre AS (
            SELECT u.id, COUNT(c.id) AS cnt
            FROM Users u
            LEFT JOIN Cart c ON c.userId = u.id
                            AND c.payDate IS NOT NULL
            GROUP BY u.id
            HAVING COUNT(c.id) > 1
        ) SELECT COUNT(id) FROM pre
        ''')    

def print_report(sql_query):
    conn = create_conn_to_db()
    cursor = conn.cursor()
    cursor.execute(sql_query)

    for row in cursor:
        print(row)

main()
