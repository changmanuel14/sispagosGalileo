from operator import truediv
from flask import Flask, render_template, request, url_for, redirect, make_response, session, Response
import pymysql
from datetime import date, datetime
import os
import webbrowser
import io
import xlwt
import pdfkit as pdfkit
import barcode
from barcode.writer import ImageWriter
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from conexion import Conhost, Conuser, Conpassword, Condb
#from flask_weasyprint import HTML, render_pdf

UPLOAD_FOLDER = r'C:\Users\galileoserver\Documents\sispagosGalileo\flaskapp\static\uploads'
app = Flask(__name__)
app.secret_key = 'd589d3d0d15d764ed0a98ff5a37af547'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def home():
	return redirect(url_for('login'))

@app.route("/verdev/<idpago>", methods=['GET', 'POST'])
def verdev(idpago):
	try:
		logeado = session['logeadocaja']
	except:
		return redirect(url_for('login'))
	try:
		conexion = pymysql.connect(host=Conhost, user=Conuser, password=Conpassword, db=Condb)
		try:
			with conexion.cursor() as cursor:
				consulta = f'SELECT urldevuelto, userdev from pagos where idpagos = {idpago};'
				cursor.execute(consulta)
				acceso = cursor.fetchall()
				idusuario = acceso[0][1]
				acceso = acceso[0][0]
				consulta = f"select nombre, apellido, user from user where iduser = {idusuario}"
				cursor.execute(consulta)
				user = cursor.fetchall()
		finally:
			conexion.close()
	except (pymysql.err.OperationalError, pymysql.err.InternalError) as e:
		print("Ocurrió un error al conectar: ", e)
	return render_template('verdev.html', title='Devolución de Pago', logeado=logeado, acceso=acceso, user=user)

@app.route("/devolucion/<idpago>", methods=['GET', 'POST'])
def devolucion(idpago):
	try:
		logeado = session['logeadocaja']
	except:
		return redirect(url_for('login'))
	try:
		conexion = pymysql.connect(host=Conhost, user=Conuser, password=Conpassword, db=Condb)
		try:
			with conexion.cursor() as cursor:
				consulta = f'SELECT c.concepto, p.nombre, p.carnet, p.total, DATE_FORMAT(p.fecha,"%d/%m/%Y"), p.extra, p.recibo from codigos c inner join pagos p on p.idcod = c.idcodigos where p.idpagos = {idpago};'
				cursor.execute(consulta)
				datapago = cursor.fetchall()
				datapago = datapago[0]
		finally:
			conexion.close()
	except (pymysql.err.OperationalError, pymysql.err.InternalError) as e:
		print("Ocurrió un error al conectar: ", e)
	if request.method == 'POST':
		file = request.files['file']
		usuario = request.form["usuario"]
		pwd = request.form["password"]
		try:
			conexion = pymysql.connect(host=Conhost, user=Conuser, password=Conpassword, db=Condb)
			try:
				with conexion.cursor() as cursor:
					consulta = f"SELECT iduser, nombre, apellido FROM user WHERE user = '{usuario}' and pwd = md5('{pwd}')"
					cursor.execute(consulta)
					data = cursor.fetchall()
					if len(data) == 0:
						return redirect(url_for('devolucion', idpago=idpago))
					else:
						nombrearc = f'dev{idpago}.'
						div = str(file.filename).split('.')
						nombrearc = nombrearc + div[1]
						file.save(os.path.join(app.config['UPLOAD_FOLDER'], nombrearc))
						consulta = f"UPDATE pagos set devuelto = 1, urldevuelto = '{nombrearc}', fechadevuelto='{date.today()}', user={session['idusercaja']}, userdev={data[0][0]} where idpagos = {idpago};"
						cursor.execute(consulta)
					conexion.commit()
			finally:
				conexion.close()
		except (pymysql.err.OperationalError, pymysql.err.InternalError) as e:
			print("Ocurrió un error al conectar: ", e)
		return redirect(url_for('repgen'))
	return render_template('devolucion.html', title='Devolución de Pago', logeado=logeado, datapago=datapago)

@app.route("/academia", methods=['GET', 'POST'])
def academia():
	try:
		logeado = session['logeadocaja']
	except:
		return redirect(url_for('login'))
	try:
		conexion = pymysql.connect(host=Conhost, user=Conuser, password=Conpassword, db=Condb)
		try:
			with conexion.cursor() as cursor:
				consulta = 'SELECT carrera, codigo, idcarreras from carreras where institucion = 2 order by carrera asc'
				cursor.execute(consulta)
				carreras = cursor.fetchall()
		finally:
			conexion.close()
	except (pymysql.err.OperationalError, pymysql.err.InternalError) as e:
		print("Ocurrió un error al conectar: ", e)
	meses = ["Enero", "Febrero","Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
	if request.method == 'POST':
		carnet = request.form["carnet"]
		if len(carnet) < 1:
			carnet = 0
		nombre = request.form["nombre"]
		cantidad = int(request.form["cant"])
		carrera = request.form["carrera"]
		try:
			insc = request.form["insc"]
		except:
			insc = 0
		datameses = ""
		for i in range(cantidad):
			aux = f'mes{i + 1}'
			mes = request.form[aux]
			if i > 0:
				datameses = f'{datameses},{mes}'
			else:
				datameses = f'{datameses}{mes}'
		return redirect(url_for('confirmacionaca', nombre=nombre, carnet=carnet, datameses=datameses, carrera = carrera, insc=insc))
	return render_template('academia.html', title='Academia', logeado=logeado, carreras=carreras, meses=meses)

@app.route("/confirmacionaca/<nombre>&<carnet>&<datameses>&<carrera>&<insc>", methods=['GET', 'POST'])
def confirmacionaca(nombre, carnet, datameses, carrera, insc):
	try:
		logeado = session['logeadocaja']
	except:
		return redirect(url_for('login'))
	nombre = str(nombre)
	carnet = str(carnet)
	carrera = str(carrera)
	insc = int(insc)
	meses = datameses.split(",")
	cantidad = len(meses)
	try:
		conexion = pymysql.connect(host=Conhost, user=Conuser, password=Conpassword, db=Condb)
		try:
			with conexion.cursor() as cursor:
				consulta = f'SELECT carrera from carreras where idcarreras = {carrera}'
				cursor.execute(consulta)
				datacarrera = cursor.fetchone()
				consulta = "SELECT idcodigos, precio from codigos where cod = 'ACAINS'"
				cursor.execute(consulta)
				codins = cursor.fetchone()
				consulta = "SELECT idcodigos, precio from codigos where cod = 'ACAMEN'"
				cursor.execute(consulta)
				codmen = cursor.fetchone()
		finally:
			conexion.close()
	except (pymysql.err.OperationalError, pymysql.err.InternalError) as e:
		print("Ocurrió un error al conectar: ", e)
	total = 0
	if insc == 1:
		total = total + float(codins[1])
	total = total + (cantidad * float(codmen[1]))
	if request.method == 'POST':
		try:
			conexion = pymysql.connect(host=Conhost, user=Conuser, password=Conpassword, db=Condb)
			try:
				with conexion.cursor() as cursor:
					idpagos = []
					if insc == 1:
						consulta = "INSERT INTO pagos(idcod,nombre,carnet,total,fecha,extra,recibo, user) VALUES (%s,%s,%s,%s,%s,%s,%s, %s);"
						cursor.execute(consulta, (codins[0], nombre, carnet,codins[1], date.today(), 'Curso: ' + str(datacarrera[0]) ,0, session['idusercaja']))
						conexion.commit()
						consulta = "Select MAX(idpagos) from pagos;"
						cursor.execute(consulta)
						idpago = cursor.fetchone()
						idpago = idpago[0]
						idpagos.append(idpago)
					for i in meses:
						consulta = "INSERT INTO pagos(idcod,nombre,carnet,total,fecha,extra,recibo, user) VALUES (%s,%s,%s,%s,%s,%s,%s, %s);"
						cursor.execute(consulta, (codmen[0], nombre, carnet, codmen[1], date.today(), 'Mes: ' + i ,0, session['idusercaja']))
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
	return render_template('confirmacionaca.html', title='Confirmación Academia', logeado=logeado, nombre=nombre, carnet=carnet, cantidad=cantidad, total = total, datacarrera=datacarrera, insc=insc, meses=meses)

@app.route("/auxenf", methods=['GET', 'POST'])
def auxenf():
	try:
		logeado = session['logeadocaja']
	except:
		return redirect(url_for('login'))
	meses = ["Enero", "Febrero","Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
	if request.method == 'POST':
		carnet = request.form["carnet"]
		if len(carnet) < 1:
			carnet = 0
		nombre = request.form["nombre"]
		cantidad = int(request.form["cant"]) + 1
		mora = request.form["mora"]
		try:
			insc = request.form["insc"]
		except:
			insc = 0
		datameses = ""
		for i in range(cantidad):
			aux = 'mes' + str(i)
			mes = request.form[aux] 
			if len(mes) > 0:
				if i > 0:
					datameses = f'{datameses},{mes}'
				else:
					datameses = f'{datameses}{mes}'
		if len(datameses) < 1:
			datameses = 'None'
		return redirect(url_for('confirmacionauxenf', nombre=nombre, carnet=carnet, insc=insc, datameses=datameses, mora=mora))
	return render_template('auxenf.html', title='Auxiliares de Enfermeria', logeado=logeado, meses=meses)

@app.route("/confirmacionauxenf/<nombre>&<carnet>&<insc>&<datameses>&<mora>", methods=['GET', 'POST'])
def confirmacionauxenf(nombre, carnet, insc, datameses, mora):
	try:
		logeado = session['logeadocaja']
	except:
		return redirect(url_for('login'))
	nombre = str(nombre)
	carnet = str(carnet)
	insc = int(insc)
	mora = float(mora)
	cantidad = 0
	if datameses != 'None':
		meses = datameses.split(",")
		cantidad = len(meses)
	else:
		meses = ""
	try:
		conexion = pymysql.connect(host=Conhost, user=Conuser, password=Conpassword, db=Condb)
		try:
			with conexion.cursor() as cursor:
				consulta = 'SELECT idcodigos, precio from codigos where cod like "%AUXE%" order by cod asc'
				cursor.execute(consulta)
				cuotas = cursor.fetchall()
				pagoant = False
				for i in range(cantidad):
					consulta = f'SELECT idpagos from pagos where nombre = "{nombre}" and extra like "%{meses[i]}%" and extra like "%MENSAUXE%"'
					cursor.execute(consulta)
					pagosprev = cursor.fetchall()
					if len(pagosprev) > 0:
						pagoant = True
		finally:
			conexion.close()
	except (pymysql.err.OperationalError, pymysql.err.InternalError) as e:
		print("Ocurrió un error al conectar: ", e)
	if pagoant:
		return redirect(url_for('auxenf', mensaje = 1))
	total = 0
	if insc == 1:
		total = total + float(cuotas[0][1])
	for i in range(cantidad):
		total = total + float(cuotas[1][1])
	if mora > 0:
		total = total + mora
	if request.method == 'POST':
		try:
			conexion = pymysql.connect(host=Conhost, user=Conuser, password=Conpassword, db=Condb)
			try:
				with conexion.cursor() as cursor:
					idpago = 0
					if insc == 1:
						consulta = f"INSERT INTO pagos(idcod,nombre,carnet,total,fecha,extra,recibo, user) VALUES ({cuotas[0][0]},'{nombre}','{carnet}',{cuotas[0][1]},'{date.today()}','Inscripción Auxiliar de enfermeria',0, {session['idusercaja']});"
						cursor.execute(consulta)
						conexion.commit()
					for i in meses:
						consulta = f"INSERT INTO pagos(idcod,nombre,carnet,total,fecha,extra,recibo, user) VALUES ({cuotas[1][0]},'{nombre}','{carnet}',{cuotas[1][1]},'{date.today()}','{i}',0, {session['idusercaja']});"
						cursor.execute(consulta)
						conexion.commit()
					if mora > 0:
						consulta = f"INSERT INTO pagos(idcod,nombre,carnet,total,fecha,extra,recibo, user) VALUES ({cuotas[2][0]},'{nombre}','{carnet}',{mora},'{date.today()}','Mora Auxiliar de enfermeria',0, {session['idusercaja']});"
						cursor.execute(consulta)
						conexion.commit()
						consulta = "Select MAX(idpagos) from pagos;"
						cursor.execute(consulta)
						idpago = cursor.fetchone()
						idpago = idpago[0]
						imprimir = True
					else:
						imprimir = False
			finally:
				conexion.close()
		except (pymysql.err.OperationalError, pymysql.err.InternalError) as e:
			print("Ocurrió un error al conectar: ", e)
		if imprimir:
			return redirect(url_for('imprimir', idpagos=idpago))
		else:
			return redirect(url_for('auxenf'))
	return render_template('confirmacionauxenf.html', title='Confirmación Auxiliar de Enfermeria', logeado=logeado, nombre=nombre, carnet=carnet, cantidad=cantidad, total = total, insc=insc, meses=meses, mora = mora)

@app.route('/repauxenf', methods=['GET', 'POST'])
def repauxenf():
	try:
		logeado = session['logeadocaja']
	except:
		return redirect(url_for('login'))
	meses = ["Enero", "Febrero","Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
	try:
		conexion = pymysql.connect(host=Conhost, user=Conuser, password=Conpassword, db=Condb)
		try:
			with conexion.cursor() as cursor:
				datagen = []
				consulta = f"SELECT p.nombre, p.carnet from pagos p inner join codigos c on c.idcodigos = p.idcod where c.concepto like '%Inscripción Auxiliar de enfermeria%' and p.extra not like '%Retirado%' group by p.nombre order by p.nombre;"
				cursor.execute(consulta)
				nombres = cursor.fetchall()
				datos = []
				for i in nombres:
					data = [i[0], i[1]]
					for j in meses:
						consulta = f"SELECT DATE_FORMAT(p.fecha,'%d/%m/%Y') from pagos p inner join codigos c on c.idcodigos = p.idcod where c.concepto like '%Mensualidad Auxiliar de enfermeria%' and p.extra like '%{j}%' and p.nombre like '%{i[0]}%' order by p.nombre asc;"
						cursor.execute(consulta)
						pago = cursor.fetchall()
						if len(pago) > 0:
							data.append(pago[0][0])
						else:
							data.append("Pend")
					datos.append(data)
		finally:
			conexion.close()
	except (pymysql.err.OperationalError, pymysql.err.InternalError) as e:
		print("Ocurrió un error al conectar: ", e)
	return render_template('repauxenf.html', title="Reporte Auxiliares de Enfermeria", datos = datos, meses = meses, logeado=logeado)

@app.route('/repauxenfexcel', methods=['GET', 'POST'])
def repauxenfexcel():
	try:
		logeado = session['logeadocaja']
	except:
		return redirect(url_for('login'))
	meses = ["Enero", "Febrero","Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
	try:
		conexion = pymysql.connect(host=Conhost, user=Conuser, password=Conpassword, db=Condb)
		try:
			with conexion.cursor() as cursor:
				datagen = []
				consulta = f"SELECT p.nombre, p.carnet from pagos p inner join codigos c on c.idcodigos = p.idcod where c.concepto like '%Inscripción Auxiliar de enfermeria%' and p.extra not like '%Retirado%' group by p.nombre order by p.nombre;"
				cursor.execute(consulta)
				nombres = cursor.fetchall()
				datos = []
				for i in nombres:
					data = [i[0], i[1]]
					for j in meses:
						consulta = f"SELECT DATE_FORMAT(p.fecha,'%d/%m/%Y') from pagos p inner join codigos c on c.idcodigos = p.idcod where c.concepto like '%Mensualidad Auxiliar de enfermeria%' and p.extra like '%{j}%' and p.nombre like '%{i[0]}%' order by p.nombre asc;"
						cursor.execute(consulta)
						pago = cursor.fetchall()
						if len(pago) > 0:
							data.append(pago[0][0])
						else:
							data.append("Pend")
					datos.append(data)
		finally:
			conexion.close()
	except (pymysql.err.OperationalError, pymysql.err.InternalError) as e:
		print("Ocurrió un error al conectar: ", e)
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

	

	sh1.write(0,0,"Ciclo 1", tittle_style)
	sh1.write(3,0,"No.", header_style)
	sh1.write(3,1,"Nombre", header_style)
	sh1.write(3,2,"Carnet", header_style)
	for i in range(12):
		sh1.write(3,i+3,meses[i], header_style)

	if len(datos) > 0:
		for i in range(len(datos)):
			sh1.write(i+4,0,i+1, content_style1)
			sh1.write(i+4,1,datos[i][0], content_style1)
			sh1.write(i+4,2,datos[i][1], content_style1)
			for j in range(12):
				if datos[i][j+2] == "Pend":
					sh1.write(i+4,j+3,datos[i][j+2], content_style)
				else:
					sh1.write(i+4,j+3,datos[i][j+2], content_style1)
	
	sh1.col(0).width = 0x0d00 + len("Ciclo 1")
	try:
		sh1.col(1).width = 256 * (max([len(str(row[i])) for row in datos[i][0]]) + 1) * 10
		sh1.col(2).width = 256 * (max([len(str(row[i])) for row in datos[i][1]]) + 1) * 10
		sh1.col(3).width = 256 * (max([len(str(row[i])) for row in datos[i][2]]) + 1) * 10
		sh1.col(4).width = 256 * (max([len(str(row[i])) for row in datos[i][3]]) + 1) * 10
		sh1.col(5).width = 256 * (max([len(str(row[i])) for row in datos[i][4]]) + 1) * 10
	except:
		sh1.col(1).width = 256 * 20
		sh1.col(2).width = 256 * 30
		sh1.col(3).width = 256 * 20
		sh1.col(4).width = 256 * 20
		sh1.col(5).width = 256 * 20
	workbook.save(output)
	output.seek(0)

	return Response(output, mimetype="application/ms-excel", headers={"Content-Disposition":"attachment;filename=Reporteauxenf.xls"})

@app.route("/ingles", methods=['GET', 'POST'])
@app.route("/ingles/<mensaje>", methods=['GET', 'POST'])
def ingles(mensaje = 0):
	try:
		logeado = session['logeadocaja']
	except:
		return redirect(url_for('login'))
	meses = ["Enero", "Febrero","Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
	try:
		conexion = pymysql.connect(host=Conhost, user=Conuser, password=Conpassword, db=Condb)
		try:
			with conexion.cursor() as cursor:
				consulta = 'SELECT idcodigos, precio from codigos where cod like "%MAINGLES%" order by cod asc'
				cursor.execute(consulta)
				cuotas = cursor.fetchall()
		finally:
			conexion.close()
	except (pymysql.err.OperationalError, pymysql.err.InternalError) as e:
		print("Ocurrió un error al conectar: ", e)
	if request.method == 'POST':
		carnet = request.form["carnet"]
		if len(carnet) < 1:
			carnet = 0
		nombre = request.form["nombre"]
		try:
			ciclo = request.form["ciclo"]
		except:
			ciclo = 0
		cantidad = int(request.form["cant"]) + 1
		plan = request.form["plan"]
		ciclomen = request.form["ciclomen"]
		try:
			insc = request.form["insc"]
		except:
			insc = 0
		datameses = ""
		for i in range(cantidad):
			aux = f'mes{i}'
			mes = request.form[aux]
			if len(mes) > 0:
				if i > 0:
					datameses = f"{datameses},{mes}"
				else:
					datameses = f"{datameses}{mes}"
		if len(datameses) < 1:
			datameses = 'None'
		return redirect(url_for('confirmacioningles', nombre=nombre, carnet=carnet, plan = plan, insc=insc, datameses=datameses, ciclo=ciclo, ciclomen = ciclomen))
	return render_template('ingles.html', title='Ingles', logeado=logeado, meses=meses, cuotas=cuotas, mensaje = mensaje)

@app.route("/confirmacioningles/<nombre>&<carnet>&<plan>&<insc>&<datameses>&<ciclo>&<ciclomen>", methods=['GET', 'POST'])
def confirmacioningles(nombre, carnet, plan, insc, datameses, ciclo, ciclomen):
	try:
		logeado = session['logeadocaja']
	except:
		return redirect(url_for('login'))
	nombre = str(nombre)
	carnet = str(carnet)
	plan = int(plan)
	insc = int(insc)
	ciclomen = int(ciclomen)
	cantidad = 0
	if datameses != 'None':
		meses = datameses.split(",")
		cantidad = len(meses)
	else:
		meses = ""
	try:
		conexion = pymysql.connect(host=Conhost, user=Conuser, password=Conpassword, db=Condb)
		try:
			with conexion.cursor() as cursor:
				if plan == 1:
					consulta = 'SELECT idcodigos, precio from codigos where cod like "%MAINGLES%"'
					cursor.execute(consulta)
					datainsc = cursor.fetchall()
					consulta = 'SELECT idcodigos, precio from codigos where cod like "MEINGLEST%"'
					cursor.execute(consulta)
					datamen = cursor.fetchall()
				else:
					consulta = 'SELECT idcodigos, precio from codigos where cod like "%MAINGLES%"'
					cursor.execute(consulta)
					datainsc = cursor.fetchall()
					consulta = 'SELECT idcodigos, precio from codigos where cod like "MEINGLESS"'
					cursor.execute(consulta)
					datamen = cursor.fetchall()
				pagoant = False
				for i in range(cantidad):
					consulta = f'SELECT idpagos from pagos where nombre = "{nombre}" and extra like "%{meses[i]}%" and extra like "%{ciclomen}%"'
					cursor.execute(consulta)
					pagosprev = cursor.fetchall()
					if len(pagosprev) > 0:
						pagoant = True
		finally:
			conexion.close()
	except (pymysql.err.OperationalError, pymysql.err.InternalError) as e:
		print("Ocurrió un error al conectar: ", e)
	if pagoant:
		return redirect(url_for('ingles', mensaje = 1))
	total = 0
	if insc == 1:
		total = total + float(datainsc[0][1]) + float(datainsc[1][1])
	for i in datamen:
		for j in range(cantidad):
			total = total + float(i[1])

	if request.method == 'POST':
		try:
			conexion = pymysql.connect(host=Conhost, user=Conuser, password=Conpassword, db=Condb)
			try:
				with conexion.cursor() as cursor:
					idpagos = []
					if insc == 1:
						consulta = "INSERT INTO pagos(idcod,nombre,carnet,total,fecha,extra,recibo, user) VALUES (%s,%s,%s,%s,%s,%s,%s, %s);"
						cursor.execute(consulta, (datainsc[0][0], nombre, carnet,datainsc[0][1], date.today(), 'Ciclo: ' + str(ciclo) ,0, session['idusercaja']))
						conexion.commit()
						consulta = "Select MAX(idpagos) from pagos;"
						cursor.execute(consulta)
						idpago = cursor.fetchone()
						idpago = idpago[0]
						idpagos.append(idpago)
						consulta = "INSERT INTO pagos(idcod,nombre,carnet,total,fecha,extra,recibo, user) VALUES (%s,%s,%s,%s,%s,%s,%s, %s);"
						cursor.execute(consulta, (datainsc[1][0], nombre, carnet,datainsc[1][1], date.today(), 'Ciclo: ' + str(ciclo) ,0, session['idusercaja']))
						conexion.commit()
						consulta = "Select MAX(idpagos) from pagos;"
						cursor.execute(consulta)
						idpago = cursor.fetchone()
						idpago = idpago[0]
						idpagos.append(idpago)
					for i in range(cantidad):
						for j in datamen:
							consulta = "INSERT INTO pagos(idcod,nombre,carnet,total,fecha,extra,recibo, user) VALUES (%s,%s,%s,%s,%s,%s,%s, %s);"
							cursor.execute(consulta, (j[0], nombre, carnet, j[1], date.today(), 'Mes: ' + meses[i] + ", Ciclo: " + str(ciclomen),0, session['idusercaja']))
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
	return render_template('confirmacioningles.html', title='Confirmación Ingles', logeado=logeado, nombre=nombre, carnet=carnet, cantidad=cantidad, total = total, datainsc=datainsc, datamen=datamen, insc=insc, meses=meses, ciclo=ciclo, ciclomen = ciclomen)

@app.route('/repingles', methods=['GET', 'POST'])
def repingles():
	try:
		logeado = session['logeadocaja']
	except:
		return redirect(url_for('login'))
	meses1 = ["Agosto", "Septiembre", "Octubre"]
	meses2 = ["Julio", "Agosto", "Septiembre"]
	meses3 = ["Octubre", "Noviembre", "Diciembre"]
	meses4 = ["Octubre", "Noviembre", "Diciembre"]
	mesesbase = []
	mesesbase.append(meses1)
	mesesbase.append(meses2)
	mesesbase.append(meses3)
	mesesbase.append(meses4)
	try:
		conexion = pymysql.connect(host=Conhost, user=Conuser, password=Conpassword, db=Condb)
		try:
			with conexion.cursor() as cursor:
				datagen = []
				for n in range(4):
					ciclo = n+1
					datos = []
					consulta = f"SELECT p.nombre, p.carnet from pagos p inner join codigos c on c.idcodigos = p.idcod where c.concepto like '%Mensualidad Ingles Trimestral (A)%' and p.extra like '%{ciclo}%' and (p.extra like '%{mesesbase[n][0]}%' or p.extra like '%{mesesbase[n][1]}%' or p.extra like '%{mesesbase[n][2]}%')  and p.fecha > DATE_SUB(CURDATE(),INTERVAL 6 MONTH) group by p.nombre order by p.nombre;"
					cursor.execute(consulta)
					nombres = cursor.fetchall()
					for i in nombres:
						data = [i[0], i[1]]
						for j in mesesbase[n]:
							consulta = f"SELECT DATE_FORMAT(p.fecha,'%d/%m/%Y') from pagos p inner join codigos c on c.idcodigos = p.idcod where c.concepto like '%Mensualidad Ingles Trimestral (A)%' and p.extra like '%{j}%' and p.extra like '%{ciclo}%' and p.nombre like '%{i[0]}%' and p.fecha > DATE_SUB(CURDATE(),INTERVAL 6 MONTH) order by p.nombre asc;"
							print(consulta)
							cursor.execute(consulta)
							pago = cursor.fetchall()
							if len(pago) > 0:
								data.append(pago[0][0])
							else:
								data.append("Pend")
						datos.append(data)
					datagen.append(datos)
			# Con fetchall traemos todas las filas
		finally:
			conexion.close()
	except (pymysql.err.OperationalError, pymysql.err.InternalError) as e:
		print("Ocurrió un error al conectar: ", e)
	return render_template('repingles.html', title="Reporte ingles", datos = datagen, meses = mesesbase, logeado=logeado)

@app.route('/repinglesexcel', methods=['GET', 'POST'])
def repinglesexcel():
	try:
		logeado = session['logeadocaja']
	except:
		return redirect(url_for('login'))
	meses1 = ["Agosto", "Septiembre", "Octubre"]
	meses2 = ["Julio", "Agosto", "Septiembre"]
	meses3 = ["Octubre", "Noviembre", "Diciembre"]
	meses4 = ["Octubre", "Noviembre", "Diciembre"]
	mesesbase = []
	mesesbase.append(meses1)
	mesesbase.append(meses2)
	mesesbase.append(meses3)
	mesesbase.append(meses4)
	try:
		conexion = pymysql.connect(host=Conhost, user=Conuser, password=Conpassword, db=Condb)
		try:
			with conexion.cursor() as cursor:
				datagen = []
				for n in range(4):
					ciclo = n+1
					datos = []
					consulta = f"SELECT p.nombre, p.carnet from pagos p inner join codigos c on c.idcodigos = p.idcod where c.concepto like '%Mensualidad Ingles Trimestral (A)%' and p.extra like '%{ciclo}%' and (p.extra like '%{mesesbase[n][0]}%' or p.extra like '%{mesesbase[n][1]}%' or p.extra like '%{mesesbase[n][2]}%')  and p.fecha > DATE_SUB(CURDATE(),INTERVAL 6 MONTH) group by p.nombre order by p.nombre;"
					cursor.execute(consulta)
					nombres = cursor.fetchall()
					for i in nombres:
						data = [i[0], i[1]]
						for j in mesesbase[n]:
							consulta = f"SELECT DATE_FORMAT(p.fecha,'%d/%m/%Y') from pagos p inner join codigos c on c.idcodigos = p.idcod where c.concepto like '%Mensualidad Ingles Trimestral (A)%' and p.extra like '%{j}%' and p.extra like '%{ciclo}%' and p.nombre like '%{i[0]}%' and p.fecha > DATE_SUB(CURDATE(),INTERVAL 6 MONTH) order by p.nombre asc;"
							print(consulta)
							cursor.execute(consulta)
							pago = cursor.fetchall()
							if len(pago) > 0:
								data.append(pago[0][0])
							else:
								data.append("Pend")
						datos.append(data)
					datagen.append(datos)
			# Con fetchall traemos todas las filas
		finally:
			conexion.close()
	except (pymysql.err.OperationalError, pymysql.err.InternalError) as e:
		print("Ocurrió un error al conectar: ", e)
	output = io.BytesIO()
	workbook = xlwt.Workbook(encoding="utf-8")
	sh1 = workbook.add_sheet("Ciclo 1")

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

	

	sh1.write(0,0,"Ciclo 1", tittle_style)
	sh1.write(3,0,"No.", header_style)
	sh1.write(3,1,"Nombre", header_style)
	sh1.write(3,2,"Carnet", header_style)
	for i in range(3):
		sh1.write(3,i+3,mesesbase[0][i], header_style)

	if len(datagen[0]) > 0:
		for i in range(len(datagen[0])):
			sh1.write(i+4,0,i+1, content_style1)
			sh1.write(i+4,1,datagen[0][i][0], content_style1)
			sh1.write(i+4,2,datagen[0][i][1], content_style1)
			if datagen[0][i][2] == "Pend":
				sh1.write(i+4,3,datagen[0][i][2], content_style)
			else:
				sh1.write(i+4,3,datagen[0][i][2], content_style1)
			if datagen[0][i][3] == "Pend":
				sh1.write(i+4,4,datagen[0][i][3], content_style)
			else:
				sh1.write(i+4,4,datagen[0][i][3], content_style1)
			if datagen[0][i][4] == "Pend":
				sh1.write(i+4,5,datagen[0][i][4], content_style)
			else:
				sh1.write(i+4,5,datagen[0][i][4], content_style1)
	
	sh1.col(0).width = 0x0d00 + len("Ciclo 1")
	try:
		sh1.col(1).width = 256 * (max([len(str(row[i])) for row in datagen[0][i][0]]) + 1) * 10
		sh1.col(2).width = 256 * (max([len(str(row[i])) for row in datagen[0][i][1]]) + 1) * 10
		sh1.col(3).width = 256 * (max([len(str(row[i])) for row in datagen[0][i][2]]) + 1) * 10
		sh1.col(4).width = 256 * (max([len(str(row[i])) for row in datagen[0][i][3]]) + 1) * 10
		sh1.col(5).width = 256 * (max([len(str(row[i])) for row in datagen[0][i][4]]) + 1) * 10
	except:
		sh1.col(1).width = 256 * 20
		sh1.col(2).width = 256 * 20
		sh1.col(3).width = 256 * 20
		sh1.col(4).width = 256 * 20
		sh1.col(5).width = 256 * 20
	
	sh2 = workbook.add_sheet("Ciclo 2")
	sh2.write(0,0,"Ciclo 2", tittle_style)

	sh2.write(3,0,"No.", header_style)
	sh2.write(3,1,"Nombre", header_style)
	sh2.write(3,2,"Carnet", header_style)
	for i in range(3):
		sh2.write(3,i+3,mesesbase[1][i], header_style)

	if len(datagen[1]) > 0:
		for i in range(len(datagen[1])):
			sh2.write(i+4,0,i+1, content_style1)
			sh2.write(i+4,1,datagen[1][i][0], content_style1)
			sh2.write(i+4,2,datagen[1][i][1], content_style1)
			if datagen[1][i][2] == "Pend":
				sh2.write(i+4,3,datagen[1][i][2], content_style)
			else:
				sh2.write(i+4,3,datagen[1][i][2], content_style1)
			if datagen[1][i][3] == "Pend":
				sh2.write(i+4,4,datagen[1][i][3], content_style)
			else:
				sh2.write(i+4,4,datagen[1][i][3], content_style1)
			if datagen[1][i][4] == "Pend":
				sh2.write(i+4,5,datagen[1][i][4], content_style)
			else:
				sh2.write(i+4,5,datagen[1][i][4], content_style1)
	
	sh2.col(0).width = 0x0d00 + len("Ciclo 2")
	try:
		sh2.col(1).width = 256 * (max([len(str(row[i])) for row in datagen[1][i][0]]) + 1) * 10
		sh2.col(2).width = 256 * (max([len(str(row[i])) for row in datagen[1][i][1]]) + 1) * 10
		sh2.col(3).width = 256 * (max([len(str(row[i])) for row in datagen[1][i][2]]) + 1) * 10
		sh2.col(4).width = 256 * (max([len(str(row[i])) for row in datagen[1][i][3]]) + 1) * 10
		sh2.col(5).width = 256 * (max([len(str(row[i])) for row in datagen[1][i][4]]) + 1) * 10
	except:
		sh2.col(1).width = 256 * 20
		sh2.col(2).width = 256 * 20
		sh2.col(3).width = 256 * 20
		sh2.col(4).width = 256 * 20
		sh2.col(5).width = 256 * 20

	sh3 = workbook.add_sheet("Ciclo 3")
	sh3.write(0,0,"Ciclo 3", tittle_style)

	sh3.write(3,0,"No.", header_style)
	sh3.write(3,1,"Nombre", header_style)
	sh3.write(3,2,"Carnet", header_style)
	for i in range(3):
		sh3.write(3,i+3,mesesbase[2][i], header_style)

	if len(datagen[2]) > 0:
		for i in range(len(datagen[2])):
			sh3.write(i+4,0,i+1, content_style1)
			sh3.write(i+4,1,datagen[2][i][0], content_style1)
			sh3.write(i+4,2,datagen[2][i][1], content_style1)
			if datagen[2][i][2] == "Pend":
				sh3.write(i+4,3,datagen[2][i][2], content_style)
			else:
				sh3.write(i+4,3,datagen[2][i][2], content_style1)
			if datagen[2][i][3] == "Pend":
				sh3.write(i+4,4,datagen[2][i][3], content_style)
			else:
				sh3.write(i+4,4,datagen[2][i][3], content_style1)
			if datagen[2][i][4] == "Pend":
				sh3.write(i+4,5,datagen[2][i][4], content_style)
			else:
				sh3.write(i+4,5,datagen[2][i][4], content_style1)
	
	sh3.col(0).width = 0x0d00 + len("Ciclo 3")
	try:
		sh3.col(1).width = 256 * (max([len(str(row[i])) for row in datagen[2][i][0]]) + 1) * 20
		sh3.col(2).width = 256 * (max([len(str(row[i])) for row in datagen[2][i][1]]) + 1) * 10
		sh3.col(3).width = 256 * (max([len(str(row[i])) for row in datagen[2][i][2]]) + 1) * 10
		sh3.col(4).width = 256 * (max([len(str(row[i])) for row in datagen[2][i][3]]) + 1) * 10
		sh3.col(5).width = 256 * (max([len(str(row[i])) for row in datagen[2][i][4]]) + 1) * 10
	except:
		sh3.col(1).width = 256 * 20
		sh3.col(2).width = 256 * 20
		sh3.col(3).width = 256 * 20
		sh3.col(4).width = 256 * 20
		sh3.col(5).width = 256 * 20

	sh4 = workbook.add_sheet("Ciclo 4")
	sh4.write(0,0,"Ciclo 4", tittle_style)
	sh4.write(3,0,"No.", header_style)
	sh4.write(3,1,"Nombre", header_style)
	sh4.write(3,2,"Carnet", header_style)
	for i in range(3):
		sh4.write(3,i+3,mesesbase[3][i], header_style)

	if len(datagen[3]) > 0:
		for i in range(len(datagen[3])):
			sh4.write(i+4,0,i+1, content_style1)
			sh4.write(i+4,1,datagen[3][i][0], content_style1)
			sh4.write(i+4,2,datagen[3][i][1], content_style1)
			if datagen[3][i][2] == "Pend":
				sh4.write(i+4,3,datagen[3][i][2], content_style)
			else:
				sh4.write(i+4,3,datagen[3][i][2], content_style1)
			if datagen[3][i][3] == "Pend":
				sh4.write(i+4,4,datagen[3][i][3], content_style)
			else:
				sh4.write(i+4,4,datagen[3][i][3], content_style1)
			if datagen[3][i][4] == "Pend":
				sh4.write(i+4,5,datagen[3][i][4], content_style)
			else:
				sh4.write(i+4,5,datagen[3][i][4], content_style1)
	
	sh4.col(0).width = 0x0d00 + len("Ciclo 4")
	try:
		sh4.col(1).width = 256 * (max([len(str(row[i])) for row in datagen[3][i][0]]) + 1) * 10
		sh4.col(2).width = 256 * (max([len(str(row[i])) for row in datagen[3][i][1]]) + 1) * 10
		sh4.col(3).width = 256 * (max([len(str(row[i])) for row in datagen[3][i][2]]) + 1) * 10
		sh4.col(4).width = 256 * (max([len(str(row[i])) for row in datagen[3][i][3]]) + 1) * 10
		sh4.col(5).width = 256 * (max([len(str(row[i])) for row in datagen[3][i][4]]) + 1) * 10
	except:
		sh4.col(1).width = 256 * 20
		sh4.col(2).width = 256 * 20
		sh4.col(3).width = 256 * 20
		sh4.col(4).width = 256 * 20
		sh4.col(5).width = 256 * 20
	workbook.save(output)
	output.seek(0)

	return Response(output, mimetype="application/ms-excel", headers={"Content-Disposition":"attachment;filename=Reporteingles.xls"})

@app.route("/laboratorio", methods=['GET', 'POST'])
def laboratorio():
	try:
		logeado = session['logeadocaja']
	except:
		return redirect(url_for('login'))
	fechaact = datetime.today().strftime('%Y-%m-%d')
	try:
		conexion = pymysql.connect(host=Conhost, user=Conuser, password=Conpassword, db=Condb)
		try:
			with conexion.cursor() as cursor:
				consulta = f'SELECT nombre, idtipoexamen, precio, idexameneslab from exameneslab where DATE(fechaactivo) = "0000-00-00" or DATE(fechaactivo) > "{fechaact}" order by idtipoexamen;'
				cursor.execute(consulta)
				examenes = cursor.fetchall()
				consulta = 'SELECT nombre, descuento from empresa order by nombre asc;'
				cursor.execute(consulta)
				empresas = cursor.fetchall()
				consulta = 'SELECT nombre, idtipoexamen from tipoexamen order by idtipoexamen asc;'
				cursor.execute(consulta)
				tipoexamen = cursor.fetchall()
		finally:
			conexion.close()
	except (pymysql.err.OperationalError, pymysql.err.InternalError) as e:
		print("Ocurrió un error al conectar: ", e)
	if request.method == 'POST':
		carnet = request.form["carnet"]
		if len(carnet) < 1:
			carnet = 0
		nombre = request.form["nombre"]
		cantidad = request.form["cant"]
		dataexamenes = ""
		for i in range(int(cantidad)):
			aux = f"examen{i}"
			idexamen = request.form[aux]
			aux1 = f"precio{i}"
			precio = request.form[aux1]
			dataexamenes = f"{dataexamenes}{idexamen},{precio};"
		return redirect(url_for('confirmacionlab', nombre=nombre, carnet=carnet, dataexamenes=dataexamenes))
	return render_template('laboratorio.html', title='Laboratorio', logeado=logeado, examenes=examenes, empresas=empresas, tipoexamen=tipoexamen)

@app.route("/confirmacionlab/<nombre>&<carnet>&<dataexamenes>", methods=['GET', 'POST'])
def confirmacionlab(nombre, carnet, dataexamenes):
	try:
		logeado = session['logeadocaja']
	except:
		return redirect(url_for('login'))
	nombre = str(nombre)
	carnet = str(carnet)
	examenes = []
	arreglo = dataexamenes.split(";")
	for i in arreglo:
		examen = []
		exaaux = i.split(",")
		for i in exaaux:
			examen.append(i)
		examenes.append(examen)
	examenes.pop()
	cantidad = len(examenes)
	total = 0
	dataaux = []
	for i in examenes:
		datae = []
		total = total + float(i[1])
		try:
			conexion = pymysql.connect(host=Conhost, user=Conuser, password=Conpassword, db=Condb)
			try:
				with conexion.cursor() as cursor:
					consulta = f"SELECT e.nombre, t.nombre from exameneslab e inner join tipoexamen t on e.idtipoexamen = t.idtipoexamen where e.idexameneslab = {i[0]};"
					cursor.execute(consulta)
					queryinfo = cursor.fetchone()
					datae.append(i[0])
					datae.append(queryinfo[0])
					datae.append(queryinfo[1])
					datae.append(i[1])
					dataaux.append(datae)
			finally:
				conexion.close()
		except (pymysql.err.OperationalError, pymysql.err.InternalError) as e:
			print("Ocurrió un error al conectar: ", e)
	if request.method == 'POST':
		try:
			conexion = pymysql.connect(host=Conhost, user=Conuser, password=Conpassword, db=Condb)
			try:
				with conexion.cursor() as cursor:
					consulta = "SELECT idcodigos from codigos where cod = 'LAB'"
					cursor.execute(consulta)
					codlab = cursor.fetchone()
					codlab = codlab[0]
					idpagos = []
					for i in dataaux:
						consulta = "INSERT INTO pagos(idcod,nombre,carnet,total,fecha,extra,recibo, user) VALUES (%s,%s,%s,%s,%s,%s,%s, %s);"
						cursor.execute(consulta, (codlab, nombre, carnet, i[3], date.today(), f"{i[2]} -  {i[1]}" ,0, session['idusercaja']))
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
	return render_template('confirmacionlab.html', title='Confirmación Laboratorio', logeado=logeado, dataaux=dataaux, nombre=nombre, carnet=carnet, cantidad=cantidad, total = total)

@app.route("/eliminarpago/<idpago>", methods=['GET', 'POST'])
def eliminarpago(idpago):
	try:
		logeado = session['logeadocaja']
	except:
		return redirect(url_for('login'))
	try:
		conexion = pymysql.connect(host=Conhost, user=Conuser, password=Conpassword, db=Condb)
		try:
			with conexion.cursor() as cursor:
				consulta = f'DELETE from pagos where idpagos = {idpago};'
				cursor.execute(consulta)
				conexion.commit()
		finally:
			conexion.close()
	except (pymysql.err.OperationalError, pymysql.err.InternalError) as e:
		print("Ocurrió un error al conectar: ", e)
	return redirect(url_for('repdiario'))

@app.route("/editarpago/<idpago>", methods=['GET', 'POST'])
def editarpago(idpago):
	try:
		logeado = session['logeadocaja']
	except:
		return redirect(url_for('login'))
	try:
		conexion = pymysql.connect(host=Conhost, user=Conuser, password=Conpassword, db=Condb)
		try:
			with conexion.cursor() as cursor:
				consulta = f'SELECT p.idcod, p.nombre, p.carnet, p.total, p.fecha, p.extra from codigos c inner join pagos p on p.idcod = c.idcodigos where p.idpagos = {idpago};'
				cursor.execute(consulta)
				datapago = cursor.fetchall()
				datapago = datapago[0]
				consulta = 'SELECT idcodigos, concepto from codigos order by concepto;'
				cursor.execute(consulta)
				codigos = cursor.fetchall()
		finally:
			conexion.close()
	except (pymysql.err.OperationalError, pymysql.err.InternalError) as e:
		print("Ocurrió un error al conectar: ", e)
	if request.method == 'POST':
		carnet = request.form["carnet"]
		nombre = request.form["nombre"]
		codigo = request.form["codigo"]
		extra = request.form["extra"]
		fecha = request.form["fecha"]
		total = request.form["total"]
		if len(carnet) < 1:
			carnet = datapago[2]
		if len(nombre) < 1:
			nombre = datapago[1]
		if len(extra) < 1:
			extra = datapago[5]
		if len(total) < 1:
			total = datapago[3]

		try:
			conexion = pymysql.connect(host=Conhost, user=Conuser, password=Conpassword, db=Condb)
			try:
				with conexion.cursor() as cursor:
					consulta = 'UPDATE pagos set nombre=%s, carnet=%s, total=%s, fecha=%s, extra=%s, idcod=%s, user=%s where idpagos=%s;'
					cursor.execute(consulta, (nombre, carnet,total, fecha, extra, codigo, session['idusercaja'], idpago))
				conexion.commit()
			finally:
				conexion.close()
		except (pymysql.err.OperationalError, pymysql.err.InternalError) as e:
			print("Ocurrió un error al conectar: ", e)
		return redirect(url_for('repdiario'))
	return render_template('editarpago.html', title='Editar Pago', logeado=logeado, datapago=datapago, codigos=codigos)

@app.route('/', methods=['GET', 'POST'])
@app.route('/home', methods=['GET', 'POST'])
@app.route('/login', methods=['GET', 'POST'])
def login():
	try:
		logeado = session['logeadocaja']
	except:
		logeado = 0
	if logeado != 0:
		return redirect(url_for('pagos'))
	if request.method == 'POST':
		user = request.form["user"]
		pwd = request.form["pwd"]
		try:
			conexion = pymysql.connect(host=Conhost, user=Conuser, password=Conpassword, db=Condb)
			try:
				with conexion.cursor() as cursor:
					consulta = f"SELECT iduser, nombre, apellido FROM user WHERE user = '{user}' and pwd = md5('{pwd}')"
					cursor.execute(consulta)
					data = cursor.fetchall()
					if len(data) == 0:
						return render_template('login.html', title='Iniciar sesión', logeado=logeado, mensaje="Datos inválidos, intente nuevamente")
					else:
						session['logeadocaja'] = 1
						session['idusercaja'] = data[0][0]
						session['nombreusercaja'] = data[0][1]
						session['apellidousercaja'] = data[0][2]
						session['usercaja'] = user
						return redirect(url_for('pagos'))
			finally:
				conexion.close()
		except (pymysql.err.OperationalError, pymysql.err.InternalError) as e:
			print("Ocurrió un error al conectar: ", e)
	return render_template('login.html', title='Iniciar sesión', logeado=logeado, mensaje="")

@app.route("/logout")
def logout():
	session['logeadocaja'] = 0
	session['idusercaja'] = ''
	session['nombreusercaja'] = ''
	session['apellidousercaja'] = ''
	session['usercaja'] = ''
	return redirect(url_for('login'))

@app.route("/crearusuario", methods=['GET', 'POST'])
def crearusuario():
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
	return render_template('crearusuario.html', title='Nuevo Usuario', mensaje=mensaje)

@app.route('/optica', methods=['GET', 'POST'])
def optica():
	try:
		logeado = session['logeadocaja']
	except:
		return redirect(url_for('login'))
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
		if len(aro) < 1:
			aro = 0
		if len(lente) < 1:
			lente = 0
		return redirect(url_for('confirmacionopt', carnet = carnet, nombre = nombre, aro=aro, lente=lente, exavis=exavis, exaviseps = exaviseps))
	return render_template('optica.html', title="Óptica", logeado=logeado)

@app.route('/confirmacionopt/<carnet>&<nombre>&<aro>&<lente>&<exavis>&<exaviseps>', methods=['GET', 'POST'])
def confirmacionopt(carnet, nombre, aro, lente, exavis, exaviseps):
	try:
		logeado = session['logeadocaja']
	except:
		return redirect(url_for('login'))
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
	return render_template('confirmacionopt.html', title="Confirmación Óptica", carnet = carnet, nombre = nombre, aro=aro, lente=lente, exavis=exavis, exaviseps=exaviseps,logeado=logeado)

@app.route('/i', methods=['GET', 'POST'])
def i():
	try:
		logeado = session['logeadocaja']
	except:
		return redirect(url_for('login'))
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
	return render_template('inscripciones.html', title="Inscripciones", carreras=carreras, logeado=logeado)

@app.route('/confirmacioni/<carrera>&<carnet>&<nombre>&<rinsc>&<rint>&<rrein>&<mesextra>&<exavis>', methods=['GET', 'POST'])
def confirmacioni(carrera, carnet, nombre, rinsc, rint, rrein, mesextra, exavis):
	try:
		logeado = session['logeadocaja']
	except:
		return redirect(url_for('login'))
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
	examenvista = 0
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
					if rrein != 0:
						consulta = "INSERT INTO pagos(idcod,nombre,carnet,total,fecha,extra,recibo, user) VALUES (%s,%s,%s,%s,%s,%s,%s,%s);"
						cursor.execute(consulta, (3, nombre, carnet, 100, date.today(), "Internet Reinscripcion " +str(data[0][3]),0, session['idusercaja']))
						conexion.commit()
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
						examenvista = 1
						consulta = "Select MAX(idpagos) from pagos;"
						cursor.execute(consulta)
						pagoexamen = cursor.fetchone()
						pagoexamen = pagoexamen[0]
			finally:
				conexion.close()
		except (pymysql.err.OperationalError, pymysql.err.InternalError) as e:
			print("Ocurrió un error al conectar: ", e)
		if examenvista == 0:
			return redirect(url_for('i'))
		else:
			return redirect(url_for('imprimir', idpagos=pagoexamen))
	return render_template('confirmacioni.html', title="Confirmación", carrera = carrera, carnet = carnet, nombre = nombre, data=data, rinsc=rinsc, rint=rint, rrein=rrein, mesextra=mesextra, logeado=logeado)

@app.route('/repi', methods=['GET', 'POST'])
def repi():
	try:
		logeado = session['logeadocaja']
	except:
		return redirect(url_for('login'))
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
	return render_template('repi.html', title="Reporte inscripciones", data = data, suma=suma, carreras=carreras, logeado=logeado)

@app.route('/ini', methods=['GET', 'POST'])
def ini():
	try:
		logeado = session['logeadocaja']
	except:
		return redirect(url_for('login'))
	try:
		conexion = pymysql.connect(host=Conhost, user=Conuser, password=Conpassword, db=Condb)
		try:
			with conexion.cursor() as cursor:
				cursor.execute("SELECT idcarreras, codigo FROM carreras;")
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
		return redirect(url_for('confirmacionini', carrera = datacarrera, carnet = datacarnet, nombre = datanombre))
	return render_template('internetins.html', title="Internet Inscripciones",  carreras=carreras, logeado=logeado)

@app.route('/confirmacionini/<carrera>&<carnet>&<nombre>', methods=['GET', 'POST'])
def confirmacionini(carrera, carnet, nombre):
	try:
		logeado = session['logeadocaja']
	except:
		return redirect(url_for('login'))
	carrera = str(carrera)
	carnet = str(carnet)
	nombre = str(nombre)
	if request.method == "POST":
		try:
			conexion = pymysql.connect(host=Conhost, user=Conuser, password=Conpassword, db=Condb)
			try:
				with conexion.cursor() as cursor:
					consulta1 = f'SELECT idcodigos, precio FROM codigos WHERE cod = "IN{carrera}"'
					cursor.execute(consulta1)
					precios1 = cursor.fetchall()
					print(precios1[0])
					consulta = "INSERT INTO pagos(idcod,nombre,carnet,total,fecha,extra,recibo,user) VALUES (%s,%s,%s,%s,%s,%s,%s.%s);"
					cursor.execute(consulta, (precios1[0][0], nombre, carnet, precios1[0][1], date.today(), "",0,session['idusercaja']))
				conexion.commit()
			finally:
				conexion.close()
		except (pymysql.err.OperationalError, pymysql.err.InternalError) as e:
			print("Ocurrió un error al conectar: ", e)
		return redirect(url_for('ini'))
	return render_template('confirmacionini.html', title="Confirmación", carrera = carrera, carnet = carnet, nombre = nombre, logeado=logeado)

@app.route('/repini', methods=['GET', 'POST'])
def repini():
	try:
		logeado = session['logeadocaja']
	except:
		return redirect(url_for('login'))
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
				where d.cod LIKE 'IN%'
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
	return render_template('repini.html', title="Reporte internet", data = data, suma=suma, carreras=carreras, logeado=logeado)

@app.route('/ir', methods=['GET', 'POST'])
def ir():
	try:
		logeado = session['logeadocaja']
	except:
		return redirect(url_for('login'))
	try:
		conexion = pymysql.connect(host=Conhost, user=Conuser, password=Conpassword, db=Condb)
		try:
			with conexion.cursor() as cursor:
				cursor.execute("SELECT idcarreras, codigo FROM carreras;")
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
		return redirect(url_for('confirmacionir', carrera = datacarrera, carnet = datacarnet, nombre = datanombre))
	return render_template('internetreins.html', title="Internet Reinscripciones",  carreras=carreras, logeado=logeado)

@app.route('/confirmacionir/<carrera>&<carnet>&<nombre>', methods=['GET', 'POST'])
def confirmacionir(carrera, carnet, nombre):
	try:
		logeado = session['logeadocaja']
	except:
		return redirect(url_for('login'))
	carrera = str(carrera)
	carnet = str(carnet)
	nombre = str(nombre)
	if request.method == "POST":
		try:
			conexion = pymysql.connect(host=Conhost, user=Conuser, password=Conpassword, db=Condb)
			try:
				with conexion.cursor() as cursor:
					consulta = f'SELECT idcodigos, precio FROM codigos WHERE cod = "IR{carrera}"'
					cursor.execute(consulta)
					precios1 = cursor.fetchall()
					print(precios1[0])
					consulta = "INSERT INTO pagos(idcod,nombre,carnet,total,fecha,extra, recibo, user) VALUES (%s,%s,%s,%s,%s,%s,%s,%s);"
					cursor.execute(consulta, (precios1[0][0], nombre, carnet, precios1[0][1], date.today(), "",0,session['idusercaja']))
				conexion.commit()
			finally:
				conexion.close()
		except (pymysql.err.OperationalError, pymysql.err.InternalError) as e:
			print("Ocurrió un error al conectar: ", e)
		return redirect(url_for('ir'))
	return render_template('confirmacionini.html', title="Confirmación", carrera = carrera, carnet = carnet, nombre = nombre, logeado=logeado)

@app.route('/repir', methods=['GET', 'POST'])
def repir():
	try:
		logeado = session['logeadocaja']
	except:
		return redirect(url_for('login'))
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
				where d.cod LIKE 'IR%'
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

	return render_template('repir.html', title="Reporte internet reingreso", data = data, suma=suma, carreras=carreras, logeado=logeado)

@app.route('/extra', methods=['GET', 'POST'])
def extra():
	try:
		logeado = session['logeadocaja']
	except:
		return redirect(url_for('login'))
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
	return render_template('extra.html', title="Pagos extra", data = data, logeado=logeado)

@app.route('/confirmacionextra/<carnet>&<nombre>&<idp>&<cod>&<descripcion>', methods=['GET', 'POST'])
def confirmacionextra(carnet, nombre, idp, cod, descripcion):
	try:
		logeado = session['logeadocaja']
	except:
		return redirect(url_for('login'))
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
		if  "Congreso" in cod:
			idpago = int(idpago)
			idpago = str(idpago)
			number = idpago.rjust(6, '0')
			number = f"{number}98765"
			barcode_format = barcode.get_barcode_class('upc')
			#Generate barcode and render as image
			my_barcode = barcode_format(number, writer=ImageWriter())
			#Save barcode as PNG
			aux = f"C:\\Users\\galileoserver\\Documents\\sispagosGalileo\\flaskapp\\static\\codbars\\{idpago}"
			my_barcode.save(aux)
			#Inserción a archivo de Google Sheets
			scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
			creds = ServiceAccountCredentials.from_json_keyfile_name(r"C:\Users\galileoserver\Documents\sispagosGalileo\flaskapp\clientcongreso.json", scope)
			client = gspread.authorize(creds)
			sheet = client.open("Tabulación Congreso").sheet1
			row = [nombre, carnet, descripcion, idpago]
			index = 2
			sheet.insert_row(row, index)
		return redirect(url_for('imprimir', idpagos = idpago))
	return render_template('confirmacionextra.html', title="Confirmación", carnet = carnet, nombre = nombre, idp = idp, cod = cod, logeado=logeado, descripcion=descripcion)

@app.route('/repextra', methods=['GET', 'POST'])
def repextra():
	try:
		logeado = session['logeadocaja']
	except:
		return redirect(url_for('login'))
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
	return render_template('repextra.html', title="Reporte Pagos Extra", data = data, suma=suma, logeado=logeado)

@app.route('/u', methods=['GET', 'POST'])
def u():
	try:
		logeado = session['logeadocaja']
	except:
		return redirect(url_for('login'))
	try:
		conexion = pymysql.connect(host=Conhost, user=Conuser, password=Conpassword, db=Condb)
		try:
			with conexion.cursor() as cursor:
				cursor.execute("SELECT idcodigos, cod, concepto FROM codigos WHERE uniformes = 1 ORDER BY cod asc;")
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
		uid = data[0]
		ucod = data[1]
		datatotal = request.form["total"]
		datatalla = request.form["talla"]
		return redirect(url_for('confirmacionu', uid = uid, carnet = datacarnet, nombre = datanombre, total = datatotal, talla= datatalla, ucod = ucod))
	return render_template('uniformes.html', title="Uniformes",  carreras=carreras, logeado=logeado)

@app.route('/confirmacionu/<uid>&<carnet>&<nombre>&<total>&<talla>&<ucod>', methods=['GET', 'POST'])
def confirmacionu(uid, carnet, nombre, total, talla, ucod):
	try:
		logeado = session['logeadocaja']
	except:
		return redirect(url_for('login'))
	uid = int(uid)
	carnet = str(carnet)
	nombre = str(nombre)
	total = float(total)
	talla = str(talla)
	ucod = str(ucod)
	if request.method == "POST":
		try:
			conexion = pymysql.connect(host=Conhost, user=Conuser, password=Conpassword, db=Condb)
			try:
				with conexion.cursor() as cursor:
					consulta = "INSERT INTO pagos(idcod,nombre,carnet,total,fecha,extra,recibo,user) VALUES (%s,%s,%s,%s,%s,%s,%s,%s);"
					cursor.execute(consulta, (uid, nombre, carnet, total, date.today(), f"Talla: {talla}",0,session['idusercaja']))
				conexion.commit()
			finally:
				conexion.close()
		except (pymysql.err.OperationalError, pymysql.err.InternalError) as e:
			print("Ocurrió un error al conectar: ", e)
		return redirect(url_for('u'))
	return render_template('confirmacionu.html', title="Confirmación", uid = uid, carnet = carnet, nombre = nombre, total = total, talla= talla, ucod = ucod, logeado=logeado)

@app.route('/repu', methods=['GET', 'POST'])
def repu():
	try:
		logeado = session['logeadocaja']
	except:
		return redirect(url_for('login'))
	try:
		conexion = pymysql.connect(host=Conhost, user=Conuser, password=Conpassword, db=Condb)
		try:
			with conexion.cursor() as cursor:
				cursor.execute("SELECT idcarreras, codigo FROM carreras;")
			# Con fetchall traemos todas las filas
				carreras = cursor.fetchall()
				consulta = '''select p.nombre, p.carnet, p.fecha, c.codigo, p.extra, p.total from pagos p 
				inner join codigos d on p.idcod = d.idcodigos
				inner join carreras c on d.idcarrera = c.idcarreras
				where d.cod LIKE 'U%'
				order by p.fecha asc, c.codigo desc'''
				cursor.execute(consulta)
			# Con fetchall traemos todas las filas
				data = cursor.fetchall()
				suma = 0
				for i in data:
					suma = suma + i[5]
		finally:
			conexion.close()
	except (pymysql.err.OperationalError, pymysql.err.InternalError) as e:
		print("Ocurrió un error al conectar: ", e)
	if request.method == 'POST':
		defecha = request.form["defecha"]
		afecha = request.form["afecha"]
		try:
			conexion = pymysql.connect(host=Conhost, user=Conuser, password=Conpassword, db=Condb)
			try:
				with conexion.cursor() as cursor:
					cursor.execute("SELECT idcarreras, codigo FROM carreras;")
			# Con fetchall traemos todas las filas
					carreras = cursor.fetchall()
					consulta = '''select p.nombre, p.carnet, p.fecha, c.codigo, p.extra, p.total from pagos p 
					inner join codigos d on p.idcod = d.idcodigos
					inner join carreras c on d.idcarrera = c.idcarreras
					where d.cod LIKE 'U%' and p.fecha >= "'''
					consulta = consulta + f'{defecha}" and p.fecha <= "{afecha}" order by p.fecha asc, c.codigo desc'
					cursor.execute(consulta)
			# Con fetchall traemos todas las filas
					data = cursor.fetchall()
					suma = 0
					for i in data:
						suma = suma + i[5]
			finally:
				conexion.close()
		except (pymysql.err.OperationalError, pymysql.err.InternalError) as e:
			print("Ocurrió un error al conectar: ", e)
	return render_template('repu.html', title="Reporte Uniformes", data = data, suma=suma, carreras=carreras, logeado=logeado)

@app.route('/p', methods=['GET', 'POST'])
def p():
	try:
		logeado = session['logeadocaja']
	except:
		return redirect(url_for('login'))
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
		datalugar = request.form["lugar"]
		if len(datalugar) < 1:
			datalugar = 0
		datafechainicio = request.form["fechainicio"]
		if len(datafechainicio) < 1:
			datafechainicio = 0
		datafechafin = request.form["fechafin"]
		if len(datafechafin) < 1:
			datafechafin = 0
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
		return redirect(url_for('confirmacionp', carnet = datacarnet, nombre = datanombre, datames= datames, pid = pid, pcod = pcod, cantidad=cantidad, lugar=datalugar, fechainicio = datafechainicio, fechafin=datafechafin))
	return render_template('practica.html', title="Practica",  carreras=carreras, numeros=numeros, meses=meses, logeado=logeado)

@app.route('/confirmacionp/<carnet>&<nombre>&<datames>&<pid>&<pcod>&<cantidad>&<lugar>&<fechainicio>&<fechafin>', methods=['GET', 'POST'])
def confirmacionp(carnet, nombre, datames, pid, pcod,cantidad, lugar, fechainicio, fechafin):
	try:
		logeado = session['logeadocaja']
	except:
		return redirect(url_for('login'))
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
						elif 'THDQ' in pcod or 'TLCQ' in pcod:
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
								imprimir = True
							else:
								imprimir = False
							cursor.execute(consulta, (precios1[0][0], nombre, carnet, precioasig, date.today(), meses[i],0,session['idusercaja']))
							if 'LENQ' in precios1[0][2]:
								consulta = "INSERT INTO practicalenq(nombre,carnet,practica,lugar,fechainicio,fechafin,fecha) VALUES (%s,%s,%s,%s,%s,%s,CURDATE());"
								cursor.execute(consulta, (nombre, carnet, meses[i], lugar, fechainicio,fechafin))
								consulta = "Select MAX(idpracticalenq) from practicalenq;"
								cursor.execute(consulta)
								idpractica = cursor.fetchone()
								idpractica = idpractica[0]
								idpracticas.append(idpractica)
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
		elif 'TLCQ' in pcod:
			return redirect(url_for('hojatlcq', idpagos = idpagos))
		elif 'TRADQ' in pcod and 'Prepractica' in pcod:
			return redirect(url_for('prepracticatradq', idpagos = idpagos))
		elif 'TOPTQ' in pcod:
			return redirect(url_for('practicatoptq', idpagos = idpagos))
		else:
			return redirect(url_for('p'))
	return render_template('confirmacionp.html', title="Confirmación", carnet = carnet, nombre = nombre, meses = meses, pid = pid, pcod = pcod, cantidad=cantidad, logeado=logeado, lugar=lugar, fechainicio = fechainicio, fechafin = fechafin)

@app.route('/repp', methods=['GET', 'POST'])
def repp():
	try:
		logeado = session['logeadocaja']
	except:
		return redirect(url_for('login'))
	try:
		conexion = pymysql.connect(host=Conhost, user=Conuser, password=Conpassword, db=Condb)
		try:
			with conexion.cursor() as cursor:
				cursor.execute("SELECT idcodigos, cod, concepto FROM pagossis.codigos WHERE practica = 1 ORDER BY cod asc;")
			# Con fetchall traemos todas las filas
				carreras = cursor.fetchall()
				consulta = '''select p.nombre, p.carnet, p.fecha, d.cod, p.extra, p.total, p.idpagos from pagos p 
				inner join codigos d on p.idcod = d.idcodigos
				inner join carreras c on d.idcarrera = c.idcarreras
				where d.practica = 1
				order by p.fecha desc, c.codigo desc, p.nombre asc, p.extra asc'''
				cursor.execute(consulta)
			# Con fetchall traemos todas las filas
				data = cursor.fetchall()
				suma = 0
				for i in data:
					suma = suma + i[5]
		finally:
			conexion.close()
	except (pymysql.err.OperationalError, pymysql.err.InternalError) as e:
		print("Ocurrió un error al conectar: ", e)
	if request.method == 'POST':
		defecha = request.form["defecha"]
		afecha = request.form["afecha"]
		try:
			conexion = pymysql.connect(host=Conhost, user=Conuser, password=Conpassword, db=Condb)
			try:
				with conexion.cursor() as cursor:
					cursor.execute("SELECT idcarreras, codigo FROM carreras;")
				# Con fetchall traemos todas las filas
					carreras = cursor.fetchall()
					consulta = '''select p.nombre, p.carnet, p.fecha, c.codigo, p.extra, p.total from pagos p 
					inner join codigos d on p.idcod = d.idcodigos
					inner join carreras c on d.idcarrera = c.idcarreras
					where d.cod LIKE 'P%' and d.cod != 'PROP' and d.cod != 'PAG' and d.cod != 'PARQ' and p.fecha >= '''
					consulta = consulta + f'"{defecha}" and p.fecha <= "{afecha}"'
					consulta = consulta + ' order by p.fecha asc, c.codigo desc, p.nombre asc, p.extra asc'
					cursor.execute(consulta)
				# Con fetchall traemos todas las filas
					data = cursor.fetchall()
					suma = 0
					for i in data:
						suma = suma + i[5]
			finally:
				conexion.close()
		except (pymysql.err.OperationalError, pymysql.err.InternalError) as e:
			print("Ocurrió un error al conectar: ", e)
	return render_template('repp.html', title="Reporte Prácticas", data = data, suma=suma, carreras=carreras, logeado=logeado)

@app.route('/hojalbcq/<idpagos>', methods=['GET', 'POST'])
def hojalbcq(idpagos):
	try:
		logeado = session['logeadocaja']
	except:
		return redirect(url_for('login'))
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
	rendered = render_template('hojalbcq.html', title="Hoja de Práctica ", cantidad = cantidad, nombre = nombre, carnet = carnet, meses = meses, year = year, idhojas=idhojas)
	options = {'enable-local-file-access': None, 'page-size': 'Legal', 'margin-bottom': '35mm'}
	config = pdfkit.configuration(wkhtmltopdf="C:\\Program Files\\wkhtmltopdf\\bin\\wkhtmltopdf.exe")
	pdf = pdfkit.from_string(rendered, False, configuration=config, options=options)
	response = make_response(pdf)
	response.headers['Content-Type'] = 'application/pdf'
	response.headers['Content-Disposition'] = 'inline; filename=reportediario.pdf'
	print(response)
	return response

@app.route('/epslbcq/<idpagos>', methods=['GET', 'POST'])
def epslbcq(idpagos):
	try:
		logeado = session['logeadocaja']
	except:
		return redirect(url_for('login'))
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
	
	rendered = render_template('epslbcq.html', title="Hoja de Práctica ", cantidad = cantidad, nombre = nombre, carnet = carnet, meses = meses, year = year, idhojas=idhojas)
	options = {'enable-local-file-access': None, 'page-size': 'Legal', 'footer-right': 'Página [page] de [topage]', 'margin-bottom': '40mm'}
	config = pdfkit.configuration(wkhtmltopdf="C:\\Program Files\\wkhtmltopdf\\bin\\wkhtmltopdf.exe")
	pdf = pdfkit.from_string(rendered, False, configuration=config, options=options)
	response = make_response(pdf)
	response.headers['Content-Type'] = 'application/pdf'
	response.headers['Content-Disposition'] = 'inline; filename=practicalenq.pdf'
	print(response)
	return response

@app.route('/hojalenq/<idpagos>', methods=['GET', 'POST'])
def hojalenq(idpagos):
	try:
		logeado = session['logeadocaja']
	except:
		return redirect(url_for('login'))
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
				consulta = f'SELECT nombre, carnet, practica, lugar, DATE_FORMAT(fechainicio,"%d/%m/%Y"), DATE_FORMAT(fechafin,"%d/%m/%Y") FROM practicalenq WHERE idpracticalenq = {newarray[0]};'
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
	rendered = render_template(template, title="Hoja de Práctica ", practica = practica, year = year)
	options = {'enable-local-file-access': None, 'page-size': 'Legal', 'footer-right': 'Página [page] de [topage]', 'margin-bottom': '40mm'}
	config = pdfkit.configuration(wkhtmltopdf="C:\\Program Files\\wkhtmltopdf\\bin\\wkhtmltopdf.exe")
	pdf = pdfkit.from_string(rendered, False, configuration=config, options=options)
	response = make_response(pdf)
	response.headers['Content-Type'] = 'application/pdf'
	response.headers['Content-Disposition'] = 'inline; filename=practicalenq.pdf'
	print(response)
	return response

@app.route('/hojathdq/<idpagos>', methods=['GET', 'POST'])
def hojathdq(idpagos):
	try:
		logeado = session['logeadocaja']
	except:
		return redirect(url_for('login'))
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
	rendered = render_template('hojathdq.html', title="Hoja de Práctica ", cantidad = cantidad, nombre = nombre, carnet = carnet, year = year)
	options = {'enable-local-file-access': None, 'page-size': 'Letter','margin-right': '10mm'}
	config = pdfkit.configuration(wkhtmltopdf="C:\\Program Files\\wkhtmltopdf\\bin\\wkhtmltopdf.exe")
	pdf = pdfkit.from_string(rendered, False, configuration=config, options=options)
	response = make_response(pdf)
	response.headers['Content-Type'] = 'application/pdf'
	response.headers['Content-Disposition'] = 'inline; filename=reportediario.pdf'
	print(response)
	return response

@app.route('/hojatlcq/<idpagos>', methods=['GET', 'POST'])
def hojatlcq(idpagos):
	try:
		logeado = session['logeadocaja']
	except:
		return redirect(url_for('login'))
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
	rendered = render_template('hojatlcq.html', title="Hoja de Práctica ", cantidad = cantidad, nombre = nombre, carnet = carnet, year = year, idhojas = idhojas, meses = meses)
	options = {'enable-local-file-access': None, 'page-size': 'Legal', 'margin-bottom': '35mm'}
	config = pdfkit.configuration(wkhtmltopdf="C:\\Program Files\\wkhtmltopdf\\bin\\wkhtmltopdf.exe")
	pdf = pdfkit.from_string(rendered, False, configuration=config, options=options)
	response = make_response(pdf)
	response.headers['Content-Type'] = 'application/pdf'
	response.headers['Content-Disposition'] = 'inline; filename=reportediario.pdf'
	return response

@app.route('/prepracticatradq/<idpagos>', methods=['GET', 'POST'])
def prepracticatradq(idpagos):
	try:
		logeado = session['logeadocaja']
	except:
		return redirect(url_for('login'))
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
	rendered = render_template('prepracticatradq.html', title="Pre-Práctica TRADQ ", cantidad = cantidad, nombre = nombre, carnet = carnet, year = year, numeros = numeros)
	options = {'enable-local-file-access': None, 'page-size': 'Letter','margin-bottom': '35mm','margin-right': '10mm'}
	config = pdfkit.configuration(wkhtmltopdf="C:\\Program Files\\wkhtmltopdf\\bin\\wkhtmltopdf.exe")
	pdf = pdfkit.from_string(rendered, False, configuration=config, options=options)
	response = make_response(pdf)
	response.headers['Content-Type'] = 'application/pdf'
	response.headers['Content-Disposition'] = 'inline; filename=reportediario.pdf'
	print(response)
	return response

@app.route('/practicatoptq/<idpagos>', methods=['GET', 'POST'])
def practicatoptq(idpagos):
	try:
		logeado = session['logeadocaja']
	except:
		return redirect(url_for('login'))
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
	rendered = render_template('practicatoptq.html', title="Práctica TOPTQ", cantidad = cantidad, nombre = nombre, carnet = carnet, year = year, numeros = numeros)
	options = {'enable-local-file-access': None, 'page-size': 'Letter','margin-bottom': '35mm','margin-right': '10mm'}
	config = pdfkit.configuration(wkhtmltopdf="C:\\Program Files\\wkhtmltopdf\\bin\\wkhtmltopdf.exe")
	pdf = pdfkit.from_string(rendered, False, configuration=config, options=options)
	response = make_response(pdf)
	response.headers['Content-Type'] = 'application/pdf'
	response.headers['Content-Disposition'] = 'inline; filename=modulotoptq.pdf'
	print(response)
	return response

@app.route('/mextra', methods=['GET', 'POST'])
def mextra():
	try:
		logeado = session['logeadocaja']
	except:
		return redirect(url_for('login'))
	try:
		conexion = pymysql.connect(host=Conhost, user=Conuser, password=Conpassword, db=Condb)
		try:
			with conexion.cursor() as cursor:
				cursor.execute("SELECT idcarreras, codigo FROM carreras;")
			# Con fetchall traemos todas las filas
				carreras = cursor.fetchall()
		finally:
			conexion.close()
	except (pymysql.err.OperationalError, pymysql.err.InternalError) as e:
		print("Ocurrió un error al conectar: ", e)
	if request.method == 'POST':
		datacarnet = request.form["carnet"]
		datanombre = request.form["nombre"]
		datatotal = request.form["total"]
		datacarrera = request.form["carrera"]
		return redirect(url_for('confirmacionme', total = datatotal, carnet = datacarnet, nombre = datanombre, carrera = datacarrera))
	return render_template('mextra.html', title="Mes extra", carreras=carreras, logeado=logeado)

@app.route('/confirmacionme/<total>&<carnet>&<nombre>&<carrera>', methods=['GET', 'POST'])
def confirmacionme(total, carnet, nombre, carrera):
	try:
		logeado = session['logeadocaja']
	except:
		return redirect(url_for('login'))
	total = float(total)
	carnet = str(carnet)
	nombre = str(nombre)
	carrera = str(carrera)
	if request.method == "POST":
		try:
			conexion = pymysql.connect(host=Conhost, user=Conuser, password=Conpassword, db=Condb)
			try:
				with conexion.cursor() as cursor:
					consulta1 = 'SELECT idcodigos FROM codigos WHERE cod = "MENE"'
					cursor.execute(consulta1)
					precios1 = cursor.fetchall()
					consulta = "INSERT INTO pagos(idcod,nombre,carnet,total,fecha,extra, recibo,user) VALUES (%s,%s,%s,%s,%s,%s,%s,%s);"
					cursor.execute(consulta, (precios1[0][0], nombre, carnet, total, date.today(), carrera, 0,session['idusercaja']))
				conexion.commit()
			finally:
				conexion.close()
		except (pymysql.err.OperationalError, pymysql.err.InternalError) as e:
			print("Ocurrió un error al conectar: ", e)
		return redirect(url_for('mextra'))
	return render_template('confirmacionme.html', title="Confirmación", total = total, carnet = carnet, nombre = nombre, carrera = carrera, logeado=logeado)

@app.route('/repme', methods=['GET', 'POST'])
def repme():
	try:
		logeado = session['logeadocaja']
	except:
		return redirect(url_for('login'))
	try:
		conexion = pymysql.connect(host=Conhost, user=Conuser, password=Conpassword, db=Condb)
		try:
			with conexion.cursor() as cursor:
				cursor.execute("SELECT idcarreras, codigo FROM carreras;")
			# Con fetchall traemos todas las filas
				carreras = cursor.fetchall()
				consulta = 'select nombre, carnet, fecha, extra, total from pagos where idcod = 64 order by fecha asc;'
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
	return render_template('repme.html', title="Reporte Meses Extra", data = data, suma=suma, carreras=carreras, logeado=logeado)

@app.route('/parqueo', methods=['GET', 'POST'])
def parqueo():
	try:
		logeado = session['logeadocaja']
	except:
		return redirect(url_for('login'))
	if request.method == 'POST':
		datacantidad = request.form["cantidad"]
		return redirect(url_for('confirmacionparqueo', cantidad = datacantidad))
	return render_template('parqueo.html', title="Parqueo", logeado=logeado)

@app.route('/confirmacionparqueo/<cantidad>', methods=['GET', 'POST'])
def confirmacionparqueo(cantidad):
	try:
		logeado = session['logeadocaja']
	except:
		return redirect(url_for('login'))
	cantidad = int(cantidad)
	total = cantidad * 10
	if request.method == "POST":
		try:
			conexion = pymysql.connect(host=Conhost, user=Conuser, password=Conpassword, db=Condb)
			try:
				with conexion.cursor() as cursor:
					consulta = "INSERT INTO pagos(idcod,nombre,carnet,total,fecha,extra, recibo,user) VALUES (%s,%s,%s,%s,%s,%s,%s,%s);"
					cursor.execute(consulta, (65, 'Parqueo', 0, total, date.today(), f"Cantidad parqueo: {cantidad}", 0,session['idusercaja']))
				conexion.commit()
			finally:
				conexion.close()
		except (pymysql.err.OperationalError, pymysql.err.InternalError) as e:
			print("Ocurrió un error al conectar: ", e)
		return redirect(url_for('parqueo'))
	return render_template('confirmacionparqueo.html', title="Confirmación", cantidad = cantidad, total = total, logeado=logeado)

@app.route('/repparq', methods=['GET', 'POST'])
def repparq():
	try:
		logeado = session['logeadocaja']
	except:
		return redirect(url_for('login'))
	try:
		conexion = pymysql.connect(host=Conhost, user=Conuser, password=Conpassword, db=Condb)
		try:
			with conexion.cursor() as cursor:
				consulta = 'select extra, fecha, total from pagos where idcod = 65 order by fecha asc'
				cursor.execute(consulta)
			# Con fetchall traemos todas las filas
				data = cursor.fetchall()
				suma = 0
				for i in data:
					suma = suma + i[2]
		finally:
			conexion.close()
	except (pymysql.err.OperationalError, pymysql.err.InternalError) as e:
		print("Ocurrió un error al conectar: ", e)
	return render_template('repparq.html', title="Reporte Parqueo", data = data, suma=suma, logeado=logeado)

@app.route('/m', methods=['GET', 'POST'])
def m():
	try:
		logeado = session['logeadocaja']
	except:
		return redirect(url_for('login'))
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
		datakit = ""
		for i in range(cantidad):
			aux1 = f'curso{i+1}'
			aux = request.form[aux1]
			if(len(aux) > 0):
				datacurso.append(aux)
			aux1 = f'kit{i+1}'
			try:
				aux = request.form[aux1]
				aux = int(aux)
				if aux > 0:
					datakit = datakit + str(aux) + ","
			except:
				pass
		if datakit == "":
			datakit = "0"
		return redirect(url_for('confirmacionm', carnet = datacarnet, nombre = datanombre, curso= datacurso, mid = mid, mcod = mcod, datakit = datakit))
	return render_template('manuales.html', title="Manuales",  carreras=carreras, logeado=logeado)

@app.route('/confirmacionm/<carnet>&<nombre>&<curso>&<mid>&<mcod>&<datakit>', methods=['GET', 'POST'])
def confirmacionm(carnet, nombre, curso, mid, mcod, datakit):
	try:
		logeado = session['logeadocaja']
	except:
		return redirect(url_for('login'))
	carnet = str(carnet)
	nombre = str(nombre)
	mid = str(mid)
	mcod = str(mcod)
	curso = str(curso)
	datakit = str(datakit)
	kits = datakit.split(',')
	kits.pop()	
	cursos = curso.split(',')
	cantidad = len(cursos)
	for i in range(cantidad):
		try:
			cursos[i] = str(cursos[i].split("'")[1])
		except:
			cursos[i] = cursos[i]
	if request.method == "POST":
		try:
			conexion = pymysql.connect(host=Conhost, user=Conuser, password=Conpassword, db=Condb)
			try:
				with conexion.cursor() as cursor:
					consulta1 = f'SELECT idcodigos, precio FROM codigos WHERE idcodigos = "{mid}"'
					cursor.execute(consulta1)
					precios1 = cursor.fetchall()
					idpagos = []
					for i in range(cantidad):
						consulta = "INSERT INTO pagos(idcod,nombre,carnet,total,fecha,extra, recibo,user) VALUES (%s,%s,%s,%s,%s,%s,%s,%s);"
						cursor.execute(consulta, (precios1[0][0], nombre, carnet, precios1[0][1], date.today(), "Curso: "+cursos[i], 0,session['idusercaja']))
						conexion.commit()
						consulta = "Select MAX(idpagos) from pagos;"
						cursor.execute(consulta)
						idpago = cursor.fetchone()
						idpago = idpago[0]
						idpagos.append(idpago)
					consulta = f'SELECT concepto FROM codigos WHERE idcodigos = "{mid}"'
					cursor.execute(consulta)
					concepto = cursor.fetchone()
					if "TLCQ" in concepto[0]:
						carrera = "TLCQ"
					elif "LBCQ" in concepto[0]:
						carrera = "LBCQ"
					consulta = f'SELECT idcodigos FROM codigos WHERE concepto like "%Kit individual {carrera}"'
					cursor.execute(consulta)
					preciokit = cursor.fetchone()
					for i in kits:
						try:
							if int(i) > 0:
								consulta = "INSERT INTO pagos(idcod,nombre,carnet,total,fecha,extra, recibo,user) VALUES (%s,%s,%s,%s,%s,%s,%s,%s);"
								cursor.execute(consulta, (preciokit[0], nombre, carnet, str(i), date.today(), "Kit Individual "+carrera, 0,session['idusercaja']))
								conexion.commit()
								consulta = "Select MAX(idpagos) from pagos;"
								cursor.execute(consulta)
								idpago = cursor.fetchone()
								idpago = idpago[0]
								idpagos.append(idpago)
						except:
							pass
			finally:
				conexion.close()
		except (pymysql.err.OperationalError, pymysql.err.InternalError) as e:
			print("Ocurrió un error al conectar: ", e)
		return redirect(url_for('imprimir', idpagos=idpagos))
	return render_template('confirmacionm.html', title="Confirmación", carnet = carnet, nombre = nombre, cursos = cursos, mid = mid, mcod = mcod, cantidad=cantidad, logeado=logeado, kits=kits)

@app.route('/repm', methods=['GET', 'POST'])
def repm():
	fechainicio = '2023-07-07'
	try:
		conexion = pymysql.connect(host=Conhost, user=Conuser, password=Conpassword, db=Condb)
		try:
			with conexion.cursor() as cursor:
				numsmanualeslbcq = [2,4,6,8]
				numsmanualestlcq = [2,4]
				nombremanualesindlbcq = ['BIOLOGIA GENERAL II', 'QUIMICA GENERAL II', 'MICROBIOLOGIA GENERAL', 'QUIMICA ORGANICA', 'BACTERIOLOGIA', 'BIOQUIMICA CLINICA', 'INMUNOLOGIA BASICA', 'INTERPRETACION DE PRUEBAS BIOQUIMICAS', 'MICOLOGIA', 'MICROBIOLOGIA APLICADA I']
				nombremanualesindtlcq = ['HEMATOLOGIA Y COAGULACION', 'INMUNOLOGIA Y BANCO DE SANGRE', 'MICROBIOLOGIA', 'PRUEBAS ESPECIALES']
				manualeslbcq = []
				manualestlcq = []
				manualesind = []
				for i in numsmanualeslbcq:
					consulta = f"select p.nombre, p.carnet, p.fecha, c.cod, p.extra from pagos p inner join codigos c on p.idcod = c.idcodigos where p.fecha > '{fechainicio}' and c.cod like 'KITLBCQ{i}'"
					cursor.execute(consulta)
					manuales = cursor.fetchall()
					manualeslbcq.append(manuales)
				for i in numsmanualestlcq:
					consulta = f"select p.nombre, p.carnet, p.fecha, c.cod, p.extra from pagos p inner join codigos c on p.idcod = c.idcodigos where p.fecha > '{fechainicio}' and c.cod like 'KITTLCQ{i}'"
					cursor.execute(consulta)
					manuales = cursor.fetchall()
					manualestlcq.append(manuales)
				for i in nombremanualesindlbcq:
					consulta = f"select p.nombre, p.carnet, p.fecha, c.cod, p.extra from pagos p inner join codigos c on p.idcod = c.idcodigos where p.fecha > '{fechainicio}' and p.extra like '%{i}%' and c.concepto like '%Manual LBCQ%'"
					cursor.execute(consulta)
					manuales = cursor.fetchall()
					manualesind.append(manuales)
				for i in nombremanualesindtlcq:
					consulta = f"select p.nombre, p.carnet, p.fecha, c.cod, p.extra from pagos p inner join codigos c on p.idcod = c.idcodigos where p.fecha > '{fechainicio}' and p.extra like '%{i}%' and c.concepto like '%Manual TLCQ%'"
					cursor.execute(consulta)
					manuales = cursor.fetchall()
					manualesind.append(manuales)
			# Con fetchall traemos todas las filas
		finally:
			conexion.close()
	except (pymysql.err.OperationalError, pymysql.err.InternalError) as e:
		print("Ocurrió un error al conectar: ", e)
	return render_template('repm.html', title="Reporte Manuales", numsmanualeslbcq = numsmanualeslbcq, numsmanualestlcq=numsmanualestlcq, manualeslbcq=manualeslbcq, manualestlcq=manualestlcq, manualesind=manualesind)

@app.route('/entregarm/<idpago>', methods=['GET', 'POST'])
def entregarm(idpago):
	try:
		logeado = session['logeadocaja']
	except:
		return redirect(url_for('login'))
	try:
		conexion = pymysql.connect(host=Conhost, user=Conuser, password=Conpassword, db=Condb)
		try:
			with conexion.cursor() as cursor:
				consulta = f"update pagos set extra1 = 1, fechaextra1 = '{date.today()}' where idpagos = {idpago};"
				cursor.execute(consulta)
			conexion.commit()
		finally:
			conexion.close()
	except (pymysql.err.OperationalError, pymysql.err.InternalError) as e:
		print("Ocurrió un error al conectar: ", e)
	return redirect(url_for('repm'))

@app.route('/pag', methods=['GET', 'POST'])
def pag():
	try:
		logeado = session['logeadocaja']
	except:
		return redirect(url_for('login'))
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
	return render_template('pag.html', title="Pagos", carreras = carreras, logeado=logeado, meses=meses)

@app.route('/confirmacionpag/<carnet>&<nombre>&<total>&<descripcion>&<pid>&<pcod>&<ptotal>', methods=['GET', 'POST'])
def confirmacionpag(carnet, nombre, total, descripcion, pid, pcod, ptotal):
	try:
		logeado = session['logeadocaja']
	except:
		return redirect(url_for('login'))
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
	return render_template('confirmacionpag.html', title="Confirmación", carnet = carnet, nombre = nombre, total=total, descripcion=descripcion, pid = pid, pcod = pcod,ptotal = ptotal, logeado=logeado)

@app.route('/reppag', methods=['GET', 'POST'])
def reppag():
	try:
		logeado = session['logeadocaja']
	except:
		return redirect(url_for('login'))
	try:
		conexion = pymysql.connect(host=Conhost, user=Conuser, password=Conpassword, db=Condb)
		try:
			with conexion.cursor() as cursor:
				consulta = 'select p.nombre, p.carnet, p.fecha, c.cod, p.extra, p.total from pagos p inner join codigos c on p.idcod = c.idcodigos where c.pagos = 1 order by p.fecha desc, c.cod asc, p.extra asc, p.nombre asc'
				cursor.execute(consulta)
			# Con fetchall traemos todas las filas
				data = cursor.fetchall()
				suma = 0
				for i in data:
					suma = suma + i[5]
		finally:
			conexion.close()
	except (pymysql.err.OperationalError, pymysql.err.InternalError) as e:
		print("Ocurrió un error al conectar: ", e)
	return render_template('reppag.html', title="Reporte Pagos", data = data, suma=suma, logeado=logeado)

@app.route('/grad', methods=['GET', 'POST'])
def grad():
	try:
		logeado = session['logeadocaja']
	except:
		return redirect(url_for('login'))
	if request.method == 'POST':
		datacarnet = request.form["carnet"]
		datanombre = request.form["nombre"]
		datatipo = request.form["tipo"]
		return redirect(url_for('confirmaciongrad', tipo = datatipo, carnet = datacarnet, nombre = datanombre))
	return render_template('graduacion.html', title="Graduación", logeado=logeado)

@app.route('/confirmaciongrad/<tipo>&<carnet>&<nombre>', methods=['GET', 'POST'])
def confirmaciongrad(tipo, carnet, nombre):
	try:
		logeado = session['logeadocaja']
	except:
		return redirect(url_for('login'))
	tipo = int(tipo)
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
					elif tipo == 2:
						consulta1 = 'SELECT idcodigos, precio FROM codigos WHERE cod = "GRADL"'
						cursor.execute(consulta1)
						precios1 = cursor.fetchall()
					consulta = "INSERT INTO pagos(idcod,nombre,carnet,total,fecha,extra, recibo,user) VALUES (%s,%s,%s,%s,%s,%s,%s,%s);"
					cursor.execute(consulta, (precios1[0][0], nombre, carnet, precios1[0][1], date.today(), "",0,session['idusercaja']))
				conexion.commit()
			finally:
				conexion.close()
		except (pymysql.err.OperationalError, pymysql.err.InternalError) as e:
			print("Ocurrió un error al conectar: ", e)
		return redirect(url_for('grad'))
	return render_template('confirmaciongrad.html', title="Confirmación", nombre = nombre, carnet = carnet, tipo = tipo, logeado=logeado)

@app.route('/repgrad', methods=['GET', 'POST'])
def repgrad():
	try:
		logeado = session['logeadocaja']
	except:
		return redirect(url_for('login'))
	try:
		conexion = pymysql.connect(host=Conhost, user=Conuser, password=Conpassword, db=Condb)
		try:
			with conexion.cursor() as cursor:
				consulta = '''select p.nombre, p.carnet, p.fecha, c.cod, p.total from pagos p 
				inner join codigos c on p.idcod = c.idcodigos
				where p.idcod = 59 or p.idcod = 60 order by p.fecha asc'''
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
	return render_template('repgrad.html', title="Reporte Graduación", data = data, suma=suma, logeado=logeado)

@app.route('/reportes', methods=['GET', 'POST'])
def reportes():
	try:
		logeado = session['logeadocaja']
	except:
		return redirect(url_for('login'))
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
	return render_template('reportes.html', title="Reportes", sumas = sumas, sumtotal=sumtotal, logeado=logeado, datadev=datadev, totaldev=totaldev, totaltotal=totaltotal, efectivo=efectivo, facturas = facturas)

@app.route('/unificarcajas')
def unificarcajas():
	try:
		logeado = session['logeadocaja']
	except:
		return redirect(url_for('login'))
	idusuario = session['idusercaja']
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
def nuevafactura():
	try:
		logeado = session['logeadocaja']
	except:
		return redirect(url_for('login'))
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
	return render_template('nuevafactura.html', title="Ingresar Factura", logeado=logeado, nuevo=1, factura=factura)

@app.route('/editarfactura/<idfactura>', methods=['GET', 'POST'])
def editarfactura(idfactura):
	try:
		logeado = session['logeadocaja']
	except:
		return redirect(url_for('login'))
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
	return render_template('nuevafactura.html', title="Editar Factura", logeado=logeado, nuevo=0, factura=factura)

@app.route("/eliminarfactura/<idfactura>", methods=['GET', 'POST'])
def eliminarfactura(idfactura):
	try:
		logeado = session['logeadocaja']
	except:
		return redirect(url_for('login'))
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
def repdiario():
	try:
		logeado = session['logeadocaja']
	except:
		return redirect(url_for('login'))
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
				consulta = f'select recibo from pagos where length(recibo) < 5 and fecha = "{fechasig}" order by recibo desc;'
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
	return render_template('repdiario.html', title="Reporte diario", data = data, suma=suma, logeado=logeado, datadev=datadev, resumen=resumen, boletasig = boletasig, facturas=facturas)

@app.route('/repdiariopdf', methods=['GET', 'POST'])
def repdiariopdf():
	try:
		logeado = session['logeadocaja']
	except:
		return redirect(url_for('login'))
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
				consulta = 'SELECT p.nombre, p.carnet, DATE_FORMAT(p.fechadevuelto,"%d/%m/%Y"), c.concepto, p.extra, round(p.total), p.idpagos, p.recibo, u.iniciales FROM pagos p INNER JOIN codigos c ON p.idcod = c.idcodigos inner join user u on u.iduser = p.userdev WHERE fechadevuelto = CURDATE() order by c.cod asc, p.nombre asc;'
				cursor.execute(consulta)
				datadev = cursor.fetchall()
				contdev = len(datadev)
				sumadev = 0
				for i in datadev:
					sumadev = sumadev + float(i[5])
				aux = suma - sumadev
				sumas.append(aux)
				#resumen optica, resumen lab, resumen academica, resumen auxiliares, resumen tarjeta opt, resumen tarjeta lab
				resumenes = []
				#total optica, lab, academia, auxiliares, tarjeta opt, tarjeta lab, facturas, vales
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

@app.route('/replenq', methods=['GET', 'POST'])
def replenq():
	try:
		logeado = session['logeadocaja']
	except:
		return redirect(url_for('login'))
	data = []
	conteo = 0
	datacarnet = ""
	datafechapago = ""
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
		datafechapago = request.form["fechapago"]
		try:
			conexion = pymysql.connect(host=Conhost, user=Conuser, password=Conpassword, db=Condb)
			try:
				with conexion.cursor() as cursor:
					consulta = f'SELECT nombre, carnet, fecha, practica, lugar, fechainicio, fechafin, idpracticalenq FROM practicalenq where nombre like "%{datanombre}%" and carnet like "%{datacarnet}%"'
					if len(datafechaini) != 0:
						consulta = consulta + f' and fechainicio = "{datafechaini}"'
					if len(datafechafin) != 0:
						consulta = consulta + f' and fechafin = "{datafechafin}"'
					if len(datafechapago) != 0:
						consulta = consulta + f' and fecha = "{datafechapago}"'
					consulta = consulta + f' and lugar like "%{datalugar}%" and practica like "%{datadescripcion}%" order by fecha desc, practica asc, nombre asc;'
					cursor.execute(consulta)
				# Con fetchall traemos todas las filas
					data = cursor.fetchall()
					conteo = len(data)
			finally:
				conexion.close()
		except (pymysql.err.OperationalError, pymysql.err.InternalError) as e:
			print("Ocurrió un error al conectar: ", e)
		return render_template('replenq.html', title="Reporte Práctica Enfermeria", data = data, logeado=logeado, conteo=conteo, datacarnet = datacarnet, datanombre = datanombre, datafechaini = datafechaini, datafechafin = datafechafin, datafechapago = datafechapago, datadescripcion = datadescripcion)
	return render_template('replenq.html', title="Reporte Práctica Enfermeria", data = data, logeado=logeado, conteo=conteo, datacarnet = datacarnet, datanombre = datanombre, datafechaini = datafechaini, datafechafin = datafechafin, datafechapago = datafechapago, datadescripcion = datadescripcion)

@app.route('/replbcq', methods=['GET', 'POST'])
def replbcq():
	try:
		logeado = session['logeadocaja']
	except:
		return redirect(url_for('login'))
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
		return render_template('replbcq.html', title="Reporte Práctica Química Biológica", data = data, logeado=logeado, conteo=conteo, datacarnet = datacarnet, datanombre = datanombre, datafechapago = datafechapago, datadescripcion = datadescripcion)
	return render_template('replbcq.html', title="Reporte Práctica  Química Biológica", data = data, logeado=logeado, conteo=conteo, datacarnet = datacarnet, datanombre = datanombre, datafechapago = datafechapago, datadescripcion = datadescripcion)

@app.route('/repgen', methods=['GET', 'POST'])
def repgen():
	try:
		logeado = session['logeadocaja']
	except:
		return redirect(url_for('login'))
	data = []
	conteo = 0
	datacarnet = ""
	dataconcepto = ""
	datafechaini = ""
	datafechafin = ""
	datanombre = ""
	datadescripcion = ""
	datarecibo = ""
	if request.method == "POST":
		datacarnet = request.form["carnet"]
		datanombre = request.form["nombre"]
		datafechaini = request.form["fechaini"]
		datafechafin = request.form["fechafin"]
		dataconcepto = request.form["concepto"]
		datadescripcion = request.form["descripcion"]
		datarecibo = request.form["recibo"]
		try:
			conexion = pymysql.connect(host=Conhost, user=Conuser, password=Conpassword, db=Condb)
			try:
				with conexion.cursor() as cursor:
					consulta = f'SELECT p.nombre, p.carnet, p.fecha, c.concepto, p.extra, p.recibo, p.total, p.idpagos, p.devuelto FROM pagos p INNER JOIN codigos c ON p.idcod = c.idcodigos where p.nombre like "%{datanombre}%" and p.carnet like "%{datacarnet}%"'
					if len(datafechaini) != 0:
						consulta = consulta + f' and p.fecha >= "{datafechaini}"'
					if len(datafechafin) != 0:
						consulta = consulta + f' and p.fecha <= "{datafechafin}"'
					consulta = consulta + f' and c.concepto like "%{dataconcepto}%" and p.extra like "%{datadescripcion}%" and p.recibo like "%{datarecibo}%" order by p.fecha desc, c.concepto asc, p.extra asc, p.nombre asc;'
					cursor.execute(consulta)
				# Con fetchall traemos todas las filas
					data = cursor.fetchall()
					conteo = len(data)
			finally:
				conexion.close()
		except (pymysql.err.OperationalError, pymysql.err.InternalError) as e:
			print("Ocurrió un error al conectar: ", e)
		return render_template('repgen.html', title="Reporte general", data = data, logeado=logeado, conteo=conteo, datacarnet = datacarnet, datanombre = datanombre, datafechaini = datafechaini, datafechafin = datafechafin, dataconcepto = dataconcepto, datadescripcion = datadescripcion, datarecibo = datarecibo)
	return render_template('repgen.html', title="Reporte general", data = data, logeado=logeado, conteo=conteo, datacarnet = datacarnet, datanombre = datanombre, datafechaini = datafechaini, datafechafin = datafechafin, dataconcepto = dataconcepto, datadescripcion = datadescripcion, datarecibo = datarecibo)

@app.route('/pagos')
def pagos():
	try:
		logeado = session['logeadocaja']
	except:
		return redirect(url_for('login'))
	return render_template('pagos.html', title="Pagos", logeado=logeado)

@app.route('/transferencias', methods=['GET', 'POST'])
def transferencias():
	try:
		logeado = session['logeadocaja']
	except:
		return redirect(url_for('login'))
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
	return render_template('transferencias.html', title="Ingresar Transferencia", logeado=logeado)

@app.route('/reptransferencias', methods=['GET', 'POST'])
def reptransferencias():
	try:
		logeado = session['logeadocaja']
	except:
		return redirect(url_for('login'))
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
	return render_template('reptransferencias.html', title="Transferencias", logeado=logeado, transferencias=transferencias)

@app.route('/imprimir/<idpagos>')
def imprimir(idpagos):
	try:
		logeado = session['logeadocaja']
	except:
		return redirect(url_for('login'))
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
	rendered = render_template('imprimir.html', title="Reporte diario", datagen = datagen, suma=suma, numpagos=numpagos, newarray=newarray)
	options = {'enable-local-file-access': None, 'page-size': 'A8', 'orientation': 'Portrait', 'margin-left': '0', 'margin-right': '5mm', 'margin-top': '0', 'margin-bottom': '0', 'encoding': 'utf-8'}
	config = pdfkit.configuration(wkhtmltopdf="C:\\Program Files\\wkhtmltopdf\\bin\\wkhtmltopdf.exe")
	pdf = pdfkit.from_string(rendered, False, configuration=config, options=options)
	response = make_response(pdf)
	response.headers['Content-Type'] = 'application/pdf'
	response.headers['Content-Disposition'] = 'inline; filename=reportediario.pdf'
	print(response)
	return response

@app.route('/admin')
def admin():
	try:
		logeado = session['logeadocaja']
	except:
		return redirect(url_for('login'))
	return render_template('admin.html', title="Panel Administrativo", logeado=logeado)

@app.route('/pagosadmin')
def pagosadmin():
	try:
		logeado = session['logeadocaja']
	except:
		return redirect(url_for('login'))
	try:
		conexion = pymysql.connect(host=Conhost, user=Conuser, password=Conpassword, db=Condb)
		try:
			with conexion.cursor() as cursor:
				consulta = 'SELECT p.idcodigos, p.cod, p.concepto, c.codigo, p.precio, p.manual, p.practica, p.pagos, p.pagose, p.uniformes from codigos p left join carreras c on p.idcarrera = c.idcarreras ORDER by p.concepto asc'
				cursor.execute(consulta)
				codigos = cursor.fetchall()
		finally:
			conexion.close()
	except (pymysql.err.OperationalError, pymysql.err.InternalError) as e:
		print("Ocurrió un error al conectar: ", e)
	return render_template('pagosadmin.html', title="Admin Pagos", logeado=logeado, codigos = codigos)

@app.route('/nuevocodigo', methods=['GET', 'POST'])
def nuevocodigo():
	try:
		logeado = session['logeadocaja']
	except:
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
			conexion = pymysql.connect(host=Conhost, user=Conuser, password=Conpassword, db=Condb)
			try:
				with conexion.cursor() as cursor:
					consulta = f"insert into codigos(concepto, cod, idcarrera, precio, activo, manual, practica, pagos, pagose, uniformes) values('{concepto}', '{codigo}', {carrera}, {precio}, 1, {manual}, {practica},{pagos}, {pagose}, null);"
					print(consulta)
					cursor.execute(consulta)
				conexion.commit()
			finally:
				conexion.close()
		except (pymysql.err.OperationalError, pymysql.err.InternalError) as e:
			print("Ocurrió un error al conectar: ", e)
		return redirect(url_for('pagosadmin'))
	return render_template('nuevocodigo.html', title="Nuevo Código", logeado=logeado, carreras = carreras)

@app.route('/editarcodigo/<id>', methods=['GET', 'POST'])
def editarcodigo(id):
	try:
		logeado = session['logeadocaja']
	except:
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
			conexion = pymysql.connect(host=Conhost, user=Conuser, password=Conpassword, db=Condb)
			try:
				with conexion.cursor() as cursor:
					consulta = f"update codigos set concepto = '{concepto}', cod = '{codigo}', idcarrera = {carrera}, precio = {precio}, manual = {manual}, practica = {practica}, pagos = {pagos}, pagose = {pagose} where idcodigos = {id};"
					cursor.execute(consulta)
				conexion.commit()
			finally:
				conexion.close()
		except (pymysql.err.OperationalError, pymysql.err.InternalError) as e:
			print("Ocurrió un error al conectar: ", e)
		return redirect(url_for('pagosadmin'))
	return render_template('editarcodigo.html', title="Editar Código", logeado=logeado, carreras = carreras, datacodigo = datacodigo)

@app.route('/carreras')
def carreras():
	try:
		logeado = session['logeadocaja']
	except:
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
	return render_template('carreras.html', title="Admin Carreras", logeado=logeado, carreras = carreras)

@app.route('/nuevacarrera', methods=['GET', 'POST'])
def nuevacarrera():
	try:
		logeado = session['logeadocaja']
	except:
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
	return render_template('nuevacarrera.html', title="Nueva Carrera", logeado=logeado)

if __name__ == '__main__':
	app.run(host='0.0.0.0', port=5000, threaded=True, debug=True)