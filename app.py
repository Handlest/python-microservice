from flask import Flask, request, jsonify, Blueprint
from flask_sqlalchemy import SQLAlchemy
from flask_restx import Api, Resource, fields
import logging
from logging.handlers import RotatingFileHandler
import os

# Загрузка переменных окружения

# Инициализация Flask
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URI', 'sqlite:///app.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Инициализация SQLAlchemy
db = SQLAlchemy(app)

# Логирование
handler = RotatingFileHandler('app.log', maxBytes=100000, backupCount=3)
logging.basicConfig(level=logging.INFO, handlers=[handler],
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Создание API
api_blueprint = Blueprint('api', __name__, url_prefix='/api')
api = Api(api_blueprint, doc='/docs')
app.register_blueprint(api_blueprint)

# Модель данных
class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(200))

# Swagger описание модели
Product_model = api.model('Product', {
    'id': fields.Integer(readonly=True, description='The Product unique identifier'),
    'name': fields.String(required=True, description='The name of the Product'),
    'description': fields.String(description='The description of the Product')
})

# Роуты
@api.route('/products')
class ProductList(Resource):
    def get(self):
        """Получить все элементы"""
        products = Product.query.all()
        return [{'id': Product.id, 'name': Product.name, 'description': Product.description} for Product in products], 200

    @api.expect(Product_model)
    def post(self):
        """Создать новый элемент"""
        data = request.get_json()
        try:
            new_Product = Product(name=data['name'], description=data.get('description', ''))
            db.session.add(new_Product)
            db.session.commit()
            return {'message': 'Product created', 'id': new_Product.id}, 201
        except Exception as e:
            logger.error(f"Error creating Product: {e}")
            return {'error': 'Invalid data'}, 400

@api.route('/products/<int:id>')
class ProductDetail(Resource):
    def get(self, id):
        """Получить элемент по ID"""
        product = Product.query.get_or_404(id)
        return {'id': product.id, 'name': product.name, 'description': product.description}

    @api.expect(Product_model)
    def put(self, id):
        """Обновить элемент"""
        data = request.get_json()
        product = Product.query.get(id)
        if product:
            product.name = data['name']
            product.description = data.get('description', product.description)
            db.session.commit()
            return {'message': 'Product updated'}
        logger.warning(f"Product with ID {id} not found")
        return {'error': 'Product not found'}, 404

    def delete(self, id):
        """Удалить элемент"""
        product = Product.query.get(id)
        if product:
            db.session.delete(product)
            db.session.commit()
            return {'message': 'Product deleted'}
        logger.warning(f"Product with ID {id} not found")
        return {'error': 'Product not found'}, 404

# Инициализация базы данных
@app.before_request
def initialize_database():
    with app.app_context():
        db.create_all()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8080)