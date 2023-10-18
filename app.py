from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import pymysql
from werkzeug.utils import secure_filename
import os

pymysql.install_as_MySQLdb()

db_password = os.environ.get("DB_PASSWORD")

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:Password#74@localhost/Project2'
app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql://root:{db_password}@localhost/Project2'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # Silence the deprecation warning
db = SQLAlchemy(app)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static/images')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(150), nullable=False)
    description = db.Column(db.String(500), nullable=True)
    image = db.Column(db.String(255), nullable=True)

@app.route('/')
def index():
    items = Item.query.all()
    sort_by = request.args.get('sort_by', 'id')
    if sort_by == 'name':
        items.sort(key=lambda x: x.name)
    return render_template('items.html', items=items)


@app.route('/search', methods=['GET'])
def search():
    keyword = request.args.get('keyword')
    item_id = request.args.get('id')
    print(f"Keyword: {keyword}, Item ID: {item_id}")  # Logging the received values

    if keyword:
        items = Item.query.filter(Item.name.contains(keyword)).all()
        print("Searching by keyword")  # Logging the executed condition
    elif item_id and item_id.isdigit():
        items = [Item.query.get(int(item_id))]
        print("Searching by ID")  # Logging the executed condition
    else:
        items = []
        print("No valid keyword or ID")  # Logging the executed condition

    return render_template('items.html', items=items)



def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


DEFAULT_IMAGE = "No_image_available.svg.png"

@app.route('/add-item', methods=['GET', 'POST'])
def add_item():
    if request.method == 'POST':
        file = request.files.get('image')  # Using .get() method

        filename = DEFAULT_IMAGE  # Set the filename as the default image initially
        if file and file.filename != '' and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        # Storing form data and saving to the database
        name = request.form['name']
        description = request.form.get('description')  # Using .get() method to handle no description

        # Creating new_item with optional description and image
        new_item = Item(name=name, description=description, image=filename)
        db.session.add(new_item)
        db.session.commit()

        return redirect(url_for('index'))  # Redirecting to the index route after processing
    else:
        # This block will handle GET requests and render the form
        return render_template('add_item.html')


@app.route('/edit-item/<int:item_id>', methods=['GET', 'POST'])
def edit(item_id):
    item = Item.query.get(item_id)
    if request.method == 'POST':
        item.name = request.form.get('name')
        item.description = request.form.get('description')

        delete_image = request.form.get('delete_image')  # get the checkbox value
        file = request.files.get('image')

        if delete_image:
            item.image = 'No_image_available.svg.png'
        elif file and file.filename != '' and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            item.image = filename

        db.session.commit()
        return redirect(url_for('index'))

    return render_template('edit_item.html', item=item)


@app.route('/delete-item/<int:item_id>', methods=['GET'])
def delete(item_id):
    item = Item.query.get(item_id)
    db.session.delete(item)
    db.session.commit()
    return redirect(url_for('items'))

@app.route('/items', methods=['GET'])
def items():
    items_query = Item.query

    # Search
    search_term = request.args.get('search')
    if search_term:
        items_query = items_query.filter(Item.name.contains(search_term))

    # Sort
    sort_by = request.args.get('sort_by')
    if sort_by == 'id':
        items_query = items_query.order_by(Item.id)
    elif sort_by == 'name':
        items_query = items_query.order_by(Item.name)

    items = items_query.all()
    return render_template('items.html', items=items)


if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # In case tables haven't been created yet
    app.run(debug=True)