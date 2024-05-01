from flask import Flask, jsonify, request, redirect, render_template, url_for
from database import *
from flask_cors import CORS
import calendar
import json
from sqlalchemy import extract
from datetime import datetime, timedelta, timezone
import pytz
from calendar import monthrange

app = Flask(__name__)
CORS(app)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///DATAbase.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
app.config['TIMEZONE'] = 'Asia/Tashkent'

dp.init_app(app)

with app.app_context():
    dp.create_all()

first_request_executed = False


def update_monthly_values():
    today = datetime.now(timezone.utc)

    if today.day == 1:
        with app.app_context():
            entries_to_reset = (
                dp.session.query(DolglistEntry).filter(
                    DolglistEntry.paid_month_sum != 0,
                    DolglistEntry.paid_month_dol != 0,
                ).all())

            for entry in entries_to_reset:
                # Обнулить значения
                entry.paid_month_sum = 0
                entry.paid_month_dol = 0

                # Проверить, стали ли amountSum и amountDol равными нулю
                if entry.amountSum == 0 and entry.amountDol == 0:
                    dp.session.delete(entry)

                dp.session.commit()
# Регистрация функции в приложении Flask
@app.before_request
def before_request():
    global first_request_executed

    try:
        if not first_request_executed:
            update_monthly_values()
            first_request_executed = True
    except Exception as e:
        print(f"Ошибка в before_request: {e}")


# Инициализация переменной перед первым запросом
update_monthly_values()
first_request_executed = True

# Главная страница
@app.route('/')
def index():
    return print("""
    ⠛⠛⣿⣿⣿⣿⣿⡷⢶⣦⣶⣶⣤⣤⣤⣀⠀⠀⠀
    ⠀⠀⠀⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣷⡀⠀
    ⠀⠀⠀⠉⠉⠉⠙⠻⣿⣿⠿⠿⠛⠛⠛⠻⣿⣿⣇⠀
    ⠀⠀⢤⣀⣀⣀⠀⠀⢸⣷⡄⠀⣁⣀⣤⣴⣿⣿⣿⣆
    ⠀⠀⠀⠀⠹⠏⠀⠀⠀⣿⣧⠀⠹⣿⣿⣿⣿⣿⡿⣿
    ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠛⠿⠇⢀⣼⣿⣿⠛⢯⡿⡟
    ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠦⠴⢿⢿⣿⡿⠷⠀⣿⠀
    ⠀⠀⠀⠀⠀⠀⠀⠙⣷⣶⣶⣤⣤⣤⣤⣤⣶⣦⠃⠀
    ⠀⠀⠀⠀⠀⠀⠀⢐⣿⣾⣿⣿⣿⣿⣿⣿⣿⣿⠀⠀
    ⠀⠀⠀⠀⠀⠀⠀⠈⣿⣿⣿⣿⣿⣿⣿⣿⣿⡇⠀⠀
    ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠙⠻⢿⣿⣿⣿⣿⠟⠁""")


# Список всех пользователей
@app.route('/users/all')
def users():
    users = Users.query.all()
    user_list = []

    for user in users:
        order = Order.query.filter_by(user_id=user.id).first()
        if order:
            paid_amountSum = user.paid_amountSum
            paid_amountDol = user.paid_amountDol
        user_dict = {
            "id": user.id,
            "full_name": user.full_name,
            "phone": user.phone,
            "year": user.year,
            "known_from": user.known_from,
            "company": user.company,
            "in_blacklist": is_user_in_blacklist(user.id),
            "in_dolg": is_user_in_dolglist(user.id),
            "Долг в суммах": user.amountSum,
            "Долг в долларах": user.amountDol,
            "Общее количество купленных продуктов": user.all_quant,
            "Общее сумма покупок в суммах": user.all_priceSum,
            "Общее сумма покупок в долларах": user.all_priceDol,
            'paid_amountSum': user.paid_amountSum,
            'paid_amountDol': user.paid_amountDol,
        }
        user_list.append(user_dict)

    if user_list == []:
        return jsonify({"message": "Нет пользователей"}), 200
    else:
        return jsonify(user_list)


def is_user_in_blacklist(user_id):
    blacklist_entry = BlacklistEntry.query.filter_by(user_id=user_id).first()
    return blacklist_entry is not None


def is_user_in_dolglist(user_id):
    dolglist_entry = DolglistEntry.query.filter_by(user_id=user_id).first()
    return dolglist_entry is not None


# Список пользователей в черном списке
@app.route("/users/blacklist_users", methods=["GET"])
def blacklist_users():
    # Получить все записи в черном списке
    blacklist_entries = BlacklistEntry.query.all()

    # Создать список пользователей в черном списке с дополнительными данными
    user_list = []
    for entry in blacklist_entries:
        if entry.user:
            user_data = {
                'id': entry.user.id,
                'full_name': entry.user.full_name,
                'phone': entry.user.phone,
                'amountSum': entry.user.amountSum,
                'amountDol': entry.user.amountDol
                # Другие атрибуты пользователя, которые вам интересны
            }
            user_list.append(user_data)

    return jsonify(user_list)


# Список пользователей у которых есть ДОЛГ
@app.route('/users/dolg_list', methods=['GET'])
def dolg_list():
    dolg_entries = DolglistEntry.query.all()
    user_list = []

    for entry in dolg_entries:
        if entry.user and (entry.amountSum > 0 or entry.amountDol > 0):
            # Получение информации о сумме, оплаченной пользователем
            paid_amountDol = 0
            paid_amountSum = 0
            user = Users.query.filter_by(id=entry.user.id).first()
            if user:
                paid_amountSum = user.paid_amountSum
                paid_amountDol = user.paid_amountDol

            user_data = {
                'id': entry.user.id,
                'full_name': entry.user.full_name,
                'phone': entry.user.phone,
                'year': entry.user.year,
                'amountSum': entry.amountSum if entry.user.amountSum is not None else 0,
                'amountDol': entry.amountDol if entry.user.amountDol is not None else 0,
                'date': entry.date,
                'paid_amountSum': paid_amountSum,
                'paid_amountDol': paid_amountDol
            }
            user_list.append(user_data)

    return jsonify(user_list)


# Создание нового пользователя
@app.route('/users/create_user', methods=['POST'])
def create_user():
    if request.method == 'POST':
        full_name = request.form['full_name']
        phone = request.form['phone']
        year = request.form['year']
        company = request.form['company']
        known_from = request.form['known_from']

        user = Users(full_name=full_name, phone=phone, year=year, company=company, known_from=known_from)

        try:
            dp.session.add(user)
            dp.session.commit()
            return jsonify({'message': "Клиент успешно добавлен"})
        except:
            return jsonify({'message': "Ошибка"})


# Добавление пользователя в черный список
@app.route('/users/add_to_blacklist/<int:user_id>', methods=['POST'])
def add_to_blacklist(user_id):
    user = Users.query.get(user_id)
    if not user:
        return jsonify({"error": "Пользователь не найден"}), 404

    # Проверка, находится ли пользователь уже в черном списке
    if BlacklistEntry.query.filter_by(user_id=user_id).first():
        return jsonify({"error": "Пользователь уже в черном списке"}), 400

    blacklist_entry = BlacklistEntry(user=user)
    dp.session.add(blacklist_entry)
    dp.session.commit()

    return jsonify({"message": "Пользователь добавлен в черный список"}), 200


# Удаление пользователя
@app.route("/users/delete_user/<int:user_id>", methods=["DELETE"])
def delete_user(user_id):
    try:
        user = dp.session.get(Users, user_id)
        if user is not None:
            dp.session.delete(user)
            dp.session.commit()
            return jsonify({"message": "Успешно удален с базы"})
        else:
            return jsonify({"message": "Произошла ошибка или пользлватель не найден"})
    except Exception as e:
        app.logger.error(f"An error occurred: {str(e)}")
        return jsonify({"error": "Произошла ошибка при удалении пользователя"}), 500


# Удаление пользователя из черного списка
@app.route("/users/remote_from_blacklist/<int:user_id>", methods=["DELETE"])
def remote_from_blacklist(user_id):
    user = Users.query.get(user_id)

    if not user:
        return jsonify({"error": "Пользователь не найден"}), 404

    blacklist_entry = BlacklistEntry.query.filter_by(user=user).first()
    if not blacklist_entry:
        return jsonify({"error": "Пользователь не в черном списке"}), 400

    dp.session.delete(blacklist_entry)
    dp.session.commit()

    return jsonify({"message": "Пользователь успешно удален из черного списка"}), 200


# Добавление пользователя в списолк должников
@app.route('/users/dolg/<int:user_id>', methods=['POST'])
def manage_dolg(user_id):
    if request.method == 'POST':
        amountSum = request.form['amountSum']
        amountDol = request.form['amountDol']

        # Проверяем, является ли amount_str числом
        try:
            amountSum = float(amountSum)
            amountDol = float(amountDol)
        except ValueError:
            print("Недопустимая сумма:", amountDol)
            print("Недопустимая сумма:", amountSum)
            return "Сумма должна быть действительным числом.."

        user = Users.query.get(user_id)

        if user:
            # Проверяем, существует ли уже запись о долге для этого пользователя
            dolg_entry = DolglistEntry.query.filter_by(user_id=user_id).first()

            if dolg_entry:
                # Если запись найдена, добавляем к существующему долгу
                dolg_entry.amountDol += amountDol
                dolg_entry.amountSum += amountSum
            else:
                # Если записи нет, создаем новую
                dolg_entry = DolglistEntry(user=user, amountSum=amountSum, amountDol=amountDol)
                dp.session.add(dolg_entry)

            dp.session.commit()
            return jsonify({
                "message": 'Новый пользователь добавлен в базу должников'})  # Перенаправляем на страницу со списком записей dolg

    return "Неверный запрос"


# Удаление пользователя из черного списка
@app.route("/users/remote_from_dolglist/<int:user_id>", methods=["DELETE"])
def remote_from_dolglist(user_id):
    user = Users.query.get(user_id)

    if user:
        dolglist_entry = DolglistEntry.query.filter_by(user=user).first()
        if dolglist_entry:
            dp.session.delete(dolglist_entry)
            dp.session.commit()
            if DolglistEntry.amountSum == 0 and DolglistEntry.amountDol == 0:
                dp.session.delete(dolglist_entry)
                dp.session.commit()

    return 'Успешно удален с базы'


@app.route("/users/update_debt/<int:user_id>", methods=["PATCH"])
def update_debt(user_id):
    current_time = datetime.now(pytz.timezone('Asia/Tashkent'))
    try:
        data = request.get_json()
        new_debt_amountSum = data.get('debt_amountSum')
        new_debt_amountDol = data.get('debt_amountDol')
        if new_debt_amountSum is None:
            return jsonify({'error': 'Не указана сумма долга в суммах'}), 400
        if new_debt_amountDol is None:
            return jsonify({'error': 'Не указана сумма долга в доллараз'}), 400

        try:
            new_debt_amountSum = float(new_debt_amountSum)
            new_debt_amountDol = float(new_debt_amountDol)
        except ValueError:
            return jsonify({'error': 'Сумма долга должна быть числом'}), 400

        user = Users.query.filter_by(id=user_id).first()
        if user:
            user.paid_amountSum = user.paid_amountSum or 0  # Установить значение по умолчанию 0, если None
            user.paid_amountDol = user.paid_amountDol or 0  # Установить значение по умолчанию 0, если None
            user.paid_amountSum += new_debt_amountSum
            user.paid_amountDol += new_debt_amountDol

        dolglist_entry = DolglistEntry.query.filter_by(user_id=user_id).first()
        if dolglist_entry:
            dolglist_entry.amountSum = dolglist_entry.amountSum or 0  # Установить значение по умолчанию 0, если None
            dolglist_entry.amountDol = dolglist_entry.amountDol or 0  # Установить значение по умолчанию 0, если None

            dolglist_entry.amountSum -= new_debt_amountSum
            dolglist_entry.amountDol -= new_debt_amountDol

            dolglist_entry.paid_day_sum = new_debt_amountSum
            dolglist_entry.paid_month_sum = (dolglist_entry.paid_month_sum or 0) + new_debt_amountSum

            dolglist_entry.paid_day_dol = new_debt_amountDol
            dolglist_entry.paid_month_dol = (dolglist_entry.paid_month_dol or 0) + new_debt_amountDol

            dolglist_entry.date = current_time

            # if dolglist_entry.amountSum <= 0 and dolglist_entry.amountDol <= 0:
            #     dp.session.delete(dolglist_entry)

            dp.session.commit()
            return jsonify({'message': 'Долг успешно обновлен'}), 200
        else:
            return jsonify({'error': 'Пользователь не найден в списке должников'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ----------------------------------------------------------------------------------------------------------------------
# Меню продуктов

@app.route('/products/products_menu', methods=['GET'])
def products_menu():
    products = Products.query.all()
    product_list = []

    for product in products:
        product_dict = {
            "id": product.product_id,
            "product_name": product.product_name,  # Исправлено: product.name -> product.product_name
            "product_description": product.product_description,
            # Исправлено: product.description -> product.product_description
            "product_quantity": product.product_quantity,
            "product_photo": product.product_photo,
            "product_amount": product.product_amount
        }
        product_list.append(product_dict)

    if product_list == []:
        return jsonify({"message": "Нет продуктов"}), 200
    else:
        return jsonify(product_list)


@app.route("/products/new_product", methods=["POST"])
def new_product():
    if request.method == 'POST':
        product_name = request.form['product_name']
        product_description = request.form['product_description']
        product_quantity = request.form['product_quantity']
        product_amount = request.form['product_amount']
        product_photo = request.form['product_photo']

        product = Products(product_name=product_name, product_description=product_description,
                           product_quantity=product_quantity, product_amount=product_amount,
                           product_photo=product_photo)

        try:
            dp.session.add(product)
            dp.session.commit()
            return jsonify({'message': "Продукт успешно создан"})
        except:
            return jsonify({'message': "пРОИЗОШЛА ОШИБКА"})


@app.route("/products/delete_product/<int:product_id>", methods=["DELETE"])
def delete_product(product_id):
    product = dp.session.query(Products).get(product_id)
    if product is not None:
        dp.session.delete(product)
        dp.session.commit()
        return jsonify({"message": "Успешно удален с базы"})
    else:
        return jsonify({
            "error": "Произошла ошибка при удалении продукта"}), 500


# ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------


# Изменение Количества Продукта
@app.route('/products/update_product/<int:product_id>', methods=['PATCH'])
def update_product(product_id):
    try:
        # Получаем продукт из базы данных
        product = Products.query.get(product_id)

        if not product:
            return jsonify({"error": "Продукт не найден"}), 404

        # Получаем данные из запроса
        product_quantity = request.form.get('product_quantity')
        product_amount = request.form.get('product_amount')

        # Проверяем, присутствует ли значение product_quantity в данных запроса
        if product_quantity is not None:
            # Обновляем значение product_quantity
            product.product_quantity += float(product_quantity)
        if product_amount is not None:
            product.product_amount = float(product_amount)
        # Сохраняем изменения в базе данных
        dp.session.commit()

        return jsonify({"message": "Продукт успешно обновлен"}), 200

    except Exception as e:
        return jsonify({"Ошибка": str(e)}), 500


# ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# НОВЫЙ ЗАКАЗ

print("""

⠛⠛⣿⣿⣿⣿⣿⡷⢶⣦⣶⣶⣤⣤⣤⣀⠀⠀⠀
⠀⠀⠀⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣷⡀⠀
⠀⠀⠀⠉⠉⠉⠙⠻⣿⣿⠿⠿⠛⠛⠛⠻⣿⣿⣇⠀
⠀⠀⢤⣀⣀⣀⠀⠀⢸⣷⡄⠀⣁⣀⣤⣴⣿⣿⣿⣆
⠀⠀⠀⠀⠹⠏⠀⠀⠀⣿⣧⠀⠹⣿⣿⣿⣿⣿⡿⣿
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠛⠿⠇⢀⣼⣿⣿⠛⢯⡿⡟
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠦⠴⢿⢿⣿⡿⠷⠀⣿⠀
⠀⠀⠀⠀⠀⠀⠀⠙⣷⣶⣶⣤⣤⣤⣤⣤⣶⣦⠃⠀
⠀⠀⠀⠀⠀⠀⠀⢐⣿⣾⣿⣿⣿⣿⣿⣿⣿⣿⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠈⣿⣿⣿⣿⣿⣿⣿⣿⣿⡇⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠙⠻⢿⣿⣿⣿⣿⠟⠁""")


@app.route('/orders/new_order', methods=['POST'])
def create_order():
    current_time = datetime.now(pytz.timezone('Asia/Tashkent'))
    products_data = request.form['products']
    user_id = request.form['user_id']
    pay_method = request.form['pay_method']

    all_quantity = 0
    all_priceSum = 0
    all_priceDol = 0
    products_list = json.loads(products_data)
    for product_info in products_list:
        product_id = product_info["product_id"]
        product_quantity = product_info["amount"]
        product_amount = product_info["price"]
        # product_description = product_info["description"]
        # product_recept = product_info.get("recept", [])
        profitsum = product_quantity * product_amount
        amountsum = product_amount
        product = Products.query.get(product_id)
        total_record = Totality.query.first()
        if not total_record:
            total_record = Totality(totalsum=0)
            dp.session.add(total_record)
        print(total_record.totalsum)
        # Обновляем значения
        total_record.totalsum += profitsum
        dp.session.commit()

        # Проверяем, существует ли продукт
        if product:
            # Присваиваем значение product_amount переменной privet
            product_amount_real = product.product_amount
        else:
            # Если продукт не найден, выводим сообщение об ошибке или устанавливаем privet в None
            print("Продукт не найден sum")

        new_profit = Profit(profitsum=profitsum, quantity=product_quantity, product=product_id,
                            product_amount_real=product_amount_real, amountsum=amountsum, created=current_time)
        dp.session.add(new_profit)

        # Получение продукта из базы данных
        product = dp.session.query(Products).get(product_id)
        if product and product.product_quantity >= product_quantity:
            # Уменьшение количества продукта на складе
            product.product_quantity -= product_quantity

            # Расчет общего количества и стоимости
            all_quantity += product_quantity
            all_priceSum += product_amount * product_quantity
        else:
            # Обработка ошибки: продукт не найден или недостаточно на складе
            return jsonify({"error": f"Продукт с ID {product_id} не найден или недостаточно на складе"}), 400

    # добавить заказ в базу
    new_order = Order(products=products_data, user_id=user_id, all_quantity=all_quantity, pay_method=pay_method,
                      all_priceSum=all_priceSum, all_priceDol=all_priceDol, create_at=current_time)
    dp.session.add(new_order)
    dp.session.commit()
    if pay_method == "ДОЛГ":
        user = dp.session.get(Users, user_id)  # Получение объекта пользователя
        dolg_entry = DolglistEntry.query.filter_by(user_id=user_id).first()

        if dolg_entry:
            dolg_entry.amountSum += all_priceSum
            dolg_entry.amountDol += all_priceDol
        else:
            dolg_entry = DolglistEntry(user=user, amountSum=all_priceSum, amountDol=all_priceDol,
                                       date=datetime.now())
            dp.session.add(dolg_entry)

    # обратботка юзера и paymethod
    user = dp.session.query(Users).get(user_id)
    if user.all_quant is None:
        user.all_quant = 0
    user.all_quant += all_quantity

    if user.all_priceSum is None:
        user.all_priceSum = 0
    user.all_priceSum += all_priceSum
    dp.session.commit()
    return jsonify({"message": "Заказ успешно создан", "Общая стоимость заказа в суммах": all_priceSum,
                    "Общая стоимость заказа в долларах": all_priceDol}), 201


@app.route('/orders/put_order/<int:order_id>', methods=['PUT'])
def put_order(order_id):
    current_time = datetime.now(pytz.timezone('Asia/Tashkent'))
    order = dp.session.get(Order, order_id)
    if not order:
        return jsonify({'message': 'Заказ не найден'}), 404

    try:
        # Get JSON data from the request body
        data = request.get_json()
        print(data)
        products = data['products']
        user_id = data['user_id']
        pay_method = data['pay_method']
        all_quantity = 0
        all_priceSum = 0
        all_priceDol = 0

        # Преобразование строки в список словарей
        products_list = products
        for product_info in products_list:
            product_id = product_info["product_id"]
            product_quantity = product_info["amount"]
            product_amount = product_info["price"]
            product_description = product_info["description"]
            product_recept = product_info.get("recept", [])
            profitsum = product_quantity * product_amount
            amountsum = product_amount
            product = Products.query.get(product_id)
            # total_record = Totality.query.first()
            # if not total_record:
            #     total_record = Totality(totalsum=0)
            #     dp.session.add(total_record)
            # print(total_record.totalsum)
            # # Обновляем значения
            # total_record.totalsum += profitsum
            # dp.session.commit()
            # Проверяем, существует ли продукт
            # if product:
            #     # Присваиваем значение product_amount переменной privet
            #     product_amount_real = product.product_amount
            # else:
            #     # Если продукт не найден, выводим сообщение об ошибке или устанавливаем privet в None
            #     print("Продукт не найден sum")
            #
            # new_profit = Profit(profitsum=profitsum, quantity=product_quantity, product=product_id,
            #                     product_amount_real=product_amount_real, amountsum=amountsum, created=current_time)
            # dp.session.add(new_profit)

            # Получение продукта из базы данных
            product = dp.session.query(Products).get(product_id)
            if product and product.product_quantity >= product_quantity:
                # Уменьшение количества продукта на складе
                # product.product_quantity -= product_quantity

                # Расчет общего количества и стоимости
                all_quantity += product_quantity
                all_priceSum += product_amount * product_quantity
            else:
                # Обработка ошибки: продукт не найден или недостаточно на складе
                return jsonify({"error": f"Продукт с ID {product_id} не найден или недостаточно на складе"}), 400

            if product_recept:
                for recept_info in product_recept:
                    recept_product_id = recept_info["product_id"]
                    recept_product_quantity = recept_info["amount"]
                    recept_product_amount = recept_info["price"]
                    profitdol = recept_product_quantity * recept_product_amount
                    amountdol = recept_product_amount
                    product = Products.query.get(recept_product_id)

                    # Проверяем, существует ли продукт
                    if product:
                        # Присваиваем значение product_amount переменной privet
                        recept_product_amountreal = product.product_amount
                    else:
                        # Если продукт не найден, выводим сообщение об ошибке или устанавливаем privet в None
                        print("Продукт не найден")

                    total_record = Totality.query.first()
                    if not total_record:
                        total_record = Totality(profitdol=0)
                        dp.session.add(total_record)
                    # Обновляем значения
                    total_record.totaldol += profitdol
                    dp.session.commit()

                    # print({"vot": f"id {recept_product_id} = {profitdol} , Продали {recept_product_quantity}"})
                    news_profit = Profit(profitdol=profitdol, quantity=recept_product_quantity,
                                         product=recept_product_id, product_amount_real=recept_product_amountreal,
                                         amountdol=amountdol, created=current_time)
                    dp.session.add(news_profit)

                    # Получение продукта из базы данных
                    recept_product = dp.session.query(Products).get(recept_product_id)
                    if recept_product and recept_product.product_quantity >= recept_product_quantity:
                        # Уменьшение количества продукта на складе
                        recept_product.product_quantity -= recept_product_quantity

                        # Расчет общего количества и стоимости
                        all_quantity += recept_product_quantity
                        all_priceDol += recept_product_amount * recept_product_quantity
                    else:
                        # Обработка ошибки: продукт не найден или недостаточно на складе
                        return jsonify(
                            {"error": f"Продукт с ID {recept_product_id} не найден или недостаточно на складе"}), 400

        # добавить заказ в базу
        order.products = json.dumps(products_list)
        order.user_id = user_id
        order.all_quantity = all_quantity
        order.pay_method = pay_method
        order.all_priceDol = all_priceDol
        order.all_priceSum = all_priceSum
        order.create_at = current_time
        dp.session.commit()

        if pay_method == "ДОЛГ":
            user = dp.session.get(Users, user_id)  # Получение объекта пользователя
            dolg_entry = DolglistEntry.query.filter_by(user_id=user_id).first()

            if dolg_entry:
                # dolg_entry.amountSum += all_priceSum
                dolg_entry.amountDol += all_priceDol
            else:
                dolg_entry = DolglistEntry(user=user, amountSum=all_priceSum, amountDol=all_priceDol,
                                           date=datetime.now())
                dp.session.add(dolg_entry)

        # обратботка юзера и paymethod
        user = dp.session.query(Users).get(user_id)
        if user.all_quant is None:
            user.all_quant = 0
        user.all_quant += all_quantity

        if user.all_priceSum is None:
            user.all_priceSum = 0
        user.all_priceSum += all_priceSum

        if user.all_priceDol is None:
            user.all_priceDol = 0
        user.all_priceDol += all_priceDol

        dp.session.commit()
        return jsonify({"message": "Заказ успешно создан", "Общая стоимость заказа в суммах": all_priceSum,
                        "Общая стоимость заказа в долларах": all_priceDol}), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route('/paymethod/<int:order_id>', methods=['PATCH'])
def paymethod(order_id):
    # Получение заказа по ID
    order = Order.query.get(order_id)
    if not order:
        return jsonify({'message': 'Заказ не найден'}), 404

    # Получение данных из JSON тела запроса
    data = request.get_json()
    paidSum = data.get('paidSum', 0)
    paidDol = data.get('paidDol', 0)
    cash = data.get('cash', 0)
    terminal = data.get('terminal', 0)
    card = data.get('card', 0)
    transfers = data.get('transfers', 0)
    dollar = data.get('dollar', 0)
    dolgsum = data.get('dolgsum', 0)
    dolgdol = data.get('dolgdol', 0)

    order = Order.query.get(order_id)
    if not order:
        return jsonify({'error': 'Заказ не найден'}), 404

    order.cash = cash
    order.terminal = terminal
    order.card = card
    order.transfers = transfers
    order.dollar = dollar
    order.dolgsum = dolgsum
    order.dolgdol = dolgdol
    dp.session.commit()
    print(dollar)
    try:
        paidSum = float(paidSum)
        paidDol = float(paidDol)
    except ValueError:
        return jsonify({'message': 'Некорректное значение для paid'}), 400

    allpriceSum = order.all_priceSum
    allpriceDol = order.all_priceDol
    user_id = order.user_id
    user = dp.session.get(Users, user_id)
    if user.paid_amountSum is None:
        user.paid_amountSum = 0
    # Обновление оплаченной суммы и расчет долга
    user.paid_amountSum += paidSum

    if user.paid_amountDol is None:
        user.paid_amountDol = 0
    # Обновление оплаченной суммы и расчет долга
    user.paid_amountDol += paidDol

    # Обновление оплаченной суммы
    if order.was_paidSum is None:
        order.was_paidSum = 0
    order.was_paidSum += paidSum
    allpriceSum -= paidSum

    if order.was_paidDol is None:
        order.was_paidDol = 0
    order.was_paidDol += paidDol
    allpriceDol -= paidDol

    # if allpriceSum == 0 and allpriceDol == 0:
    #     # Поиск записи долга для пользователя
    #     dolg_entry = DolglistEntry.query.filter_by(user_id=user_id).first()
    #     if dolg_entry:
    #     # Если запись найдена, удаляем ее из базы данных
    #         dp.session.delete(dolg_entry)
    # else:
    #     # Ваш существующий код для обновления или добавления записи долга
    #     dolg_entry = DolglistEntry.query.filter_by(user_id=user_id).first()
    #     if dolg_entry:
    #         dolg_entry.amountSum -= paidSum
    #         dolg_entry.amountDol -= paidDol
    #         dp.session.commit()
    #     else:
    #         dolg_entry = DolglistEntry(user=user, amountSum=allpriceSum, amountDol=allpriceDol, date=datetime.now(), )
    #         dp.session.add(dolg_entry)

        # Ваш существующий код для обновления или добавления записи долга
    dolg_entry = DolglistEntry.query.filter_by(user_id=user_id).first()
    if dolg_entry:
        dolg_entry.amountSum -= paidSum
        dolg_entry.amountDol -= paidDol
        dp.session.commit()
    else:
        dolg_entry = DolglistEntry(user=user, amountSum=allpriceSum, amountDol=allpriceDol, date=datetime.now(), )
        dp.session.add(dolg_entry)

    dp.session.commit()
    return jsonify({
        "message": "Метод оплаты обновлен",
        "Оплачено в суммах": paidSum,
        "Оплачено в долларах": paidDol,
        "Долг в суммах": dolg_entry.amountSum if dolg_entry and dolg_entry.amountSum is not None else 0,
        "Долг в долларах": dolg_entry.amountDol if dolg_entry and dolg_entry.amountDol is not None else 0
    }), 200


@app.route('/orders/delete_order/<int:order_id>', methods=['DELETE'])
def delete_order(order_id):
    # Находим заказ по ID
    order = dp.session.query(Order).get(order_id)
    if not order:
        return jsonify({'message': 'Заказ не найден'}), 404

    # Преобразование строки в список словарей
    products_list = json.loads(order.products)

    # Возвращаем количество каждого товара обратно в базу продуктов
    for product_info in products_list:
        product_id = product_info["product_id"]
        product_quantity = product_info["amount"]

        # Получение продукта из базы данных
        product = dp.session.query(Products).get(product_id)
        if product:
            product.product_quantity += product_quantity
        else:
            # Если продукт не найден, прерываем процесс с ошибкой
            dp.session.rollback()
            return jsonify({"error": f"Продукт с ID {product_id} не найден в базе данных"}), 400

    order = dp.session.query(Order).get(order_id)  # Получаем объект заказа
    if order:
        user = dp.session.query(Users).get(order.user_id)  # Получаем объект пользователя
        if user:
            if user.all_priceSum is not None and order.all_priceSum is not None:
                user.all_priceSum = user.all_priceSum - order.all_priceSum  # Обновляем all_priceSum

            if user.all_priceDol is not None and order.all_priceDol is not None:
                user.all_priceDol = user.all_priceDol - order.all_priceDol  # Обновляем all_priceDol

            # Другие действия, если необходимо
        else:
            dp.session.rollback()
            return jsonify({'error': 'Пользователь для данного заказа не найден'}), 400
    else:
        dp.session.rollback()
        return jsonify({'error': 'Заказ не найден'}), 400
    user = dp.session.query(Users).get(order.user_id)
    if user:
        # Проверяем, что хотя бы одно из значений не равно None
        if user.all_quant is not None or order.all_quantity is not None:
            # Проверяем, что оба значения не равны None перед выполнением вычислений
            if user.all_quant is not None and order.all_quantity is not None:
                user.all_quant = float(user.all_quant) - float(order.all_quantity)
                # Другие действия, если необходимо
        # Если хотя бы одно из значений None, просто пропускаем вычисления
    else:
        dp.session.rollback()
        return jsonify({'error': 'Пользователь не найден для данного заказа'}), 400

    dp.session.delete(order)
    dp.session.commit()
    return jsonify({'message': 'Заказ успешно удален'}), 200


@app.route('/vozvrat', methods=['PATCH'])
def vozvrat():
    current_time = datetime.now(pytz.timezone('Asia/Tashkent'))
    data = request.get_json()

    user_id = data.get("user_id")
    description = data.get('description')
    products = data.get('products')

    if not description or description.strip() == "":
        return jsonify({'error': 'Описание не может быть пустым'}), 400
    if not products:
        return jsonify({'error': 'Отсутствуют данные о продуктах'}), 400

    products_json = json.dumps(products)  # Сериализация списка продуктов в JSON строку

    new_vozvrat = Vozvrat(
        products=products_json,
        description=description,
        date=current_time
    )
    dp.session.add(new_vozvrat)

    for product_info in products:
        product_id = product_info.get("product_id")
        quantity = product_info.get("quantity", 0)  # Установка значения по умолчанию, если не предоставлено
        summаSum = product_info.get("summаSum", 0)  # Установка 0, если поле отсутствует
        summаDol = product_info.get("summаDol", 0)  # Установка 0, если поле отсутствует

        # Проверяем наличие всех необходимых полей в запросе, кроме summаSum и summаDol, для которых установлены значения по умолчанию
        if not all([product_id, quantity]):
            return jsonify({'error': 'Некорректные данные в запросе'}), 400
        total_record = Totality.query.first()  # Предполагаем, что есть только одна запись

        if total_record:
            # Вычитаем outgo из totalsum и totaldol
            if summаSum:
                total_record.totalsum -= float(summаSum)  # Преобразование в float перед вычитанием
            if summаDol:
                total_record.totaldol -= float(summаDol)

        product = Products.query.get(product_id)
        if not product:
            return jsonify({"error": f"Продукт с ID {product_id} не найден в базе данных"}), 400
        product_name = product.product_name

        product.product_quantity += int(quantity)

        dp.session.commit()



    # Обновление данных пользователя и общих записей (примерное решение, требует доработки)
        user = Users.query.get(user_id)
        if user:
            user.all_priceSum = (user.all_priceSum or 0) - float(summаSum)
            user.all_priceDol = (user.all_priceDol or 0) - float(summаDol)
            user.all_quant = (user.all_quant or 0) - int(quantity)
            dp.session.commit()
        else:
            dp.session.rollback()
            return jsonify({'error': 'Пользователь для данного заказа не найден'}), 400

    return jsonify({"message": "Возврат успешно обработан"}), 200


@app.route('/vozvrats', methods=['GET'])
def get_all_vozvrats():
    all_vozvrats = Vozvrat.query.all()
    result = []
    for vozvrat in all_vozvrats:
        vozvrat_data = {
            'id': vozvrat.id,
            'date': vozvrat.date.isoformat(),
            'products': json.loads(vozvrat.products),  # Десериализация строки JSON в объект Python
            'description': vozvrat.description
        }
        result.append(vozvrat_data)

    return jsonify(result)
# ----------------------------------------------------------------------------------------------------------------------


@app.route('/orders/all_orders', methods=['GET'])
def get_all_orders():
    orders = Order.query.all()
    orders_data = []  # Инициализация списка для данных заказов
    for order in orders:
        user = Users.query.get(order.user_id)
        if user:  # Проверка, найден ли пользователь
            full_name = user.full_name
            user_phone = user.phone
        else:
            full_name = "Пользователь не найден"

        order_data = {
            "order_id": order.id,
            "user_id": order.user_id,
            "user_full_name": full_name,  # Добавление полного имени пользователя
            "phone": user_phone,
            "products": order.products,
            "all_quantity": order.all_quantity,
            "all_priceSum": order.all_priceSum,
            "all_priceDol": order.all_priceDol,
            "pay_method": order.pay_method,
            "create_at": order.create_at.isoformat() if order.create_at else None,
            "was_paidSum": order.was_paidSum,
            "was_paidDol": order.was_paidDol,
            "cash": order.cash,
            "card": order.card,
            "dollars": order.dollar,
            "terminal": order.terminal,
            "transfers": order.transfers,
            "dolgsum": order.dolgsum,
            "dolgdol": order.dolgdol
        }
        orders_data.append(order_data)  # Добавление данных о заказе в список

    # Возвращение данных в формате JSON
    return jsonify(orders_data), 200


@app.route('/orders/today', methods=['GET'])
def get_orders_today():
    # Определение начала и конца текущего дня
    start_date = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    end_date = start_date + timedelta(days=1)

    # Запрос общего количества проданных товаров за сегодня
    total_quantity_sold = dp.session.query(func.sum(Order.all_quantity)).filter(Order.create_at >= start_date,
                                                                                Order.create_at < end_date).scalar()
    total_orders_today = dp.session.query(func.count(Order.id)).filter(
        Order.create_at >= start_date, Order.create_at < end_date).scalar()
    # Запрос заказов за сегодня
    orders = Order.query.filter(Order.create_at >= start_date, Order.create_at < end_date).all()

    orders_list = []

    for order in orders:
        orders_list.append({
            "order_id": order.id,
            "user_id": order.user_id,
            "products": order.products,
            "all_quantity": order.all_quantity,
            "all_priceSum": order.all_priceSum,
            "all_priceDol": order.all_priceDol,
            "pay_method": order.pay_method,
            "create_at": order.create_at.isoformat(),
            "cash": order.cash,
            "dollars": order.dollar,
            "terminal": order.terminal,
            "transfers": order.transfers
        })

    # Включаем информацию об общем количестве проданных товаров
    result = {'Общее проданных продуктов': total_quantity_sold, 'Общее количество заказов': total_orders_today,
              'Общее заказов сегодня': orders_list}

    return jsonify(result)


@app.route('/orders/<int:year>', methods=['GET'])
def get_orders_by_year(year):
    monthly_results = []

    for month in range(1, 13):
        # Определение начала и конца месяца
        start_date = datetime(year, month, 1)
        end_date = datetime(year, month, calendar.monthrange(year, month)[1]) + timedelta(days=1)

        total_quantity_sold = dp.session.query(func.sum(Order.all_quantity)).filter(
            Order.create_at >= start_date, Order.create_at < end_date).scalar()

        total_orders_month = dp.session.query(func.count(Order.id)).filter(
            Order.create_at >= start_date, Order.create_at < end_date).scalar()

        # Assuming each order has a 'price' field
        total_revenueSum = dp.session.query(func.sum(Order.all_priceSum)).filter(
            Order.create_at >= start_date, Order.create_at < end_date).scalar()
        total_revenueDol = dp.session.query(func.sum(Order.all_priceDol)).filter(
            Order.create_at >= start_date, Order.create_at < end_date).scalar()
        total_cash = dp.session.query(func.sum(Order.cash)).filter(
            Order.create_at >= start_date, Order.create_at < end_date).scalar()
        total_dollar = dp.session.query(func.sum(Order.dollar)).filter(
            Order.create_at >= start_date, Order.create_at < end_date).scalar()
        total_terminal = dp.session.query(func.sum(Order.terminal)).filter(
            Order.create_at >= start_date, Order.create_at < end_date).scalar()
        total_card = dp.session.query(func.sum(Order.card)).filter(
            Order.create_at >= start_date, Order.create_at < end_date).scalar()
        total_transfers = dp.session.query(func.sum(Order.transfers)).filter(
            Order.create_at >= start_date, Order.create_at < end_date).scalar()
        total_dolgsum = dp.session.query(func.sum(Order.dolgsum)).filter(
            Order.create_at >= start_date, Order.create_at < end_date).scalar()
        total_dolgdol = dp.session.query(func.sum(Order.dolgdol)).filter(
            Order.create_at >= start_date, Order.create_at < end_date).scalar()

        total_paiddolgdol = dp.session.query(func.sum(DolglistEntry.paid_month_dol)).filter(
            DolglistEntry.date >= start_date, DolglistEntry.date < end_date).scalar()
        total_paiddolgsum = dp.session.query(func.sum(DolglistEntry.paid_month_sum)).filter(
            DolglistEntry.date >= start_date, DolglistEntry.date < end_date).scalar()

        month_result = {
            'month': month,
            'sold_products': total_quantity_sold if total_quantity_sold is not None else 0,
            'quantity_orders': total_orders_month if total_orders_month is not None else 0,
            'all_priceSum': total_revenueSum if total_revenueSum is not None else 0,
            'all_priceDol': total_revenueDol if total_revenueDol is not None else 0,
            "total_cash": total_cash if total_cash is not None else 0,
            "total_dollar": total_dollar if total_dollar is not None else 0,
            "total_terminal": total_terminal if total_terminal is not None else 0,
            "total_card": total_card if total_card is not None else 0,
            "total_transfers": total_transfers if total_transfers is not None else 0,
            "total_dolgsum": total_dolgsum if total_dolgsum is not None else 0,
            "total_dolgdol": total_dolgdol if total_dolgdol is not None else 0,
            "total_paiddolgdol": total_paiddolgdol if total_paiddolgdol is not None else 0,
            "total_paiddolgsum": total_paiddolgsum if total_paiddolgsum is not None else 0
        }
        monthly_results.append(month_result)

    return jsonify(monthly_results)


@app.route('/orders/<int:year>/<int:month>', methods=['GET'])
def get_orders_by_month(year, month):
    # Определение количества дней в месяце
    num_days = calendar.monthrange(year, month)[1]

    daily_results = []

    for day in range(1, num_days + 1):
        start_date = datetime(year, month, day)
        end_date = start_date + timedelta(days=1)

        total_quantity_sold = dp.session.query(func.sum(Order.all_quantity)).filter(
            Order.create_at >= start_date, Order.create_at < end_date).scalar()

        total_orders_day = dp.session.query(func.count(Order.id)).filter(
            Order.create_at >= start_date, Order.create_at < end_date).scalar()

        total_revenueSum = dp.session.query(func.sum(Order.all_priceSum)).filter(
            Order.create_at >= start_date, Order.create_at < end_date).scalar()
        total_revenueDol = dp.session.query(func.sum(Order.all_priceDol)).filter(
            Order.create_at >= start_date, Order.create_at < end_date).scalar()
        total_cash = dp.session.query(func.sum(Order.cash)).filter(
            Order.create_at >= start_date, Order.create_at < end_date).scalar()
        total_dollar = dp.session.query(func.sum(Order.dollar)).filter(
            Order.create_at >= start_date, Order.create_at < end_date).scalar()
        total_terminal = dp.session.query(func.sum(Order.terminal)).filter(
            Order.create_at >= start_date, Order.create_at < end_date).scalar()
        total_card = dp.session.query(func.sum(Order.card)).filter(
            Order.create_at >= start_date, Order.create_at < end_date).scalar()
        total_transfers = dp.session.query(func.sum(Order.transfers)).filter(
            Order.create_at >= start_date, Order.create_at < end_date).scalar()
        total_dolgsum = dp.session.query(func.sum(Order.dolgsum)).filter(
            Order.create_at >= start_date, Order.create_at < end_date).scalar()
        total_dolgdol = dp.session.query(func.sum(Order.dolgdol)).filter(
            Order.create_at >= start_date, Order.create_at < end_date).scalar()

        total_paiddolgdol = dp.session.query(func.sum(DolglistEntry.paid_month_dol)).filter(
            DolglistEntry.date >= start_date, DolglistEntry.date < end_date).scalar()
        total_paiddolgsum = dp.session.query(func.sum(DolglistEntry.paid_month_sum)).filter(
            DolglistEntry.date >= start_date, DolglistEntry.date < end_date).scalar()

        daily_results.append({
            'date': start_date.strftime('%Y-%m-%d'),
            'sold_products': total_quantity_sold if total_quantity_sold is not None else 0,
            'quantity_orders': total_orders_day if total_orders_day is not None else 0,
            'all_priceSum': total_revenueSum if total_revenueSum is not None else 0,
            'all_priceDol': total_revenueDol if total_revenueDol is not None else 0,
            "total_cash": total_cash if total_cash is not None else 0,
            "total_dollar": total_dollar if total_dollar is not None else 0,
            "total_terminal": total_terminal if total_terminal is not None else 0,
            "total_card": total_card if total_card is not None else 0,
            "total_transfers": total_transfers if total_transfers is not None else 0,
            "total_dolgsum": total_dolgsum if total_dolgsum is not None else 0,
            "total_dolgdol": total_dolgdol if total_dolgdol is not None else 0,
            "total_paiddolgdol": total_paiddolgdol if total_paiddolgdol is not None else 0,
            "total_paiddolgsum": total_paiddolgsum if total_paiddolgsum is not None else 0
        })

    return jsonify(daily_results)


@app.route('/orders/<int:year>/<int:month>/<int:day>', methods=['GET'])
def get_orders_by_day(year, month, day):
    start_date = datetime(year, month, day)
    end_date = start_date + timedelta(days=1)
    daily_results = []
    orders = dp.session.query(
        Order.id.label('order_id'),
        Order.create_at.label('data'),
        Users.full_name.label('user_name'),
        Users.phone.label('phone')).join(Users).filter(
        Order.create_at >= start_date,  Order.create_at < end_date).all()

    total_orders_day = dp.session.query(func.count(Order.id)).filter(
        Order.create_at >= start_date, Order.create_at < end_date).scalar()

    total_revenueSum = dp.session.query(func.sum(Order.all_priceSum)).filter(
        Order.create_at >= start_date, Order.create_at < end_date).scalar()
    total_revenueDol = dp.session.query(func.sum(Order.all_priceDol)).filter(
        Order.create_at >= start_date, Order.create_at < end_date).scalar()
    total_cash = dp.session.query(func.sum(Order.cash)).filter(
        Order.create_at >= start_date, Order.create_at < end_date).scalar()
    total_dollar = dp.session.query(func.sum(Order.dollar)).filter(
        Order.create_at >= start_date, Order.create_at < end_date).scalar()
    total_terminal = dp.session.query(func.sum(Order.terminal)).filter(
        Order.create_at >= start_date, Order.create_at < end_date).scalar()
    total_card = dp.session.query(func.sum(Order.card)).filter(
        Order.create_at >= start_date, Order.create_at < end_date).scalar()
    total_transfers = dp.session.query(func.sum(Order.transfers)).filter(
        Order.create_at >= start_date, Order.create_at < end_date).scalar()
    total_dolgsum = dp.session.query(func.sum(Order.dolgsum)).filter(
        Order.create_at >= start_date, Order.create_at < end_date).scalar()
    total_dolgdol = dp.session.query(func.sum(Order.dolgdol)).filter(
        Order.create_at >= start_date, Order.create_at < end_date).scalar()

    total_paiddolgdol = dp.session.query(func.sum(DolglistEntry.paid_month_dol)).filter(
        DolglistEntry.date >= start_date, DolglistEntry.date < end_date).scalar()
    total_paiddolgsum = dp.session.query(func.sum(DolglistEntry.paid_month_sum)).filter(
        DolglistEntry.date >= start_date, DolglistEntry.date < end_date).scalar()

    results = []
    for order in orders:
        results.append({
            'order_id': order.order_id,
            'user_name': order.user_name,
            'phone': order.phone,
            'data': order.data.strftime('%Y-%m-%d %H:%M:%S')
        })
    daily_results.append({
        'all_priceSum': total_revenueSum if total_revenueSum is not None else 0,
        'all_priceDol': total_revenueDol if total_revenueDol is not None else 0,
        "total_cash": total_cash if total_cash is not None else 0,
        "total_dollar": total_dollar if total_dollar is not None else 0,
        "total_terminal": total_terminal if total_terminal is not None else 0,
        "total_card": total_card if total_card is not None else 0,
        "total_transfers": total_transfers if total_transfers is not None else 0,
        "total_dolgsum": total_dolgsum if total_dolgsum is not None else 0,
        "total_dolgdol": total_dolgdol if total_dolgdol is not None else 0,
        "total_paiddolgdol": total_paiddolgdol if total_paiddolgdol is not None else 0,
        "total_paiddolgsum": total_paiddolgsum if total_paiddolgsum is not None else 0,
        "all_orders_today": results
    })
    return jsonify(daily_results)


@app.route('/orders/<int:year>/<int:month>/<int:day>/<int:order_id>', methods=['GET'])
def get_order_details(year, month, day, order_id):
    order = dp.session.query(
        Order,
        Users.full_name.label('user_name')
    ).join(Users, Order.user_id == Users.id).filter(
        Order.id == order_id,
        extract('year', Order.create_at) == year,
        extract('month', Order.create_at) == month,
        extract('day', Order.create_at) == day
    ).first()

    if order is None:
        return jsonify({'message': 'Order not found'}), 404
    all_priceSum = order.Order.all_priceSum
    was_paidSum = order.Order.was_paidSum
    no_paidSum = float(all_priceSum) - float(was_paidSum)

    all_priceDol = order.Order.all_priceDol
    was_paidDol = order.Order.was_paidDol
    no_paidDol = float(all_priceDol) - float(was_paidDol)
    order_details = {
        'user_name': order.user_name,
        'products': order.Order.products,  # Предполагается, что это JSON-строка
        'datetime': order.Order.create_at.strftime('%Y-%m-%d %H:%M:%S'),
        'all_priceSum': order.Order.all_priceSum,
        'all_priceDol': order.Order.all_priceDol,
        'dolgSum': no_paidSum,
        'dolgDol': no_paidDol,
        'pay_method': order.Order.pay_method,
        "cash": order.Order.cash,
        "card": order.Order.card,
        "dollars": order.Order.dollar,
        "terminal": order.Order.terminal,
        "transfers": order.Order.transfers
    }

    return jsonify(order_details)


@app.route('/orders/last_week', methods=['GET'])
def get_orders_last_week():
    today = datetime.utcnow().date()
    # Calculate the start of the week (Monday)
    start_of_this_week = today - timedelta(days=today.weekday())
    start_of_last_week = start_of_this_week - timedelta(days=7)
    end_of_last_week = start_of_this_week - timedelta(days=1)

    total_quantity_sold = dp.session.query(func.sum(Order.all_quantity)).filter(
        Order.create_at >= start_of_last_week, Order.create_at <= end_of_last_week).scalar()
    total_orders_last_week = dp.session.query(func.count(Order.id)).filter(
        Order.create_at >= start_of_last_week, Order.create_at <= end_of_last_week).scalar()
    total_revenueSum = dp.session.query(func.sum(Order.all_priceSum)).filter(
        Order.create_at >= start_of_last_week, Order.create_at <= end_of_last_week).scalar()
    total_revenueDol = dp.session.query(func.sum(Order.all_priceDol)).filter(
        Order.create_at >= start_of_last_week, Order.create_at <= end_of_last_week).scalar()

    # Запрос заказов за прошедшую неделю
    orders = Order.query.filter(
        Order.create_at >= start_of_last_week, Order.create_at <= end_of_last_week).all()

    orders_list = []

    for order in orders:
        orders_list.append({
            "order_id": order.id,
            "user_id": order.user_id,
            "products": order.products,
            "all_quantity": order.all_quantity,
            "all_priceSum": order.all_priceSum,
            "all_priceDol": order.all_priceDol,
            "pay_method": order.pay_method,
            "create_at": order.create_at.isoformat()
        })

    result = {'Общее проданных продуктов на прошлой неделе': total_quantity_sold, 'Заказы прошлой недели': orders_list,
              'Общее количество заказов': total_orders_last_week if total_orders_last_week is not None else 0,
              'Общая выручка в долларах': total_revenueDol if total_revenueDol is not None else 0,
              'Общая выручка в суммах': total_revenueSum if total_revenueSum is not None else 0
              }

    return jsonify(result)


@app.route('/users/<string:phone>', methods=['GET'])
def get_user_by_phone(phone):
    user = Users.query.filter_by(phone=phone).first()
    if user:
        order = Order.query.filter_by(user_id=user.id).first()
        user_dict = {
            '🔢 Ваш ID': user.id,
            '📝 Полное имя': user.full_name,
            "📞 Номер телефона": user.phone,
            "🗓 Год рождения": user.year,
            "💬 Узнали вы о нас": user.known_from,
            "⭕️ Есть ли в черном списке": "НЕТ❌" if not is_user_in_blacklist(user.id) else "ДА✅",
            "🛒 Общее количество купленных продуктов": user.all_quant,
        }
        return jsonify(user_dict)
    else:
        return jsonify({"message": "Пользователь не найден"}), 404

# ----------------------------------------------------------------------------------------------------------------------


@app.route('/profit/', methods=['GET'])
def profit():
    profits = Profit.query.all()
    result = []
    total_product_amountsum = 0
    total_product_amountdol = 0

    # Используем словарь для хранения сумм по каждому product_id
    product_totals = {}

    for profit in profits:
        # Находим продукт по product_id
        product = Products.query.get(profit.product)
        product_name = product.product_name if product else "Неизвестный продукт"
        pricekg = product.product_amount * profit.quantity if product else 0

        # Проверяем, был ли уже выведен продукт с этим product_id
        if profit.product in product_totals:
            # Суммируем значения для одинаковых product_id
            product_totals[profit.product]['profitsum'] += profit.profitsum if profit.profitsum else 0
            product_totals[profit.product]['profitdol'] += profit.profitdol if profit.profitdol else 0
            product_totals[profit.product]['quantity'] += profit.quantity
        else:
            product_totals[profit.product] = {
                'product_id': profit.product,
                'product_name': product_name,
                'product_amount_real': profit.product_amount_real,
                'pricekg': pricekg,
                'product_amount': product.product_amount if product else 0,
                'profitsum': profit.profitsum if profit.profitsum else 0,
                'profitdol': profit.profitdol if profit.profitdol else 0,
                'quantity': profit.quantity
            }

        if profit.amountsum:
            total_product_amountsum += product.product_amount * profit.quantity
        else:
            total_product_amountdol += product.product_amount * profit.quantity

    # Преобразуем словарь в список для вывода
    result.extend(product_totals.values())

    # Расчет прибыли
    total_profit_sum = sum(item['profitsum'] for item in product_totals.values())
    total_profit_dol = sum(item['profitdol'] for item in product_totals.values())
    # total_product_amountsum = sum(item['pricekg'] for item in product_totals.values())
    # total_product_amountdol = sum(item['pricekg'] for item in product_totals.values())

    priblsum = total_profit_sum - total_product_amountsum
    pribldol = total_profit_dol - total_product_amountdol

    # Добавляем суммарные значения в результат
    result.append({
        "Total_profit_sum": total_profit_sum,
        "Total_profit_dol": total_profit_dol,
        "Total_product_amountsum": total_product_amountsum,
        "Total_product_amountdol": total_product_amountdol,
        "Priblsum": priblsum,
        "Pribldol": pribldol
    })

    return jsonify(result)


# @app.route('/profit/<int:year>', methods=['GET'])
# def profit_by_year(year):
#     monthly_profits = {}
#     total_product_amountsum = 0
#     total_product_amountdol = 0
#
#     for month in range(1, 13):
#         profits = Profit.query.filter(extract('year', Profit.created) == year,
#                                       extract('month', Profit.created) == month).all()
#
#         product_totals = {}
#
#         for profit in profits:
#             # Находим продукт по product_id
#             product = Products.query.get(profit.product)
#             product_name = product.product_name if product else "Неизвестный продукт"
#             pricekg = product.product_amount * profit.quantity if product else 0
#
#             # Проверяем, был ли уже выведен продукт с этим product_id
#             if profit.product in product_totals:
#                 # Суммируем значения для одинаковых product_id
#                 product_totals[profit.product]['profitsum'] += profit.profitsum if profit.profitsum else 0
#                 product_totals[profit.product]['profitdol'] += profit.profitdol if profit.profitdol else 0
#                 product_totals[profit.product]['quantity'] += profit.quantity
#             else:
#                 product_totals[profit.product] = {
#                     'product_id': profit.product,
#                     'product_name': product_name,
#                     'product_amount_real': profit.product_amount_real,
#                     'pricekg': pricekg,
#                     'product_amount': product.product_amount if product else 0,
#                     'profitsum': profit.profitsum if profit.profitsum else 0,
#                     'profitdol': profit.profitdol if profit.profitdol else 0,
#                     'quantity': profit.quantity
#                 }
#             if profit.amountsum:
#                 total_product_amountsum += product.product_amount * profit.quantity
#             else:
#                 total_product_amountdol += product.product_amount * profit.quantity
#         # Преобразуем словарь в список для вывода
#         monthly_profits[str(month)] = list(product_totals.values())
#
#     # Расчет прибыли по году
#     total_profit_sum = sum(item['profitsum'] for month_totals in monthly_profits.values() for item in month_totals)
#     total_profit_dol = sum(item['profitdol'] for month_totals in monthly_profits.values() for item in month_totals)
#
#     priblsum = total_profit_sum - total_product_amountsum
#     pribldol = total_profit_dol - total_product_amountdol
#
#     # Добавляем суммарные значения в результат
#     monthly_profits['Total'] = {
#         "Total_profit_sum": total_profit_sum,
#         "Total_profit_dol": total_profit_dol,
#         "Total_product_amountsum": total_product_amountsum,
#         "Total_product_amountdol": total_product_amountdol,
#         "Priblsum": priblsum,
#         "Pribldol": pribldol
#     }
#
#     return jsonify(monthly_profits)

@app.route('/profit/<int:year>', methods=['GET'])
def profit_by_year(year):
    total_product_amountsum = 0
    total_product_amountdol = 0

    # Создаем словарь для хранения общей прибыли по каждому продукту
    product_totals = {}

    # Получаем все прибыли за указанный год
    profits = Profit.query.filter(extract('year', Profit.created) == year).all()

    for profit in profits:
        # Находим продукт по product_id
        product = Products.query.get(profit.product)
        product_name = product.product_name if product else "Неизвестный продукт"
        pricekg = product.product_amount * profit.quantity if product else 0

        # Проверяем, был ли уже выведен продукт с этим product_id
        if profit.product in product_totals:
            # Суммируем значения для одинаковых product_id
            product_totals[profit.product]['profitsum'] += profit.profitsum if profit.profitsum else 0
            product_totals[profit.product]['profitdol'] += profit.profitdol if profit.profitdol else 0
            product_totals[profit.product]['quantity'] += profit.quantity
        else:
            product_totals[profit.product] = {
                'product_id': profit.product,
                'product_name': product_name,
                'product_amount_real': profit.product_amount_real,
                'pricekg': pricekg,
                'product_amount': product.product_amount if product else 0,
                'profitsum': profit.profitsum if profit.profitsum else 0,
                'profitdol': profit.profitdol if profit.profitdol else 0,
                'quantity': profit.quantity
            }
        if profit.amountsum:
            total_product_amountsum += product.product_amount * profit.quantity
        else:
            total_product_amountdol += product.product_amount * profit.quantity

    # Преобразуем словарь в список для вывода
    detailed_profits = list(product_totals.values())

    # Расчет прибыли по дню
    total_profit_sum = sum(item['profitsum'] for item in detailed_profits)
    total_profit_dol = sum(item['profitdol'] for item in detailed_profits)

    priblsum = total_profit_sum - total_product_amountsum
    pribldol = total_profit_dol - total_product_amountdol

    # Добавляем суммарные значения в результат
    daily_profit_summary = {
        "Total_profit_sum": total_profit_sum,
        "Total_profit_dol": total_profit_dol,
        "Total_product_amountsum": total_product_amountsum,
        "Total_product_amountdol": total_product_amountdol,
        "Priblsum": priblsum,
        "Pribldol": pribldol,
        "detailed_profits": detailed_profits
    }

    return jsonify(daily_profit_summary)


@app.route('/profit/<int:year>/<int:month>', methods=['GET'])
def profit_by_month(year, month):
    # Определение количества дней в месяце
    total_product_amountsum = 0
    total_product_amountdol = 0

    # Создаем словарь для хранения общей прибыли по каждому продукту
    product_totals = {}

    # Получаем все прибыли за указанный год
    profits = Profit.query.filter(extract('year', Profit.created) == year,
                                  extract('month', Profit.created) == month).all()

    for profit in profits:
        # Находим продукт по product_id
        product = Products.query.get(profit.product)
        product_name = product.product_name if product else "Неизвестный продукт"
        pricekg = product.product_amount * profit.quantity if product else 0

        # Проверяем, был ли уже выведен продукт с этим product_id
        if profit.product in product_totals:
            # Суммируем значения для одинаковых product_id
            product_totals[profit.product]['profitsum'] += profit.profitsum if profit.profitsum else 0
            product_totals[profit.product]['profitdol'] += profit.profitdol if profit.profitdol else 0
            product_totals[profit.product]['quantity'] += profit.quantity
        else:
            product_totals[profit.product] = {
                'product_id': profit.product,
                'product_name': product_name,
                'product_amount_real': profit.product_amount_real,
                'pricekg': pricekg,
                'product_amount': product.product_amount if product else 0,
                'profitsum': profit.profitsum if profit.profitsum else 0,
                'profitdol': profit.profitdol if profit.profitdol else 0,
                'quantity': profit.quantity
            }
        if profit.amountsum:
            total_product_amountsum += product.product_amount * profit.quantity
        else:
            total_product_amountdol += product.product_amount * profit.quantity

    # Преобразуем словарь в список для вывода
    detailed_profits = list(product_totals.values())

    # Расчет прибыли по дню
    total_profit_sum = sum(item['profitsum'] for item in detailed_profits)
    total_profit_dol = sum(item['profitdol'] for item in detailed_profits)

    priblsum = total_profit_sum - total_product_amountsum
    pribldol = total_profit_dol - total_product_amountdol

    # Добавляем суммарные значения в результат
    daily_profit_summary = {
        "Total_profit_sum": total_profit_sum,
        "Total_profit_dol": total_profit_dol,
        "Total_product_amountsum": total_product_amountsum,
        "Total_product_amountdol": total_product_amountdol,
        "Priblsum": priblsum,
        "Pribldol": pribldol,
        "detailed_profits": detailed_profits
    }

    return jsonify(daily_profit_summary)


@app.route('/profit/<int:year>/<int:month>/<int:day>', methods=['GET'])
def profit_by_specific_day(year, month, day):
    try:
        date = datetime(year, month, day)
    except ValueError:
        return jsonify({"error": "Неверная дата"}), 400

    profits = Profit.query.filter(extract('year', Profit.created) == year,
                                  extract('month', Profit.created) == month,
                                  extract('day', Profit.created) == day).all()

    product_totals = {}
    total_product_amountsum = 0
    total_product_amountdol = 0
    for profit in profits:
        # Находим продукт по product_id
        product = Products.query.get(profit.product)
        product_name = product.product_name if product else "Неизвестный продукт"
        pricekg = product.product_amount * profit.quantity if product else 0

        # Проверяем, был ли уже выведен продукт с этим product_id
        if profit.product in product_totals:
            # Суммируем значения для одинаковых product_id
            product_totals[profit.product]['profitsum'] += profit.profitsum if profit.profitsum else 0
            product_totals[profit.product]['profitdol'] += profit.profitdol if profit.profitdol else 0
            product_totals[profit.product]['quantity'] += profit.quantity
        else:
            product_totals[profit.product] = {
                'product_id': profit.product,
                'product_name': product_name,
                'product_amount_real': profit.product_amount_real,
                'pricekg': pricekg,
                'product_amount': product.product_amount if product else 0,
                'profitsum': profit.profitsum if profit.profitsum else 0,
                'profitdol': profit.profitdol if profit.profitdol else 0,
                'quantity': profit.quantity
            }
        if profit.amountsum:
            total_product_amountsum += product.product_amount * profit.quantity
        else:
            total_product_amountdol += product.product_amount * profit.quantity
    # Преобразуем словарь в список для вывода
    detailed_profits = list(product_totals.values())

    # Расчет прибыли по дню
    total_profit_sum = sum(item['profitsum'] for item in detailed_profits)
    total_profit_dol = sum(item['profitdol'] for item in detailed_profits)

    priblsum = total_profit_sum - total_product_amountsum
    pribldol = total_profit_dol - total_product_amountdol

    # Добавляем суммарные значения в результат
    daily_profit_summary = {
        "Total_profit_sum": total_profit_sum,
        "Total_profit_dol": total_profit_dol,
        "Total_product_amountsum": total_product_amountsum,
        "Total_product_amountdol": total_product_amountdol,
        "Priblsum": priblsum,
        "Pribldol": pribldol,
        "detailed_profits": detailed_profits
    }

    return jsonify(daily_profit_summary)


#-----------------------------------------------------------------------------------------------------------------------
@app.route('/vozvrats/<int:year>', methods=['GET'])
def get_vozvrats_by_year(year):
    monthly_results = []

    for month in range(1, 13):
        # Определение начала и конца месяца
        start_date = datetime(year, month, 1)
        end_date = datetime(year, month, calendar.monthrange(year, month)[1], 23, 59, 59)

        # Извлечение возвратов за месяц
        vozvrats = Vozvrat.query.filter(
            Vozvrat.date >= start_date,
            Vozvrat.date <= end_date
        ).all()

        month_result = {
            'month': month,
            'total_returns': len(vozvrats),
            'details': [
                {
                    'id': vozvrat.id,
                    'date': vozvrat.date.isoformat(),
                    'description': vozvrat.description,
                    'products': json.loads(vozvrat.products)  # Десериализация строки JSON в объект Python
                } for vozvrat in vozvrats
            ]
        }
        monthly_results.append(month_result)

    return jsonify(monthly_results)


@app.route('/vozvrats/<int:year>/<int:month>', methods=['GET'])
def get_vozvrats_by_month(year, month):
    daily_results = []
    num_days = calendar.monthrange(year, month)[1]

    for day in range(1, num_days + 1):
        start_date = datetime(year, month, day)
        end_date = start_date + timedelta(days=1)

        vozvrats = Vozvrat.query.filter(
            Vozvrat.date >= start_date,
            Vozvrat.date < end_date
        ).all()

        day_result = {
            'date': start_date.date().isoformat(),
            'total_returns': len(vozvrats),
            'details': [
                {
                    'id': vozvrat.id,
                    'date': vozvrat.date.isoformat(),
                    'description': vozvrat.description,
                    'products': json.loads(vozvrat.products)  # Десериализация строки JSON в объект Python
                } for vozvrat in vozvrats
            ]
        }
        daily_results.append(day_result)

    return jsonify(daily_results)


@app.route('/vozvrats/<int:year>/<int:month>/<int:day>', methods=['GET'])
def get_vozvrats_by_day(year, month, day):
    start_date = datetime(year, month, day)
    end_date = start_date + timedelta(days=1)

    vozvrats = Vozvrat.query.filter(
        Vozvrat.date >= start_date,
        Vozvrat.date < end_date
    ).all()

    daily_results = {
        'date': start_date.date().isoformat(),
        'total_returns': len(vozvrats),
        'details': [
            {
                'id': vozvrat.id,
                'date': vozvrat.date.isoformat(),
                'description': vozvrat.description,
                'products': json.loads(vozvrat.products)  # Десериализация строки JSON в объект Python
            } for vozvrat in vozvrats
        ]
    }

    return jsonify(daily_results)
# ----------------------------------------------------------------------------------------------------------------------


@app.route('/Expenditure', methods=['GET'])
def expenditure():
    # Запрашиваем все записи из таблицы расходов
    expenditures = Expenditure.query.all()

    # Создаем список словарей, каждый из которых представляет расход
    expenditures_list = []
    for expenditure in expenditures:
        expenditure_data = {
            'id': expenditure.id,
            'date': expenditure.date.isoformat(),
            'description': expenditure.description,
            'outgosum': expenditure.outgosum,
            'outgodol': expenditure.outgodol
        }
        expenditures_list.append(expenditure_data)

    # Возвращаем данные в формате JSON
    return jsonify(expenditures_list)


@app.route('/Expenditurepost', methods=['POST'])
def add_expenditure():
    data = request.json
    outgosum = float(data.get('outgosum')) if data.get('outgosum') is not None else 0
    outgodol = float(data.get('outgodol')) if data.get('outgodol') is not None else 0
    description = data.get('description')

    # Получаем запись из таблицы Totality
    total_record = Totality.query.first()  # Предполагаем, что есть только одна запись

    if total_record:
        # Вычитаем outgo из totalsum и totaldol
        if outgosum:
            total_record.totalsum -= outgosum
        if outgodol:
            total_record.totaldol -= outgodol

        # Добавляем запись в таблицу Expenditure
        new_expenditure = Expenditure(outgosum=outgosum, outgodol=outgodol, description=description,
                                      obsheesum=total_record.totalsum, obsheedol=total_record.totaldol)
        dp.session.add(new_expenditure)

        # Сохраняем изменения в базе данных
        dp.session.commit()
        return jsonify({"message": "Expenditure added and profit updated"})
    else:
        return jsonify({"error": "Totality record not found"}), 404


@app.route('/get_products_info', methods=['GET'])
def get_products_info():
    orders = Order.query.all()
    product_name_dict = {product.product_id: product.product_name for product in Products.query.all()}

    result = {}

    for order in orders:
        # Проверяем, является ли products строкой (предполагаем, что это строка JSON)
        if isinstance(order.products, str):
            order.products = json.loads(order.products)

        for product in order.products:
            product_id = product.get('product_id')
            amount = product.get('amount')

            # Получаем имя продукта из product_name_dict
            product_name = product_name_dict.get(product_id, f"Unknown Product {product_id}")

            # Добавляем amount к существующему значению или устанавливаем новое значение
            result[product_name] = result.get(product_name, 0) + amount

            # Обработка вложенного списка "recept"
            if 'recept' in product:
                for recept in product['recept']:
                    recept_product_id = recept.get('product_id')
                    recept_amount = recept.get('amount')

                    # Получаем имя продукта из product_name_dict
                    recept_product_name = product_name_dict.get(recept_product_id, f"Unknown Product {recept_product_id}")

                    # Добавляем recept_amount к существующему значению или устанавливаем новое значение
                    result[recept_product_name] = result.get(recept_product_name, 0) + recept_amount

    return jsonify(result)


@app.route('/get_products_info/<int:year>', methods=['GET'])
def get_products_info_by_year(year):
    # Фильтруем заказы по указанному году
    orders = Order.query.filter(extract('year', Order.create_at) == year).all()

    # Создаем словарь имен продуктов
    product_name_dict = {product.product_id: product.product_name for product in Products.query.all()}

    result = {}

    # Обрабатываем каждый заказ
    for order in orders:
        # Проверяем, является ли products строкой (предполагаем, что это строка JSON)
        if isinstance(order.products, str):
            order.products = json.loads(order.products)

        # Обрабатываем каждый продукт в заказе
        for product in order.products:
            product_id = product.get('product_id')
            amount = product.get('amount')

            # Получаем имя продукта из product_name_dict
            product_name = product_name_dict.get(product_id, f"Unknown Product {product_id}")

            # Добавляем amount к существующему значению или устанавливаем новое значение
            result[product_name] = result.get(product_name, 0) + amount

            # Обработка вложенного списка "recept"
            if 'recept' in product:
                for recept in product['recept']:
                    recept_product_id = recept.get('product_id')
                    recept_amount = recept.get('amount')

                    # Получаем имя продукта из product_name_dict
                    recept_product_name = product_name_dict.get(recept_product_id,
                                                                f"Unknown Product {recept_product_id}")

                    # Добавляем recept_amount к существующему значению или устанавливаем новое значение
                    result[recept_product_name] = result.get(recept_product_name, 0) + recept_amount

    return jsonify(result)


@app.route('/get_products_info/<int:year>/<int:month>', methods=['GET'])
def get_products_info_by_month(year, month):
    # Фильтруем заказы по указанному году и месяцу
    orders = Order.query.filter(extract('year', Order.create_at) == year,
                                extract('month', Order.create_at) == month).all()

    # Создаем словарь имен продуктов
    product_name_dict = {product.product_id: product.product_name for product in Products.query.all()}

    result = {}

    # Обрабатываем каждый заказ
    for order in orders:
        # Проверяем, является ли products строкой (предполагаем, что это строка JSON)
        if isinstance(order.products, str):
            order.products = json.loads(order.products)

        # Обрабатываем каждый продукт в заказе
        for product in order.products:
            product_id = product.get('product_id')
            amount = product.get('amount')

            # Получаем имя продукта из product_name_dict
            product_name = product_name_dict.get(product_id, f"Unknown Product {product_id}")

            # Добавляем amount к существующему значению или устанавливаем новое значение
            result[product_name] = result.get(product_name, 0) + amount

            # Обработка вложенного списка "recept"
            if 'recept' in product:
                for recept in product['recept']:
                    recept_product_id = recept.get('product_id')
                    recept_amount = recept.get('amount')

                    # Получаем имя продукта из product_name_dict
                    recept_product_name = product_name_dict.get(recept_product_id,
                                                                f"Unknown Product {recept_product_id}")

                    # Добавляем recept_amount к существующему значению или устанавливаем новое значение
                    result[recept_product_name] = result.get(recept_product_name, 0) + recept_amount

    return jsonify(result)


@app.route('/get_products_info/<int:year>/<int:month>/<int:day>', methods=['GET'])
def get_products_info_by_date(year, month, day):
    # Фильтруем заказы по указанной дате
    orders = Order.query.filter(
        extract('year', Order.create_at) == year,
        extract('month', Order.create_at) == month,
        extract('day', Order.create_at) == day
    ).all()

    # Создаем словарь имен продуктов
    product_name_dict = {product.product_id: product.product_name for product in Products.query.all()}

    result = {}

    # Обрабатываем каждый заказ
    for order in orders:
        # Проверяем, является ли products строкой (предполагаем, что это строка JSON)
        if isinstance(order.products, str):
            order.products = json.loads(order.products)

        # Обрабатываем каждый продукт в заказе
        for product in order.products:
            product_id = product.get('product_id')
            amount = product.get('amount')

            # Получаем имя продукта из product_name_dict
            product_name = product_name_dict.get(product_id, f"Unknown Product {product_id}")

            # Добавляем amount к существующему значению или устанавливаем новое значение
            result[product_name] = result.get(product_name, 0) + amount

            # Обработка вложенного списка "recept"
            if 'recept' in product:
                for recept in product['recept']:
                    recept_product_id = recept.get('product_id')
                    recept_amount = recept.get('amount')

                    # Получаем имя продукта из product_name_dict
                    recept_product_name = product_name_dict.get(recept_product_id,
                                                                f"Unknown Product {recept_product_id}")

                    # Добавляем recept_amount к существующему значению или устанавливаем новое значение
                    result[recept_product_name] = result.get(recept_product_name, 0) + recept_amount

    return jsonify(result)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)