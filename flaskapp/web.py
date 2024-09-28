from operator import truediv
from flask import Flask, render_template, request, url_for, redirect, make_response, session, Response, Blueprint, flash
import pymysql
from datetime import date, datetime
import os
from os import getcwd, path
import io
import xlwt
import pdfkit as pdfkit
import qrcode
import gspread
from PIL import Image
from fpdf import FPDF
from oauth2client.service_account import ServiceAccountCredentials
from conexion import Conhost, Conuser, Conpassword, Condb
import unicodedata
import requests
from functools import wraps
from pymysql.cursors import DictCursor
#from flask_weasyprint import HTML, render_pdf

app = Flask(__name__)
app.secret_key = 'd589d3d0d15d764ed0a98ff5a37af547'
route_files = Blueprint("route_files", __name__)
mi_string = chr(92)
PATH_FILE = getcwd() + f'{mi_string}flaskapp{mi_string}'
usuariosadministrativo = [2,3,4,7]

def login_required(f):
	@wraps(f)
	def decorated_function(*args, **kwargs):
		if 'logeadocaja' not in session:
			session['logeadocaja'] = 0
			return redirect(url_for('login'))
		return f(*args, **kwargs)
	return decorated_function

def get_db_connection():
	return pymysql.connect(host=Conhost, user=Conuser, password=Conpassword, db=Condb)

def get_query_all(query, params=None):
	try:
		with get_db_connection() as conexion:
			with conexion.cursor() as cursor:
				cursor.execute(query, params or ())
				return cursor.fetchall()
	except (pymysql.err.OperationalError, pymysql.err.InternalError) as e:
		print("Ocurrió un error al conectar: ", e)
		return None

def get_query_one(query, params=None):
	try:
		with get_db_connection() as conexion:
			with conexion.cursor() as cursor:
				cursor.execute(query, params or ())
				return cursor.fetchone()
	except (pymysql.err.OperationalError, pymysql.err.InternalError) as e:
		print("Ocurrió un error al conectar: ", e)
		return None

def execute_query(query, params=None):
	try:
		with get_db_connection() as conexion:
			with conexion.cursor() as cursor:
				cursor.execute(query, params or ())
				return conexion.commit()
	except (pymysql.err.OperationalError, pymysql.err.InternalError) as e:
		print("Ocurrió un error al conectar: ", e)
		return None

@app.route('/error')
def error_page():
	# You can pass the error message and category as query parameters
	error_message = request.args.get('message', 'An unknown error occurred')
	error_category = request.args.get('category', 'error')
	return render_template('error.html', title='Error', error_message=error_message, error_category=error_category, logeado=session['logeadocaja'])

def home():
	return redirect(url_for('login'))

@app.route("/verdev/<int:idpago>", methods=['GET', 'POST'])
@login_required
def verdev(idpago):
	pago = get_query_one('SELECT urldevuelto, userdev FROM pagos WHERE idpagos = %s',(idpago,))
	if not pago:
		return redirect(url_for('error_page', message='Pago no encontrado', category='error'))
	user = get_query_one("SELECT nombre, apellido, user FROM user WHERE iduser = %s", (pago[1],))
	if not user:
		return redirect(url_for('error_page', message='Ningun usuario aprobó esta devolución, favor comunicarse al encargado del sistema', category='error'))
	return render_template('verdev.html', title='Devolución de Pago', logeado=session['logeadocaja'], acceso=pago[0], user=user, barranav=2)

@app.route("/devolucion/<idpago>", methods=['GET', 'POST'])
@login_required
def devolucion(idpago):
	datapago = get_query_one('SELECT c.concepto, p.nombre, p.carnet, p.total, DATE_FORMAT(p.fecha,"%%d/%%m/%%Y"), p.extra, p.recibo FROM codigos c INNER JOIN pagos p ON p.idcod = c.idcodigos WHERE p.idpagos = %s',(idpago))
	if request.method == 'POST':
		file = request.files['file']
		usuario = request.form["usuario"]
		pwd = request.form["password"]
		data = get_query_one("SELECT iduser, nombre, apellido FROM user WHERE user = %s and pwd = md5(%s)", (usuario, pwd))
		if data is None:
			return redirect(url_for('devolucion', idpago=idpago))
		else:
			nombrearc = f'dev{idpago}.{file.filename.split(".")[-1]}'
			ruta = os.path.join(PATH_FILE, "static", "uploads")
			file.save(os.path.join(ruta, nombrearc))
			execute_query("UPDATE pagos SET devuelto = 1, urldevuelto = %s, fechadevuelto = %s, user = %s, userdev = %s WHERE idpagos = %s;", (nombrearc, date.today(), session['idusercaja'], data[0], idpago))
		return redirect(url_for('repgen'))
	return render_template('devolucion.html', title='Devolución de Pago', logeado=session['logeadocaja'], datapago=datapago, barranav=2)

@app.route("/verdocumento/<nombredocumento>", methods=['GET', 'POST'])
@login_required
def verdocumento(nombredocumento):
	return render_template('verdocumento.html', title='Visualización de Documento', logeado=session['logeadocaja'], nombredocumento = nombredocumento)

@app.route("/academia", methods=['GET', 'POST'])
@login_required
def academia():
	carreras = get_query_all('SELECT carrera, codigo, idcarreras FROM carreras WHERE institucion = 2 ORDER BY carrera ASC')
	meses = ["Enero", "Febrero","Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
	if request.method == 'POST':
		carnet = request.form.get("carnet", 0)  # Si no existe, lo inicializamos a 0
		carnet = carnet if carnet else 0
		nombre = request.form.get("nombre", "")
		cantidad = int(request.form.get("cant", 0))  # Convertimos a entero, con valor predeterminado 0
		carrera = request.form.get("carrera", "")
		insc = request.form.get("insc", 0)  # Predeterminado a 0 si no existe
		datameses = ",".join([request.form.get(f'mes{i + 1}', '') for i in range(cantidad)])  # Construimos la cadena de meses
		return redirect(url_for('confirmacionaca', nombre=nombre, carnet=carnet, datameses=datameses, carrera = carrera, insc=insc))
	return render_template('academia.html', title='Academia', logeado=session['logeadocaja'], carreras=carreras, meses=meses, barranav=1)

@app.route("/confirmacionaca/<nombre>&<carnet>&<datameses>&<carrera>&<insc>", methods=['GET', 'POST'])
@login_required
def confirmacionaca(nombre, carnet, datameses, carrera, insc):
	nombre = str(nombre)
	carnet = str(carnet)
	carrera = str(carrera)
	insc = int(insc)
	meses = datameses.split(",")
	cantidad = len(meses)
	datacarrera = get_query_one('SELECT carrera FROM carreras WHERE idcarreras = %s', (carrera,))
	codins = get_query_one("SELECT idcodigos, precio FROM codigos WHERE cod = 'ACAINS'")
	codmen = get_query_one("SELECT idcodigos, precio FROM codigos WHERE cod = 'ACAMEN'")
	total = float(codins[1]) if insc == 1 else 0
	total += cantidad * float(codmen[1])
	if request.method == 'POST':
		idpagos = []
		if insc == 1:
			execute_query("INSERT INTO pagos(idcod, nombre, carnet, total, fecha, extra, recibo, user) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)", 
				(codins[0], nombre, carnet, codins[1], date.today(), f'Curso: {datacarrera[0]}', 0, session['idusercaja']))
			idpagos.append(get_query_one("SELECT MAX(idpagos) FROM pagos")[0])
		for mes in meses:
			execute_query("INSERT INTO pagos(idcod, nombre, carnet, total, fecha, extra, recibo, user) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)", 
				(codmen[0], nombre, carnet, codmen[1], date.today(), f'Mes: {mes}', 0, session['idusercaja']))
			idpagos.append(get_query_one("SELECT MAX(idpagos) FROM pagos")[0])
		return redirect(url_for('imprimir', idpagos=idpagos))
	return render_template('confirmacionaca.html', title='Confirmación Academia', logeado=session['logeadocaja'], nombre=nombre, carnet=carnet, cantidad=cantidad, total = total, datacarrera=datacarrera, insc=insc, meses=meses, barranav=1)

@app.route("/auxenf", methods=['GET', 'POST'])
@login_required
def auxenf():
	meses = ["Enero", "Febrero","Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
	if request.method == 'POST':
		carnet = request.form.get("carnet", 0)  # Asigna 0 si el carnet no tiene valor
		nombre = request.form.get("nombre", "")
		cantidad = int(request.form.get("cant", 0)) + 1
		mora = request.form.get("mora", 0)
		insc = request.form.get("insc", 0)
		promocion = request.form.get("promocion", 0)
		datameses = ",".join([request.form.get(f'mes{i}', '') for i in range(cantidad) if request.form.get(f'mes{i}', '')])
		if len(datameses) < 1:
			datameses = 'None'
		return redirect(url_for('confirmacionauxenf', nombre=nombre, carnet=carnet, insc=insc, datameses=datameses, mora=mora, promocion = promocion))
	return render_template('auxenf.html', title='Auxiliares de Enfermeria', logeado=session['logeadocaja'], meses=meses, barranav=1)

@app.route("/confirmacionauxenf/<nombre>&<carnet>&<insc>&<datameses>&<mora>&<promocion>", methods=['GET', 'POST'])
@login_required
def confirmacionauxenf(nombre, carnet, insc, datameses, mora, promocion):
	nombre = str(nombre)
	carnet = str(carnet)
	insc = int(insc)
	mora = float(mora)
	promocion = int(promocion)
	if datameses != 'None':
		meses = datameses.split(",")
		cantidad = len(meses)
	else:
		meses = []
		cantidad = 0
	cuotas = get_query_all('SELECT idcodigos, precio FROM codigos WHERE cod LIKE "%%INSCAUXE%%" OR cod LIKE "%%MENSAUXE%%" OR cod LIKE "%%MORAAUXE%%" ORDER BY cod ASC')
	pagoant = False
	for mes in meses:
		data = get_query_one('SELECT idpagos FROM pagos WHERE nombre = %s AND INSTR(extra, %s) > 0 AND idcod = %s', (nombre, mes, cuotas[1][0]))
		print(data)
		if data:
			pagoant = True
			break
	if pagoant:
		return redirect(url_for('auxenf', mensaje=1))
	total = 0
	if insc == 1:
		total += float(cuotas[0][1])  # Precio de inscripción
	total += cantidad * float(cuotas[1][1])  # Precio mensual
	if mora > 0:
		total += mora
	if request.method == 'POST':
		idpago = 0
		if insc == 1:
			execute_query("INSERT INTO pagos(idcod, nombre, carnet, total, fecha, extra, recibo, user) VALUES (%s, %s, %s, %s, %s, %s, %s, %s);",
				(cuotas[0][0], nombre, carnet, cuotas[0][1], date.today(), f"Promocion {promocion}", 0, session['idusercaja']))
		for mes in meses:
			execute_query("INSERT INTO pagos(idcod, nombre, carnet, total, fecha, extra, recibo, user) VALUES (%s, %s, %s, %s, %s, %s, %s, %s);",
				(cuotas[1][0], nombre, carnet, cuotas[1][1], date.today(), mes, 0, session['idusercaja']))
		if mora > 0:
			execute_query("INSERT INTO pagos(idcod, nombre, carnet, total, fecha, extra, recibo, user) VALUES (%s, %s, %s, %s, %s, %s, %s, %s);",
				(cuotas[2][0], nombre, carnet, mora, date.today(), 'Mora Auxiliar de Enfermería', 0, session['idusercaja']))
			idpago = get_query_one("SELECT MAX(idpagos) FROM pagos;")[0]
			imprimir = True
		else:
			imprimir = False
		if imprimir:
			return redirect(url_for('imprimir', idpagos=idpago))
		else:
			return redirect(url_for('auxenf'))
	return render_template('confirmacionauxenf.html', title='Confirmación Auxiliar de Enfermeria', logeado=session['logeadocaja'], nombre=nombre, carnet=carnet, cantidad=cantidad, total = total, insc=insc, meses=meses, mora=mora, promocion=promocion, barranav=1)

@app.route('/repauxenf', methods=['GET', 'POST'])
@login_required
def repauxenf():
	meses = ["Enero", "Febrero","Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
	fechaact = date.today()
	year = fechaact.year
	consulta = "SELECT p.nombre, p.carnet FROM pagos p INNER JOIN codigos c ON c.idcodigos = p.idcod WHERE c.concepto LIKE '%%Inscripción Auxiliar de enfermeria%%' AND p.extra NOT LIKE '%%Retirado%%' AND p.extra LIKE %s GROUP BY p.nombre ORDER BY p.nombre;"
	print(consulta)
	nombres = get_query_all(consulta, (f"%%{year}%%",))
	datos = []
	print(nombres)
	for nombre, carnet in nombres:
		data = [nombre, carnet]
		for mes in meses:
			pago = get_query_one("SELECT DATE_FORMAT(p.fecha, '%%d/%%m/%%Y') FROM pagos p INNER JOIN codigos c ON c.idcodigos = p.idcod WHERE c.concepto LIKE '%%Mensualidad Auxiliar de enfermeria%%' AND p.extra LIKE %s AND p.nombre = %s AND p.carnet = %s ORDER BY p.nombre ASC;", (f"%%{mes}%%", nombre, carnet))
			data.append(pago[0] if pago else "Pend")
		datos.append(data)
	return render_template('repauxenf.html', title="Reporte Auxiliares de Enfermeria", datos = datos, meses = meses, logeado=session['logeadocaja'], barranav=2)

@app.route('/repauxenfexcel', methods=['GET', 'POST'])
@login_required
def repauxenfexcel():
	meses = ["Enero", "Febrero","Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
	fechaact = date.today()
	year = fechaact.year
	consulta = "SELECT p.nombre, p.carnet FROM pagos p INNER JOIN codigos c ON c.idcodigos = p.idcod WHERE c.concepto LIKE '%%Inscripción Auxiliar de enfermeria%%' AND p.extra NOT LIKE '%%Retirado%%' AND p.extra LIKE %s GROUP BY p.nombre ORDER BY p.nombre;"
	print(consulta)
	nombres = get_query_all(consulta, (f"%%{year}%%",))
	datos = []
	print(nombres)
	for nombre, carnet in nombres:
		data = [nombre, carnet]
		for mes in meses:
			pago = get_query_one("SELECT DATE_FORMAT(p.fecha, '%%d/%%m/%%Y') FROM pagos p INNER JOIN codigos c ON c.idcodigos = p.idcod WHERE c.concepto LIKE '%%Mensualidad Auxiliar de enfermeria%%' AND p.extra LIKE %s AND p.nombre = %s AND p.carnet = %s ORDER BY p.nombre ASC;", (f"%%{mes}%%", nombre, carnet))
			data.append(pago[0] if pago else "Pend")
		datos.append(data)
	output = io.BytesIO()
	workbook = xlwt.Workbook(encoding="utf-8")
	sh1 = workbook.add_sheet("Auxiliares de Enfermeria")

	xlwt.add_palette_colour("Orange", 0x21) # the second argument must be a number between 8 and 64
	workbook.set_colour_RGB(0x21, 255, 165, 0) # Red — 79, Green — 129, Blue — 189
	xlwt.add_palette_colour("Lightgreen", 0x22) # the second argument must be a number between 8 and 64
	workbook.set_colour_RGB(0x22, 144, 238, 144) # Red — 79, Green — 129, Blue — 189
	
	#bordes
	borders = xlwt.Borders()
	borders.left = 1
	borders.right = 1
	borders.top = 1
	borders.bottom = 1

	#encabezados
	header_font = xlwt.Font()
	header_font.name = 'Arial'
	header_font.bold = True
	header_style = xlwt.XFStyle()
	header_style.font = header_font
	header_style.borders = borders

	#contenido1
	content_font = xlwt.Font()
	content_font.name = 'Arial'
	content_pattern = xlwt.Pattern()
	content_pattern.pattern = xlwt.Pattern.SOLID_PATTERN
	content_pattern.pattern_fore_colour = xlwt.Style.colour_map['orange']
	content_style = xlwt.XFStyle()
	content_style.font = content_font
	content_style.borders = borders
	content_style.pattern = content_pattern

	#contenido1
	content_font1 = xlwt.Font()
	content_font1.name = 'Arial'
	content_pattern1 = xlwt.Pattern()
	content_pattern1.pattern = xlwt.Pattern.SOLID_PATTERN
	content_pattern1.pattern_fore_colour = xlwt.Style.colour_map['light_green']
	content_style1 = xlwt.XFStyle()
	content_style1.font = content_font1
	content_style1.borders = borders
	content_style1.pattern = content_pattern1

	#titulos
	tittle_font = xlwt.Font()
	tittle_font.name = 'Arial'
	tittle_font.bold = True
	tittle_font.italic = True
	tittle_font.height = 20*20
	tittle_style = xlwt.XFStyle()
	tittle_style.font = tittle_font

	sh1.write(0,0,"Auxiliares de Enfermeria", tittle_style)
	sh1.write(3,0,"No.", header_style)
	sh1.write(3,1,"Nombre", header_style)
	sh1.write(3,2,"Carnet", header_style)
	for i, mes in enumerate(meses):
		sh1.write(3, i + 3, mes, header_style)

	for idx, data in enumerate(datos):
		sh1.write(idx + 4, 0, idx + 1, content_style1)
		sh1.write(idx + 4, 1, data[0], content_style1)
		sh1.write(idx + 4, 2, data[1], content_style1)
		for j in range(12):
			cell_style = content_style if data[j + 2] == "Pend" else content_style1
			sh1.write(idx + 4, j + 3, data[j + 2], cell_style)
	
	sh1.col(0).width = 256 * 6  # Ancho de la columna "No."
	sh1.col(1).width = 256 * 30  # Ancho de la columna "Nombre"
	sh1.col(2).width = 256 * 20  # Ancho de la columna "Carnet"

	for i in range(3, 15):
		sh1.col(i).width = 256 * 15  # Ancho de las columnas de los meses

	# Guardar el Excel en el buffer
	workbook.save(output)
	output.seek(0)
	return Response(output, mimetype="application/ms-excel", headers={"Content-Disposition":"attachment;filename=Reporteauxenf.xls"})

@app.route("/ingles", methods=['GET', 'POST'])
@app.route("/ingles/<mensaje>", methods=['GET', 'POST'])
@login_required
def ingles(mensaje=0):
	meses = ["Enero", "Febrero","Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
	cuotas = get_query_all('SELECT idcodigos, precio FROM codigos WHERE cod LIKE "%MAINGLES%" ORDER BY cod ASC')
	if request.method == 'POST':
		carnet = request.form.get("carnet", 0)
		nombre = request.form.get("nombre", "")
		ciclo = request.form.get("ciclo", 0)
		cantidad = int(request.form.get("cant", 0)) + 1
		plan = request.form.get("plan", "")
		ciclomen = request.form.get("ciclomen", "")
		insc = request.form.get("insc", 0)
		datameses = ""
		for i in range(cantidad):
			mes = request.form.get(f'mes{i}', "")
			if mes:
				if datameses:
					datameses = f"{datameses},{mes}"
				else:
					datameses = mes
		# Si no se seleccionaron meses, establecemos un valor por defecto
		if not datameses:
			datameses = 'None'
		return redirect(url_for('confirmacioningles', nombre=nombre, carnet=carnet, plan = plan, insc=insc, datameses=datameses, ciclo=ciclo, ciclomen = ciclomen))
	return render_template('ingles.html', title='Ingles', logeado=session['logeadocaja'], meses=meses, cuotas=cuotas, mensaje = mensaje, barranav=1)

@app.route("/confirmacioningles/<nombre>&<carnet>&<plan>&<insc>&<datameses>&<ciclo>&<ciclomen>", methods=['GET', 'POST'])
@login_required
def confirmacioningles(nombre, carnet, plan, insc, datameses, ciclo, ciclomen):
	nombre = str(nombre)
	carnet = str(carnet)
	plan = int(plan)
	insc = int(insc)
	ciclomen = int(ciclomen)
	meses = datameses.split(",") if datameses != 'None' else []
	cantidad = len(meses)
	datainsc = []
	datamen = []
	datainsc = get_query_one('SELECT idcodigos, precio FROM codigos WHERE cod LIKE "%MAINGLES%"')
	if plan == 1:
		datamen = get_query_one('SELECT idcodigos, precio FROM codigos WHERE cod LIKE "%MEINGLEST%"')
	else:
		datamen = get_query_one('SELECT idcodigos, precio FROM codigos WHERE cod LIKE "%MEINGLESS%"')
	pagoant = False
	for mes in meses:
		data = get_query_all('SELECT idpagos FROM pagos WHERE nombre = %s AND INSTR(extra, %s) > 0 and carnet = %s and INSTR(extra, %s) > 0', (nombre, mes, carnet, ciclomen))
		if data:
			pagoant = True
			break
	if pagoant:
		return redirect(url_for('auxenf', mensaje=1))
	if insc == 1:
		total += sum(float(datainsc[i][1]) for i in range(2))
	total += sum(float(j[1]) for j in datamen) * cantidad

	if request.method == 'POST':
		idpagos = []
		if insc == 1:
			for i in range(2):
				execute_query("INSERT INTO pagos(idcod, nombre, carnet, total, fecha, extra, recibo, user) VALUES (%s, %s, %s, %s, %s, %s, %s, %s);",
					(datainsc[i][0], nombre, carnet, datainsc[i][1], date.today(), f'Ciclo: {ciclo}', 0, session['idusercaja']))
				idpagos.append(get_query_one("SELECT MAX(idpagos) FROM pagos")[0])
			for mes in meses:
				for j in datamen:
					execute_query("INSERT INTO pagos(idcod, nombre, carnet, total, fecha, extra, recibo, user) VALUES (%s, %s, %s, %s, %s, %s, %s, %s);",
						(j[0], nombre, carnet, j[1], date.today(), f'Mes: {mes}, Ciclo: {ciclomen}', 0, session['idusercaja']))
					idpagos.append(get_query_one("SELECT MAX(idpagos) FROM pagos")[0])
		return redirect(url_for('imprimir', idpagos=idpagos))
	return render_template('confirmacioningles.html', title='Confirmación Ingles', logeado=session['logeadocaja'], nombre=nombre, carnet=carnet, cantidad=cantidad, total = total, datainsc=datainsc, insc=insc, meses=meses, ciclo=ciclo, barranav=1)

@app.route('/repingles', methods=['GET', 'POST'])
@login_required
def repingles():
	mesesbase = [
		["Abril", "Mayo", "Junio"],
		["Abril", "Mayo", "Junio"],
		["Julio", "Agosto", "Septiembre"],
		["Marzo", "Abril", "Mayo"]
	]
	datagen = []
	for n in range(4):
		ciclo = n + 1
		datos = []
		
		nombres = get_query_all("SELECT p.nombre, p.carnet FROM pagos p INNER JOIN codigos c ON c.idcodigos = p.idcod WHERE c.concepto LIKE %s AND p.extra LIKE %s AND (p.extra LIKE %s OR p.extra LIKE %s OR p.extra LIKE %s) AND p.fecha > DATE_SUB(CURDATE(), INTERVAL 10 MONTH) AND p.extra NOT LIKE %s GROUP BY p.nombre ORDER BY p.nombre", 
					('%Mensualidad Ingles Trimestral (A)%', f'%{ciclo}%', f'%{mesesbase[n][0]}%', f'%{mesesbase[n][1]}%', f'%{mesesbase[n][2]}%', '%Retirado%'))
		if nombres:
			for nombre, carnet in nombres:
				data = [nombre, carnet]
				for mes in mesesbase[n]:
					pago = get_query_one("SELECT DATE_FORMAT(p.fecha, '%%d/%%m/%%Y') FROM pagos p INNER JOIN codigos c ON c.idcodigos = p.idcod WHERE c.concepto LIKE %s AND p.extra LIKE %s AND p.extra LIKE %s AND p.nombre LIKE %s AND p.fecha > DATE_SUB(CURDATE(), INTERVAL 10 MONTH) ORDER BY p.nombre ASC", 
						('%Mensualidad Ingles Trimestral (A)%', f'%{mes}%', f'%{ciclo}%', f'%{nombre}%'))
					data.append(pago[0] if pago else "Pend")
				datos.append(data)
		datagen.append(datos)
	return render_template('repingles.html', title="Reporte ingles", datos = datagen, meses = mesesbase, logeado=session['logeadocaja'], barranav=2)

@app.route('/repinglesexcel', methods=['GET', 'POST'])
@login_required
def repinglesexcel():
	mesesbase = [
		["Abril", "Mayo", "Junio"],
		["Abril", "Mayo", "Junio"],
		["Julio", "Agosto", "Septiembre"],
		["Marzo", "Abril", "Mayo"]
	]
	datagen = []
	for n in range(4):
		ciclo = n + 1
		datos = []
		
		nombres = get_query_all("SELECT p.nombre, p.carnet FROM pagos p INNER JOIN codigos c ON c.idcodigos = p.idcod WHERE c.concepto LIKE %s AND p.extra LIKE %s AND (p.extra LIKE %s OR p.extra LIKE %s OR p.extra LIKE %s) AND p.fecha > DATE_SUB(CURDATE(), INTERVAL 10 MONTH) AND p.extra NOT LIKE %s GROUP BY p.nombre ORDER BY p.nombre", 
					('%Mensualidad Ingles Trimestral (A)%', f'%{ciclo}%', f'%{mesesbase[n][0]}%', f'%{mesesbase[n][1]}%', f'%{mesesbase[n][2]}%', '%Retirado%'))
		if nombres:
			for nombre, carnet in nombres:
				data = [nombre, carnet]
				for mes in mesesbase[n]:
					pago = get_query_one("SELECT DATE_FORMAT(p.fecha, '%%d/%%m/%%Y') FROM pagos p INNER JOIN codigos c ON c.idcodigos = p.idcod WHERE c.concepto LIKE %s AND p.extra LIKE %s AND p.extra LIKE %s AND p.nombre LIKE %s AND p.fecha > DATE_SUB(CURDATE(), INTERVAL 10 MONTH) ORDER BY p.nombre ASC", 
						('%Mensualidad Ingles Trimestral (A)%', f'%{mes}%', f'%{ciclo}%', f'%{nombre}%'))
					data.append(pago[0] if pago else "Pend")
				datos.append(data)
		datagen.append(datos)
	output = io.BytesIO()
	workbook = xlwt.Workbook(encoding="utf-8")

	# Definición de estilos
	xlwt.add_palette_colour("Orange", 0x21)
	workbook.set_colour_RGB(0x21, 255, 165, 0)
	xlwt.add_palette_colour("Lightgreen", 0x22)
	workbook.set_colour_RGB(0x22, 144, 238, 144)
	borders = xlwt.Borders()
	borders.left = borders.right = borders.top = borders.bottom = 1
	header_font = xlwt.Font()
	header_font.name, header_font.bold = 'Arial', True
	header_style = xlwt.XFStyle()
	header_style.font, header_style.borders = header_font, borders

	def create_content_style(color):
		font = xlwt.Font()
		font.name = 'Arial'
		pattern = xlwt.Pattern()
		pattern.pattern = xlwt.Pattern.SOLID_PATTERN
		pattern.pattern_fore_colour = xlwt.Style.colour_map[color]
		style = xlwt.XFStyle()
		style.font, style.borders, style.pattern = font, borders, pattern
		return style

	content_style = create_content_style('orange')
	content_style1 = create_content_style('light_green')
	tittle_font = xlwt.Font()
	tittle_font.name, tittle_font.bold, tittle_font.italic = 'Arial', True, True
	tittle_font.height = 20*20
	tittle_style = xlwt.XFStyle()
	tittle_style.font = tittle_font

	def create_sheet(cycle):
		sh = workbook.add_sheet(f"Ciclo {cycle}")
		sh.write(0, 0, f"Ciclo {cycle}", tittle_style)
		headers = ["No.", "Nombre", "Carnet"] + mesesbase[cycle-1]
		for col, header in enumerate(headers):
			sh.write(3, col, header, header_style)

		if datagen[cycle-1]:
			for row, data in enumerate(datagen[cycle-1], start=4):
				sh.write(row, 0, row-3, content_style1)
				sh.write(row, 1, data[0], content_style1)
				sh.write(row, 2, data[1], content_style1)
				for col, value in enumerate(data[2:], start=3):
					style = content_style if value == "Pend" else content_style1
					sh.write(row, col, value, style)
		sh.col(0).width = 0x0d00 + len(f"Ciclo {cycle}")
		try:
			for col in range(1, 6):
				max_length = max(len(str(row[col-1])) for row in datagen[cycle-1]) + 1
				sh.col(col).width = 256 * max_length * (20 if col == 1 and cycle == 3 else 10)
		except:
			for col in range(1, 6):
				sh.col(col).width = 256 * 20
	for cycle in range(1, 5):
		create_sheet(cycle)
	workbook.save(output)
	output.seek(0)
	return Response(output, mimetype="application/ms-excel", headers={"Content-Disposition":"attachment;filename=Reporteingles.xls"})

@app.route("/laboratorio", methods=['GET', 'POST'])
@login_required
def laboratorio():
	fechaact = datetime.today().strftime('%Y-%m-%d')
	examenes = get_query_all('SELECT nombre, idtipoexamen, precio, idexameneslab FROM exameneslab WHERE DATE(fechaactivo) = "0000-00-00" OR DATE(fechaactivo) > %s ORDER BY idtipoexamen', (fechaact,))
	empresas = get_query_all('SELECT nombre, descuento FROM empresa ORDER BY nombre ASC')
	tipoexamen = get_query_all('SELECT nombre, idtipoexamen FROM tipoexamen ORDER BY idtipoexamen ASC')
	
	if request.method == 'POST':
		carnet = request.form.get("carnet", "0")
		nombre = request.form["nombre"]
		cantidad = int(request.form["cant"])
		dataexamenes = ";".join(
			f"{request.form[f'examen{i}']},{request.form[f'precio{i}']}"
			for i in range(cantidad)
		)
		
		return redirect(url_for('confirmacionlab', nombre=nombre, carnet=carnet, dataexamenes=dataexamenes))
	return render_template('laboratorio.html', title='Laboratorio', logeado=session['logeadocaja'], 
							examenes=examenes, empresas=empresas, tipoexamen=tipoexamen, barranav=1)

@app.route("/confirmacionlab/<nombre>&<carnet>&<dataexamenes>", methods=['GET', 'POST'])
@login_required
def confirmacionlab(nombre, carnet, dataexamenes):
	nombre = str(nombre)
	carnet = str(carnet)
	examenes = [examen.split(",") for examen in dataexamenes.split(";") if examen]
	cantidad = len(examenes)
	total = sum(float(examen[1]) for examen in examenes)
	
	dataaux = []
	for id_examen, precio in examenes:
		query_info = get_query_one(
			"SELECT e.nombre, t.nombre FROM exameneslab e INNER JOIN tipoexamen t ON e.idtipoexamen = t.idtipoexamen WHERE e.idexameneslab = %s",
			(id_examen,)
		)
		if query_info:
			dataaux.append([id_examen, query_info[0], query_info[1], precio])
	
	if request.method == 'POST':
		cod_lab = get_query_one("SELECT idcodigos FROM codigos WHERE cod = 'LAB'")
		if cod_lab:
			cod_lab = cod_lab[0]
			idpagos = []
			for examen in dataaux:
				id_pago = execute_query("INSERT INTO pagos(idcod,nombre,carnet,total,fecha,extra,recibo,user) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)",
					(cod_lab, nombre, carnet, examen[3], date.today(), f"{examen[2]} - {examen[1]}", 0, session['idusercaja']))
				if id_pago:
					max_id = get_query_one("SELECT MAX(idpagos) FROM pagos")
					if max_id:
						idpagos.append(max_id[0])
			if idpagos:
				return redirect(url_for('imprimir', idpagos=idpagos))
	return render_template('confirmacionlab.html', title='Confirmación Laboratorio', logeado=session['logeadocaja'],
							dataaux=dataaux, nombre=nombre, carnet=carnet, cantidad=cantidad, total=total, barranav=1)

@app.route("/eliminarpago/<idpago>", methods=['GET', 'POST'])
@login_required
def eliminarpago(idpago):
	query = "DELETE FROM pagos WHERE idpagos = %s"
	result = execute_query(query, (idpago,))
	if result is None:
		print("Ocurrió un error al eliminar el pago.")
	return redirect(url_for('repdiario'))

@app.route("/editarpago/<idpago>", methods=['GET', 'POST'])
@login_required
def editarpago(idpago):
	datapago = get_query_one('SELECT p.idcod, p.nombre, p.carnet, p.total, p.fecha, p.extra FROM codigos c INNER JOIN pagos p ON p.idcod = c.idcodigos WHERE p.idpagos = %s', (idpago,))
	codigos = get_query_all('SELECT idcodigos, concepto FROM codigos ORDER BY concepto')
	
	if request.method == 'POST':
		carnet = request.form.get("carnet") or datapago[2]
		nombre = request.form.get("nombre") or datapago[1]
		codigo = request.form["codigo"]
		extra = request.form.get("extra") or datapago[5]
		fecha = request.form["fecha"]
		total = request.form.get("total") or datapago[3]
		result = execute_query('UPDATE pagos SET nombre=%s, carnet=%s, total=%s, fecha=%s, extra=%s, idcod=%s, user=%s WHERE idpagos=%s',
			(nombre, carnet, total, fecha, extra, codigo, session['idusercaja'], idpago))
		
		if result is None:
			print("Ocurrió un error al actualizar el pago.")
		return redirect(url_for('repdiario'))
	return render_template('editarpago.html', title='Editar Pago', logeado=session['logeadocaja'], datapago=datapago, codigos=codigos, barranav=2)

@app.route('/', methods=['GET', 'POST'])
@app.route('/home', methods=['GET', 'POST'])
@app.route('/login', methods=['GET', 'POST'])
def login():
	if 'logeadocaja' in session:
		logeado = session['logeadocaja']
	else:
		session['logeadocaja'] = 0
		logeado = 0
	if logeado != 0:
		return redirect(url_for('pagos'))
	if request.method == 'POST':
		user = request.form["user"]
		pwd = request.form["pwd"]
		try:
			with get_db_connection() as conexion:
				with conexion.cursor() as cursor:
					consulta = f"SELECT iduser, nombre, apellido FROM user WHERE user = '{user}' and pwd = md5('{pwd}')"
					cursor.execute(consulta)
					data = cursor.fetchall()
					if len(data) == 0:
						return render_template('login.html', title='Iniciar sesión', logeado=session['logeadocaja'], mensaje="Datos inválidos, intente nuevamente")
					else:
						session['logeadocaja'] = 1
						session['idusercaja'] = data[0][0]
						session['nombreusercaja'] = data[0][1]
						session['apellidousercaja'] = data[0][2]
						session['usercaja'] = user
						return redirect(url_for('pagos'))
		except (pymysql.err.OperationalError, pymysql.err.InternalError) as e:
			print("Ocurrió un error al conectar: ", e)
	return render_template('login.html', title='Iniciar sesión', logeado=session['logeadocaja'], mensaje="")

@app.route("/logout")
def logout():
	session.pop('logeadocaja', None)
	session.pop('idusercaja', None)
	session.pop('nombreusercaja', None)
	session.pop('apellidousercaja', None)
	session.pop('usercaja', None)
	return redirect(url_for('login'))

@app.route("/crearusuario", methods=['GET', 'POST'])
@login_required
def crearusuario():
	if session['idusercaja'] not in usuariosadministrativo:
		return redirect(url_for('login'))
	mensaje = ''
	if request.method == 'POST':
		nombre = request.form["nombre"]
		apellido = request.form["apellido"]
		user = request.form["user"]
		pwd = request.form["pwd"]
		iniciales = request.form["iniciales"]
		try:
			conexion = pymysql.connect(host=Conhost, user=Conuser, password=Conpassword, db=Condb)
			try:
				with conexion.cursor() as cursor:
					consulta = "INSERT INTO user(nombre, apellido, user, pwd, iniciales) values (%s, %s, %s, MD5(%s), %s);"
					cursor.execute(consulta, (nombre, apellido, user, pwd, iniciales))
				conexion.commit()
			finally:
				conexion.close()
		except (pymysql.err.OperationalError, pymysql.err.InternalError) as e:
			print("Ocurrió un error al conectar: ", e)
		return redirect(url_for('login'))
	return render_template('crearusuario.html', title='Nuevo Usuario', mensaje=mensaje, barranav=3)

@app.route('/optica', methods=['GET', 'POST'])
@login_required
def optica():
	if request.method == 'POST':
		carnet = request.form["carnet"]
		nombre = request.form["nombre"]
		aro = request.form["aro"]
		lente = request.form["lente"]
		try:
			exavis = request.form["exavis"]
		except:
			exavis = 0
		try:
			exaviseps = request.form["exaviseps"]
		except:
			exaviseps = 0
		try:
			exavisjornada = request.form["exavisjornada"]
		except:
			exavisjornada = 0
		if len(aro) < 1:
			aro = 0
		if len(lente) < 1:
			lente = 0
		return redirect(url_for('confirmacionopt', carnet = carnet, nombre = nombre, aro=aro, lente=lente, exavis=exavis, exaviseps = exaviseps, exavisjornada = exavisjornada))
	return render_template('optica.html', title="Óptica", logeado=session['logeadocaja'], barranav=1)

@app.route('/verventasoptica', methods=['GET', 'POST'])
@login_required
def verventasoptica():
	try:
		conexion = pymysql.connect(host=Conhost, user=Conuser, password=Conpassword, db=Condb)
		try:
			with conexion.cursor() as cursor:
				consulta = "select nombre, nit, precioaro, preciolente, total, idpagooptica from pagooptica;"
				cursor.execute(consulta)
				ventas = cursor.fetchall()
		finally:
			conexion.close()
	except (pymysql.err.OperationalError, pymysql.err.InternalError) as e:
		print("Ocurrió un error al conectar: ", e)
	return render_template('verventasoptica.html', title="Ventas Óptica", logeado=session['logeadocaja'], ventas=ventas, barranav=1)

@app.route('/recibirpagooptica/<id>', methods=['GET', 'POST'])
@login_required
def recibirpagooptica(id):
	try:
		conexion = pymysql.connect(host=Conhost, user=Conuser, password=Conpassword, db=Condb)
		try:
			with conexion.cursor() as cursor:
				consulta = "select nombre, nit, precioaro, preciolente, total from pagooptica where idpagooptica = %s;"
				cursor.execute(consulta, id)
				venta = cursor.fetchone()
				if float(venta[2]) > 0:
					consulta = 'select idcodigos from codigos where cod = "OPTARO"'
					cursor.execute(consulta)
					datos = cursor.fetchall()
					idaro = datos[0][0]
					consulta = "INSERT INTO pagos(idcod,nombre,carnet,total,fecha,extra,recibo, user) VALUES (%s,%s,%s,%s,%s,%s,%s,%s);"
					cursor.execute(consulta, (idaro, venta[0], venta[1], venta[2], date.today(), "Aro - Optica",0, session['idusercaja']))
					conexion.commit()
				if float(venta[3]) > 0:
					consulta = 'select idcodigos from codigos where cod = "OPTLEN"'
					cursor.execute(consulta)
					datos = cursor.fetchall()
					idlente = datos[0][0]
					consulta = "INSERT INTO pagos(idcod,nombre,carnet,total,fecha,extra,recibo, user) VALUES (%s,%s,%s,%s,%s,%s,%s, %s);"
					cursor.execute(consulta, (idlente, venta[0], venta[1], venta[3], date.today(), "Lente - Optica",0, session['idusercaja']))
					conexion.commit()
				consulta = "delete from pagooptica where idpagooptica = %s;"
				cursor.execute(consulta, id)
				conexion.commit()
		finally:
			conexion.close()
	except (pymysql.err.OperationalError, pymysql.err.InternalError) as e:
		print("Ocurrió un error al conectar: ", e)
	return redirect(url_for('optica'))

@app.route('/confirmacionopt/<carnet>&<nombre>&<aro>&<lente>&<exavis>&<exaviseps>&<exavisjornada>', methods=['GET', 'POST'])
@login_required
def confirmacionopt(carnet, nombre, aro, lente, exavis, exaviseps,exavisjornada):
	examen = 0
	if request.method == "POST":
		try:
			conexion = pymysql.connect(host=Conhost, user=Conuser, password=Conpassword, db=Condb)
			try:
				with conexion.cursor() as cursor:
					if exavis != 0 and exavis != '0':
						consulta = 'select idcodigos from codigos where cod = "EXAVIS"'
						cursor.execute(consulta)
						datos = cursor.fetchall()
						idexamen = datos[0][0]
						consulta = "INSERT INTO pagos(idcod,nombre,carnet,total,fecha,extra,recibo, user) VALUES (%s,%s,%s,%s,%s,%s,%s,%s);"
						cursor.execute(consulta, (idexamen, nombre, carnet, 50, date.today(), "Examen de la Vista",0, session['idusercaja']))
						conexion.commit()
						examen = 1
						consulta = "Select MAX(idpagos) from pagos;"
						cursor.execute(consulta)
						pagoexamen = cursor.fetchone()
						pagoexamen = pagoexamen[0]
					if exaviseps != 0 and exaviseps != '0':
						consulta = 'select idcodigos from codigos where cod = "EXAVIS"'
						cursor.execute(consulta)
						datos = cursor.fetchall()
						idexamen = datos[0][0]
						consulta = "INSERT INTO pagos(idcod,nombre,carnet,total,fecha,extra,recibo, user) VALUES (%s,%s,%s,%s,%s,%s,%s,%s);"
						cursor.execute(consulta, (idexamen, nombre, carnet, 40, date.today(), "Examen de la Vista EPS",0, session['idusercaja']))
						conexion.commit()
						examen = 1
						consulta = "Select MAX(idpagos) from pagos;"
						cursor.execute(consulta)
						pagoexamen = cursor.fetchone()
						pagoexamen = pagoexamen[0]
					if exavisjornada != 0 and exavisjornada != '0':
						consulta = 'select idcodigos from codigos where cod = "EXAVIS"'
						cursor.execute(consulta)
						datos = cursor.fetchall()
						idexamen = datos[0][0]
						consulta = "INSERT INTO pagos(idcod,nombre,carnet,total,fecha,extra,recibo, user) VALUES (%s,%s,%s,%s,%s,%s,%s,%s);"
						cursor.execute(consulta, (idexamen, nombre, carnet, 25, date.today(), "Examen de la Vista Jornada",0, session['idusercaja']))
						conexion.commit()
						examen = 1
						consulta = "Select MAX(idpagos) from pagos;"
						cursor.execute(consulta)
						pagoexamen = cursor.fetchone()
						pagoexamen = pagoexamen[0]
					if float(aro) > 0:
						consulta = 'select idcodigos from codigos where cod = "OPTARO"'
						cursor.execute(consulta)
						datos = cursor.fetchall()
						idaro = datos[0][0]
						consulta = "INSERT INTO pagos(idcod,nombre,carnet,total,fecha,extra,recibo, user) VALUES (%s,%s,%s,%s,%s,%s,%s,%s);"
						cursor.execute(consulta, (idaro, nombre, carnet, aro, date.today(), "Aro - Optica",0, session['idusercaja']))
						conexion.commit()
					if float(lente) > 0:
						consulta = 'select idcodigos from codigos where cod = "OPTLEN"'
						cursor.execute(consulta)
						datos = cursor.fetchall()
						idlente = datos[0][0]
						consulta = "INSERT INTO pagos(idcod,nombre,carnet,total,fecha,extra,recibo, user) VALUES (%s,%s,%s,%s,%s,%s,%s, %s);"
						cursor.execute(consulta, (idlente, nombre, carnet, lente, date.today(), "Lente - Optica",0, session['idusercaja']))
						conexion.commit()
			finally:
				conexion.close()
		except (pymysql.err.OperationalError, pymysql.err.InternalError) as e:
			print("Ocurrió un error al conectar: ", e)
		if examen == 0:
			return redirect(url_for('optica'))
		else:
			return redirect(url_for('imprimir', idpagos=pagoexamen))
	return render_template('confirmacionopt.html', title="Confirmación Óptica", carnet = carnet, nombre = nombre, aro=aro, lente=lente, exavis=exavis, exaviseps=exaviseps,logeado=session['logeadocaja'], barranav=1)

@app.route('/i', methods=['GET', 'POST'])
@login_required
def i():
	try:
		conexion = pymysql.connect(host=Conhost, user=Conuser, password=Conpassword, db=Condb)
		try:
			with conexion.cursor() as cursor:
				cursor.execute("SELECT idinscripciones, inscripcion, precio, internet FROM inscripciones order by inscripcion asc;")
				carreras = cursor.fetchall()
		finally:
			conexion.close()
	except (pymysql.err.OperationalError, pymysql.err.InternalError) as e:
		print("Ocurrió un error al conectar: ", e)
	if request.method == 'POST':
		datacarnet = request.form["carnet"]
		datanombre = request.form["nombre"]
		datacarrera = request.form["carrera"]
		mesextra = request.form["mesextra"]
		if len(mesextra) < 1:
			mesextra = 0
		try:
			rinsc = request.form["rinsc"]
		except:
			rinsc = 0
		try:
			rint = request.form["rint"]
		except:
			rint = 0
		try:
			rrein = request.form["rrein"]
		except:
			rrein = 0
		try:
			exavis = request.form["exavis"]
		except:
			exavis = 0
		return redirect(url_for('confirmacioni', carrera = datacarrera, carnet = datacarnet, nombre = datanombre, rinsc=rinsc, rint=rint, rrein=rrein, mesextra=mesextra, exavis=exavis))
	return render_template('inscripciones.html', title="Inscripciones", carreras=carreras, logeado=session['logeadocaja'], barranav=1)

@app.route('/confirmacioni/<carrera>&<carnet>&<nombre>&<rinsc>&<rint>&<rrein>&<mesextra>&<exavis>', methods=['GET', 'POST'])
@login_required
def confirmacioni(carrera, carnet, nombre, rinsc, rint, rrein, mesextra, exavis):
	carrera = str(carrera)
	carnet = str(carnet)
	nombre = str(nombre)
	rinsc = int(rinsc)
	rint = int(rint)
	rrein = int(rrein)
	exavis = int(exavis)
	mesextra = int(mesextra)
	try:
		conexion = pymysql.connect(host=Conhost, user=Conuser, password=Conpassword, db=Condb)
		try:
			with conexion.cursor() as cursor:
				consulta = f'SELECT i.inscripcion, i.precio, i.internet, c.codigo FROM inscripciones i inner join carreras c on i.idcarrera = c.idcarreras WHERE i.idinscripciones = {carrera};'
				cursor.execute(consulta)
				data = cursor.fetchall()
		finally:
			conexion.close()
	except (pymysql.err.OperationalError, pymysql.err.InternalError) as e:
		print("Ocurrió un error al conectar: ", e)
	imprimir = 0
	if request.method == "POST":
		try:
			conexion = pymysql.connect(host=Conhost, user=Conuser, password=Conpassword, db=Condb)
			try:
				with conexion.cursor() as cursor:
					if rinsc != 0:
						consulta = "INSERT INTO pagos(idcod,nombre,carnet,total,fecha,extra,recibo, user) VALUES (%s,%s,%s,%s,%s,%s,%s,%s);"
						cursor.execute(consulta, (1, nombre, carnet, data[0][1], date.today(), data[0][0],0, session['idusercaja']))
						conexion.commit()
					if rint != 0:
						consulta = "INSERT INTO pagos(idcod,nombre,carnet,total,fecha,extra,recibo, user) VALUES (%s,%s,%s,%s,%s,%s,%s, %s);"
						cursor.execute(consulta, (2, nombre, carnet, data[0][2], date.today(), "Internet " +str(data[0][3]), 0, session['idusercaja']))
						conexion.commit()
						imprimir = 1
						consulta = "Select MAX(idpagos) from pagos;"
						cursor.execute(consulta)
						pagoexamen = cursor.fetchone()
						pagoexamen = pagoexamen[0]
					if rrein != 0:
						consulta = "INSERT INTO pagos(idcod,nombre,carnet,total,fecha,extra,recibo, user) VALUES (%s,%s,%s,%s,%s,%s,%s,%s);"
						cursor.execute(consulta, (3, nombre, carnet, 100, date.today(), "Internet Reinscripcion " +str(data[0][3]),0, session['idusercaja']))
						conexion.commit()
						imprimir = 1
						consulta = "Select MAX(idpagos) from pagos;"
						cursor.execute(consulta)
						pagoexamen = cursor.fetchone()
						pagoexamen = pagoexamen[0]
					if mesextra != 0:
						consulta = 'select idcodigos from codigos where cod = "MENE"'
						cursor.execute(consulta)
						datos = cursor.fetchall()
						idcodigo = datos[0][0]
						consulta = "INSERT INTO pagos(idcod,nombre,carnet,total,fecha,extra,recibo,user) VALUES (%s,%s,%s,%s,%s,%s,%s, %s);"
						cursor.execute(consulta, (idcodigo, nombre, carnet, mesextra, date.today(), "Mensualidad Extra" +str(data[0][3]),0, session['idusercaja']))
						conexion.commit()
					if exavis != 0:
						consulta = 'select idcodigos from codigos where cod = "EXAVIS"'
						cursor.execute(consulta)
						datos = cursor.fetchall()
						idexamen = datos[0][0]
						consulta = "INSERT INTO pagos(idcod,nombre,carnet,total,fecha,extra,recibo, user) VALUES (%s,%s,%s,%s,%s,%s,%s,%s);"
						cursor.execute(consulta, (idexamen, nombre, carnet, 50, date.today(), "Examen de la Vista",0, session['idusercaja']))
						conexion.commit()
						imprimir = 1
						consulta = "Select MAX(idpagos) from pagos;"
						cursor.execute(consulta)
						pagoexamen = cursor.fetchone()
						pagoexamen = pagoexamen[0]
			finally:
				conexion.close()
		except (pymysql.err.OperationalError, pymysql.err.InternalError) as e:
			print("Ocurrió un error al conectar: ", e)
		if imprimir == 0:
			return redirect(url_for('i'))
		else:
			return redirect(url_for('imprimir', idpagos=pagoexamen))
	return render_template('confirmacioni.html', title="Confirmación", carrera = carrera, carnet = carnet, nombre = nombre, data=data, rinsc=rinsc, rint=rint, rrein=rrein, mesextra=mesextra, logeado=session['logeadocaja'], barranav=1)

@app.route('/repi', methods=['GET', 'POST'])
@login_required
def repi():
	try:
		conexion = pymysql.connect(host=Conhost, user=Conuser, password=Conpassword, db=Condb)
		try:
			with conexion.cursor() as cursor:
				cursor.execute("SELECT idcarreras, codigo FROM carreras;")
			# Con fetchall traemos todas las filas
				carreras = cursor.fetchall()
				consulta = '''select p.nombre, p.carnet, p.fecha, c.codigo, d.precio from pagos p 
				inner join codigos d on p.idcod = d.idcodigos
				inner join carreras c on d.idcarrera = c.idcarreras
				where p.idcod < 13 and p.idcod >= 1
				order by p.fecha asc, c.codigo desc'''
				cursor.execute(consulta)
			# Con fetchall traemos todas las filas
				data = cursor.fetchall()
				suma = 0
				for i in data:
					suma = suma + i[4]
		finally:
			conexion.close()
	except (pymysql.err.OperationalError, pymysql.err.InternalError) as e:
		print("Ocurrió un error al conectar: ", e)
	return render_template('repi.html', title="Reporte inscripciones", data = data, suma=suma, carreras=carreras, logeado=session['logeadocaja'], barranav=2)

@app.route('/extra', methods=['GET', 'POST'])
@login_required
def extra():
	try:
		conexion = pymysql.connect(host=Conhost, user=Conuser, password=Conpassword, db=Condb)
		try:
			with conexion.cursor() as cursor:
				cursor.execute("SELECT idcodigos, cod, concepto FROM codigos WHERE pagose = 1 ORDER BY concepto asc;")
			# Con fetchall traemos todas las filas
				data = cursor.fetchall()
		finally:
			conexion.close()
	except (pymysql.err.OperationalError, pymysql.err.InternalError) as e:
		print("Ocurrió un error al conectar: ", e)
	if request.method == 'POST':
		datacarnet = request.form["carnet"]
		datanombre = request.form["nombre"]
		descripcion = request.form["descripcion"]
		dataextra = request.form["extra"]
		data = dataextra.split(',')
		extraid = data[0]
		extracod = data[1]
		return redirect(url_for('confirmacionextra', carnet = datacarnet, nombre = datanombre, idp = extraid, cod = extracod, descripcion = descripcion))
	return render_template('extra.html', title="Pagos extra", data = data, logeado=session['logeadocaja'], barranav=1)

@app.route('/confirmacionextra/<carnet>&<nombre>&<idp>&<cod>&<descripcion>', methods=['GET', 'POST'])
@login_required
def confirmacionextra(carnet, nombre, idp, cod, descripcion):
	idp = int(idp)
	carnet = str(carnet)
	nombre = str(nombre)
	cod = str(cod)
	descripcion = str(descripcion)
	if request.method == "POST":
		try:
			conexion = pymysql.connect(host=Conhost, user=Conuser, password=Conpassword, db=Condb)
			try:
				with conexion.cursor() as cursor:
					consulta1 = f'SELECT precio FROM codigos WHERE idcodigos = "{idp}"'
					cursor.execute(consulta1)
					precios1 = cursor.fetchall()
					consulta = "INSERT INTO pagos(idcod,nombre,carnet,total,fecha,extra, recibo,user) VALUES (%s,%s,%s,%s,%s,%s,%s,%s);"
					cursor.execute(consulta, (idp, nombre, carnet, precios1[0][0], date.today(), descripcion,0,session['idusercaja']))
					conexion.commit()
					consulta = "Select MAX(idpagos) from pagos;"
					cursor.execute(consulta)
					pagos = cursor.fetchone()
					idpago = pagos[0]
			finally:
				conexion.close()
		except (pymysql.err.OperationalError, pymysql.err.InternalError) as e:
			print("Ocurrió un error al conectar: ", e)
		return redirect(url_for('imprimir', idpagos = idpago))
	return render_template('confirmacionextra.html', title="Confirmación", carnet = carnet, nombre = nombre, idp = idp, cod = cod, logeado=session['logeadocaja'], descripcion=descripcion, barranav=1)

@app.route('/repextra', methods=['GET', 'POST'])
@login_required
def repextra():
	try:
		conexion = pymysql.connect(host=Conhost, user=Conuser, password=Conpassword, db=Condb)
		try:
			with conexion.cursor() as cursor:
				consulta = '''select p.nombre, p.carnet, p.fecha, c.cod, p.total from pagos p 
				inner join codigos c on p.idcod = c.idcodigos
				where p.idcod = 61 or p.idcod = 66 or p.idcod = 67 or p.idcod = 68 order by p.fecha asc'''
				cursor.execute(consulta)
			# Con fetchall traemos todas las filas
				data = cursor.fetchall()
				suma = 0
				for i in data:
					suma = suma + i[4]
		finally:
			conexion.close()
	except (pymysql.err.OperationalError, pymysql.err.InternalError) as e:
		print("Ocurrió un error al conectar: ", e)
	return render_template('repextra.html', title="Reporte Pagos Extra", data = data, suma=suma, logeado=session['logeadocaja'], barranav=2)

@app.route('/p', methods=['GET', 'POST'])
@login_required
def p():
	numeros = []
	for i in range(10):
		numeros.append(i+1)
	meses = ["Enero", "Febrero","Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
	try:
		conexion = pymysql.connect(host=Conhost, user=Conuser, password=Conpassword, db=Condb)
		try:
			with conexion.cursor() as cursor:
				cursor.execute("SELECT idcodigos, cod, concepto FROM pagossis.codigos WHERE practica = 1 ORDER BY cod asc;")
			# Con fetchall traemos todas las filas
				carreras = cursor.fetchall()
		finally:
			conexion.close()
	except (pymysql.err.OperationalError, pymysql.err.InternalError) as e:
		print("Ocurrió un error al conectar: ", e)
	if request.method == 'POST':
		datacarnet = request.form["carnet"]
		datanombre = request.form["nombre"]
		datacarrera = request.form["carrera"]
		datalugar = request.form["lugar1"]
		datalugar2 = request.form["lugar2"]
		datalugar3 = request.form["lugar3"]
		if len(datalugar) < 1:
			datalugar = 0
		if len(datalugar2) < 1:
			datalugar2 = 0
		if len(datalugar3) < 1:
			datalugar3 = 0
		datafechainicio = request.form["fechainicio"]
		if len(datafechainicio) < 1:
			datafechainicio = '0000-00-00'
		datafechafin = request.form["fechafin"]
		if len(datafechafin) < 1:
			datafechafin = '0000-00-00'
		data = datacarrera.split(',')
		pid = data[0]
		pcod = data[1]
		cantidad = request.form["cant"]
		cantidad = int(cantidad)
		datames = []
		for i in range(cantidad):
			aux1 = f'mes{i+1}'
			aux = request.form[aux1]
			if(len(aux) > 0):
				datames.append(aux)
		return redirect(url_for('confirmacionp', carnet = datacarnet, nombre = datanombre, datames= datames, pid = pid, pcod = pcod, cantidad=cantidad, lugar=datalugar, fechainicio = datafechainicio, fechafin=datafechafin, lugar2 = datalugar2, lugar3 = datalugar3))
	return render_template('practica.html', title="Practica",  carreras=carreras, numeros=numeros, meses=meses, logeado=session['logeadocaja'], barranav=1)

@app.route('/confirmacionp/<carnet>&<nombre>&<datames>&<pid>&<pcod>&<cantidad>&<lugar>&<fechainicio>&<fechafin>&<lugar2>&<lugar3>', methods=['GET', 'POST'])
@login_required
def confirmacionp(carnet, nombre, datames, pid, pcod,cantidad, lugar, fechainicio, fechafin, lugar2, lugar3):
	carnet = str(carnet)
	cantidad = int(cantidad)
	nombre = str(nombre)
	pid = int(pid)
	agregar = False
	meses=datames.split(',')
	for i in range(len(meses)):
		if 'LBCQ' in pcod or 'TLCQ' in pcod or 'MGGQ' in pcod:
			try:
				meses[i] = 'Mes: ' + str(meses[i].split("\'")[1])
			except:
				meses[i] = 'Mes: ' + str(meses[i])
		elif 'TOPTQ' in pcod or ('TRADQ' in pcod and 'Pre' in pcod):
			try:
				meses[i] = 'Módulo: ' + str(meses[i].split("\'")[1])
			except:
				meses[i] = 'Módulo: ' + str(meses[i])
		else:
			try:
				meses[i] = str(meses[i].split("'")[1])
			except:
				meses[i] = meses[i]
	if request.method == "POST":
		try:
			conexion = pymysql.connect(host=Conhost, user=Conuser, password=Conpassword, db=Condb)
			try:
				with conexion.cursor() as cursor:
					consulta1 = f'SELECT idcodigos, precio, concepto FROM codigos WHERE idcodigos = "{pid}"'
					cursor.execute(consulta1)
					precios1 = cursor.fetchall()
					precioasig = float(precios1[0][1])
					idpagos = []
					idpracticas = []
					for i in range(cantidad):
						if 'TUEVQ' in pcod:
							consulta = "INSERT INTO pagos(idcod,nombre,carnet,total,fecha,extra,recibo,user) VALUES (%s,%s,%s,%s,%s,%s,%s,%s);"
							cursor.execute(consulta, (precios1[0][0], nombre, carnet, meses[i], date.today(), 'Practica TUEVQ',0,session['idusercaja']))
							conexion.commit()
						elif 'LBCQ' in pcod:
							if 'Banco' in pcod:
								consulta = "INSERT INTO practicalbcq(nombre, carnet, idcodigo, fecha, descripcion, user) VALUES (%s,%s,%s,CURDATE(),%s,%s);"
								cursor.execute(consulta, (nombre, carnet, pid, meses[i],session['idusercaja']))
								conexion.commit()
								consulta = "Select MAX(idpracticalbcq) from practicalbcq;"
								cursor.execute(consulta)
								idpago = cursor.fetchone()
								idpago = idpago[0]
								idpagos.append(idpago)
							else:
								consulta = "INSERT INTO pagos(idcod,nombre,carnet,total,fecha,extra,recibo,user) VALUES (%s,%s,%s,%s,%s,%s,%s,%s);"
								cursor.execute(consulta, (precios1[0][0], nombre, carnet, precioasig, date.today(), meses[i],0,session['idusercaja']))
								consulta = "INSERT INTO practicalbcq(nombre, carnet, idcodigo, fecha, descripcion, user) VALUES (%s,%s,%s,CURDATE(),%s,%s);"
								cursor.execute(consulta, (nombre, carnet, pid, meses[i],session['idusercaja']))
								conexion.commit()
								consulta = "Select MAX(idpracticalbcq) from practicalbcq;"
								cursor.execute(consulta)
								idpago = cursor.fetchone()
								idpago = idpago[0]
								idpagos.append(idpago)
						elif 'THDQ' in pcod or 'TLCQ' in pcod or 'Diálisis' in pcod:
							consulta = "INSERT INTO pagos(idcod,nombre,carnet,total,fecha,extra,recibo,user) VALUES (%s,%s,%s,%s,%s,%s,%s,%s);"
							cursor.execute(consulta, (precios1[0][0], nombre, carnet, precioasig, date.today(), meses[i],0,session['idusercaja']))
							conexion.commit()
							consulta = "Select MAX(idpagos) from pagos;"
							cursor.execute(consulta)
							idpago = cursor.fetchone()
							idpago = idpago[0]
							idpagos.append(idpago)
						elif ('TRADQ' in pcod and 'Prepractica' in pcod) or ('TOPTQ' in pcod):
							consulta = "INSERT INTO pagos(idcod,nombre,carnet,total,fecha,extra,recibo,user) VALUES (%s,%s,%s,%s,%s,%s,%s,%s);"
							cursor.execute(consulta, (precios1[0][0], nombre, carnet, precioasig, date.today(), meses[i],0,session['idusercaja']))
							conexion.commit()
							consulta = "Select MAX(idpagos) from pagos;"
							cursor.execute(consulta)
							idpago = cursor.fetchone()
							idpago = idpago[0]
							idpagos.append(idpago)
						else:
							consulta = "INSERT INTO pagos(idcod,nombre,carnet,total,fecha,extra,recibo,user) VALUES (%s,%s,%s,%s,%s,%s,%s,%s);"
							if 'LENQ' in precios1[0][2] and 'Pago 3' in meses[i]:
								precioasig = 200
								if lugar == 0 or fechainicio == '0000-00-00' or fechafin == '0000-00-00':
									imprimir = False
								else:
									imprimir = True
							else:
								imprimir = False
							cursor.execute(consulta, (precios1[0][0], nombre, carnet, precioasig, date.today(), meses[i],0,session['idusercaja']))
							if 'LENQ' in precios1[0][2]:
								consulta = "INSERT INTO practicalenq(nombre,carnet,practica,lugar,fechainicio,fechafin,fecha,lugar2, lugar3) VALUES (%s,%s,%s,%s,%s,%s,CURDATE(),%s,%s);"
								cursor.execute(consulta, (nombre, carnet, meses[i], lugar, fechainicio,fechafin,lugar2,lugar3))
								consulta = "Select MAX(idpracticalenq) from practicalenq;"
								cursor.execute(consulta)
								idpractica = cursor.fetchone()
								idpracticas = idpractica[0]
								consulta = "Select MAX(idpagos) from pagos;"
								cursor.execute(consulta)
								idpago = cursor.fetchone()
								idpago = idpago[0]
								idpagos.append(idpago)
							conexion.commit()
			finally:
				conexion.close()
		except (pymysql.err.OperationalError, pymysql.err.InternalError) as e:
			print("Ocurrió un error al conectar: ", e)
		if 'LBCQ' in pcod:
			if 'EPS' in pcod:
				return redirect(url_for('epslbcq', idpagos = idpagos))
			else:
				return redirect(url_for('hojalbcq', idpagos = idpagos))
		elif 'LENQ' in pcod:
			if imprimir:
				return redirect(url_for('hojalenq', idpagos = idpracticas))
			else:
				return redirect(url_for('imprimir', idpagos = idpagos))
		elif 'THDQ' in pcod:
			return redirect(url_for('hojathdq', idpagos = idpagos))
		elif 'Diálisis' in pcod:
			return redirect(url_for('hojadialisis', idpagos = idpagos))
		elif 'TLCQ' in pcod:
			return redirect(url_for('hojatlcq', idpagos = idpagos))
		elif 'TRADQ' in pcod and 'Prepractica' in pcod:
			return redirect(url_for('prepracticatradq', idpagos = idpagos))
		elif 'TOPTQ' in pcod:
			return redirect(url_for('practicatoptq', idpagos = idpagos))
		else:
			return redirect(url_for('p'))
	return render_template('confirmacionp.html', title="Confirmación", carnet = carnet, nombre = nombre, meses = meses, pid = pid, pcod = pcod, cantidad=cantidad, logeado=session['logeadocaja'], lugar=lugar, fechainicio = fechainicio, fechafin = fechafin, lugar2 = lugar2, lugar3 = lugar3, barranav=1)

@app.route('/repp', methods=['GET', 'POST'])
@login_required
def repp():
	datacarnet = ""
	datanombre = ""
	datafechainicio = ""
	datafechafin = ""
	datacarrera = ""
	datadescripcion = ""
	accion = 0
	data = []
	conteo = 0
	if request.method == "POST":
		datacarnet = request.form["carnet"]
		datanombre = request.form["nombre"]
		datafechainicio = request.form["fechaini"]
		datafechafin = request.form["fechafin"]
		datacarrera = request.form["carrera"]
		datadescripcion = request.form["descripcion"]
		accion = request.form["accion"]
		try:
			conexion = pymysql.connect(host=Conhost, user=Conuser, password=Conpassword, db=Condb)
			try:
				with conexion.cursor() as cursor:
					consulta = f'select p.nombre, p.carnet, DATE_FORMAT(p.fecha,"%d/%m/%Y"), d.cod, p.extra, p.total, p.idpagos from pagos p inner join codigos d on p.idcod = d.idcodigos inner join carreras c on d.idcarrera = c.idcarreras where d.practica = 1 and p.nombre like "%{datanombre}%" and p.carnet like "%{datacarnet}%"'
					if len(datafechainicio) != 0:
						consulta = consulta + f' and p.fecha >= "{datafechainicio}"'
					if len(datafechafin) != 0:
						consulta = consulta + f' and p.fecha <= "{datafechafin}"'
					consulta = consulta + f' and d.cod like "%{datacarrera}%" and p.extra like "%{datadescripcion}%" order by p.fecha desc, c.codigo desc, p.nombre asc, p.extra asc;'
					cursor.execute(consulta)
				# Con fetchall traemos todas las filas
					data = cursor.fetchall()
					conteo = len(data)
			finally:
				conexion.close()
		except (pymysql.err.OperationalError, pymysql.err.InternalError) as e:
			print("Ocurrió un error al conectar: ", e)
		if int(accion) == 1:
			return render_template('repp.html', title="Reporte Prácticas", data = data, carreras=carreras, logeado=session['logeadocaja'], conteo=conteo, datacarnet = datacarnet, datanombre = datanombre, datafechainicio = datafechainicio, datafechafin = datafechafin, datacarrera = datacarrera, datadescripcion = datadescripcion)
		elif int(accion) == 2:
			output = io.BytesIO()
			workbook = xlwt.Workbook(encoding="utf-8")
			sh1 = workbook.add_sheet("Reporte Prácticas")

			xlwt.add_palette_colour("Orange", 0x21) # the second argument must be a number between 8 and 64
			workbook.set_colour_RGB(0x21, 255, 165, 0) # Red — 79, Green — 129, Blue — 189
			xlwt.add_palette_colour("Lightgreen", 0x22) # the second argument must be a number between 8 and 64
			workbook.set_colour_RGB(0x22, 144, 238, 144) # Red — 79, Green — 129, Blue — 189
			
			#bordes
			borders = xlwt.Borders()
			borders.left = 1
			borders.right = 1
			borders.top = 1
			borders.bottom = 1

			#encabezados
			header_font = xlwt.Font()
			header_font.name = 'Arial'
			header_font.bold = True
			header_style = xlwt.XFStyle()
			header_style.font = header_font
			header_style.borders = borders

			#contenido1
			content_font = xlwt.Font()
			content_font.name = 'Arial'
			content_pattern = xlwt.Pattern()
			content_style = xlwt.XFStyle()
			content_style.font = content_font
			content_style.borders = borders
			content_style.pattern = content_pattern

			#titulos
			tittle_font = xlwt.Font()
			tittle_font.name = 'Arial'
			tittle_font.bold = True
			tittle_font.italic = True
			tittle_font.height = 20*20
			tittle_style = xlwt.XFStyle()
			tittle_style.font = tittle_font

			sh1.write(0,0,"Reporte Prácticas", tittle_style)
			sh1.write(1,0,"Total de Resultados: "+str(conteo), tittle_style)
			sh1.write(3,0,"No.", header_style)
			sh1.write(3,1,"Nombre", header_style)
			sh1.write(3,2,"Carnet", header_style)
			sh1.write(3,3,"Fecha", header_style)
			sh1.write(3,4,"Código", header_style)
			sh1.write(3,5,"Descripción", header_style)
			sh1.write(3,6,"Total", header_style)

			if len(data) > 0:
				for i in range(len(data)):
					sh1.write(i+4,0,i+1, content_style)
					sh1.write(i+4,1,data[i][0], content_style)
					sh1.write(i+4,2,data[i][1], content_style)
					sh1.write(i+4,3,data[i][2], content_style)
					sh1.write(i+4,4,data[i][3], content_style)
					sh1.write(i+4,5,data[i][4], content_style)
					sh1.write(i+4,6,"Q"+str(data[i][5]), content_style)
			
			sh1.col(0).width = 0x0d00 + len("No.")
			try:
				sh1.col(1).width = 256 * (max([len(str(row[i])) for row in data[i][0]]) + 1) * 10
				sh1.col(2).width = 256 * (max([len(str(row[i])) for row in data[i][1]]) + 1) * 10
				sh1.col(3).width = 256 * (max([len(str(row[i])) for row in data[i][2]]) + 1) * 10
				sh1.col(4).width = 256 * (max([len(str(row[i])) for row in data[i][3]]) + 1) * 10
				sh1.col(5).width = 256 * (max([len(str(row[i])) for row in data[i][4]]) + 1) * 10
				sh1.col(6).width = 256 * (max([len(str(row[i])) for row in data[i][5]]) + 1) * 10
				sh1.col(7).width = 256 * (max([len(str(row[i])) for row in data[i][6]]) + 1) * 10
			except:
				sh1.col(1).width = 256 * 20
				sh1.col(2).width = 256 * 20
				sh1.col(3).width = 256 * 20
				sh1.col(4).width = 256 * 20
				sh1.col(5).width = 256 * 20
				sh1.col(6).width = 256 * 20
				sh1.col(7).width = 256 * 20
			workbook.save(output)
			output.seek(0)
			return Response(output, mimetype="application/ms-excel", headers={"Content-Disposition":"attachment;filename=reportepracticas.xls"})
	return render_template('repp.html', title="Reporte Prácticas", data = data, carreras=carreras, logeado=session['logeadocaja'], conteo=conteo, datacarnet = datacarnet, datanombre = datanombre, datafechainicio = datafechainicio, datafechafin = datafechafin, datacarrera = datacarrera, datadescripcion = datadescripcion, barranav=2)

@app.route('/hojalbcq/<idpagos>', methods=['GET', 'POST'])
@login_required
def hojalbcq(idpagos):
	array = idpagos.split(',')
	newarray = []
	cantidad = len(array)
	for i in range(cantidad):
		varaux = ''
		for j in array[i]:
			if j.isdigit():
				varaux = varaux + str(j)
		newarray.append(varaux)
	try:
		conexion = pymysql.connect(host=Conhost, user=Conuser, password=Conpassword, db=Condb)
		try:
			with conexion.cursor() as cursor:
				meses = []
				idhojas = []
				for i in range(cantidad):
					consulta = f'SELECT nombre, carnet, descripcion, idpracticalbcq FROM practicalbcq WHERE idpracticalbcq = {newarray[i]};'
					cursor.execute(consulta)
				# Con fetchall traemos todas las filas
					data = cursor.fetchone()
					nombre = data[0]
					carnet = data[1]
					aux = data[2]
					aux = str(aux).split(':')
					meses.append(aux[1])
					idhojas.append(data[3])
		finally:
			conexion.close()
	except (pymysql.err.OperationalError, pymysql.err.InternalError) as e:
		print("Ocurrió un error al conectar: ", e)
	fechaact = date.today()
	year = fechaact.year
	rendered = render_template('hojalbcq.html', title="Hoja de Práctica ", cantidad = cantidad, nombre = nombre, carnet = carnet, meses = meses, year = year, idhojas=idhojas, path=PATH_FILE)
	options = {'enable-local-file-access': None, 'page-size': 'Legal', 'margin-bottom': '35mm'}
	config = pdfkit.configuration(wkhtmltopdf="C:\\Program Files\\wkhtmltopdf\\bin\\wkhtmltopdf.exe")
	pdf = pdfkit.from_string(rendered, False, configuration=config, options=options)
	response = make_response(pdf)
	response.headers['Content-Type'] = 'application/pdf'
	response.headers['Content-Disposition'] = 'inline; filename=reportediario.pdf'
	print(response)
	return response

@app.route('/epslbcq/<idpagos>', methods=['GET', 'POST'])
@login_required
def epslbcq(idpagos):
	array = idpagos.split(',')
	newarray = []
	cantidad = len(array)
	for i in range(cantidad):
		varaux = ''
		for j in array[i]:
			if j.isdigit():
				varaux = varaux + str(j)
		newarray.append(varaux)
	try:
		conexion = pymysql.connect(host=Conhost, user=Conuser, password=Conpassword, db=Condb)
		try:
			with conexion.cursor() as cursor:
				meses = []
				idhojas = []
				for i in range(cantidad):
					consulta = f'SELECT nombre, carnet, descripcion, idpracticalbcq FROM practicalbcq WHERE idpracticalbcq = {newarray[i]};'
					cursor.execute(consulta)
				# Con fetchall traemos todas las filas
					data = cursor.fetchone()
					nombre = data[0]
					carnet = data[1]
					aux = data[2]
					aux = str(aux).split(':')
					meses.append(aux[1])
					idhojas.append(data[3])
		finally:
			conexion.close()
	except (pymysql.err.OperationalError, pymysql.err.InternalError) as e:
		print("Ocurrió un error al conectar: ", e)
	fechaact = date.today()
	year = fechaact.year
	
	rendered = render_template('epslbcq.html', title="Hoja de Práctica ", cantidad = cantidad, nombre = nombre, carnet = carnet, meses = meses, year = year, idhojas=idhojas, path=PATH_FILE)
	options = {'enable-local-file-access': None, 'page-size': 'Legal', 'footer-right': 'Página [page] de [topage]', 'margin-bottom': '40mm'}
	config = pdfkit.configuration(wkhtmltopdf="C:\\Program Files\\wkhtmltopdf\\bin\\wkhtmltopdf.exe")
	pdf = pdfkit.from_string(rendered, False, configuration=config, options=options)
	response = make_response(pdf)
	response.headers['Content-Type'] = 'application/pdf'
	response.headers['Content-Disposition'] = 'inline; filename=practicalenq.pdf'
	print(response)
	return response

@app.route('/hojalenq/<idpagos>', methods=['GET', 'POST'])
@login_required
def hojalenq(idpagos):
	array = idpagos.split(',')
	newarray = []
	cantidad = len(array)
	for i in range(cantidad):
		varaux = ''
		for j in array[i]:
			if j.isdigit():
				varaux = varaux + str(j)
		newarray.append(varaux)
	try:
		conexion = pymysql.connect(host=Conhost, user=Conuser, password=Conpassword, db=Condb)
		try:
			with conexion.cursor() as cursor:
				meses = []
				consulta = f'SELECT nombre, carnet, practica, lugar, DATE_FORMAT(fechainicio,"%d/%m/%Y"), DATE_FORMAT(fechafin,"%d/%m/%Y"), lugar2, lugar3 FROM practicalenq WHERE idpracticalenq = {newarray[0]};'
				cursor.execute(consulta)
			# Con fetchall traemos todas las filas
				practica = cursor.fetchone()
		finally:
			conexion.close()
	except (pymysql.err.OperationalError, pymysql.err.InternalError) as e:
		print("Ocurrió un error al conectar: ", e)
	fechaact = date.today()
	year = fechaact.year
	if '1)' in practica[2]:
		template = 'hojalenq1.html'
	elif '2)' in practica[2]:
		template = 'hojalenq2.html'
	elif '3)' in practica[2]:
		template = 'hojalenq3.html'
	elif '4)' in practica[2]:
		template = 'hojalenq4.html'
	elif '5)' in practica[2]:
		template = 'hojalenq5.html'
	elif '6)' in practica[2]:
		template = 'hojalenq6.html'
	#Se genera el PDF
	rendered = render_template(template, title="Hoja de Práctica ", practica = practica, year = year, path=PATH_FILE)
	options = {'enable-local-file-access': None, 'page-size': 'Legal', 'footer-right': 'Página [page] de [topage]', 'margin-bottom': '40mm'}
	config = pdfkit.configuration(wkhtmltopdf="C:\\Program Files\\wkhtmltopdf\\bin\\wkhtmltopdf.exe")
	pdf = pdfkit.from_string(rendered, False, configuration=config, options=options)
	response = make_response(pdf)
	response.headers['Content-Type'] = 'application/pdf'
	response.headers['Content-Disposition'] = 'inline; filename=practicalenq.pdf'
	print(response)
	return response

@app.route('/hojathdq/<idpagos>', methods=['GET', 'POST'])
@login_required
def hojathdq(idpagos):
	array = idpagos.split(',')
	newarray = []
	cantidad = len(array)
	for i in range(cantidad):
		varaux = ''
		for j in array[i]:
			if j.isdigit():
				varaux = varaux + str(j)
		newarray.append(varaux)

	try:
		conexion = pymysql.connect(host=Conhost, user=Conuser, password=Conpassword, db=Condb)
		try:
			with conexion.cursor() as cursor:
				consulta = f'SELECT nombre, carnet FROM pagos WHERE idpagos = {newarray[0]};'
				cursor.execute(consulta)
			# Con fetchall traemos todas las filas
				data = cursor.fetchone()
				nombre = data[0]
				carnet = data[1]
		finally:
			conexion.close()
	except (pymysql.err.OperationalError, pymysql.err.InternalError) as e:
		print("Ocurrió un error al conectar: ", e)
	fechaact = date.today()
	year = fechaact.year
	#Se genera el PDF
	rendered = render_template('hojathdq.html', title="Hoja de Práctica ", cantidad = cantidad, nombre = nombre, carnet = carnet, year = year, path = PATH_FILE)
	options = {'enable-local-file-access': None, 'page-size': 'Letter','margin-right': '10mm'}
	config = pdfkit.configuration(wkhtmltopdf="C:\\Program Files\\wkhtmltopdf\\bin\\wkhtmltopdf.exe")
	pdf = pdfkit.from_string(rendered, False, configuration=config, options=options)
	response = make_response(pdf)
	response.headers['Content-Type'] = 'application/pdf'
	response.headers['Content-Disposition'] = 'inline; filename=reportediario.pdf'
	print(response)
	return response

@app.route('/hojadialisis/<idpagos>', methods=['GET', 'POST'])
@login_required
def hojadialisis(idpagos):
	array = idpagos.split(',')
	newarray = []
	cantidad = len(array)
	for i in range(cantidad):
		varaux = ''
		for j in array[i]:
			if j.isdigit():
				varaux = varaux + str(j)
		newarray.append(varaux)
	try:
		conexion = pymysql.connect(host=Conhost, user=Conuser, password=Conpassword, db=Condb)
		try:
			with conexion.cursor() as cursor:
				consulta = f'SELECT nombre, carnet FROM pagos WHERE idpagos = {newarray[0]};'
				cursor.execute(consulta)
			# Con fetchall traemos todas las filas
				data = cursor.fetchone()
				nombre = data[0]
				carnet = data[1]
		finally:
			conexion.close()
	except (pymysql.err.OperationalError, pymysql.err.InternalError) as e:
		print("Ocurrió un error al conectar: ", e)
	fechaact = date.today()
	year = fechaact.year
	#Se genera el PDF
	rendered = render_template('hojadialisis.html', title="Hoja de Práctica Dialisis Peritoneal", cantidad = cantidad, nombre = nombre, carnet = carnet, year = year, path=PATH_FILE)
	options = {'enable-local-file-access': None, 'page-size': 'Letter','margin-right': '10mm'}
	config = pdfkit.configuration(wkhtmltopdf="C:\\Program Files\\wkhtmltopdf\\bin\\wkhtmltopdf.exe")
	pdf = pdfkit.from_string(rendered, False, configuration=config, options=options)
	response = make_response(pdf)
	response.headers['Content-Type'] = 'application/pdf'
	response.headers['Content-Disposition'] = 'inline; filename=reportediario.pdf'
	print(response)
	return response

@app.route('/hojatlcq/<idpagos>', methods=['GET', 'POST'])
@login_required
def hojatlcq(idpagos):
	array = idpagos.split(',')
	newarray = []
	cantidad = len(array)
	for i in range(cantidad):
		varaux = ''
		for j in array[i]:
			if j.isdigit():
				varaux = varaux + str(j)
		newarray.append(varaux)
	try:
		conexion = pymysql.connect(host=Conhost, user=Conuser, password=Conpassword, db=Condb)
		try:
			with conexion.cursor() as cursor:
				meses = []
				idhojas = []
				for i in range(cantidad):
					consulta = f'SELECT nombre, carnet, extra, idpagos FROM pagos WHERE idpagos = {newarray[i]};'
					cursor.execute(consulta)
				# Con fetchall traemos todas las filas
					data = cursor.fetchone()
					nombre = data[0]
					carnet = data[1]
					aux = data[2]
					aux = str(aux).split(':')
					meses.append(aux[1])
					idhojas.append(data[3])
		finally:
			conexion.close()
	except (pymysql.err.OperationalError, pymysql.err.InternalError) as e:
		print("Ocurrió un error al conectar: ", e)
	fechaact = date.today()
	year = fechaact.year
	#Se Genera el PDF
	rendered = render_template('hojatlcq.html', title="Hoja de Práctica ", cantidad = cantidad, nombre = nombre, carnet = carnet, year = year, idhojas = idhojas, meses = meses, path = PATH_FILE)
	options = {'enable-local-file-access': None, 'page-size': 'Legal', 'margin-bottom': '35mm'}
	config = pdfkit.configuration(wkhtmltopdf="C:\\Program Files\\wkhtmltopdf\\bin\\wkhtmltopdf.exe")
	pdf = pdfkit.from_string(rendered, False, configuration=config, options=options)
	response = make_response(pdf)
	response.headers['Content-Type'] = 'application/pdf'
	response.headers['Content-Disposition'] = 'inline; filename=reportediario.pdf'
	return response

@app.route('/prepracticatradq/<idpagos>', methods=['GET', 'POST'])
@login_required
def prepracticatradq(idpagos):
	array = idpagos.split(',')
	newarray = []
	cantidad = len(array)
	for i in range(cantidad):
		varaux = ''
		for j in array[i]:
			if j.isdigit():
				varaux = varaux + str(j)
		newarray.append(varaux)
	try:
		conexion = pymysql.connect(host=Conhost, user=Conuser, password=Conpassword, db=Condb)
		try:
			with conexion.cursor() as cursor:
				numeros = []
				for i in range(cantidad):
					consulta = f'SELECT nombre, carnet, extra FROM pagos WHERE idpagos = {newarray[i]};'
					cursor.execute(consulta)
				# Con fetchall traemos todas las filas
					data = cursor.fetchone()
					nombre = data[0]
					carnet = data[1]
					aux = data[2]
					aux = str(aux).split(':')
					numeros.append(int(aux[1]))
		finally:
			conexion.close()
	except (pymysql.err.OperationalError, pymysql.err.InternalError) as e:
		print("Ocurrió un error al conectar: ", e)
	fechaact = date.today()
	year = fechaact.year
	#Se genera PDF
	rendered = render_template('prepracticatradq.html', title="Pre-Práctica TRADQ ", cantidad = cantidad, nombre = nombre, carnet = carnet, year = year, numeros = numeros, path=PATH_FILE)
	options = {'enable-local-file-access': None, 'page-size': 'Letter','margin-bottom': '35mm','margin-right': '10mm'}
	config = pdfkit.configuration(wkhtmltopdf="C:\\Program Files\\wkhtmltopdf\\bin\\wkhtmltopdf.exe")
	pdf = pdfkit.from_string(rendered, False, configuration=config, options=options)
	response = make_response(pdf)
	response.headers['Content-Type'] = 'application/pdf'
	response.headers['Content-Disposition'] = 'inline; filename=reportediario.pdf'
	print(response)
	return response

@app.route('/practicatoptq/<idpagos>', methods=['GET', 'POST'])
@login_required
def practicatoptq(idpagos):
	array = idpagos.split(',')
	newarray = []
	cantidad = len(array)
	for i in range(cantidad):
		varaux = ''
		for j in array[i]:
			if j.isdigit():
				varaux = varaux + str(j)
		newarray.append(varaux)
		id = newarray[0]
	try:
		conexion = pymysql.connect(host=Conhost, user=Conuser, password=Conpassword, db=Condb)
		try:
			with conexion.cursor() as cursor:
				numeros = []
				consulta = f'SELECT nombre, carnet, extra, DATE_FORMAT(fecha,"%d/%m/%Y") FROM pagos WHERE idpagos = {id};'
				cursor.execute(consulta)
			# Con fetchall traemos todas las filas
				data = cursor.fetchone()
				nombre = data[0]
				carnet = data[1]
				aux = data[2]
				fecha = data[3]
				aux = str(aux).split(':')
				numeros.append(int(aux[1]))
		finally:
			conexion.close()
	except (pymysql.err.OperationalError, pymysql.err.InternalError) as e:
		print("Ocurrió un error al conectar: ", e)
	fechaact = date.today()
	year = fechaact.year
	#Se genera PDF
	rendered = render_template('practicatoptq.html', title="Práctica TOPTQ", cantidad = cantidad, nombre = nombre, carnet = carnet, year = year, numeros = numeros, fecha =fecha, path=PATH_FILE)
	options = {'enable-local-file-access': None, 'page-size': 'Letter','margin-bottom': '35mm','margin-right': '10mm'}
	config = pdfkit.configuration(wkhtmltopdf="C:\\Program Files\\wkhtmltopdf\\bin\\wkhtmltopdf.exe")
	pdf = pdfkit.from_string(rendered, False, configuration=config, options=options)
	response = make_response(pdf)
	response.headers['Content-Type'] = 'application/pdf'
	response.headers['Content-Disposition'] = 'inline; filename=modulotoptq.pdf'
	print(response)
	return response

@app.route('/m', methods=['GET', 'POST'])
@login_required
def m():
	try:
		conexion = pymysql.connect(host=Conhost, user=Conuser, password=Conpassword, db=Condb)
		try:
			with conexion.cursor() as cursor:
				cursor.execute("SELECT idcodigos, cod, concepto FROM codigos WHERE manual = 1 ORDER BY cod asc;")
			# Con fetchall traemos todas las filas
				carreras = cursor.fetchall()
		finally:
			conexion.close()
	except (pymysql.err.OperationalError, pymysql.err.InternalError) as e:
		print("Ocurrió un error al conectar: ", e)
	if request.method == 'POST':
		datacarnet = request.form["carnet"]
		datanombre = request.form["nombre"]
		datacarrera = request.form["carrera"]
		data = datacarrera.split(',')
		mid = data[0]
		mcod = data[1]
		cantidad = request.form["cant"]
		cantidad = int(cantidad)
		datacurso = []
		for i in range(cantidad):
			aux1 = f'curso{i+1}'
			aux = request.form[aux1]
			if(len(aux) > 0):
				datacurso.append(aux)
			aux1 = f'kit{i+1}'
		return redirect(url_for('confirmacionm', carnet = datacarnet, nombre = datanombre, curso= datacurso, mid = mid, mcod = mcod))
	return render_template('manuales.html', title="Manuales",  carreras=carreras, logeado=session['logeadocaja'], barranav=1)

@app.route('/confirmacionm/<carnet>&<nombre>&<curso>&<mid>&<mcod>', methods=['GET', 'POST'])
@login_required
def confirmacionm(carnet, nombre, curso, mid, mcod):
	numsmanualeslbcq = [2,4,6,8]
	numsmanualestlcq = [2,4]
	nombremanualesindlbcq = [['BIOLOGIA GENERAL II', 290], ['MICROBIOLOGIA GENERAL', 440], ['BACTERIOLOGIA', 435], ['INMUNOLOGIA BASICA', 305], ['BIOQUIMICA CLINICA', 275], ['MICOLOGIA', 260], ['MICROBIOLOGIA APLICADA I', 260], ['INTERPRETACION DE PRUEBAS BIOQUIMICAS', 265]]
	nombremanualesindtlcq = [['HEMATOLOGIA Y COAGULACION', 325], ['INMUNOLOGIA Y BANCO DE SANGRE', 300], ['MICROBIOLOGIA', 280], ['PRUEBAS ESPECIALES', 330]]
	carnet = str(carnet)
	nombre = str(nombre)
	mid = str(mid)
	mcod = str(mcod)
	curso = str(curso).upper()
	cursos = curso.split(',')
	cantidad = len(cursos)
	for i in range(cantidad):
		try:
			cursos[i] = str(cursos[i].split("'")[1])
		except:
			pass
	if request.method == "POST":
		try:
			conexion = pymysql.connect(host=Conhost, user=Conuser, password=Conpassword, db=Condb)
			try:
				with conexion.cursor() as cursor:
					consulta = f'SELECT concepto FROM codigos WHERE idcodigos = "{mid}"'
					cursor.execute(consulta)
					concepto = cursor.fetchone()
					kit = True
					if "TLCQ" in concepto[0]:
						carrera = "TLCQ"
						if "Manual" in concepto[0]:
							kit = False
					elif "LBCQ" in concepto[0]:
						carrera = "LBCQ"
						if "Manual" in concepto[0]:
							kit = False
					consulta1 = f'SELECT idcodigos, precio FROM codigos WHERE idcodigos = "{mid}"'
					cursor.execute(consulta1)
					precios1 = cursor.fetchall()
					idpagos = []
					for i in range(cantidad):
						if kit == False:
							total = 175
							if carrera == 'LBCQ':
								for j in nombremanualesindlbcq:
									if unicodedata.normalize('NFKD', cursos[i]).encode('ASCII', 'ignore').strip() == unicodedata.normalize('NFKD', j[0]).encode('ASCII', 'ignore').strip():
										total = j[1]
										if cursos[i] == j[0]:
											pass
										else:
											cursos[i] = j[0]
							elif carrera == "TLCQ":
								for j in nombremanualesindtlcq:
									if unicodedata.normalize('NFKD', cursos[i]).encode('ASCII', 'ignore').strip() == unicodedata.normalize('NFKD', j[0]).encode('ASCII', 'ignore').strip():
										total = j[1]
										if cursos[i] == j[0]:
											pass
										else:
											cursos[i] = j[0]
							consulta = "INSERT INTO pagos(idcod,nombre,carnet,total,fecha,extra, recibo,user) VALUES (%s,%s,%s,%s,%s,%s,%s,%s);"
							cursor.execute(consulta, (precios1[0][0], nombre, carnet, total, date.today(), "Curso: "+cursos[i], 0,session['idusercaja']))
						else:
							consulta = "INSERT INTO pagos(idcod,nombre,carnet,total,fecha,extra, recibo,user) VALUES (%s,%s,%s,%s,%s,%s,%s,%s);"
							cursor.execute(consulta, (precios1[0][0], nombre, carnet, precios1[0][1], date.today(), "Curso: "+cursos[i], 0,session['idusercaja']))
						conexion.commit()
						consulta = "Select MAX(idpagos) from pagos;"
						cursor.execute(consulta)
						idpago = cursor.fetchone()
						idpago = idpago[0]
						idpagos.append(idpago)
			finally:
				conexion.close()
		except (pymysql.err.OperationalError, pymysql.err.InternalError) as e:
			print("Ocurrió un error al conectar: ", e)
		return redirect(url_for('imprimir', idpagos=idpagos))
	return render_template('confirmacionm.html', title="Confirmación", carnet = carnet, nombre = nombre, cursos = cursos, mid = mid, mcod = mcod, cantidad=cantidad, logeado=session['logeadocaja'], barranav=1)

@app.route('/repm', methods=['GET', 'POST'])
def repm():
	fechainicio = '2024-07-01'
	try:
		conexion = pymysql.connect(host=Conhost, user=Conuser, password=Conpassword, db=Condb)
		try:
			with conexion.cursor() as cursor:
				numsmanualeslbcq = [2,4,6,8]
				numsmanualestlcq = [2,4]
				nombremanualesindlbcq = [['BIOLOGIA GENERAL II', 265], ['QUIMICA GENERAL II', 175], ['MICROBIOLOGIA GENERAL', 415], ['QUIMICA ORGANICA', 175], ['BACTERIOLOGIA', 410],  ['BIOQUIMICA CLINICA', 250], ['INMUNOLOGIA BASICA', 280],['MICOLOGIA', 235], ['INTERPRETACION DE PRUEBAS BIOQUIMICAS', 335], ['MICROBIOLOGIA APLICADA I', 235]]
				nombremanualesindtlcq = [['HEMATOLOGIA Y COAGULACION', 300], ['INMUNOLOGIA Y BANCO DE SANGRE', 275], ['MICROBIOLOGIA', 255], ['PRUEBAS ESPECIALES', 305]]
				manualeslbcq = []
				manualestlcq = []
				manualesindlbcq = []
				manualesindtlcq = []
				for i in numsmanualeslbcq:
					consulta = f"select p.nombre, p.carnet, p.fecha, c.cod, p.extra from pagos p inner join codigos c on p.idcod = c.idcodigos where p.fecha > '{fechainicio}' and c.cod like 'KITLBCQ{i}' and p.devuelto = 0"
					cursor.execute(consulta)
					manuales = cursor.fetchall()
					manualeslbcq.append(manuales)
				for i in numsmanualestlcq:
					consulta = f"select p.nombre, p.carnet, p.fecha, c.cod, p.extra from pagos p inner join codigos c on p.idcod = c.idcodigos where p.fecha > '{fechainicio}' and c.cod like 'KITTLCQ{i}' and p.devuelto = 0"
					cursor.execute(consulta)
					manuales = cursor.fetchall()
					manualestlcq.append(manuales)
				for i in nombremanualesindlbcq:
					consulta = f"select p.nombre, p.carnet, p.fecha, c.cod, p.extra from pagos p inner join codigos c on p.idcod = c.idcodigos where p.fecha > '{fechainicio}' and p.extra like '%{i[0]}%' and c.concepto like '%Manual LBCQ%' and p.devuelto = 0"
					cursor.execute(consulta)
					manuales = cursor.fetchall()
					manualesindlbcq.append(manuales)
				for i in nombremanualesindtlcq:
					consulta = f"select p.nombre, p.carnet, p.fecha, c.cod, p.extra from pagos p inner join codigos c on p.idcod = c.idcodigos where p.fecha > '{fechainicio}' and p.extra like '%{i[0]}%' and c.concepto like '%Manual TLCQ%' and p.devuelto = 0"
					cursor.execute(consulta)
					manuales = cursor.fetchall()
					manualesindtlcq.append(manuales)
			# Con fetchall traemos todas las filas
			#print(manualesindlbcq[1][1])
			print(manualesindtlcq)
		finally:
			conexion.close()
	except (pymysql.err.OperationalError, pymysql.err.InternalError) as e:
		print("Ocurrió un error al conectar: ", e)
	return render_template('repm.html', title="Reporte Manuales", numsmanualeslbcq = numsmanualeslbcq, numsmanualestlcq=numsmanualestlcq, manualeslbcq=manualeslbcq, manualestlcq=manualestlcq, manualesindlbcq=manualesindlbcq, manualesindtlcq=manualesindtlcq)

@app.route('/congreso', methods=['GET', 'POST'])
@login_required
def congreso():
	try:
		conexion = pymysql.connect(host=Conhost, user=Conuser, password=Conpassword, db=Condb)
		try:
			with conexion.cursor() as cursor:
				cursor.execute("SELECT idcodigos, concepto FROM codigos WHERE congreso = 1 ORDER BY concepto asc;")
			# Con fetchall traemos todas las filas
				congresos = cursor.fetchall()
				cursor.execute("SELECT codigo, carrera FROM carreras WHERE institucion = 1 ORDER BY codigo asc;")
			# Con fetchall traemos todas las filas
				carreras = cursor.fetchall()
		finally:
			conexion.close()
	except (pymysql.err.OperationalError, pymysql.err.InternalError) as e:
		print("Ocurrió un error al conectar: ", e)
	if request.method == 'POST':
		datacarnet = request.form["carnet"]
		datanombre = request.form["nombre"]
		datacarrera = request.form["carrera"]
		datacongreso = request.form["congreso"]
		data = datacongreso.split(',')
		datacongreso = data[0]
		concepto = data[1]
		cantidad = request.form["cant"]
		cantidad = int(cantidad)
		datacurso = []
		for i in range(cantidad):
			aux1 = f'curso{i+1}'
			aux = request.form[aux1]
			if(len(aux) > 0):
				datacurso.append(aux)
			aux1 = f'kit{i+1}'
		return redirect(url_for('confirmacioncongreso', carnet = datacarnet, nombre = datanombre, curso= datacurso, carrera = datacarrera, congreso = datacongreso, concepto=concepto))
	return render_template('congreso.html', title="Congreso",  congresos=congresos, carreras=carreras, logeado=session['logeadocaja'], barranav=1)

@app.route('/confirmacioncongreso/<carnet>&<nombre>&<curso>&<carrera>&<congreso>&<concepto>', methods=['GET', 'POST'])
@login_required
def confirmacioncongreso(carnet, nombre, curso, carrera, congreso, concepto):
	carnet = str(carnet)
	nombre = str(nombre)
	carrera = str(carrera)
	congreso = str(congreso)
	curso = str(curso).upper()
	cursos = curso.split(',')
	cantidad = len(cursos)
	concepto = str(concepto)
	for i in range(cantidad):
		try:
			cursos[i] = str(cursos[i].split("'")[1])
		except:
			pass
	if request.method == "POST":
		try:
			conexion = pymysql.connect(host=Conhost, user=Conuser, password=Conpassword, db=Condb)
			try:
				with conexion.cursor() as cursor:
					consulta1 = f'SELECT idcodigos, precio, concepto FROM codigos WHERE idcodigos = {congreso}'
					cursor.execute(consulta1)
					precios1 = cursor.fetchall()
					idpagos = []
					cadenaaux = ""
					for i in range(cantidad):
						if i != 0:
							cadenaaux = cadenaaux + ", " + str(cursos[i])
						else:
							cadenaaux = str(cursos[i])
					consulta = "INSERT INTO pagos(idcod,nombre,carnet,total,fecha,extra, recibo,user) VALUES (%s,%s,%s,%s,%s,%s,%s,%s);"
					cursor.execute(consulta, (precios1[0][0], nombre, carnet, precios1[0][1], date.today(), f"{carrera} {cadenaaux}", 0,session['idusercaja']))
					conexion.commit()
					consulta = "Select MAX(idpagos) from pagos;"
					cursor.execute(consulta)
					idpago = cursor.fetchone()
					idpago = idpago[0]
					for i in range(cantidad):
						descripcion = str(carrera) + " " + str(cursos[i])
						url = f"https://apoyoensaludyeducacion.pythonanywhere.com/guardarcongreso/{nombre}&{carnet}&{descripcion}&{idpago}"
						response = requests.get(url)
						# Verifica si la solicitud fue exitosa
						if response.status_code == 200:
							# Obtén el contenido de la página
							content = response.text
							print(content)
					idpago = int(idpago)
					idpago = str(idpago)
					number = idpago.rjust(7, '0')
					img = qrcode.make(number)
					type(img)  # qrcode.image.pil.PilImage
					ruta = PATH_FILE + f"static{mi_string}codbars{mi_string}{idpago}.png"
					img.save(ruta)
			finally:
				conexion.close()
		except (pymysql.err.OperationalError, pymysql.err.InternalError) as e:
			print("Ocurrió un error al conectar: ", e)
		return redirect(url_for('imprimir', idpagos=idpago))
	return render_template('confirmacioncongreso.html', title="Confirmación Congreso", carnet = carnet, nombre = nombre, cursos = cursos, congreso = congreso, carrera = carrera, cantidad=cantidad, concepto = concepto, logeado=session['logeadocaja'], barranav=1)

@app.route('/pag', methods=['GET', 'POST'])
@login_required
def pag():
	try:
		conexion = pymysql.connect(host=Conhost, user=Conuser, password=Conpassword, db=Condb)
		try:
			with conexion.cursor() as cursor:
				cursor.execute("SELECT idcodigos, cod, concepto, precio FROM codigos WHERE pagos = 1 ORDER BY concepto asc;")
			# Con fetchall traemos todas las filas
				carreras = cursor.fetchall()
		finally:
			conexion.close()
	except (pymysql.err.OperationalError, pymysql.err.InternalError) as e:
		print("Ocurrió un error al conectar: ", e)
	meses = ["Enero", "Febrero","Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
	if request.method == 'POST':
		datacarnet = request.form["carnet"]
		datanombre = request.form["nombre"]
		datatotal = request.form["total"]
		datadescripcion = request.form["descripcion"]
		datacarrera = request.form["carrera"]
		data = datacarrera.split(',')
		if len(datadescripcion) < 1:
			datadescripcion = data[1]
		if len(datatotal) < 1:
			datatotal = data[2]
		pid = data[0]
		pcod = data[1]
		ptotal = data[2]
		return redirect(url_for('confirmacionpag', carnet = datacarnet, nombre = datanombre, total = datatotal, descripcion= datadescripcion, pid = pid, pcod = pcod, ptotal = ptotal))
	return render_template('pag.html', title="Pagos", carreras = carreras, logeado=session['logeadocaja'], meses=meses, barranav=1)

@app.route('/confirmacionpag/<carnet>&<nombre>&<total>&<descripcion>&<pid>&<pcod>&<ptotal>', methods=['GET', 'POST'])
@login_required
def confirmacionpag(carnet, nombre, total, descripcion, pid, pcod, ptotal):
	carnet = str(carnet)
	nombre = str(nombre)
	total = float(total)
	descripcion = str(descripcion)
	pid = str(pid)
	pcod = str(pcod)
	ptotal = str(ptotal)
	if pcod != 'Pagos' and pcod != 'Curso Dirigido':
		total = float(ptotal)
		descripcion = pcod
	if request.method == "POST":
		try:
			conexion = pymysql.connect(host=Conhost, user=Conuser, password=Conpassword, db=Condb)
			try:
				with conexion.cursor() as cursor:
					consulta = "INSERT INTO pagos(idcod,nombre,carnet,total,fecha,extra, recibo,user) VALUES (%s,%s,%s,%s,%s,%s,%s,%s);"
					cursor.execute(consulta, (pid, nombre, carnet, total, date.today(), descripcion, 0,session['idusercaja']))
				conexion.commit()
			finally:
				conexion.close()
		except (pymysql.err.OperationalError, pymysql.err.InternalError) as e:
			print("Ocurrió un error al conectar: ", e)
		return redirect(url_for('pag'))
	return render_template('confirmacionpag.html', title="Confirmación", carnet = carnet, nombre = nombre, total=total, descripcion=descripcion, pid = pid, pcod = pcod,ptotal = ptotal, logeado=session['logeadocaja'], barranav=1)

@app.route('/grad', methods=['GET', 'POST'])
@login_required
def grad():
	if request.method == 'POST':
		datacarnet = request.form["carnet"]
		datanombre = request.form["nombre"]
		datatipo = request.form["tipo"]
		if int(datatipo) == 3:
			datacant = request.form["cantalmuerzos"]
		else:
			datacant = 0
		return redirect(url_for('confirmaciongrad', tipo = datatipo, carnet = datacarnet, nombre = datanombre, cant = datacant))
	return render_template('graduacion.html', title="Graduación", logeado=session['logeadocaja'], barranav=1)

@app.route('/confirmaciongrad/<tipo>&<carnet>&<nombre>&<cant>', methods=['GET', 'POST'])
@login_required
def confirmaciongrad(tipo, carnet, nombre, cant):
	tipo = int(tipo)
	cant = int(cant)
	carnet = str(carnet)
	nombre = str(nombre)
	if request.method == "POST":
		try:
			conexion = pymysql.connect(host=Conhost, user=Conuser, password=Conpassword, db=Condb)
			try:
				with conexion.cursor() as cursor:
					if tipo == 1:
						consulta1 = 'SELECT idcodigos, precio FROM codigos WHERE cod = "GRADT"'
						cursor.execute(consulta1)
						precios1 = cursor.fetchall()
						consulta = "INSERT INTO pagos(idcod,nombre,carnet,total,fecha,extra, recibo,user) VALUES (%s,%s,%s,%s,%s,%s,%s,%s);"
						cursor.execute(consulta, (precios1[0][0], nombre, carnet, precios1[0][1], date.today(), "",0,session['idusercaja']))
						conexion.commit()
					elif tipo == 2:
						consulta1 = 'SELECT idcodigos, precio FROM codigos WHERE cod = "GRADL"'
						cursor.execute(consulta1)
						precios1 = cursor.fetchall()
						consulta = "INSERT INTO pagos(idcod,nombre,carnet,total,fecha,extra, recibo,user) VALUES (%s,%s,%s,%s,%s,%s,%s,%s);"
						cursor.execute(consulta, (precios1[0][0], nombre, carnet, precios1[0][1], date.today(), "",0,session['idusercaja']))
						conexion.commit()
					elif tipo == 3:
						consulta1 = 'SELECT idcodigos, precio FROM codigos WHERE cod = "GRADAUXENF"'
						cursor.execute(consulta1)
						precios1 = cursor.fetchall()
						consulta = "INSERT INTO pagos(idcod,nombre,carnet,total,fecha,extra, recibo,user) VALUES (%s,%s,%s,%s,%s,%s,%s,%s);"
						cursor.execute(consulta, (precios1[0][0], nombre, carnet, precios1[0][1], date.today(), "",0,session['idusercaja']))
						conexion.commit()
						if cant > 0:
							consulta1 = 'SELECT idcodigos, precio FROM codigos WHERE cod = "ALGRAAUXENF"'
							cursor.execute(consulta1)
							precios1 = cursor.fetchall()
							totalalmuerzos = cant * float(precios1[0][1])
							aux = str(cant) + " almuerzos."
							consulta = "INSERT INTO pagos(idcod,nombre,carnet,total,fecha,extra, recibo,user) VALUES (%s,%s,%s,%s,%s,%s,%s,%s);"
							cursor.execute(consulta, (precios1[0][0], nombre, carnet,totalalmuerzos, date.today(), aux,0,session['idusercaja']))
							conexion.commit()
							consulta = "Select MAX(idpagos) from pagos;"
							cursor.execute(consulta)
							idpago = cursor.fetchone()
							idpago = idpago[0]
			finally:
				conexion.close()
		except (pymysql.err.OperationalError, pymysql.err.InternalError) as e:
			print("Ocurrió un error al conectar: ", e)
		if tipo == 3:
			return redirect(url_for('imprimir', idpagos=idpago))
		else:
			return redirect(url_for('grad'))
	return render_template('confirmaciongrad.html', title="Confirmación", nombre = nombre, carnet = carnet, tipo = tipo, logeado=session['logeadocaja'], cant = cant, barranav=1)

@app.route('/reportes', methods=['GET', 'POST'])
@login_required
def reportes():
	try:
		conexion = pymysql.connect(host=Conhost, user=Conuser, password=Conpassword, db=Condb)
		try:
			with conexion.cursor() as cursor:
				consulta = f'select billete1, billete5, billete10, billete20, billete50, billete100, billete200, vales, tarjeta, idefectivo from efectivo where fecha = CURDATE() and iduser = {session["idusercaja"]};'
				cursor.execute(consulta)
				efectivo = cursor.fetchall()
				if len(efectivo) > 0:
					efectivo = efectivo[0]
				else:
					consulta = f'INSERT INTO efectivo(billete1, billete5, billete10, billete20, billete50, billete100, billete200, vales, tarjeta, fecha, iduser) values (0,0,0,0,0,0,0,0,0,CURDATE(),{session["idusercaja"]});'
					cursor.execute(consulta)
					conexion.commit()
					consulta = f'select billete1, billete5, billete10, billete20, billete50, billete100, billete200, vales, tarjeta, idefectivo from efectivo where fecha = CURDATE() and iduser = {session["idusercaja"]};'
					cursor.execute(consulta)
					efectivo = cursor.fetchone()
				consulta = f'SELECT SUM(monto), count(monto) FROM factura WHERE fecha = CURDATE() and usuario = {session["idusercaja"]};'
				cursor.execute(consulta)
				facturas = cursor.fetchone()
				if int(facturas[1]) > 0:
					facturas = float(facturas[0])
				else:
					facturas = 0
				consulta = f'SELECT c.cod, c.concepto, count(p.total), round(sum(p.total),2) FROM pagos p INNER JOIN codigos c ON p.idcod = c.idcodigos WHERE fecha = CURDATE() and p.recibo = 0 and p.user = {session["idusercaja"]} group by c.cod order by c.cod asc, p.nombre asc;'
				cursor.execute(consulta)
				sumas = cursor.fetchall()
				sumtotal = 0
				for i in sumas:
					sumtotal = sumtotal + float(i[3])
				consulta = f'SELECT p.fechadevuelto, c.cod, c.concepto, round(p.total,2) FROM pagos p INNER JOIN codigos c ON p.idcod = c.idcodigos WHERE fechadevuelto = CURDATE() order by c.cod asc, p.nombre asc;'
				cursor.execute(consulta)
				datadev = cursor.fetchall()
				totaldev = 0
				for i in datadev:
					totaldev = totaldev + float(i[3])
				totaldev = round(totaldev, 2)
				totaltotal = sumtotal - totaldev
		finally:
			conexion.close()
	except (pymysql.err.OperationalError, pymysql.err.InternalError) as e:
		print("Ocurrió un error al conectar: ", e)
	if request.method == "POST":
		q1 = request.form['Q1']
		q5 = request.form['Q5']
		q10 = request.form['Q10']
		q20 = request.form['Q20']
		q50 = request.form['Q50']
		q100 = request.form['Q100']
		q200 = request.form['Q200']
		facturas = request.form['facturas']
		vales = request.form['vales']
		tarjeta = request.form['tarjeta']
		if len(q1) < 1:
			q1 = 0
		if len(q5) < 1:
			q5 = 0
		if len(q10) < 1:
			q10 = 0
		if len(q20) < 1:
			q20 = 0
		if len(q50) < 1:
			q50 = 0
		if len(q100) < 1:
			q100 = 0
		if len(q200) < 1:
			q200 = 0
		if len(facturas) < 1:
			facturas = 0
		if len(vales) < 1:
			vales = 0
		if len(tarjeta) < 1:
			tarjeta = 0
		try:
			conexion = pymysql.connect(host=Conhost, user=Conuser, password=Conpassword, db=Condb)
			try:
				with conexion.cursor() as cursor:
					consulta = "UPDATE efectivo set billete1=%s, billete5=%s, billete10=%s, billete20=%s, billete50=%s, billete100=%s, billete200=%s, facturas=%s, vales=%s, tarjeta=%s where idefectivo = %s and iduser = %s;"
					cursor.execute(consulta, (q1, q5, q10, q20, q50, q100, q200, facturas, vales, tarjeta, efectivo[9], session['idusercaja']))
				conexion.commit()
			finally:
				conexion.close()
		except (pymysql.err.OperationalError, pymysql.err.InternalError) as e:
			print("Ocurrió un error al conectar: ", e)
		return redirect(url_for('reportes'))
	return render_template('reportes.html', title="Reportes", sumas = sumas, sumtotal=sumtotal, logeado=session['logeadocaja'], datadev=datadev, totaldev=totaldev, totaltotal=totaltotal, efectivo=efectivo, facturas = facturas, barranav=2)

@app.route('/unificarcajas')
@login_required
def unificarcajas():
	try:
		conexion = pymysql.connect(host=Conhost, user=Conuser, password=Conpassword, db=Condb)
		try:
			with conexion.cursor() as cursor:
				consulta = 'update pagos set user = %s where fecha = CURDATE()'
				cursor.execute(consulta, session['idusercaja'])
				consulta = 'update factura set usuario = %s where fecha = CURDATE()'
				cursor.execute(consulta, session['idusercaja'])
				consulta = 'update efectivo set billete1 = 0, billete5 = 0, billete10 = 0, billete20 = 0, billete50 = 0, billete100 = 0, billete200 = 0, facturas = 0, vales = 0, tarjeta = 0 where fecha = CURDATE() and iduser != %s'
				cursor.execute(consulta, session['idusercaja'])
			conexion.commit()
		finally:
			conexion.close()
	except (pymysql.err.OperationalError, pymysql.err.InternalError) as e:
		print("Ocurrió un error al conectar: ", e)
	return redirect(url_for('reportes'))

@app.route('/nuevafactura', methods=['GET', 'POST'])
@login_required
def nuevafactura():
	factura = ["","","",""]
	if request.method == 'POST':
		documento = request.form["documento"]
		proveedor = request.form["proveedor"]
		descripcion = request.form["descripcion"]
		monto = request.form["monto"]
		try:
			conexion = pymysql.connect(host=Conhost, user=Conuser, password=Conpassword, db=Condb)
			try:
				with conexion.cursor() as cursor:
					consulta = 'INSERT INTO factura(documento, proveedor, descripcion, monto, fecha, usuario) values(%s,%s,%s,%s,CURDATE(),%s)'
					cursor.execute(consulta, (documento, proveedor, descripcion, monto, session['idusercaja']))
				conexion.commit()
			finally:
				conexion.close()
		except (pymysql.err.OperationalError, pymysql.err.InternalError) as e:
			print("Ocurrió un error al conectar: ", e)
		return redirect(url_for('reportes'))
	return render_template('nuevafactura.html', title="Ingresar Factura", logeado=session['logeadocaja'], nuevo=1, factura=factura, barranav=2)

@app.route('/editarfactura/<idfactura>', methods=['GET', 'POST'])
@login_required
def editarfactura(idfactura):
	try:
		conexion = pymysql.connect(host=Conhost, user=Conuser, password=Conpassword, db=Condb)
		try:
			with conexion.cursor() as cursor:
				consulta = f'SELECT documento, proveedor, descripcion, monto from factura where idfactura = {idfactura};'
				cursor.execute(consulta)
				factura = cursor.fetchone()
		finally:
			conexion.close()
	except (pymysql.err.OperationalError, pymysql.err.InternalError) as e:
		print("Ocurrió un error al conectar: ", e)
	if request.method == 'POST':
		documento = request.form["documento"]
		proveedor = request.form["proveedor"]
		descripcion = request.form["descripcion"]
		monto = request.form["monto"]
		try:
			conexion = pymysql.connect(host=Conhost, user=Conuser, password=Conpassword, db=Condb)
			try:
				with conexion.cursor() as cursor:
					consulta = f'update factura set documento = "{documento}", proveedor = "{proveedor}", descripcion = "{descripcion}", monto = {monto}, usuario = {session["idusercaja"]} where idfactura = {idfactura}'
					cursor.execute(consulta)
				conexion.commit()
			finally:
				conexion.close()
		except (pymysql.err.OperationalError, pymysql.err.InternalError) as e:
			print("Ocurrió un error al conectar: ", e)
		return redirect(url_for('reportes'))
	return render_template('nuevafactura.html', title="Editar Factura", logeado=session['logeadocaja'], nuevo=0, factura=factura, barranav=2)

@app.route("/eliminarfactura/<idfactura>", methods=['GET', 'POST'])
@login_required
def eliminarfactura(idfactura):
	try:
		conexion = pymysql.connect(host=Conhost, user=Conuser, password=Conpassword, db=Condb)
		try:
			with conexion.cursor() as cursor:
				consulta = f'DELETE from factura where idfactura = {idfactura};'
				cursor.execute(consulta)
				conexion.commit()
		finally:
			conexion.close()
	except (pymysql.err.OperationalError, pymysql.err.InternalError) as e:
		print("Ocurrió un error al conectar: ", e)
	return redirect(url_for('repdiario'))

@app.route('/repdiario', methods=['GET', 'POST'])
@login_required
def repdiario():
	try:
		conexion = pymysql.connect(host=Conhost, user=Conuser, password=Conpassword, db=Condb)
		try:
			with conexion.cursor() as cursor:
				consulta = 'SELECT c.cod, c.concepto, count(p.total), round(sum(p.total),2), c.idcodigos FROM pagos p INNER JOIN codigos c ON p.idcod = c.idcodigos WHERE fecha = CURDATE() and p.recibo = 0 group by c.cod order by c.cod asc, p.nombre asc;'
				cursor.execute(consulta)
				resumen = cursor.fetchall()
				consulta = "select f.documento, f.proveedor, f.descripcion, f.monto, u.iniciales, f.idfactura from factura f inner join user u on f.usuario = u.iduser where f.fecha = CURDATE();"
				cursor.execute(consulta)
				facturas = cursor.fetchall()
				consulta = "Select fecha from pagos where recibo <> 0 and LENGTH(recibo) < 5 order by fecha desc"
				cursor.execute(consulta)
				fechasig = cursor.fetchone()
				fechasig = fechasig[0]
				consulta = f'select recibo from pagos where length(recibo) < 5 and fecha = "{fechasig}" order by (recibo * 1) desc;'
				cursor.execute(consulta)
				boletasig = cursor.fetchone()
				boletasig = boletasig[0]
				consulta = 'SELECT p.nombre, p.carnet, p.fecha, c.concepto, p.extra, round(p.total,2), p.idpagos, u.iniciales FROM pagos p INNER JOIN codigos c ON p.idcod = c.idcodigos inner join user u on u.iduser = p.user WHERE fecha = CURDATE() and p.recibo = 0 order by c.cod asc, p.nombre asc;'
				cursor.execute(consulta)
			# Con fetchall traemos todas las filas
				data = cursor.fetchall()
				suma = 0
				for i in data:
					suma = suma + i[5]
				consulta = 'SELECT p.fechadevuelto, c.cod, c.concepto, round(p.total,2) FROM pagos p INNER JOIN codigos c ON p.idcod = c.idcodigos WHERE fechadevuelto = CURDATE() order by c.cod asc, p.nombre asc;'
				cursor.execute(consulta)
				datadev = cursor.fetchall()
		finally:
			conexion.close()
	except (pymysql.err.OperationalError, pymysql.err.InternalError) as e:
		print("Ocurrió un error al conectar: ", e)
	if request.method == 'POST':
		try:
			conexion = pymysql.connect(host=Conhost, user=Conuser, password=Conpassword, db=Condb)
			try:
				with conexion.cursor() as cursor:
					regen = request.form["regen"]
					if regen == '0' or len(regen) < 1:
						for i in resumen:
							aux = f"resumen{i[4]}"
							varaux = str(request.form[aux])
							if len(varaux) > 0:
								aux = f"empresa{i[4]}"
								empresa = request.form[aux]
								consulta = f'UPDATE pagos SET recibo = "{varaux}", empresa = "{empresa}" WHERE idcod = {i[4]} and fecha = CURDATE() and recibo = 0;'
								cursor.execute(consulta)
						for i in data:
							aux = f"re{i[6]}"
							varaux = str(request.form[aux])
							if len(varaux) > 0:
								aux = f"empr{i[6]}"
								empresa = request.form[aux]
								consulta = f'UPDATE pagos SET recibo = "{varaux}", empresa = "{empresa}" WHERE idpagos = {i[6]};'
								cursor.execute(consulta)
					else:
						empresa = request.form["empresagen"]
						for i in data:
							consulta = f'UPDATE pagos SET recibo = "{regen}", empresa = "{empresa}" WHERE idpagos = {i[6]};'
							cursor.execute(consulta)
				conexion.commit()
			finally:
				conexion.close()
		except (pymysql.err.OperationalError, pymysql.err.InternalError) as e:
			print("Ocurrió un error al conectar: ", e)
		return redirect(url_for('repdiario'))
	return render_template('repdiario.html', title="Reporte diario", data = data, suma=suma, logeado=session['logeadocaja'], datadev=datadev, resumen=resumen, boletasig = boletasig, facturas=facturas, barranav=2)

@app.route('/repdiariopdf', methods=['GET', 'POST'])
@login_required
def repdiariopdf():
	today = date.today()
	d1 = today.strftime("%d/%m/%Y")
	try:
		conexion = pymysql.connect(host=Conhost, user=Conuser, password=Conpassword, db=Condb)
		try:
			with conexion.cursor() as cursor:
				#suma total, suma sin optica, suma sin lab, suma sin academia, suma sin auxiliares, suma sin tarjeta opt, suma sin tarjeta lab, suma sin facturas, suma sin vales
				sumas = []
				consulta = 'SELECT p.nombre, p.carnet, DATE_FORMAT(p.fecha,"%d/%m/%Y"), c.concepto, p.extra, round(p.total,2), p.idpagos, p.recibo, u.iniciales FROM pagos p INNER JOIN codigos c ON p.idcod = c.idcodigos inner join user u on u.iduser = p.user WHERE fecha = CURDATE() order by c.cod asc, p.nombre asc;'
				cursor.execute(consulta)
				data = cursor.fetchall()
				suma = 0
				for i in data:
					suma = suma + float(i[5])
				consulta = 'SELECT p.nombre, p.carnet, DATE_FORMAT(p.fechadevuelto,"%d/%m/%Y"), c.concepto, p.extra, round(p.total, 2), p.idpagos, p.recibo, u.iniciales FROM pagos p INNER JOIN codigos c ON p.idcod = c.idcodigos inner join user u on u.iduser = p.userdev WHERE fechadevuelto = CURDATE() order by c.cod asc, p.nombre asc;'
				cursor.execute(consulta)
				datadev = cursor.fetchall()
				contdev = len(datadev)
				sumadev = 0
				for i in datadev:
					sumadev = sumadev + float(i[5])
				aux = suma - sumadev
				sumas.append(aux)
				#resumen optica, resumen lab, resumen academica, resumen auxiliares, resumen tarjeta opt, resumen tarjeta lab, resumen Dr. Juarez
				resumenes = []
				#total optica, lab, academia, auxiliares, tarjeta opt, tarjeta lab, facturas, vales, Dr Juarez
				totales = []
				#resumen optica
				consulta = 'SELECT c.cod, c.concepto, count(p.total), round(sum(p.total),2), p.recibo FROM pagos p INNER JOIN codigos c ON p.idcod = c.idcodigos WHERE p.fecha = CURDATE() and p.empresa = "Óptica" group by recibo, cod order by p.recibo asc, c.cod asc, p.nombre asc;'
				cursor.execute(consulta)
				resumenopt = cursor.fetchall()
				aux = 0
				for i in resumenopt:
					aux = aux + float(i[3])
				totales.append(aux)
				sumas.append(sumas[0] - aux)
				resumenes.append(resumenopt)
				#resumen laboratorio
				consulta = 'SELECT c.cod, c.concepto, count(p.total), round(sum(p.total),2), p.recibo FROM pagos p INNER JOIN codigos c ON p.idcod = c.idcodigos WHERE p.fecha = CURDATE() and p.empresa = "Laboratorio" group by recibo, cod order by p.recibo asc, c.cod asc, p.nombre asc;'
				cursor.execute(consulta)
				resumenlab = cursor.fetchall()
				aux = 0
				for i in resumenlab:
					aux = aux + float(i[3])
				sumas.append(sumas[1] - aux)
				totales.append(aux)
				resumenes.append(resumenlab)
				#resumen academia
				consulta = 'SELECT c.cod, c.concepto, count(p.total), round(sum(p.total),2), p.recibo FROM pagos p INNER JOIN codigos c ON p.idcod = c.idcodigos WHERE p.fecha = CURDATE() and p.empresa = "Academia" group by recibo, cod order by p.recibo asc, c.cod asc, p.nombre asc;'
				cursor.execute(consulta)
				resumenaca = cursor.fetchall()
				aux = 0
				for i in resumenaca:
					aux = aux + float(i[3])
				sumas.append(sumas[2] - aux)
				totales.append(aux)
				resumenes.append(resumenaca)
				#resumen Auxiliares de Enfermeria
				consulta = 'SELECT c.cod, c.concepto, count(p.total), round(sum(p.total),2), p.recibo FROM pagos p INNER JOIN codigos c ON p.idcod = c.idcodigos WHERE p.fecha = CURDATE() and p.empresa = "Auxiliares de Enfermeria" group by recibo, cod order by p.recibo asc, c.cod asc, p.nombre asc;'
				cursor.execute(consulta)
				resumenaux = cursor.fetchall()
				aux = 0
				for i in resumenaux:
					aux = aux + float(i[3])
				sumas.append(sumas[3] - aux)
				totales.append(aux)
				resumenes.append(resumenaux)
				#resumen Óptica Tarjeta
				consulta = 'SELECT c.cod, c.concepto, count(p.total), round(sum(p.total),2), p.recibo FROM pagos p INNER JOIN codigos c ON p.idcod = c.idcodigos WHERE p.fecha = CURDATE() and p.empresa = "Óptica Tarjeta" group by recibo, cod order by p.recibo asc, c.cod asc, p.nombre asc;'
				cursor.execute(consulta)
				resumenopttar = cursor.fetchall()
				aux = 0
				for i in resumenopttar:
					aux = aux + float(i[3])
				sumas.append(sumas[4] - aux)
				totales.append(aux)
				resumenes.append(resumenopttar)
				#resumen Laboratorio Tarjeta
				consulta = 'SELECT c.cod, c.concepto, count(p.total), round(sum(p.total),2), p.recibo FROM pagos p INNER JOIN codigos c ON p.idcod = c.idcodigos WHERE p.fecha = CURDATE() and p.empresa = "Laboratorio Tarjeta" group by recibo, cod order by p.recibo asc, c.cod asc, p.nombre asc;'
				cursor.execute(consulta)
				resumenlabtar = cursor.fetchall()
				aux = 0
				for i in resumenlabtar:
					aux = aux + float(i[3])
				sumas.append(sumas[5] - aux)
				totales.append(aux)
				resumenes.append(resumenlabtar)
				#resumen Dr. Juarez
				consulta = 'SELECT c.cod, c.concepto, count(p.total), round(sum(p.total),2), p.recibo FROM pagos p INNER JOIN codigos c ON p.idcod = c.idcodigos WHERE p.fecha = CURDATE() and p.empresa = "Dr. Rodolfo Juarez" group by recibo, cod order by p.recibo asc, c.cod asc, p.nombre asc;'
				cursor.execute(consulta)
				resumendrjuarez = cursor.fetchall()
				#facturas
				consulta = "select f.documento, f.proveedor, f.descripcion, f.monto, u.iniciales, f.idfactura from factura f inner join user u on f.usuario = u.iduser where f.fecha = CURDATE();"
				cursor.execute(consulta)
				facturas = cursor.fetchall()
				totalfacturas = 0
				for i in facturas:
					totalfacturas = totalfacturas + float(i[3])
				sumas.append(sumas[6] - totalfacturas)
				totales.append(totalfacturas)
				#vales
				consulta = 'SELECT sum(vales) from efectivo where fecha = CURDATE()'
				cursor.execute(consulta)
				vales = cursor.fetchone()
				sumas.append(sumas[7] - float(vales[0]))
				totales.append(float(vales[0]))
				#recibo Dr
				consulta = 'SELECT recibo from pagos where fecha = CURDATE() and empresa = "Dr. Rodolfo Juarez"'
				cursor.execute(consulta)
				recibodr = cursor.fetchone()
				aux = 0
				for i in resumendrjuarez:
					aux = aux + float(i[3])
				totales.append(aux)
				resumenes.append(resumendrjuarez)
		finally:
			conexion.close()
	except (pymysql.err.OperationalError, pymysql.err.InternalError) as e:
		print("Ocurrió un error al conectar: ", e)
	rendered = render_template('repdiariopdf.html', title="Reporte diario", data = data, suma=suma, datadev=datadev, sumadev=sumadev, contdev=contdev, d1=d1, resumenes = resumenes, sumas = sumas, vales = vales, facturas = facturas, recibodr = recibodr, totales = totales)
	options = {'enable-local-file-access': None, 'page-size': 'Letter','margin-right': '10mm'}
	config = pdfkit.configuration(wkhtmltopdf="C:\\Program Files\\wkhtmltopdf\\bin\\wkhtmltopdf.exe")
	pdf = pdfkit.from_string(rendered, False, configuration=config, options=options)
	response = make_response(pdf)
	response.headers['Content-Type'] = 'application/pdf'
	response.headers['Content-Disposition'] = 'inline; filename=reportediario.pdf'
	print(response)
	return response

@app.route('/matrizlenq', methods=['GET', 'POST'])
@login_required
def matrizlenq():
	fechaact = date.today()
	year = fechaact.year
	fechainicio = date(year, 1,1)
	fechafin = date(year, 12,31)
	try:
		conexion = pymysql.connect(host=Conhost, user=Conuser, password=Conpassword, db=Condb)
		try:
			with conexion.cursor() as cursor:
				practicas = []
				for i in range(6):
					consulta = f"Select carnet from practicalenq where fecha >= '{fechainicio}' and fecha <= '{fechafin}' and practica like '%{i+1})%' group by carnet order by nombre "
					cursor.execute(consulta)
			# Con fetchall traemos todas las filas
					carnets = cursor.fetchall()
					datapractica = []
					for j in carnets:
						aux = []
						aux1 = []
						for k in range(3):
							consulta = f'SELECT nombre, carnet, fecha, fechainicio, fechafin, lugar, lugar2, lugar3, idpracticalenq FROM practicalenq where carnet like "%{j[0]}%" and practica like "%{i+1})%" and practica like "%Pago {k+1}%" and fecha >= "{fechainicio}" and fecha <= "{fechafin}"'
							cursor.execute(consulta)
						# Con fetchall traemos todas las filas
							data = cursor.fetchall()
							conteo = len(data)
							if conteo > 0:
								if k == 0:
									aux.append(data[0][0])
									aux.append(data[0][1])
								else:
									aux[0] = data[0][0]
									aux[1] = data[0][1]
								aux.append(data[0][2])
								aux1.append(data[0][8])
								if k == 2:
									aux.append(data[0][3])
									aux.append(data[0][4])
									aux.append(data[0][5])
									aux.append(data[0][6])
									aux.append(data[0][7])
							else:
								if k == 0:
									aux.append("Pend")
									aux.append("Pend")
								aux.append("Pend")
								aux1.append(0)
								if k == 2:
									aux.append("Pend")
									aux.append("Pend")
									aux.append("Pend")
									aux.append("Pend")
									aux.append("Pend")
						aux.append(aux1[0])
						aux.append(aux1[1])	
						aux.append(aux1[2])
						datapractica.append(aux)
					practicas.append(datapractica)
		finally:
			conexion.close()
	except (pymysql.err.OperationalError, pymysql.err.InternalError) as e:
		print("Ocurrió un error al conectar: ", e)
	print(practicas)
	return render_template('matrizlenq.html', title="Matriz Práctica Enfermeria", logeado=session['logeadocaja'], practicas = practicas, barranav=2)

@app.route("/editarpracticalenq/<carnet>&<semestre>", methods=['GET', 'POST'])
@login_required
def editarpracticalenq(carnet, semestre):
	practicas = ["1) Práctica Hospitalaria", "2) Práctica Enfermería Preventiva", "3) Práctica Médico Quirúrgica",
			"4) Práctica Enfermería Niños y Adolescentes", "5) Práctica Materno Infantil", "6) Práctica Administrativa"]
	try:
		conexion = pymysql.connect(host=Conhost, user=Conuser, password=Conpassword, db=Condb)
		try:
			with conexion.cursor() as cursor:
				consulta = f'SELECT idpracticalenq, nombre, carnet, fechainicio, fechafin, lugar, lugar2, lugar3 from practicalenq where carnet = "{carnet}" and practica like "{semestre})%" and year(fecha) = year(CURDATE());'
				cursor.execute(consulta)
				datapractica = cursor.fetchall()
		finally:
			conexion.close()
	except (pymysql.err.OperationalError, pymysql.err.InternalError) as e:
		print("Ocurrió un error al conectar: ", e)
	if request.method == 'POST':
		carnet = request.form["carnet"]
		nombre = request.form["nombre"]
		fechainicio = request.form["fechainicio"]
		fechafin = request.form["fechafin"]
		lugar1 = request.form["lugar1"]
		lugar2 = request.form["lugar2"]
		lugar3 = request.form["lugar3"]

		try:
			conexion = pymysql.connect(host=Conhost, user=Conuser, password=Conpassword, db=Condb)
			try:
				with conexion.cursor() as cursor:
					for i in datapractica:
						consulta = 'UPDATE practicalenq set nombre=%s, carnet=%s, fechainicio=%s, fechafin=%s, lugar=%s, lugar2=%s, lugar3=%s where idpracticalenq=%s;'
						cursor.execute(consulta, (nombre, carnet, fechainicio, fechafin, lugar1, lugar2, lugar3, i[0]))
				conexion.commit()
			finally:
				conexion.close()
		except (pymysql.err.OperationalError, pymysql.err.InternalError) as e:
			print("Ocurrió un error al conectar: ", e)
		return redirect(url_for('matrizlenq'))
	return render_template('editarpracticalenq.html', title='Editar Datos de Práctica Enfermeria', logeado=session['logeadocaja'], datapractica=datapractica, practicas=practicas, semestre=semestre, barranav=2)

@app.route('/matriztlcq', methods=['GET', 'POST'])
@login_required
def matriztlcq():
	fechaact = date.today()
	year = fechaact.year
	fechainicio = date(year, 1,1)
	fechafin = date(year, 12,31)
	meses = ["Enero", "Febrero","Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
	try:
		conexion = pymysql.connect(host=Conhost, user=Conuser, password=Conpassword, db=Condb)
		try:
			with conexion.cursor() as cursor:
				estudiantes = []
				consulta = f"Select p.carnet from pagos p inner join codigos c on p.idcod = c.idcodigos where p.fecha >= '{fechainicio}' and p.fecha <= '{fechafin}' and c.concepto like '%Practica TLCQ%' group by p.carnet order by p.nombre"
				cursor.execute(consulta)
		# Con fetchall traemos todas las filas
				carnets = cursor.fetchall()
				for i in carnets:
					aux = ["",""]
					for j in meses:
						consulta = f"SELECT nombre, carnet, DATE_FORMAT(p.fecha,'%d/%m/%Y') FROM pagos p inner join codigos c on p.idcod = c.idcodigos where p.fecha >= '{fechainicio}' and p.fecha <= '{fechafin}' and c.concepto like '%Practica TLCQ%' and p.extra like '%{j}%' and p.carnet like'%{i[0]}%' group by p.carnet order by p.nombre"
						cursor.execute(consulta)
					# Con fetchall traemos todas las filas
						data = cursor.fetchall()
						conteo = len(data)
						if conteo > 0:
							aux[0] = data[0][0]
							aux[1] = data[0][1]
							aux.append(data[0][2])
						else:
							aux.append("Pend")
					estudiantes.append(aux)
		finally:
			conexion.close()
	except (pymysql.err.OperationalError, pymysql.err.InternalError) as e:
		print("Ocurrió un error al conectar: ", e)
	return render_template('matriztlcq.html', title="Matriz Práctica Laboratorio Clinico", logeado=session['logeadocaja'], estudiantes = estudiantes, meses = meses, barranav=2)

@app.route('/matrizthdq', methods=['GET', 'POST'])
@login_required
def matrizthdq():
	fechaact = date.today()
	year = fechaact.year - 1
	month = fechaact.month
	day = fechaact.day
	fechainicio = date(year, month, day)
	try:
		conexion = pymysql.connect(host=Conhost, user=Conuser, password=Conpassword, db=Condb)
		try:
			with conexion.cursor() as cursor:
				estudiantes = []
				consulta = f"SELECT p.carnet from pagos p inner join codigos c on c.idcodigos = p.idcod where p.fecha >= '{fechainicio}' and (c.concepto like '%Practica THDQ%' or c.concepto like '%Practica Dialisis Peritoneal%') group by p.carnet order by p.nombre"
				cursor.execute(consulta)
		# Con fetchall traemos todas las filas
				carnets = cursor.fetchall()
				for i in carnets:
					aux = []
					consulta = f"SELECT nombre from pagos where carnet = '{i[0]}' order by fecha desc limit 1"
					cursor.execute(consulta)
					nombre = cursor.fetchone()
					aux.append(nombre[0])
					aux.append(i[0])
					consulta = f"SELECT DATE_FORMAT(p.fecha,'%d/%m/%Y') from pagos p inner join codigos c on c.idcodigos = p.idcod where carnet = '{i[0]}' and c.concepto like '%Practica THDQ%' order by p.fecha desc limit 1"
					cursor.execute(consulta)
					fecha1 = cursor.fetchone()
					try:
						if len(fecha1) < 1:
							fecha1 = "Pend"
						else:
							fecha1 = fecha1[0]
					except:
						fecha1 = "Pend"
					consulta = f"SELECT DATE_FORMAT(p.fecha,'%d/%m/%Y') from pagos p inner join codigos c on c.idcodigos = p.idcod where carnet = '{i[0]}' and c.concepto like '%Practica Dialisis%' order by p.fecha desc limit 1"
					cursor.execute(consulta)
					fecha2 = cursor.fetchone()
					try:
						if len(fecha2) < 1:
							fecha2 = "Pend"
						else:
							fecha2 = fecha2[0]
					except:
						fecha2 = "Pend"
					aux.append(fecha1)
					aux.append(fecha2)
					estudiantes.append(aux)
		finally:
			conexion.close()
	except (pymysql.err.OperationalError, pymysql.err.InternalError) as e:
		print("Ocurrió un error al conectar: ", e)
	return render_template('matrizthdq.html', title="Matriz Práctica Hemodiálisis", logeado=session['logeadocaja'], estudiantes = estudiantes, barranav=2)

@app.route('/matrizlbcq', methods=['GET', 'POST'])
@login_required
def matrizlbcq():
	fechaact = date.today()
	year = fechaact.year
	fechainicio = date(year, 1,1)
	fechafin = date(year, 12,31)
	meses = ["Enero", "Febrero","Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
	try:
		conexion = pymysql.connect(host=Conhost, user=Conuser, password=Conpassword, db=Condb)
		try:
			with conexion.cursor() as cursor:
				estudiantes = []
				consulta = f"Select p.carnet from practicalbcq p inner join codigos c on c.idcodigos = p.idcodigo where p.fecha >= '{fechainicio}' and p.fecha <= '{fechafin}' and c.concepto not like '%EPS%' group by p.carnet order by p.nombre"
				cursor.execute(consulta)
		# Con fetchall traemos todas las filas
				carnets = cursor.fetchall()
				for i in carnets:
					aux = ["",""]
					for j in meses:
						consulta = f"SELECT p.nombre, p.carnet, DATE_FORMAT(p.fecha,'%d/%m/%Y') FROM practicalbcq p inner join codigos c on c.idcodigos = p.idcodigo where p.fecha >= '{fechainicio}' and p.fecha <= '{fechafin}' and p.descripcion like '%{j}%' and p.carnet like'%{i[0]}%' and c.concepto not like '%EPS%' group by p.carnet order by p.nombre"
						cursor.execute(consulta)
					# Con fetchall traemos todas las filas
						data = cursor.fetchall()
						conteo = len(data)
						if conteo > 0:
							aux[0] = data[0][0]
							aux[1] = data[0][1]
							aux.append(data[0][2])
						else:
							aux.append("Pend")
					estudiantes.append(aux)
				estudianteseps = []
				consulta = f"Select p.carnet from practicalbcq p inner join codigos c on c.idcodigos = p.idcodigo where p.fecha >= '{fechainicio}' and p.fecha <= '{fechafin}' and c.concepto like '%EPS%' group by carnet order by nombre"
				cursor.execute(consulta)
		# Con fetchall traemos todas las filas
				carnets = cursor.fetchall()
				for i in carnets:
					aux = ["",""]
					for j in meses:
						consulta = f"SELECT p.nombre, p.carnet, DATE_FORMAT(p.fecha,'%d/%m/%Y') FROM practicalbcq p inner join codigos c on c.idcodigos = p.idcodigo where p.fecha >= '{fechainicio}' and p.fecha <= '{fechafin}' and p.descripcion like '%{j}%' and p.carnet like'%{i[0]}%' and c.concepto like '%EPS%' group by p.carnet order by p.nombre"
						cursor.execute(consulta)
					# Con fetchall traemos todas las filas
						data = cursor.fetchall()
						conteo = len(data)
						if conteo > 0:
							aux[0] = data[0][0]
							aux[1] = data[0][1]
							aux.append(data[0][2])
						else:
							aux.append("Pend")
					estudianteseps.append(aux)
		finally:
			conexion.close()
	except (pymysql.err.OperationalError, pymysql.err.InternalError) as e:
		print("Ocurrió un error al conectar: ", e)
	return render_template('matrizlbcq.html', title="Matriz Práctica Química Biológica", logeado=session['logeadocaja'], estudiantes = estudiantes, estudianteseps = estudianteseps, meses = meses, barranav=2)

@app.route('/matriztradq', methods=['GET', 'POST'])
@login_required
def matriztradq():
	fechaact = date.today()
	year = fechaact.year
	fechainicio = date(year, 1,1)
	fechafin = date(year, 12,31)
	try:
		conexion = pymysql.connect(host=Conhost, user=Conuser, password=Conpassword, db=Condb)
		try:
			with conexion.cursor() as cursor:
				estudiantes = []
				consulta = f"Select p.carnet from pagos p inner join codigos c on p.idcod = c.idcodigos where p.fecha >= '{fechainicio}' and p.fecha <= '{fechafin}' and c.concepto like '%prepractica TRADQ%' group by p.carnet order by p.nombre"
				cursor.execute(consulta)
		# Con fetchall traemos todas las filas
				carnets = cursor.fetchall()
				for i in carnets:
					aux = ["",""]
					for j in range(1,5):
						consulta = f"SELECT p.nombre, p.carnet, DATE_FORMAT(p.fecha,'%d/%m/%Y') FROM pagos p inner join codigos c on p.idcod = c.idcodigos where p.fecha >= '{fechainicio}' and p.fecha <= '{fechafin}' and c.concepto like '%prepractica TRADQ%' and p.extra like '%{j}%' and p.carnet like'%{i[0]}%' group by p.carnet order by p.nombre"
						cursor.execute(consulta)
					# Con fetchall traemos todas las filas
						data = cursor.fetchall()
						conteo = len(data)
						if conteo > 0:
							aux[0] = data[0][0]
							aux[1] = data[0][1]
							aux.append(data[0][2])
						else:
							aux.append("Pend")
					estudiantes.append(aux)
				estudiantes1 = []
				consulta = f"SELECT p.nombre, p.carnet, DATE_FORMAT(p.fecha,'%d/%m/%Y') FROM pagos p inner join codigos c on p.idcod = c.idcodigos where p.fecha >= '{fechainicio}' and p.fecha <= '{fechafin}' and c.concepto like 'Practica TRADQ%' group by p.carnet order by p.nombre"
				cursor.execute(consulta)
			# Con fetchall traemos todas las filas
				estudiantes1 = cursor.fetchall()
		finally:
			conexion.close()
	except (pymysql.err.OperationalError, pymysql.err.InternalError) as e:
		print("Ocurrió un error al conectar: ", e)
	return render_template('matriztradq.html', title="Matriz Práctica Radiologia", logeado=session['logeadocaja'], estudiantes = estudiantes, estudiantes1 = estudiantes1, barranav=2)

@app.route('/replenq', methods=['GET', 'POST'])
@login_required
def replenq():
	data = []
	conteo = 0
	datacarnet = ""
	datafechapagoinicio = ""
	datafechapagofin = ""
	datafechaini = ""
	datafechafin = ""
	datanombre = ""
	datadescripcion = ""
	if request.method == "POST":
		datacarnet = request.form["carnet"]
		datanombre = request.form["nombre"]
		datafechaini = request.form["fechaini"]
		datafechafin = request.form["fechafin"]
		datalugar = request.form["lugar"]
		datadescripcion = request.form["descripcion"]
		datafechapagoinicio = request.form["fechapagoinicio"]
		datafechapagofin = request.form["fechapagofin"]
		try:
			conexion = pymysql.connect(host=Conhost, user=Conuser, password=Conpassword, db=Condb)
			try:
				with conexion.cursor() as cursor:
					consulta = f'SELECT nombre, carnet, fecha, practica, lugar, fechainicio, fechafin, idpracticalenq FROM practicalenq where nombre like "%{datanombre}%" and carnet like "%{datacarnet}%"'
					if len(datafechaini) != 0:
						consulta = consulta + f' and fechainicio = "{datafechaini}"'
					if len(datafechafin) != 0:
						consulta = consulta + f' and fechafin = "{datafechafin}"'
					if len(datafechapagoinicio) != 0:
						consulta = consulta + f' and fecha >= "{datafechapagoinicio}"'
					if len(datafechapagofin) != 0:
						consulta = consulta + f' and fecha <= "{datafechapagofin}"'
					consulta = consulta + f' and lugar like "%{datalugar}%" and practica like "%{datadescripcion}%" order by fecha desc, practica asc, nombre asc;'
					cursor.execute(consulta)
				# Con fetchall traemos todas las filas
					data = cursor.fetchall()
					conteo = len(data)
			finally:
				conexion.close()
		except (pymysql.err.OperationalError, pymysql.err.InternalError) as e:
			print("Ocurrió un error al conectar: ", e)
		return render_template('replenq.html', title="Reporte Práctica Enfermeria", data = data, logeado=session['logeadocaja'], conteo=conteo, datacarnet = datacarnet, datanombre = datanombre, datafechaini = datafechaini, datafechafin = datafechafin, datafechapagoinicio = datafechapagoinicio, datadescripcion = datadescripcion, datafechapagofin = datafechapagofin, barranav=2)
	return render_template('replenq.html', title="Reporte Práctica Enfermeria", data = data, logeado=session['logeadocaja'], conteo=conteo, datacarnet = datacarnet, datanombre = datanombre, datafechaini = datafechaini, datafechafin = datafechafin, datafechapagoinicio = datafechapagoinicio, datadescripcion = datadescripcion, datafechapagofin = datafechapagofin, barranav=2)

@app.route('/replbcq', methods=['GET', 'POST'])
@login_required
def replbcq():
	data = []
	conteo = 0
	datacarnet = ""
	datafechapago = ""
	datanombre = ""
	datadescripcion = ""
	dataconcepto = ""
	if request.method == "POST":
		datacarnet = request.form["carnet"]
		datanombre = request.form["nombre"]
		datadescripcion = request.form["descripcion"]
		datafechapago = request.form["fechapago"]
		dataconcepto = request.form["concepto"]
		try:
			conexion = pymysql.connect(host=Conhost, user=Conuser, password=Conpassword, db=Condb)
			try:
				with conexion.cursor() as cursor:
					consulta = f'SELECT q.nombre, q.carnet, q.fecha, q.descripcion, q.idpracticalbcq, c.concepto FROM practicalbcq q inner join codigos c on q.idcodigo = c.idcodigos where q.nombre like "%{datanombre}%" and q.carnet like "%{datacarnet}%"'
					if len(datafechapago) != 0:
						consulta = consulta + f' and q.fecha = "{datafechapago}"'
					consulta = consulta + f' and q.descripcion like "%{datadescripcion}%" and c.concepto like "%{dataconcepto}%" order by fecha desc, nombre asc;'
					cursor.execute(consulta)
				# Con fetchall traemos todas las filas
					data = cursor.fetchall()
					conteo = len(data)
			finally:
				conexion.close()
		except (pymysql.err.OperationalError, pymysql.err.InternalError) as e:
			print("Ocurrió un error al conectar: ", e)
		return render_template('replbcq.html', title="Reporte Práctica Química Biológica", data = data, logeado=session['logeadocaja'], conteo=conteo, datacarnet = datacarnet, datanombre = datanombre, datafechapago = datafechapago, datadescripcion = datadescripcion, barranav=2)
	return render_template('replbcq.html', title="Reporte Práctica  Química Biológica", data = data, logeado=session['logeadocaja'], conteo=conteo, datacarnet = datacarnet, datanombre = datanombre, datafechapago = datafechapago, datadescripcion = datadescripcion, barranav=2)

@app.route('/repgen', methods=['GET', 'POST'])
@login_required
def repgen():
	data = []
	conteo = 0
	datacarnet = ""
	dataconcepto = ""
	datafechaini = ""
	datafechafin = ""
	datanombre = ""
	datadescripcion = ""
	datarecibo = ""
	dataempresa = ""
	accion = 0
	if request.method == "POST":
		datacarnet = request.form["carnet"]
		datanombre = request.form["nombre"]
		datanombre = datanombre.replace(" ", "%")
		datafechaini = request.form["fechaini"]
		datafechafin = request.form["fechafin"]
		dataconcepto = request.form["concepto"]
		datadescripcion = request.form["descripcion"]
		datarecibo = request.form["recibo"]
		dataempresa = request.form["empresa"]
		accion = request.form["accion"]
		try:
			conexion = pymysql.connect(host=Conhost, user=Conuser, password=Conpassword, db=Condb)
			try:
				with conexion.cursor() as cursor:
					consulta = f'SELECT p.nombre, p.carnet, DATE_FORMAT(p.fecha,"%d/%m/%Y"), c.concepto, p.extra, p.recibo, p.total, p.idpagos, p.devuelto, p.empresa FROM pagos p INNER JOIN codigos c ON p.idcod = c.idcodigos where p.nombre like "%{datanombre}%" and p.carnet like "%{datacarnet}%"'
					if len(datafechaini) != 0:
						consulta = consulta + f' and p.fecha >= "{datafechaini}"'
					if len(datafechafin) != 0:
						consulta = consulta + f' and p.fecha <= "{datafechafin}"'
					consulta = consulta + f' and c.concepto like "%{dataconcepto}%" and p.extra like "%{datadescripcion}%" and p.recibo like "%{datarecibo}%" and p.empresa like "%{dataempresa}%" order by p.fecha desc, c.concepto asc, p.extra asc, p.nombre asc;'
					cursor.execute(consulta)
				# Con fetchall traemos todas las filas
					data = cursor.fetchall()
					conteo = len(data)
			finally:
				conexion.close()
		except (pymysql.err.OperationalError, pymysql.err.InternalError) as e:
			print("Ocurrió un error al conectar: ", e)
		if int(accion) == 1:
			return render_template('repgen.html', title="Reporte general", data=data, logeado=session['logeadocaja'], conteo=conteo, datacarnet=datacarnet, datanombre=datanombre, datafechaini=datafechaini, datafechafin=datafechafin, dataconcepto=dataconcepto, datadescripcion=datadescripcion, datarecibo=datarecibo, dataempresa=dataempresa, barranav=2)
		elif int(accion) == 2:
			output = io.BytesIO()
			workbook = xlwt.Workbook(encoding="utf-8")
			sh1 = workbook.add_sheet("Reporte General")

			xlwt.add_palette_colour("Orange", 0x21) # the second argument must be a number between 8 and 64
			workbook.set_colour_RGB(0x21, 255, 165, 0) # Red — 79, Green — 129, Blue — 189
			xlwt.add_palette_colour("Lightgreen", 0x22) # the second argument must be a number between 8 and 64
			workbook.set_colour_RGB(0x22, 144, 238, 144) # Red — 79, Green — 129, Blue — 189
			
			#bordes
			borders = xlwt.Borders()
			borders.left = 1
			borders.right = 1
			borders.top = 1
			borders.bottom = 1

			#encabezados
			header_font = xlwt.Font()
			header_font.name = 'Arial'
			header_font.bold = True
			header_style = xlwt.XFStyle()
			header_style.font = header_font
			header_style.borders = borders

			#contenido1
			content_font = xlwt.Font()
			content_font.name = 'Arial'
			content_pattern = xlwt.Pattern()
			content_style = xlwt.XFStyle()
			content_style.font = content_font
			content_style.borders = borders
			content_style.pattern = content_pattern

			#titulos
			tittle_font = xlwt.Font()
			tittle_font.name = 'Arial'
			tittle_font.bold = True
			tittle_font.italic = True
			tittle_font.height = 20*20
			tittle_style = xlwt.XFStyle()
			tittle_style.font = tittle_font

			sh1.write(0,0,"Reporte General", tittle_style)
			sh1.write(1,0,"Total de Resultados: "+str(conteo), tittle_style)
			sh1.write(3,0,"No.", header_style)
			sh1.write(3,1,"Nombre", header_style)
			sh1.write(3,2,"Carnet", header_style)
			sh1.write(3,3,"Fecha", header_style)
			sh1.write(3,4,"Concepto", header_style)
			sh1.write(3,5,"Descripción", header_style)
			sh1.write(3,6,"Recibo", header_style)
			sh1.write(3,7,"Total", header_style)
			sh1.write(3,8,"Empresa", header_style)

			if len(data) > 0:
				for i in range(len(data)):
					sh1.write(i+4,0,i+1, content_style)
					sh1.write(i+4,1,data[i][0], content_style)
					sh1.write(i+4,2,data[i][1], content_style)
					sh1.write(i+4,3,data[i][2], content_style)
					sh1.write(i+4,4,data[i][3], content_style)
					sh1.write(i+4,5,data[i][4], content_style)
					sh1.write(i+4,6,data[i][5], content_style)
					sh1.write(i+4,7,"Q"+str(data[i][6]), content_style)
					sh1.write(i+4,8,data[i][9], content_style)
			
			sh1.col(0).width = 0x0d00 + len("No.")
			try:
				sh1.col(1).width = 256 * (max([len(str(row[i])) for row in data[i][0]]) + 1) * 10
				sh1.col(2).width = 256 * (max([len(str(row[i])) for row in data[i][1]]) + 1) * 10
				sh1.col(3).width = 256 * (max([len(str(row[i])) for row in data[i][2]]) + 1) * 10
				sh1.col(4).width = 256 * (max([len(str(row[i])) for row in data[i][3]]) + 1) * 10
				sh1.col(5).width = 256 * (max([len(str(row[i])) for row in data[i][4]]) + 1) * 10
				sh1.col(6).width = 256 * (max([len(str(row[i])) for row in data[i][5]]) + 1) * 10
				sh1.col(7).width = 256 * (max([len(str(row[i])) for row in data[i][6]]) + 1) * 10
				sh1.col(8).width = 256 * (max([len(str(row[i])) for row in data[i][6]]) + 1) * 10
			except:
				sh1.col(1).width = 256 * 20
				sh1.col(2).width = 256 * 20
				sh1.col(3).width = 256 * 20
				sh1.col(4).width = 256 * 20
				sh1.col(5).width = 256 * 20
				sh1.col(6).width = 256 * 20
				sh1.col(7).width = 256 * 20
				sh1.col(8).width = 256 * 20
			workbook.save(output)
			output.seek(0)
			return Response(output, mimetype="application/ms-excel", headers={"Content-Disposition":"attachment;filename=reportegeneral.xls"})
	return render_template('repgen.html', title="Reporte general", data=data, logeado=session['logeadocaja'], conteo=conteo, datacarnet=datacarnet, datanombre=datanombre, datafechaini=datafechaini, datafechafin=datafechafin, dataconcepto=dataconcepto, datadescripcion=datadescripcion, datarecibo=datarecibo, dataempresa=dataempresa, barranav=2)

@app.route('/pagos')
@login_required
def pagos():
	return render_template('pagos.html', title="Pagos", logeado=session['logeadocaja'], barranav=1)

@app.route('/transferencias', methods=['GET', 'POST'])
@login_required
def transferencias():
	if request.method == 'POST':
		recibo = request.form["recibo"]
		factura = request.form["factura"]
		nombre = request.form["nombre"]
		total = request.form["total"]
		try:
			conexion = pymysql.connect(host=Conhost, user=Conuser, password=Conpassword, db=Condb)
			try:
				with conexion.cursor() as cursor:
					consulta1 = 'INSERT INTO transferencias(nombre, factura, recibo, total, fecha) values(%s,%s,%s,%s,CURDATE())'
					cursor.execute(consulta1, (nombre, factura, recibo, total))
				conexion.commit()
			finally:
				conexion.close()
		except (pymysql.err.OperationalError, pymysql.err.InternalError) as e:
			print("Ocurrió un error al conectar: ", e)
		return redirect(url_for('transferencias'))
	return render_template('transferencias.html', title="Ingresar Transferencia", logeado=session['logeadocaja'], barranav=1)

@app.route('/reptransferencias', methods=['GET', 'POST'])
@login_required
def reptransferencias():
	try:
		conexion = pymysql.connect(host=Conhost, user=Conuser, password=Conpassword, db=Condb)
		try:
			with conexion.cursor() as cursor:
				consulta = 'SELECT nombre, fecha, factura, recibo, total from transferencias ORDER by fecha desc, nombre asc'
				cursor.execute(consulta)
				transferencias = cursor.fetchall()
		finally:
			conexion.close()
	except (pymysql.err.OperationalError, pymysql.err.InternalError) as e:
		print("Ocurrió un error al conectar: ", e)
	return render_template('reptransferencias.html', title="Transferencias", logeado=session['logeadocaja'], transferencias=transferencias, barranav=2)

@app.route('/imprimir/<idpagos>')
@login_required
def imprimir(idpagos):
	array = idpagos.split(',')
	newarray = []
	numpagos = len(array)
	for i in range(numpagos):
		varaux = ''
		for j in array[i]:
			if j.isdigit():
				varaux = varaux + str(j)
		newarray.append(varaux)
	datagen = []
	suma = 0
	try:
		conexion = pymysql.connect(host=Conhost, user=Conuser, password=Conpassword, db=Condb)
		try:
			with conexion.cursor() as cursor:
				for i in range(numpagos):
					consulta = f'SELECT p.nombre, p.carnet, DATE_FORMAT(p.fecha,"%d/%m/%Y"), c.concepto, p.extra, p.total, u.iniciales FROM pagos p INNER JOIN codigos c ON p.idcod = c.idcodigos inner join user u on u.iduser = p.user WHERE p.idpagos = {newarray[i]};'
					cursor.execute(consulta)
				# Con fetchall traemos todas las filas
					data = cursor.fetchone()
					suma = suma + float(data[5])
					datagen.append(data)
		finally:
			conexion.close()
	except (pymysql.err.OperationalError, pymysql.err.InternalError) as e:
		print("Ocurrió un error al conectar: ", e)
	rendered = render_template('imprimir.html', title="Reporte diario", datagen = datagen, suma=suma, numpagos=numpagos, newarray=newarray, ruta = PATH_FILE)
	options = {'enable-local-file-access': None, 'page-size': 'A8', 'orientation': 'Portrait', 'margin-left': '0', 'margin-right': '5mm', 'margin-top': '0', 'margin-bottom': '0', 'encoding': 'utf-8'}
	config = pdfkit.configuration(wkhtmltopdf="C:\\Program Files\\wkhtmltopdf\\bin\\wkhtmltopdf.exe")
	pdf = pdfkit.from_string(rendered, False, configuration=config, options=options)
	response = make_response(pdf)
	response.headers['Content-Type'] = 'application/pdf'
	response.headers['Content-Disposition'] = 'inline; filename=reportediario.pdf'
	print(response)
	return response

@app.route('/admin')
@login_required
def admin():
	if session['idusercaja'] not in usuariosadministrativo:
		return redirect(url_for('login'))
	return render_template('admin.html', title="Panel Administrativo", logeado=session['logeadocaja'], barranav=3)

@app.route('/pagosadmin')
@login_required
def pagosadmin():
	if session['idusercaja'] not in usuariosadministrativo:
		return redirect(url_for('login'))
	try:
		conexion = pymysql.connect(host=Conhost, user=Conuser, password=Conpassword, db=Condb)
		try:
			with conexion.cursor() as cursor:
				consulta = 'SELECT p.idcodigos, p.cod, p.concepto, c.codigo, p.precio, p.manual, p.practica, p.pagos, p.pagose, p.uniformes, p.congreso from codigos p left join carreras c on p.idcarrera = c.idcarreras ORDER by p.concepto asc'
				cursor.execute(consulta)
				codigos = cursor.fetchall()
		finally:
			conexion.close()
	except (pymysql.err.OperationalError, pymysql.err.InternalError) as e:
		print("Ocurrió un error al conectar: ", e)
	return render_template('pagosadmin.html', title="Admin Pagos", logeado=session['logeadocaja'], codigos = codigos, barranav=3)

@app.route('/nuevocodigo', methods=['GET', 'POST'])
@login_required
def nuevocodigo():
	if session['idusercaja'] not in usuariosadministrativo:
		return redirect(url_for('login'))
	try:
		conexion = pymysql.connect(host=Conhost, user=Conuser, password=Conpassword, db=Condb)
		try:
			with conexion.cursor() as cursor:
				consulta = 'SELECT idcarreras, carrera from carreras ORDER by carrera asc'
				cursor.execute(consulta)
				carreras = cursor.fetchall()
		finally:
			conexion.close()
	except (pymysql.err.OperationalError, pymysql.err.InternalError) as e:
		print("Ocurrió un error al conectar: ", e)
	if request.method == "POST":
		concepto = request.form["concepto"]
		codigo = request.form["codigo"]
		carrera = request.form["carrera"]
		if len(carrera) > 0:
			pass
		else:
			carrera = 'null'
		precio = request.form["precio"]
		if len(precio) > 0:
			pass
		else:
			precio = 0
		try:
			manual = request.form["manual"]
		except:
			manual = 0
		try:
			practica = request.form["practica"]
		except:
			practica = 0
		try:
			pagos = request.form["pagos"]
		except:
			pagos = 0
		try:
			pagose = request.form["pagose"]
		except:
			pagose = 0
		try:
			congreso = request.form["congreso"]
		except:
			congreso = 0
		try:
			conexion = pymysql.connect(host=Conhost, user=Conuser, password=Conpassword, db=Condb)
			try:
				with conexion.cursor() as cursor:
					consulta = f"insert into codigos(concepto, cod, idcarrera, precio, activo, manual, practica, pagos, pagose, uniformes, congreso) values('{concepto}', '{codigo}', {carrera}, {precio}, 1, {manual}, {practica},{pagos}, {pagose}, null, {congreso});"
					cursor.execute(consulta)
				conexion.commit()
			finally:
				conexion.close()
		except (pymysql.err.OperationalError, pymysql.err.InternalError) as e:
			print("Ocurrió un error al conectar: ", e)
		return redirect(url_for('pagosadmin'))
	return render_template('nuevocodigo.html', title="Nuevo Código", logeado=session['logeadocaja'], carreras = carreras, barranav=3)

@app.route('/editarcodigo/<id>', methods=['GET', 'POST'])
@login_required
def editarcodigo(id):
	if session['idusercaja'] not in usuariosadministrativo:
		return redirect(url_for('login'))
	try:
		conexion = pymysql.connect(host=Conhost, user=Conuser, password=Conpassword, db=Condb)
		try:
			with conexion.cursor() as cursor:
				consulta = 'SELECT idcarreras, carrera from carreras ORDER by carrera asc'
				cursor.execute(consulta)
				carreras = cursor.fetchall()
				consulta = f'select * from codigos where idcodigos = {id}'
				cursor.execute(consulta)
				datacodigo = cursor.fetchone()
		finally:
			conexion.close()
	except (pymysql.err.OperationalError, pymysql.err.InternalError) as e:
		print("Ocurrió un error al conectar: ", e)
	if request.method == "POST":
		concepto = request.form["concepto"]
		codigo = request.form["codigo"]
		carrera = request.form["carrera"]
		if len(carrera) > 0:
			pass
		else:
			carrera = 'null'
		precio = request.form["precio"]
		if len(precio) > 0:
			pass
		else:
			precio = 0
		try:
			manual = request.form["manual"]
		except:
			manual = 0
		try:
			practica = request.form["practica"]
		except:
			practica = 0
		try:
			pagos = request.form["pagos"]
		except:
			pagos = 0
		try:
			pagose = request.form["pagose"]
		except:
			pagose = 0
		try:
			congreso = request.form["congreso"]
		except:
			congreso = 0
		try:
			conexion = pymysql.connect(host=Conhost, user=Conuser, password=Conpassword, db=Condb)
			try:
				with conexion.cursor() as cursor:
					consulta = f"update codigos set concepto = '{concepto}', cod = '{codigo}', idcarrera = {carrera}, precio = {precio}, manual = {manual}, practica = {practica}, pagos = {pagos}, pagose = {pagose}, congreso = {congreso} where idcodigos = {id};"
					cursor.execute(consulta)
				conexion.commit()
			finally:
				conexion.close()
		except (pymysql.err.OperationalError, pymysql.err.InternalError) as e:
			print("Ocurrió un error al conectar: ", e)
		return redirect(url_for('pagosadmin'))
	return render_template('editarcodigo.html', title="Editar Código", logeado=session['logeadocaja'], carreras = carreras, datacodigo = datacodigo, barranav=3)

@app.route('/carreras')
@login_required
def carreras():
	if session['idusercaja'] not in usuariosadministrativo:
		return redirect(url_for('login'))
	try:
		conexion = pymysql.connect(host=Conhost, user=Conuser, password=Conpassword, db=Condb)
		try:
			with conexion.cursor() as cursor:
				consulta = 'SELECT * from carreras order by carrera asc'
				cursor.execute(consulta)
				carreras = cursor.fetchall()
		finally:
			conexion.close()
	except (pymysql.err.OperationalError, pymysql.err.InternalError) as e:
		print("Ocurrió un error al conectar: ", e)
	return render_template('carreras.html', title="Admin Carreras", logeado=session['logeadocaja'], carreras = carreras, barranav=3)

@app.route('/nuevacarrera', methods=['GET', 'POST'])
@login_required
def nuevacarrera():
	if session['idusercaja'] not in usuariosadministrativo:
		return redirect(url_for('login'))
	if request.method == 'POST':
		codigo = request.form["codigo"]
		carrera = request.form["carrera"]
		institucion = request.form["institucion"]
		if int(institucion) == 1:
			precio = request.form["precio"]
			internet = request.form["internet"]
		try:
			conexion = pymysql.connect(host=Conhost, user=Conuser, password=Conpassword, db=Condb)
			try:
				with conexion.cursor() as cursor:
					consulta = f"insert into carreras(codigo, carrera, institucion) values('{codigo}', '{carrera}', {institucion});"
					cursor.execute(consulta)
					conexion.commit()
					if int(institucion) == 1:
						consulta = "Select MAX(idcarreras) from carreras;"
						cursor.execute(consulta)
						idcarrera = cursor.fetchone()[0]
						consulta = f"insert into inscripciones(inscripcion, precio, internet, idcarrera) values('Inscripción {codigo}', {precio}, {internet}, {idcarrera})"
						cursor.execute(consulta)
						conexion.commit()
			finally:
				conexion.close()
		except (pymysql.err.OperationalError, pymysql.err.InternalError) as e:
			print("Ocurrió un error al conectar: ", e)
		return redirect(url_for('carreras'))
	return render_template('nuevacarrera.html', title="Nueva Carrera", logeado=session['logeadocaja'], barranav=3)

@app.route('/laboratorioadmin')
@login_required
def laboratorioadmin():
	if session['idusercaja'] not in usuariosadministrativo:
		return redirect(url_for('login'))
	try:
		conexion = pymysql.connect(host=Conhost, user=Conuser, password=Conpassword, db=Condb)
		try:
			with conexion.cursor() as cursor:
				consulta = 'SELECT t.nombre, e.nombre, e.precio, e.idexameneslab from tipoexamen t inner join exameneslab e on e.idtipoexamen = t.idtipoexamen order by t.nombre asc, e.nombre asc'
				cursor.execute(consulta)
				examenes = cursor.fetchall()
		finally:
			conexion.close()
	except (pymysql.err.OperationalError, pymysql.err.InternalError) as e:
		print("Ocurrió un error al conectar: ", e)
	return render_template('laboratorioadmin.html', title="Admin Laboratorio", logeado=session['logeadocaja'], examenes = examenes, barranav=3)

@app.route('/nuevoexamenlab', methods=['GET', 'POST'])
@login_required
def nuevoexamenlab():
	if session['idusercaja'] not in usuariosadministrativo:
		return redirect(url_for('login'))
	try:
		conexion = pymysql.connect(host=Conhost, user=Conuser, password=Conpassword, db=Condb)
		try:
			with conexion.cursor() as cursor:
				consulta = 'SELECT idtipoexamen, nombre from tipoexamen ORDER by nombre asc'
				cursor.execute(consulta)
				tipos = cursor.fetchall()
		finally:
			conexion.close()
	except (pymysql.err.OperationalError, pymysql.err.InternalError) as e:
		print("Ocurrió un error al conectar: ", e)
	if request.method == "POST":
		nombre = request.form["nombre"]
		tipo = request.form["tipo"]
		precio = request.form["precio"]
		try:
			conexion = pymysql.connect(host=Conhost, user=Conuser, password=Conpassword, db=Condb)
			try:
				with conexion.cursor() as cursor:
					consulta = f"insert into exameneslab(nombre, idtipoexamen, precio, fechaactivo) values('{nombre}', '{tipo}', {precio}, '0000-00-00');"
					print(consulta)
					cursor.execute(consulta)
				conexion.commit()
			finally:
				conexion.close()
		except (pymysql.err.OperationalError, pymysql.err.InternalError) as e:
			print("Ocurrió un error al conectar: ", e)
		return redirect(url_for('laboratorioadmin'))
	return render_template('nuevoexamenlab.html', title="Nuevo Examen de Laboratorio", logeado=session['logeadocaja'], tipos = tipos, barranav=3)

@app.route('/nuevacategorialab', methods=['GET', 'POST'])
@login_required
def nuevacategorialab():
	if session['idusercaja'] not in usuariosadministrativo:
		return redirect(url_for('login'))
	if request.method == "POST":
		nombre = request.form["nombre"]
		try:
			conexion = pymysql.connect(host=Conhost, user=Conuser, password=Conpassword, db=Condb)
			try:
				with conexion.cursor() as cursor:
					consulta = f"insert into tipoexamen(nombre) values('{nombre}');"
					print(consulta)
					cursor.execute(consulta)
				conexion.commit()
			finally:
				conexion.close()
		except (pymysql.err.OperationalError, pymysql.err.InternalError) as e:
			print("Ocurrió un error al conectar: ", e)
		return redirect(url_for('laboratorioadmin'))
	return render_template('nuevacategorialab.html', title="Nueva Categoria Examen de Laboratorio", logeado=session['logeadocaja'], barranav=3)

@app.route('/editarexamenlab/<id>', methods=['GET', 'POST'])
@login_required
def editarexamenlab(id):
	if session['idusercaja'] not in usuariosadministrativo:
		return redirect(url_for('login'))
	try:
		conexion = pymysql.connect(host=Conhost, user=Conuser, password=Conpassword, db=Condb)
		try:
			with conexion.cursor() as cursor:
				consulta = 'SELECT idtipoexamen, nombre from tipoexamen ORDER by nombre asc'
				cursor.execute(consulta)
				tipos = cursor.fetchall()
				consulta = f'select * from exameneslab where idexameneslab = {id}'
				cursor.execute(consulta)
				dataexamen = cursor.fetchone()
				print(dataexamen)
		finally:
			conexion.close()
	except (pymysql.err.OperationalError, pymysql.err.InternalError) as e:
		print("Ocurrió un error al conectar: ", e)
	if request.method == "POST":
		nombre = request.form["nombre"]
		tipo = request.form["tipo"]
		precio = request.form["precio"]
		try:
			conexion = pymysql.connect(host=Conhost, user=Conuser, password=Conpassword, db=Condb)
			try:
				with conexion.cursor() as cursor:
					consulta = f"update exameneslab set nombre = '{nombre}', idtipoexamen = '{tipo}', precio = {precio} where idexameneslab = {id};"
					cursor.execute(consulta)
				conexion.commit()
			finally:
				conexion.close()
		except (pymysql.err.OperationalError, pymysql.err.InternalError) as e:
			print("Ocurrió un error al conectar: ", e)
		return redirect(url_for('laboratorioadmin'))
	return render_template('editarexamenlab.html', title="Editar Exámen de Laboratorio", logeado=session['logeadocaja'], tipos = tipos, dataexamen = dataexamen, barranav=3)

@app.route('/usuarios')
@login_required
def usuarios():
	if session['idusercaja'] not in usuariosadministrativo:
		return redirect(url_for('login'))
	try:
		conexion = pymysql.connect(host=Conhost, user=Conuser, password=Conpassword, db=Condb)
		try:
			with conexion.cursor() as cursor:
				consulta = 'SELECT nombre, apellido, user, iniciales, iduser from user order by nombre asc, apellido asc'
				cursor.execute(consulta)
				usuarios = cursor.fetchall()
		finally:
			conexion.close()
	except (pymysql.err.OperationalError, pymysql.err.InternalError) as e:
		print("Ocurrió un error al conectar: ", e)
	return render_template('usuarios.html', title="Admin Usuarios", logeado=session['logeadocaja'], usuarios = usuarios, barranav=3)

@app.route("/editarusuario/<id>", methods=['GET', 'POST'])
@login_required
def editarusuario(id):
	if session['idusercaja'] not in usuariosadministrativo:
		return redirect(url_for('login'))
	try:
		conexion = pymysql.connect(host=Conhost, user=Conuser, password=Conpassword, db=Condb)
		try:
			with conexion.cursor() as cursor:
				consulta = "select nombre, apellido, user, iniciales from user where iduser = %s;"
				cursor.execute(consulta, (id))
				datausuario = cursor.fetchone()
		finally:
			conexion.close()
	except (pymysql.err.OperationalError, pymysql.err.InternalError) as e:
		print("Ocurrió un error al conectar: ", e)
	if request.method == 'POST':
		nombre = request.form["nombre"]
		apellido = request.form["apellido"]
		user = request.form["user"]
		iniciales = request.form["iniciales"]
		try:
			conexion = pymysql.connect(host=Conhost, user=Conuser, password=Conpassword, db=Condb)
			try:
				with conexion.cursor() as cursor:
					consulta = "update user set nombre = %s, apellido = %s, user = %s, iniciales = %s where iduser = %s;"
					cursor.execute(consulta, (nombre, apellido, user, iniciales, id))
				conexion.commit()
			finally:
				conexion.close()
		except (pymysql.err.OperationalError, pymysql.err.InternalError) as e:
			print("Ocurrió un error al conectar: ", e)
		return redirect(url_for('usuarios'))
	return render_template('editarusuario.html', title='Editar Usuario', datausuario=datausuario, barranav=3)

@app.route("/restablecerclave/<id>", methods=['GET', 'POST'])
@login_required
def restablecerclave(id):
	if session['idusercaja'] not in usuariosadministrativo:
		return redirect(url_for('login'))
	try:
		conexion = pymysql.connect(host=Conhost, user=Conuser, password=Conpassword, db=Condb)
		try:
			with conexion.cursor() as cursor:
				consulta = "select nombre, apellido, user, iniciales from user where iduser = %s;"
				cursor.execute(consulta, (id))
				datausuario = cursor.fetchone()
		finally:
			conexion.close()
	except (pymysql.err.OperationalError, pymysql.err.InternalError) as e:
		print("Ocurrió un error al conectar: ", e)
	if request.method == 'POST':
		clave = request.form["pwd"]
		try:
			conexion = pymysql.connect(host=Conhost, user=Conuser, password=Conpassword, db=Condb)
			try:
				with conexion.cursor() as cursor:
					consulta = "update user set pwd = MD5(%s) where iduser = %s;"
					cursor.execute(consulta, (clave, id))
				conexion.commit()
			finally:
				conexion.close()
		except (pymysql.err.OperationalError, pymysql.err.InternalError) as e:
			print("Ocurrió un error al conectar: ", e)
		return redirect(url_for('usuarios'))
	return render_template('restablecerclave.html', title='Restablecer Contraseña', datausuario=datausuario, barranav=3)

@app.route('/equivalencias', methods=['GET', 'POST'])
@login_required
def equivalencias():
	if session['idusercaja'] not in usuariosadministrativo:
		return redirect(url_for('login'))
	try:
		conexion = pymysql.connect(host=Conhost, user=Conuser, password=Conpassword, db=Condb)
		try:
			with conexion.cursor() as cursor:
				consulta = 'SELECT e.nombre, e.carnet, c.codigo, e.curso, e.semestre, e.seccion, e.catedratico, a.estado, e.notificacion1, e.notificacion2, e.notificacion3, e.terminado, e.idequivalencia from equivalencia e inner join carreras c on c.idcarreras = e.idcarrera inner join estado a on a.idestado = e.idestado where e.terminado = 0 and e.idestado != 1 order by e.nombre asc, e.curso asc;'
				cursor.execute(consulta)
				equivalencias = cursor.fetchall()
		finally:
			conexion.close()
	except (pymysql.err.OperationalError, pymysql.err.InternalError) as e:
		print("Ocurrió un error al conectar: ", e)
	if request.method == 'POST':
		for i in equivalencias:
			try:
				auxa1 = f"notificaciona{i[12]}"
				aux1 = int(request.form[auxa1])
			except:
				aux1 = 0
			try:
				auxa2 = f"notificacionb{i[12]}"
				aux2 = int(request.form[auxa2])
			except:
				aux2 = 0
			try:
				auxa3 = f"notificacionc{i[12]}"
				aux3 = int(request.form[auxa3])
			except:
				aux3 = 0
			try:
				auxa4 = f"terminado{i[12]}"
				aux4 = int(request.form[auxa4])
			except:
				aux4 = 0
			try:
				conexion = pymysql.connect(host=Conhost, user=Conuser, password=Conpassword, db=Condb)
				try:
					with conexion.cursor() as cursor:
						if aux1 == 1:
							consulta = 'update equivalencia set notificacion1 = %s where idequivalencia = %s;'
							cursor.execute(consulta, (aux1, i[12]))
						if aux2 == 1:
							consulta = 'update equivalencia set notificacion2 = %s where idequivalencia = %s;'
							cursor.execute(consulta, (aux2, i[12]))
						if aux3 == 1:
							consulta = 'update equivalencia set notificacion3 = %s where idequivalencia = %s;'
							cursor.execute(consulta, (aux3, i[12]))
						if aux4 == 1:
							consulta = 'update equivalencia set terminado = %s where idequivalencia = %s;'
							cursor.execute(consulta, (aux4, i[12]))
						conexion.commit()
				finally:
					conexion.close()
			except (pymysql.err.OperationalError, pymysql.err.InternalError) as e:
				print("Ocurrió un error al conectar: ", e)
		return redirect(url_for('equivalencias'))
	return render_template('equivalencias.html', title="Equivalencias", logeado=session['logeadocaja'], equivalencias = equivalencias, barranav=3)

@app.route('/aprobarequivalencias', methods=['GET', 'POST'])
@login_required
def aprobarequivalencias():
	if session['idusercaja'] not in usuariosadministrativo:
		return redirect(url_for('login'))
	try:
		conexion = pymysql.connect(host=Conhost, user=Conuser, password=Conpassword, db=Condb)
		try:
			with conexion.cursor() as cursor:
				consulta = 'SELECT idestado, estado from estado'
				cursor.execute(consulta)
				estados = cursor.fetchall()
				consulta = 'SELECT e.nombre, e.carnet, c.codigo, e.curso, e.semestre, e.seccion, e.catedratico, e.idestado, e.notificacion1, e.notificacion2, e.notificacion3, e.terminado, e.idequivalencia from equivalencia e inner join carreras c on c.idcarreras = e.idcarrera inner join estado a on a.idestado = e.idestado where e.terminado = 0 and e.idestado = 1 order by e.nombre asc, e.curso asc;'
				cursor.execute(consulta)
				equivalencias = cursor.fetchall()
		finally:
			conexion.close()
	except (pymysql.err.OperationalError, pymysql.err.InternalError) as e:
		print("Ocurrió un error al conectar: ", e)
	if request.method == 'POST':
		for i in equivalencias:
			aux = f"estado{i[12]}"
			aux1 = int(request.form[aux])
			try:
				conexion = pymysql.connect(host=Conhost, user=Conuser, password=Conpassword, db=Condb)
				try:
					with conexion.cursor() as cursor:
						consulta = 'update equivalencia set idestado = %s where idequivalencia = %s;'
						cursor.execute(consulta, (aux1, i[12]))
						conexion.commit()
				finally:
					conexion.close()
			except (pymysql.err.OperationalError, pymysql.err.InternalError) as e:
				print("Ocurrió un error al conectar: ", e)
		return redirect(url_for('aprobarequivalencias'))
	return render_template('aprobarequivalencias.html', title="Aprobación de Equivalencias", logeado=session['logeadocaja'], equivalencias = equivalencias, estados = estados, barranav=3)

@app.route('/historialequivalencias', methods=['GET', 'POST'])
@login_required
def historialequivalencias():
	if session['idusercaja'] not in usuariosadministrativo:
		return redirect(url_for('login'))
	try:
		conexion = pymysql.connect(host=Conhost, user=Conuser, password=Conpassword, db=Condb)
		try:
			with conexion.cursor() as cursor:
				consulta = 'SELECT idestado, estado from estado'
				cursor.execute(consulta)
				estados = cursor.fetchall()
				consulta = 'SELECT e.nombre, e.carnet, c.codigo, e.curso, e.semestre, e.seccion, e.catedratico, a.estado, e.notificacion1, e.notificacion2, e.notificacion3, e.terminado, e.idequivalencia from equivalencia e inner join carreras c on c.idcarreras = e.idcarrera inner join estado a on a.idestado = e.idestado where e.terminado = 1 order by e.nombre asc, e.curso asc;'
				cursor.execute(consulta)
				equivalencias = cursor.fetchall()
		finally:
			conexion.close()
	except (pymysql.err.OperationalError, pymysql.err.InternalError) as e:
		print("Ocurrió un error al conectar: ", e)
	return render_template('historialequivalencias.html', title="Historial de Equivalencias", logeado=session['logeadocaja'], equivalencias = equivalencias, estados = estados, barranav=3)

@app.route('/nuevaequivalencia/<mensaje>', methods=['GET', 'POST'])
@login_required
def nuevaequivalencia(mensaje):
	if session['idusercaja'] not in usuariosadministrativo:
		return redirect(url_for('login'))
	try:
		conexion = pymysql.connect(host=Conhost, user=Conuser, password=Conpassword, db=Condb)
		try:
			with conexion.cursor() as cursor:
				consulta = 'SELECT idcarreras, codigo, carrera from carreras order by carrera asc'
				cursor.execute(consulta)
				carreras = cursor.fetchall()
		finally:
			conexion.close()
	except (pymysql.err.OperationalError, pymysql.err.InternalError) as e:
		print("Ocurrió un error al conectar: ", e)
	if request.method == 'POST':
		nombre = request.form["nombre"]
		carnet = request.form["carnet"]
		carrera = request.form["carrera"]
		cant = int(request.form["cant"])
		try:
			conexion = pymysql.connect(host=Conhost, user=Conuser, password=Conpassword, db=Condb)
			try:
				with conexion.cursor() as cursor:
					for i in range(cant):
						acurso, acatedratico, asemestre, aseccion = f"curso{i+1}", f"catedratico{i+1}", f"semestre{i+1}", f"seccion{i+1}"
						curso = request.form[acurso]
						catedratico = request.form[acatedratico]
						semestre = request.form[asemestre]
						seccion = request.form[aseccion]
						carta = request.files['carta']
						consulta = 'insert into equivalencia(nombre, carnet, idcarrera, curso, semestre, seccion, catedratico, idestado, notificacion1, notificacion2, notificacion3, terminado) values (%s,%s,%s,%s,%s,%s,%s,1,0,0,0,0);'
						cursor.execute(consulta, (nombre, carnet, carrera, curso, semestre, seccion, catedratico))
						if carta.filename != '':
							if ".pdf" not in carta.filename:
								if carta.filename.split('.')[-1].lower() not in ['jpg', 'jpeg', 'png', 'gif']:
									mensaje = 1
									return redirect(url_for('nuevaequivalencia', mensaje = mensaje))
								else:
									conexion.commit()
									consulta = 'SELECT MAX(idequivalencia) from equivalencia;'
									cursor.execute(consulta)
									idequivalencia = cursor.fetchone()
									idequivalencia = idequivalencia[0]
									carta.save('temp.png')
									if carta.filename.split('.')[-1].lower() == 'png':
										img = Image.open('temp.png')
										rgb_img = img.convert('RGB')
										rgb_img.save('temp.jpg')
										imagen_path = 'temp.jpg'
									else:
										imagen_path = 'temp.png'
									pdf = FPDF('P', 'mm', 'Letter')  # Ajustar a tamaño Carta
									pdf.add_page()
									pdf.image(imagen_path, 0, 0, 215.9, 279.4)
									auxRuta = path.join(PATH_FILE, f"static{mi_string}uploads{mi_string}carta_{idequivalencia}.pdf")
									pdf.output(auxRuta, 'F')
									os.remove(imagen_path)
							else:
								conexion.commit()
								consulta = 'SELECT MAX(idequivalencia) from equivalencia;'
								cursor.execute(consulta)
								idequivalencia = cursor.fetchone()
								idequivalencia = idequivalencia[0]
								carta.save(path.join(PATH_FILE, f"static{mi_string}uploads{mi_string}carta_{idequivalencia}.pdf"))
			finally:
				conexion.close()
		except (pymysql.err.OperationalError, pymysql.err.InternalError) as e:
			print("Ocurrió un error al conectar: ", e)
		return redirect(url_for('aprobarequivalencias'))
	return render_template('nuevaequivalencia.html', title="Nueva Equivalencia", logeado=session['logeadocaja'], carreras = carreras, mensaje = mensaje, barranav=3)

@app.route('/editarequivalencia/<id>', methods=['GET', 'POST'])
@login_required
def editarequivalencia(id):
	if session['idusercaja'] not in usuariosadministrativo:
		return redirect(url_for('login'))
	try:
		conexion = pymysql.connect(host=Conhost, user=Conuser, password=Conpassword, db=Condb)
		try:
			with conexion.cursor() as cursor:
				consulta = 'SELECT nombre, carnet, idcarrera, curso, semestre, seccion, catedratico from equivalencia where idequivalencia = %s'
				cursor.execute(consulta, id)
				equivalencia = cursor.fetchone()
				consulta = 'SELECT idcarreras, codigo, carrera from carreras order by carrera asc'
				cursor.execute(consulta)
				carreras = cursor.fetchall()
		finally:
			conexion.close()
	except (pymysql.err.OperationalError, pymysql.err.InternalError) as e:
		print("Ocurrió un error al conectar: ", e)
	if request.method == 'POST':
		nombre = request.form["nombre"]
		carnet = request.form["carnet"]
		carrera = request.form["carrera"]
		curso = request.form["curso"]
		semestre = request.form["semestre"]
		seccion = request.form["seccion"]
		catedratico = request.form["catedratico"]
		try:
			conexion = pymysql.connect(host=Conhost, user=Conuser, password=Conpassword, db=Condb)
			try:
				with conexion.cursor() as cursor:
					consulta = 'update equivalencia set nombre = %s, carnet = %s, idcarrera = %s, curso = %s, semestre = %s, seccion = %s, catedratico = %s where idequivalencia = %s'
					cursor.execute(consulta, (nombre, carnet, carrera, curso, semestre, seccion, catedratico, id))
					conexion.commit()
			finally:
				conexion.close()
		except (pymysql.err.OperationalError, pymysql.err.InternalError) as e:
			print("Ocurrió un error al conectar: ", e)
		return redirect(url_for('equivalencias'))
	return render_template('editarequivalencia.html', title="Editar Equivalencia", logeado=session['logeadocaja'], carreras = carreras, equivalencia = equivalencia, barranav=3)

@app.route('/eliminarequivalencia/<id>', methods=['GET', 'POST'])
@login_required
def eliminarequivalencia(id):
	if session['idusercaja'] not in usuariosadministrativo:
		return redirect(url_for('login'))
	try:
		conexion = pymysql.connect(host=Conhost, user=Conuser, password=Conpassword, db=Condb)
		try:
			with conexion.cursor() as cursor:
				consulta = 'DELETE FROM equivalencia where idequivalencia = %s'
				cursor.execute(consulta, id)
				conexion.commit()
		finally:
			conexion.close()
	except (pymysql.err.OperationalError, pymysql.err.InternalError) as e:
		print("Ocurrió un error al conectar: ", e)
	return redirect(url_for('equivalencias'))

if __name__ == '__main__':
	app.run(host='0.0.0.0', port=5000, threaded=True, debug=True)