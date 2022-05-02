import os
from dotenv import load_dotenv
from flask import Flask, render_template, current_app, abort, jsonify, request
import boto3
from mysql.connector import Error, pooling
from werkzeug.utils import secure_filename
from utils import abort_message, with_cnx


load_dotenv()


def create_rds_pool():
  return pooling.MySQLConnectionPool(
      pool_name=os.getenv('POOL_NAME'),
      pool_size=int(os.getenv('POOL_SIZE')),
      host=os.getenv('RDS_HOST'),
      port=int(os.getenv('RDS_PORT')),
      user=os.getenv('RDS_USER'),
      password=os.getenv('RDS_PASSWORD'),
      database=os.getenv('RDS_DB')
  )


def rds_cnx():
  try:
    cnx = current_app.db_pool.get_connection()
    if cnx.is_connected():
      return cnx
  except Error as e:
    print('RDS Connection error: ', e)


@with_cnx(need_commit=False)
def query_messages(cursor):
  cursor.execute('SELECT content, image_url FROM messages')
  columns = [column[0] for column in cursor.description]
  output = [dict(zip(columns, row)) for row in cursor.fetchall()]
  return output


@with_cnx(need_commit=True)
def insert_message(cursor, content, image_url):
  cursor.execute(
      'INSERT INTO messages (content, image_url) VALUES (%s, %s)', (content, image_url))
  return


def upload_image(image_file):
  aws_default_region = os.getenv('AWS_DEFAULT_REGION')
  aws_access_key_id = os.getenv('AWS_ACCESS_KEY_ID')
  aws_secret_access_key = os.getenv('AWS_SECRET_ACCESS_KEY')
  s3_bucket_name = os.getenv('S3_BUCKET_NAME')
  image_file_name = secure_filename(image_file.filename)
  s3 = boto3.client('s3', aws_access_key_id=aws_access_key_id,
                    aws_secret_access_key=aws_secret_access_key)
  try:
    s3.upload_fileobj(image_file, s3_bucket_name,
                      f"msgboard/{image_file_name}")
    image_url = f"https://{s3_bucket_name}.s3.{aws_default_region}.amazonaws.com/msgboard/{image_file_name}"
    return image_url
  except Exception as e:
    abort(500, description=abort_message(e))


app = Flask(__name__)
with app.app_context():
  current_app.db_pool = create_rds_pool()
  current_app.rds_cnx = rds_cnx


@app.route('/')
def index():
  return render_template('index.html')


@app.route('/api/messages', methods=['GET'])
def get_messages():
  try:
    result = query_messages()
    return jsonify({'data': result if result else []})
  except Exception as e:
    abort(500, description=abort_message(e))


@app.route('/api/messages', methods=['POST'])
def post_message():
  try:
    content = request.form['content']
    image_file = request.files['image-file']
    if all((content, image_file)):
      image_url = upload_image(image_file)
      insert_message(content, image_url)
      return jsonify({'ok': True})
    else:
      raise TypeError('欄位不得為空。')
  except TypeError as e:
    abort(400, description=abort_message(e))
  except Exception as e:
    abort(500, description=abort_message(e))


@app.errorhandler(400)
def bad_request_error(e):
  return jsonify({'error': True, 'message': str(e.description), 'status': 400})


@app.errorhandler(500)
def internal_server_error(e):
  return jsonify({'error': True, 'message': str(e.description), 'status': 500})


if __name__ == '__main__':
  app.run(port=3000, debug=True)
