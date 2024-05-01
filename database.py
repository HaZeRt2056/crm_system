from datetime import datetime, timedelta

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import extract
from sqlalchemy.orm import joinedload
from sqlalchemy import func

dp = SQLAlchemy()


class Users(dp.Model):
    id = dp.Column(dp.Integer, primary_key=True)
    full_name = dp.Column(dp.String(80), nullable=False)
    phone = dp.Column(dp.String, nullable=False)
    year = dp.Column(dp.String, nullable=False)
    company = dp.Column(dp.String(80), nullable=False)
    known_from = dp.Column(dp.String(20), nullable=False)
    all_priceSum = dp.Column(dp.Float, default=None)
    all_priceDol = dp.Column(dp.Float, default=None)
    all_quant = dp.Column(dp.Float, default=None)
    blacklist = dp.relationship("BlacklistEntry", back_populates="user")
    dolglist = dp.relationship("DolglistEntry", back_populates="user")
    paid_amountSum = dp.Column(dp.Float, default=0)
    paid_amountDol = dp.Column(dp.Float, default=0)

    # Свойство amount только для чтения
    @property
    def amountDol(self):
        # Возвращаем сумму из DolglistEntry, если она существует, учитывая возможность None
        if self.dolglist:
            return sum(entry.amountDol if entry.amountDol is not None else 0 for entry in self.dolglist)
        return 0  # Или любое другое значение по умолчанию

    @property
    def amountSum(self):
        # Возвращаем сумму из DolglistEntry, если она существует, учитывая возможность None
        if self.dolglist:
            return sum(entry.amountSum if entry.amountSum is not None else 0 for entry in self.dolglist)
        return 0  # Или любое другое значение по умолчанию


class BlacklistEntry(dp.Model):
    id = dp.Column(dp.Integer, primary_key=True)
    user_id = dp.Column(dp.Integer, dp.ForeignKey("users.id"))
    user = dp.relationship("Users", back_populates="blacklist")
    # Нет amount здесь


class DolglistEntry(dp.Model):
    id = dp.Column(dp.Integer, primary_key=True)
    user_id = dp.Column(dp.Integer, dp.ForeignKey("users.id"))
    user = dp.relationship("Users", back_populates="dolglist")
    amountSum = dp.Column(dp.Float)
    amountDol = dp.Column(dp.Float)
    paid_day_sum = dp.Column(dp.Float, default=0)
    paid_month_sum = dp.Column(dp.Float, default=0)
    paid_day_dol = dp.Column(dp.Float, default=0)
    paid_month_dol = dp.Column(dp.Float, default=0)
    date = dp.Column(dp.DateTime, default=datetime.utcnow)

    def __init__(self, user, amountSum, amountDol, date=None):
        self.user = user
        self.amountSum = amountSum
        self.amountDol = amountDol
        self.date = date


class Products(dp.Model):
    product_id = dp.Column(dp.Integer, primary_key=True)
    product_name = dp.Column(dp.String(80), nullable=False)
    product_description = dp.Column(dp.Text(80), nullable=False)
    # product_quantity - количество продукта
    product_quantity = dp.Column(dp.Float, nullable=False)
    # product_amount - цена
    product_amount = dp.Column(dp.Float, nullable=False)
    product_photo = dp.Column(dp.String(255), nullable=False)


class Order(dp.Model):
    id = dp.Column(dp.Integer, primary_key=True)

    products = dp.Column(dp.String(), nullable=False)
    user_id = dp.Column(dp.Integer, dp.ForeignKey('users.id'), nullable=False)
    all_quantity = dp.Column(dp.Float, nullable=False)
    all_priceSum = dp.Column(dp.Float, nullable=False)
    all_priceDol = dp.Column(dp.Float, nullable=False)
    pay_method = dp.Column(dp.String(50), nullable=False)
    create_at = dp.Column(dp.DateTime, default=datetime.utcnow)
    was_paidSum = dp.Column(dp.Float, default=0)
    was_paidDol = dp.Column(dp.Float, default=0)
    cash = dp.Column(dp.Float, default=0)
    dollar = dp.Column(dp.Float, default=0)
    terminal = dp.Column(dp.Float, default=0)
    card = dp.Column(dp.Float, default=0)
    transfers = dp.Column(dp.Float, default=0)
    dolgsum = dp.Column(dp.Float, default=0)
    dolgdol = dp.Column(dp.Float, default=0)


# база данных прибыли
class Profit(dp.Model):
    id = dp.Column(dp.Integer, primary_key=True)
    created = dp.Column(dp.DateTime, default=datetime.utcnow)
    # цена умноженная на кол-во которая была дана при продаже
    profitsum = dp.Column(dp.Float)
    profitdol = dp.Column(dp.Float)
    quantity = dp.Column(dp.Float)
    # продукт id
    product = dp.Column(dp.Float)
    # цена реальная которая в меню продуктов
    product_amount_real = dp.Column(dp.Integer)
    #  product_amount ---- цена продукта то что написано в заказе
    amountsum = dp.Column(dp.Float)
    amountdol = dp.Column(dp.Float)
    # cчитает общую сумму продажи


# база данных расхода
class Expenditure(dp.Model):
    id = dp.Column(dp.Integer, primary_key=True)
    date = dp.Column(dp.DateTime, default=datetime.utcnow)
    description = dp.Column(dp.Text(120), nullable=False)
    outgosum = dp.Column(dp.Float, default=0)
    outgodol = dp.Column(dp.Float, default=0)
    obsheesum = dp.Column(dp.Float, default=0)
    obsheedol = dp.Column(dp.Float, default=0)


# база данных где хранится общая сумма продажи (чисто для работы кода)
class Totality(dp.Model):
    id = dp.Column(dp.Integer, primary_key=True)
    totalsum = dp.Column(dp.Float, default=0)
    totaldol = dp.Column(dp.Float, default=0)


class Vozvrat(dp.Model):
    id = dp.Column(dp.Integer, primary_key=True)
    date = dp.Column(dp.DateTime, default=datetime.utcnow)
    products = dp.Column(dp.String, nullable=False)  # Сохраняем как строку JSON
    description = dp.Column(dp.Text, nullable=False)



def __repr__(self):
    return '<User %r>' % self.id
