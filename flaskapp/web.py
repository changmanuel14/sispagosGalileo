from operator import truediv
from flask import Flask, render_template, request, url_for, redirect, make_response, session
import pymysql
from datetime import date, datetime
import os
import webbrowser
import pdfkit as pdfkit
import barcode
from barcode.writer import ImageWriter
import gspread
from oauth2client.service_account import ServiceAccountCredentials
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
		logeado = 0
	if logeado == 0:
		return redirect(url_for('login'))
	try:
		conexion = pymysql.connect(host='localhost', user='root', password='database', db='pagossis')
		try:
			with conexion.cursor() as cursor:
				consulta = 'SELECT urldevuelto from pagos where idpagos = ' + str(idpago) + ';'
				cursor.execute(consulta)
				acceso = cursor.fetchall()
				acceso = acceso[0][0]
		finally:
			conexion.close()
	except (pymysql.err.OperationalError, pymysql.err.InternalError) as e:
		print("Ocurrió un error al conectar: ", e)
	return render_template('verdev.html', title='Devolución de Pago', logeado=logeado, acceso=acceso)

@app.route("/devolucion/<idpago>", methods=['GET', 'POST'])
def devolucion(idpago):
	try:
		logeado = session['logeadocaja']
	except:
		logeado = 0
	if logeado == 0:
		return redirect(url_for('login'))
	try:
		conexion = pymysql.connect(host='localhost', user='root', password='database', db='pagossis')
		try:
			with conexion.cursor() as cursor:
				consulta = 'SELECT c.concepto, p.nombre, p.carnet, p.total, DATE_FORMAT(p.fecha,"%d/%m/%Y"), p.extra, p.recibo from codigos c inner join pagos p on p.idcod = c.idcodigos where p.idpagos = ' + str(idpago) + ';'
				cursor.execute(consulta)
				datapago = cursor.fetchall()
				datapago = datapago[0]
		finally:
			conexion.close()
	except (pymysql.err.OperationalError, pymysql.err.InternalError) as e:
		print("Ocurrió un error al conectar: ", e)
	if request.method == 'POST':
		file = request.files['file']
		nombrearc = 'dev' + str(idpago) + '.'
		div = str(file.filename).split('.')
		nombrearc = nombrearc + div[1]
		file.save(os.path.join(app.config['UPLOAD_FOLDER'], nombrearc))
		try:
			conexion = pymysql.connect(host='localhost', user='root', password='database', db='pagossis')
			try:
				with conexion.cursor() as cursor:
					consulta = 'UPDATE pagos set devuelto = 1, urldevuelto = %s, fechadevuelto=%s, user=%s where idpagos = %s;'
					cursor.execute(consulta, (nombrearc, date.today(), session['idusercaja'], idpago))
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
		logeado = 0
	if logeado == 0:
		return redirect(url_for('login'))
	try:
		conexion = pymysql.connect(host='localhost', user='root', password='database', db='pagossis')
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
		cantidad = int(request.form["cant"]) + 1
		carrera = request.form["carrera"]
		try:
			insc = request.form["insc"]
		except:
			insc = 0
		datameses = ""
		for i in range(cantidad):
			aux = 'mes' + str(i)
			mes = request.form[aux]
			if i > 0:
				datameses = datameses + ',' + str(mes)
			else:
				datameses = datameses + str(mes)
		return redirect(url_for('confirmacionaca', nombre=nombre, carnet=carnet, datameses=datameses, carrera = carrera, insc=insc))
	return render_template('academia.html', title='Academia', logeado=logeado, carreras=carreras, meses=meses)

@app.route("/confirmacionaca/<nombre>&<carnet>&<datameses>&<carrera>&<insc>", methods=['GET', 'POST'])
def confirmacionaca(nombre, carnet, datameses, carrera, insc):
	try:
		logeado = session['logeadocaja']
	except:
		logeado = 0
	if logeado == 0:
		return redirect(url_for('login'))
	nombre = str(nombre)
	carnet = str(carnet)
	carrera = str(carrera)
	insc = int(insc)
	meses = datameses.split(",")
	cantidad = len(meses)
	try:
		conexion = pymysql.connect(host='localhost', user='root', password='database', db='pagossis')
		try:
			with conexion.cursor() as cursor:
				consulta = 'SELECT carrera from carreras where idcarreras = ' + str(carrera)
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
			conexion = pymysql.connect(host='localhost', user='root', password='database', db='pagossis')
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

@app.route("/ingles", methods=['GET', 'POST'])
def ingles():
	try:
		logeado = session['logeadocaja']
	except:
		logeado = 0
	if logeado == 0:
		return redirect(url_for('login'))
	meses = ["Enero", "Febrero","Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
	try:
		conexion = pymysql.connect(host='localhost', user='root', password='database', db='pagossis')
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
					datameses = datameses + ',' + str(mes)
				else:
					datameses = datameses + str(mes)
		if len(datameses) < 1:
			datameses = 'None'
		return redirect(url_for('confirmacioningles', nombre=nombre, carnet=carnet, plan = plan, insc=insc, datameses=datameses, ciclo=ciclo))
	return render_template('ingles.html', title='Ingles', logeado=logeado, meses=meses, cuotas=cuotas)

@app.route("/confirmacioningles/<nombre>&<carnet>&<plan>&<insc>&<datameses>&<ciclo>", methods=['GET', 'POST'])
def confirmacioningles(nombre, carnet, plan, insc, datameses, ciclo):
	try:
		logeado = session['logeadocaja']
	except:
		logeado = 0
	if logeado == 0:
		return redirect(url_for('login'))
	nombre = str(nombre)
	carnet = str(carnet)
	plan = int(plan)
	insc = int(insc)
	cantidad = 0
	if datameses != 'None':
		meses = datameses.split(",")
		cantidad = len(meses)
	else:
		meses = ""
	try:
		conexion = pymysql.connect(host='localhost', user='root', password='database', db='pagossis')
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
		finally:
			conexion.close()
	except (pymysql.err.OperationalError, pymysql.err.InternalError) as e:
		print("Ocurrió un error al conectar: ", e)
	total = 0
	if insc == 1:
		total = total + float(datainsc[0][1]) + float(datainsc[1][1])
	for i in datamen:
		for j in range(cantidad):
			total = total + float(i[1])
	if request.method == 'POST':
		try:
			conexion = pymysql.connect(host='localhost', user='root', password='database', db='pagossis')
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
							cursor.execute(consulta, (j[0], nombre, carnet, j[1], date.today(), 'Mes: ' + meses[i] ,0, session['idusercaja']))
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
	return render_template('confirmacioningles.html', title='Confirmación Ingles', logeado=logeado, nombre=nombre, carnet=carnet, cantidad=cantidad, total = total, datainsc=datainsc, datamen=datamen, insc=insc, meses=meses, ciclo=ciclo)

@app.route('/repingles', methods=['GET', 'POST'])
def repingles():
	try:
		logeado = session['logeadocaja']
	except:
		logeado = 0
	if logeado == 0:
		return redirect(url_for('login'))
	meses = ["Enero","Febrero","Marzo","Abril","Mayo","Junio","Julio","Agosto","Septiembre","Octubre","Noviembre","Diciembre"]
	datos = []
	try:
		conexion = pymysql.connect(host='localhost', user='root', password='database', db='pagossis')
		try:
			with conexion.cursor() as cursor:
				cursor.execute("SELECT p.nombre, p.carnet from pagos p inner join codigos c on c.idcodigos = p.idcod where c.concepto like '%Mensualidad Ingles Trimestral (A)%' and p.fecha > DATE_SUB(CURDATE(),INTERVAL 6 MONTH) group by p.nombre;")
				nombres = cursor.fetchall()
				mesesdelete = []
				for i in meses:
					consulta = f"SELECT idpagos from pagos p inner join codigos c on c.idcodigos = p.idcod where c.concepto like '%Mensualidad Ingles Trimestral (A)%' and p.extra like '%{i}%' and p.fecha > DATE_SUB(CURDATE(),INTERVAL 6 MONTH);"
					cursor.execute(consulta)
					pagomeses = cursor.fetchall()
					if len(pagomeses) > 0:
						pass
					else:
						mesesdelete.append(i)
				for i in mesesdelete:
					meses.remove(i)
				for i in nombres:
					data = [i[0], i[1]]
					for j in meses:
						consulta = f"SELECT DATE_FORMAT(p.fecha,'%d/%m/%Y') from pagos p inner join codigos c on c.idcodigos = p.idcod where c.concepto like '%Mensualidad Ingles Trimestral (A)%' and p.extra like '%{j}%' and p.nombre like '%{i[0]}%' and p.fecha > DATE_SUB(CURDATE(),INTERVAL 6 MONTH) order by p.nombre asc;"
						cursor.execute(consulta)
						pago = cursor.fetchall()
						if len(pago) > 0:
							data.append(pago[0][0])
						else:
							data.append("Pend")
				datos.append(data)	
			# Con fetchall traemos todas las filas
		finally:
			conexion.close()
	except (pymysql.err.OperationalError, pymysql.err.InternalError) as e:
		print("Ocurrió un error al conectar: ", e)
	return render_template('repingles.html', title="Reporte ingles", datos = datos, meses = meses, logeado=logeado)

@app.route("/laboratorio", methods=['GET', 'POST'])
def laboratorio():
	try:
		logeado = session['logeadocaja']
	except:
		logeado = 0
	if logeado == 0:
		return redirect(url_for('login'))
	fechaact = datetime.today().strftime('%Y-%m-%d')
	try:
		conexion = pymysql.connect(host='localhost', user='root', password='database', db='pagossis')
		try:
			with conexion.cursor() as cursor:
				consulta = 'SELECT nombre, idtipoexamen, precio, idexameneslab from exameneslab where DATE(fechaactivo) = "0000-00-00" or DATE(fechaactivo) > "'+ str(fechaact) + '" order by idtipoexamen;'
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
			aux = 'examen' + str(i)
			idexamen = request.form[aux]
			aux1 = 'precio' + str(i)
			precio = request.form[aux1]
			dataexamenes = dataexamenes + str(idexamen) + ',' + str(precio) + ';'
		return redirect(url_for('confirmacionlab', nombre=nombre, carnet=carnet, dataexamenes=dataexamenes))
	return render_template('laboratorio.html', title='Laboratorio', logeado=logeado, examenes=examenes, empresas=empresas, tipoexamen=tipoexamen)

@app.route("/confirmacionlab/<nombre>&<carnet>&<dataexamenes>", methods=['GET', 'POST'])
def confirmacionlab(nombre, carnet, dataexamenes):
	try:
		logeado = session['logeadocaja']
	except:
		logeado = 0
	if logeado == 0:
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
	print("Examenes: ", examenes)
	for i in examenes:
		datae = []
		total = total + float(i[1])
		try:
			conexion = pymysql.connect(host='localhost', user='root', password='database', db='pagossis')
			try:
				with conexion.cursor() as cursor:
					consulta = 'SELECT e.nombre, t.nombre from exameneslab e inner join tipoexamen t on e.idtipoexamen = t.idtipoexamen where e.idexameneslab = ' + str(i[0]) +';'
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
			conexion = pymysql.connect(host='localhost', user='root', password='database', db='pagossis')
			try:
				with conexion.cursor() as cursor:
					consulta = "SELECT idcodigos from codigos where cod = 'LAB'"
					cursor.execute(consulta)
					codlab = cursor.fetchone()
					codlab = codlab[0]
					idpagos = []
					for i in dataaux:
						consulta = "INSERT INTO pagos(idcod,nombre,carnet,total,fecha,extra,recibo, user) VALUES (%s,%s,%s,%s,%s,%s,%s, %s);"
						cursor.execute(consulta, (codlab, nombre, carnet, i[3], date.today(), i[2] + " - " + i[1] ,0, session['idusercaja']))
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
		logeado = 0
	if logeado == 0:
		return redirect(url_for('login'))
	try:
		conexion = pymysql.connect(host='localhost', user='root', password='database', db='pagossis')
		try:
			with conexion.cursor() as cursor:
				consulta = 'SELECT recibo from pagos where idpagos = ' + str(idpago) + ';'
				cursor.execute(consulta)
				recibo = cursor.fetchone()
				recibo = recibo[0]
				print(recibo)
				if recibo == '0' or recibo == 0:
					print('eliminacion')
					consulta = 'DELETE from pagos where idpagos = ' + str(idpago) + ';'
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
		logeado = 0
	if logeado == 0:
		return redirect(url_for('login'))
	try:
		conexion = pymysql.connect(host='localhost', user='root', password='database', db='pagossis')
		try:
			with conexion.cursor() as cursor:
				consulta = 'SELECT p.idcod, p.nombre, p.carnet, p.total, DATE_FORMAT(p.fecha,"%d/%m/%Y"), p.extra from codigos c inner join pagos p on p.idcod = c.idcodigos where p.idpagos = ' + str(idpago) + ';'
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
		print(carnet)
		print(len(carnet))
		if len(carnet) < 1:
			carnet = datapago[2]
		if len(nombre) < 1:
			nombre = datapago[1]
		if len(extra) < 1:
			extra = datapago[5]
		if len(fecha) < 1:
			datos=datapago[4].split('/')
			try:
				fecha = datos[2] + '-' + datos[1] + '-' + datos[0]
			except:
				fecha = '0000-00-00'
		else:
			datos=fecha.split('/')
			try:
				fecha = datos[2] + '-' + datos[1] + '-' + datos[0]
			except:
				fecha = '0000-00-00'
		if len(total) < 1:
			total = datapago[3]

		try:
			conexion = pymysql.connect(host='localhost', user='root', password='database', db='pagossis')
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
			conexion = pymysql.connect(host='localhost', user='root', password='database', db='pagossis')
			try:
				with conexion.cursor() as cursor:
					consulta = "SELECT iduser, nombre, apellido FROM user WHERE user = %s and pwd = md5(%s)"
					cursor.execute(consulta, (user, pwd))
					data = cursor.fetchall()
					print(data)
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
	try:
		logeado = session['logeadocaja']
	except:
		logeado = 0
	mensaje = ''
	if request.method == 'POST':
		nombre = request.form["nombre"]
		apellido = request.form["apellido"]
		user = request.form["user"]
		pwd = request.form["pwd"]
		iniciales = request.form["iniciales"]
		try:
			conexion = pymysql.connect(host='localhost', user='root', password='database', db='pagossis')
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
	return render_template('crearusuario.html', title='Nuevo Usuario', logeado=logeado, mensaje=mensaje)

@app.route('/optica', methods=['GET', 'POST'])
def optica():
	try:
		logeado = session['logeadocaja']
	except:
		logeado = 0
	if logeado == 0:
		return redirect(url_for('login'))
	print(logeado)
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
		logeado = 0
	if logeado == 0:
		return redirect(url_for('login'))
	examen = 0
	if request.method == "POST":
		try:
			conexion = pymysql.connect(host='localhost', user='root', password='database', db='pagossis')
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
		logeado = 0
	if logeado == 0:
		return redirect(url_for('login'))
	try:
		conexion = pymysql.connect(host='localhost', user='root', password='database', db='pagossis')
		try:
			with conexion.cursor() as cursor:
				cursor.execute("SELECT idinscripciones, inscripcion, precio, internet FROM inscripciones;")
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
		try:
			prope = request.form["prope"]
		except:
			prope = 0
		return redirect(url_for('confirmacioni', carrera = datacarrera, carnet = datacarnet, nombre = datanombre, rinsc=rinsc, rint=rint, rrein=rrein, mesextra=mesextra, exavis=exavis, prope=prope))
	return render_template('inscripciones.html', title="Inscripciones", carreras=carreras, logeado=logeado)

@app.route('/confirmacioni/<carrera>&<carnet>&<nombre>&<rinsc>&<rint>&<rrein>&<mesextra>&<exavis>&<prope>', methods=['GET', 'POST'])
def confirmacioni(carrera, carnet, nombre, rinsc, rint, rrein, mesextra, exavis, prope):
	try:
		logeado = session['logeadocaja']
	except:
		logeado = 0
	if logeado == 0:
		return redirect(url_for('login'))
	carrera = str(carrera)
	carnet = str(carnet)
	nombre = str(nombre)
	rinsc = int(rinsc)
	rint = int(rint)
	rrein = int(rrein)
	exavis = int(exavis)
	mesextra = int(mesextra)
	prope = int(prope)
	try:
		conexion = pymysql.connect(host='localhost', user='root', password='database', db='pagossis')
		try:
			with conexion.cursor() as cursor:
				consulta = 'SELECT i.inscripcion, i.precio, i.internet, c.codigo FROM inscripciones i inner join carreras c on i.idcarrera = c.idcarreras WHERE i.idinscripciones = ' + carrera + ';'
				cursor.execute(consulta)
				data = cursor.fetchall()
		finally:
			conexion.close()
	except (pymysql.err.OperationalError, pymysql.err.InternalError) as e:
		print("Ocurrió un error al conectar: ", e)
	examenvista = 0
	if request.method == "POST":
		try:
			conexion = pymysql.connect(host='localhost', user='root', password='database', db='pagossis')
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
						cursor.execute(consulta, (3, nombre, carnet, 100, date.today(), "Internet Reinscripcion" +str(data[0][3]),0, session['idusercaja']))
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
					if prope != 0:
						consulta = 'select idcodigos from codigos where cod = "PROP"'
						cursor.execute(consulta)
						datos = cursor.fetchall()
						idprop = datos[0][0]
						consulta = "INSERT INTO pagos(idcod,nombre,carnet,total,fecha,extra,recibo, user) VALUES (%s,%s,%s,%s,%s,%s,%s,%s);"
						cursor.execute(consulta, (idprop, nombre, carnet, 1000, date.today(), "Propedeutico THDQ",0, session['idusercaja']))
						conexion.commit()
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
		logeado = 0
	if logeado == 0:
		return redirect(url_for('login'))
	try:
		conexion = pymysql.connect(host='localhost', user='root', password='database', db='pagossis')
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
		logeado = 0
	if logeado == 0:
		return redirect(url_for('login'))
	try:
		conexion = pymysql.connect(host='localhost', user='root', password='database', db='pagossis')
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
		logeado = 0
	if logeado == 0:
		return redirect(url_for('login'))
	carrera = str(carrera)
	carnet = str(carnet)
	nombre = str(nombre)
	if request.method == "POST":
		try:
			conexion = pymysql.connect(host='localhost', user='root', password='database', db='pagossis')
			try:
				with conexion.cursor() as cursor:
					consulta1 = 'SELECT idcodigos, precio FROM codigos WHERE cod = "IN' + carrera + '"'
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
		logeado = 0
	if logeado == 0:
		return redirect(url_for('login'))
	try:
		conexion = pymysql.connect(host='localhost', user='root', password='database', db='pagossis')
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
		logeado = 0
	if logeado == 0:
		return redirect(url_for('login'))
	try:
		conexion = pymysql.connect(host='localhost', user='root', password='database', db='pagossis')
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
		logeado = 0
	if logeado == 0:
		return redirect(url_for('login'))
	carrera = str(carrera)
	carnet = str(carnet)
	nombre = str(nombre)
	if request.method == "POST":
		try:
			conexion = pymysql.connect(host='localhost', user='root', password='database', db='pagossis')
			try:
				with conexion.cursor() as cursor:
					consulta1 = 'SELECT idcodigos, precio FROM codigos WHERE cod = "IR' + carrera + '"'
					cursor.execute(consulta1)
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
		logeado = 0
	if logeado == 0:
		return redirect(url_for('login'))
	try:
		conexion = pymysql.connect(host='localhost', user='root', password='database', db='pagossis')
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
		logeado = 0
	if logeado == 0:
		return redirect(url_for('login'))
	try:
		conexion = pymysql.connect(host='localhost', user='root', password='database', db='pagossis')
		try:
			with conexion.cursor() as cursor:
				cursor.execute("SELECT idcodigos, cod, concepto FROM pagossis.codigos WHERE pagose = 1 ORDER BY cod asc;")
 
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
		logeado = 0
	if logeado == 0:
		return redirect(url_for('login'))
	idp = int(idp)
	carnet = str(carnet)
	nombre = str(nombre)
	cod = str(cod)
	descripcion = str(descripcion)
	if request.method == "POST":
		try:
			conexion = pymysql.connect(host='localhost', user='root', password='database', db='pagossis')
			try:
				with conexion.cursor() as cursor:
					consulta1 = 'SELECT precio FROM codigos WHERE idcodigos = "' + str(idp) + '"'
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
			number = number + '98765'
			print(number)
			barcode_format = barcode.get_barcode_class('upc')
			#Generate barcode and render as image
			my_barcode = barcode_format(number, writer=ImageWriter())
			
			#Save barcode as PNG
			aux = "C:\\Users\\galileoserver\\Documents\\sispagosGalileo\\flaskapp\\static\\codbars\\" + str(idpago)
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
		logeado = 0
	if logeado == 0:
		return redirect(url_for('login'))
	try:
		conexion = pymysql.connect(host='localhost', user='root', password='database', db='pagossis')
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
		logeado = 0
	if logeado == 0:
		return redirect(url_for('login'))
	try:
		conexion = pymysql.connect(host='localhost', user='root', password='database', db='pagossis')
		try:
			with conexion.cursor() as cursor:
				cursor.execute("SELECT idcodigos, cod, concepto FROM pagossis.codigos WHERE uniformes = 1 ORDER BY cod asc;")
 
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
		logeado = 0
	if logeado == 0:
		return redirect(url_for('login'))
	uid = int(uid)
	carnet = str(carnet)
	nombre = str(nombre)
	total = float(total)
	talla = str(talla)
	ucod = str(ucod)
	if request.method == "POST":
		try:
			conexion = pymysql.connect(host='localhost', user='root', password='database', db='pagossis')
			try:
				with conexion.cursor() as cursor:
					consulta = "INSERT INTO pagos(idcod,nombre,carnet,total,fecha,extra,recibo,user) VALUES (%s,%s,%s,%s,%s,%s,%s,%s);"
					cursor.execute(consulta, (uid, nombre, carnet, total, date.today(), "Talla: "+talla,0,session['idusercaja']))
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
		logeado = 0
	if logeado == 0:
		return redirect(url_for('login'))
	try:
		conexion = pymysql.connect(host='localhost', user='root', password='database', db='pagossis')
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
			conexion = pymysql.connect(host='localhost', user='root', password='database', db='pagossis')
			try:
				with conexion.cursor() as cursor:
					cursor.execute("SELECT idcarreras, codigo FROM carreras;")
 
			# Con fetchall traemos todas las filas
					carreras = cursor.fetchall()
					consulta = '''select p.nombre, p.carnet, p.fecha, c.codigo, p.extra, p.total from pagos p 
					inner join codigos d on p.idcod = d.idcodigos
					inner join carreras c on d.idcarrera = c.idcarreras
					where d.cod LIKE 'U%' and p.fecha >= "'''
					consulta = consulta + str(defecha) + '" and p.fecha <= "' + str(afecha)
					consulta = consulta + '" order by p.fecha asc, c.codigo desc'
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
		logeado = 0
	if logeado == 0:
		return redirect(url_for('login'))
	numeros = []
	for i in range(10):
		numeros.append(i+1)
	meses = ["Enero", "Febrero","Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]

	try:
		conexion = pymysql.connect(host='localhost', user='root', password='database', db='pagossis')
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
			aux1 = 'mes' + str(i+1)
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
		logeado = 0
	if logeado == 0:
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
				meses[i] = 'Mes: ' + str(meses[i].split("'")[1])
			except:
				meses[i] = 'Mes: ' + str(meses[i])
		elif 'TOPTQ' in pcod or ('TRADQ' in pcod and 'Pre' in pcod):
			try:
				meses[i] = 'Módulo: ' + str(meses[i].split("'")[1])
			except:
				meses[i] = 'Módulo: ' + str(meses[i])
		else:
			try:
				meses[i] = str(meses[i].split("'")[1])
			except:
				meses[i] = meses[i]
			
	if request.method == "POST":
		try:
			conexion = pymysql.connect(host='localhost', user='root', password='database', db='pagossis')
			try:
				with conexion.cursor() as cursor:
					consulta1 = 'SELECT idcodigos, precio, concepto FROM codigos WHERE idcodigos = "' + str(pid) + '"'
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
							if 'LENQ' in precios1[0][2] and ('2' in meses[i] or '4' in meses[i] or '6' in meses[i] or ('1' in meses[i] and '3' in meses[i]) or ('3' in meses[i] and '1' not in meses[i] and '2' not in meses[i] and '3' not in meses[i]) or ('5' in meses[i] and '3' in meses[i])):
								imprimir = True
							else:
								imprimir = False
							if 'LENQ' in precios1[0][2] and ('1' in meses[i] or '3' in meses[i]  or '5' in meses[i]):
								precioasig = 200
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
		logeado = 0
	if logeado == 0:
		return redirect(url_for('login'))
	try:
		conexion = pymysql.connect(host='localhost', user='root', password='database', db='pagossis')
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
			conexion = pymysql.connect(host='localhost', user='root', password='database', db='pagossis')
			try:
				with conexion.cursor() as cursor:
					cursor.execute("SELECT idcarreras, codigo FROM carreras;")
	
				# Con fetchall traemos todas las filas
					carreras = cursor.fetchall()
					consulta = '''select p.nombre, p.carnet, p.fecha, c.codigo, p.extra, p.total from pagos p 
					inner join codigos d on p.idcod = d.idcodigos
					inner join carreras c on d.idcarrera = c.idcarreras
					where d.cod LIKE 'P%' and d.cod != 'PROP' and d.cod != 'PAG' and d.cod != 'PARQ' and p.fecha >= "'''
					consulta = consulta + str(defecha) + '" and p.fecha <= "' + str(afecha)
					consulta = consulta + '" order by p.fecha asc, c.codigo desc, p.nombre asc, p.extra asc'
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
		logeado = 0
	if logeado == 0:
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
	print(newarray)
	try:
		conexion = pymysql.connect(host='localhost', user='root', password='database', db='pagossis')
		try:
			with conexion.cursor() as cursor:
				meses = []
				idhojas = []
				for i in range(cantidad):
					consulta = 'SELECT nombre, carnet, descripcion, idpracticalbcq FROM practicalbcq WHERE idpracticalbcq = '+str(newarray[i])+';'
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
		logeado = 0
	if logeado == 0:
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
	print(newarray)
	try:
		conexion = pymysql.connect(host='localhost', user='root', password='database', db='pagossis')
		try:
			with conexion.cursor() as cursor:
				meses = []
				idhojas = []
				for i in range(cantidad):
					consulta = 'SELECT nombre, carnet, descripcion, idpracticalbcq FROM practicalbcq WHERE idpracticalbcq = '+str(newarray[i])+';'
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
		logeado = 0
	if logeado == 0:
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
		conexion = pymysql.connect(host='localhost', user='root', password='database', db='pagossis')
		try:
			with conexion.cursor() as cursor:
				meses = []
				consulta = 'SELECT nombre, carnet, practica, lugar, DATE_FORMAT(fechainicio,"%d/%m/%Y"), DATE_FORMAT(fechafin,"%d/%m/%Y") FROM practicalenq WHERE idpracticalenq = '+str(newarray[0])+';'
				cursor.execute(consulta)
			# Con fetchall traemos todas las filas
				practica = cursor.fetchone()

		finally:
			conexion.close()
	except (pymysql.err.OperationalError, pymysql.err.InternalError) as e:
		print("Ocurrió un error al conectar: ", e)
	fechaact = date.today()
	year = fechaact.year

	if '1' in practica[2]:
		template = 'hojalenq1.html'
	elif '2' in practica[2]:
		template = 'hojalenq2.html'
	elif '3' in practica[2]:
		template = 'hojalenq3.html'
	elif '4' in practica[2]:
		template = 'hojalenq4.html'
	elif '5' in practica[2]:
		template = 'hojalenq5.html'
	elif '6' in practica[2]:
		template = 'hojalenq6.html'

	
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
		logeado = 0
	if logeado == 0:
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
		conexion = pymysql.connect(host='localhost', user='root', password='database', db='pagossis')
		try:
			with conexion.cursor() as cursor:
				consulta = 'SELECT nombre, carnet FROM pagos WHERE idpagos = '+str(newarray[0])+';'
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
		logeado = 0
	if logeado == 0:
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
		conexion = pymysql.connect(host='localhost', user='root', password='database', db='pagossis')
		try:
			with conexion.cursor() as cursor:
				meses = []
				idhojas = []
				for i in range(cantidad):
					consulta = 'SELECT nombre, carnet, extra, idpagos FROM pagos WHERE idpagos = '+str(newarray[i])+';'
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
	
	rendered = render_template('hojatlcq.html', title="Hoja de Práctica ", cantidad = cantidad, nombre = nombre, carnet = carnet, year = year, idhojas = idhojas, meses = meses)
	options = {'enable-local-file-access': None, 'page-size': 'Legal', 'margin-bottom': '35mm'}
	config = pdfkit.configuration(wkhtmltopdf="C:\\Program Files\\wkhtmltopdf\\bin\\wkhtmltopdf.exe")
	pdf = pdfkit.from_string(rendered, False, configuration=config, options=options)
	response = make_response(pdf)
	response.headers['Content-Type'] = 'application/pdf'
	response.headers['Content-Disposition'] = 'inline; filename=reportediario.pdf'
	print(response)
	return response

@app.route('/prepracticatradq/<idpagos>', methods=['GET', 'POST'])
def prepracticatradq(idpagos):
	try:
		logeado = session['logeadocaja']
	except:
		logeado = 0
	if logeado == 0:
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
		conexion = pymysql.connect(host='localhost', user='root', password='database', db='pagossis')
		try:
			with conexion.cursor() as cursor:
				numeros = []
				for i in range(cantidad):
					consulta = 'SELECT nombre, carnet, extra FROM pagos WHERE idpagos = '+str(newarray[i])+';'
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
		logeado = 0
	if logeado == 0:
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
		conexion = pymysql.connect(host='localhost', user='root', password='database', db='pagossis')
		try:
			with conexion.cursor() as cursor:
				numeros = []
				for i in range(cantidad):
					consulta = 'SELECT nombre, carnet, extra FROM pagos WHERE idpagos = '+str(newarray[i])+';'
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
		logeado = 0
	if logeado == 0:
		return redirect(url_for('login'))
	try:
		conexion = pymysql.connect(host='localhost', user='root', password='database', db='pagossis')
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
		logeado = 0
	if logeado == 0:
		return redirect(url_for('login'))
	total = float(total)
	carnet = str(carnet)
	nombre = str(nombre)
	carrera = str(carrera)
	if request.method == "POST":
		try:
			conexion = pymysql.connect(host='localhost', user='root', password='database', db='pagossis')
			try:
				with conexion.cursor() as cursor:
					consulta1 = 'SELECT idcodigos FROM codigos WHERE cod = "MENE"'
					cursor.execute(consulta1)
					precios1 = cursor.fetchall()
					print(precios1[0])
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
		logeado = 0
	if logeado == 0:
		return redirect(url_for('login'))
	try:
		conexion = pymysql.connect(host='localhost', user='root', password='database', db='pagossis')
		try:
			with conexion.cursor() as cursor:
				cursor.execute("SELECT idcarreras, codigo FROM carreras;")
 
			# Con fetchall traemos todas las filas
				carreras = cursor.fetchall()
				consulta = 'select nombre, carnet, fecha, extra, total from pagos where idcod = 64 order by fecha asc'
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
		logeado = 0
	if logeado == 0:
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
		logeado = 0
	if logeado == 0:
		return redirect(url_for('login'))
	cantidad = int(cantidad)
	total = cantidad * 10
	if request.method == "POST":
		try:
			conexion = pymysql.connect(host='localhost', user='root', password='database', db='pagossis')
			try:
				with conexion.cursor() as cursor:
					consulta = "INSERT INTO pagos(idcod,nombre,carnet,total,fecha,extra, recibo,user) VALUES (%s,%s,%s,%s,%s,%s,%s,%s);"
					cursor.execute(consulta, (65, 'parqueo', 0, total, date.today(), "Cantidad parqueo: " +str(cantidad), 0,session['idusercaja']))
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
		logeado = 0
	if logeado == 0:
		return redirect(url_for('login'))
	try:
		conexion = pymysql.connect(host='localhost', user='root', password='database', db='pagossis')
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
		logeado = 0
	if logeado == 0:
		return redirect(url_for('login'))
	try:
		conexion = pymysql.connect(host='localhost', user='root', password='database', db='pagossis')
		try:
			with conexion.cursor() as cursor:
				cursor.execute("SELECT idcodigos, cod, concepto FROM pagossis.codigos WHERE manual = 1 ORDER BY cod asc;")
 
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
			aux1 = 'curso' + str(i+1)
			aux = request.form[aux1]
			if(len(aux) > 0):
				datacurso.append(aux)
		return redirect(url_for('confirmacionm', carnet = datacarnet, nombre = datanombre, curso= datacurso, mid = mid, mcod = mcod))
	return render_template('manuales.html', title="Manuales",  carreras=carreras, logeado=logeado)

@app.route('/confirmacionm/<carnet>&<nombre>&<curso>&<mid>&<mcod>', methods=['GET', 'POST'])
def confirmacionm(carnet, nombre, curso, mid, mcod):
	try:
		logeado = session['logeadocaja']
	except:
		logeado = 0
	if logeado == 0:
		return redirect(url_for('login'))
	carnet = str(carnet)
	nombre = str(nombre)
	mid = str(mid)
	mcod = str(mcod)
	curso = str(curso)
	cursos=curso.split(',')
	cantidad = len(cursos)
	for i in range(cantidad):
		try:
			cursos[i] = str(cursos[i].split("'")[1])
		except:
			cursos[i] = cursos[i]
	if request.method == "POST":
		try:
			conexion = pymysql.connect(host='localhost', user='root', password='database', db='pagossis')
			try:
				with conexion.cursor() as cursor:
					consulta1 = 'SELECT idcodigos, precio FROM codigos WHERE idcodigos = "' + mid + '"'
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
			finally:
				conexion.close()
		except (pymysql.err.OperationalError, pymysql.err.InternalError) as e:
			print("Ocurrió un error al conectar: ", e)
		return redirect(url_for('imprimir', idpagos=idpagos))
	return render_template('confirmacionm.html', title="Confirmación", carnet = carnet, nombre = nombre, cursos = cursos, mid = mid, mcod = mcod, cantidad=cantidad, logeado=logeado)

@app.route('/repm', methods=['GET', 'POST'])
def repm():
	try:
		logeado = session['logeadocaja']
	except:
		logeado = 0
	if logeado == 0:
		return redirect(url_for('login'))
	try:
		conexion = pymysql.connect(host='localhost', user='root', password='database', db='pagossis')
		try:
			with conexion.cursor() as cursor:
				cursor.execute("SELECT idcarreras, codigo FROM carreras;")
 
			# Con fetchall traemos todas las filas
				carreras = cursor.fetchall()
				consulta = '''select p.nombre, p.carnet, p.fecha, c.codigo, p.extra, p.total, p.extra1, p.fechaextra1, p.idpagos from pagos p 
				inner join codigos d on p.idcod = d.idcodigos
				inner join carreras c on d.idcarrera = c.idcarreras
				where d.concepto LIKE '%Manual%' and p.fecha > DATE_SUB(now(), INTERVAL 6 MONTH)
				order by p.fecha desc, p.nombre asc'''
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
			conexion = pymysql.connect(host='localhost', user='root', password='database', db='pagossis')
			try:
				with conexion.cursor() as cursor:
					cursor.execute("SELECT idcarreras, codigo FROM carreras;")
	
				# Con fetchall traemos todas las filas
					carreras = cursor.fetchall()
					consulta = '''select p.nombre, p.carnet, p.fecha, c.codigo, p.extra, p.total from pagos p 
					inner join codigos d on p.idcod = d.idcodigos
					inner join carreras c on d.idcarrera = c.idcarreras
					where d.concepto LIKE '%Manual%'''
					if len(defecha) > 0:
						consulta = consulta + ' and DATE(p.fecha) >= DATE("' + str(defecha) + '") '
					if len(afecha) > 0:
						consulta = consulta + ' and DATE(p.fecha) <= DATE("' + str(afecha) + '") '
					consulta = consulta + ' order by p.fecha asc, c.codigo desc'
					print(consulta)
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
	return render_template('repm.html', title="Reporte Manuales", data = data, suma=suma, carreras=carreras, logeado=logeado)

@app.route('/entregarm/<idpago>', methods=['GET', 'POST'])
def entregarm(idpago):
	try:
		logeado = session['logeadocaja']
	except:
		logeado = 0
	if logeado == 0:
		return redirect(url_for('login'))
	try:
		#date.today()
		conexion = pymysql.connect(host='localhost', user='root', password='database', db='pagossis')
		try:
			with conexion.cursor() as cursor:
				consulta = "update pagos set extra1 = 1, fechaextra1 = %s where idpagos = %s;"
				cursor.execute(consulta, (date.today(), idpago))
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
		logeado = 0
	if logeado == 0:
		return redirect(url_for('login'))
	try:
		conexion = pymysql.connect(host='localhost', user='root', password='database', db='pagossis')
		try:
			with conexion.cursor() as cursor:
				cursor.execute("SELECT idcodigos, cod, concepto, precio FROM pagossis.codigos WHERE pagos = 1 ORDER BY concepto asc;")
 
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
		datames = request.form["mes"]
		if len(datadescripcion) < 1:
			datadescripcion = 0
		if len(datatotal) < 1:
			datatotal = 0
		if len(datames) < 1:
			datames = 0
		data = datacarrera.split(',')
		pid = data[0]
		pcod = data[1]
		ptotal = data[2]
		return redirect(url_for('confirmacionpag', carnet = datacarnet, nombre = datanombre, total = datatotal, descripcion= datadescripcion, pid = pid, pcod = pcod, ptotal = ptotal, datames=datames))
	return render_template('pag.html', title="Pagos", carreras = carreras, logeado=logeado, meses=meses)

@app.route('/confirmacionpag/<carnet>&<nombre>&<total>&<descripcion>&<pid>&<pcod>&<ptotal>&<datames>', methods=['GET', 'POST'])
def confirmacionpag(carnet, nombre, total, descripcion, pid, pcod, ptotal, datames):
	try:
		logeado = session['logeadocaja']
	except:
		logeado = 0
	if logeado == 0:
		return redirect(url_for('login'))
	carnet = str(carnet)
	nombre = str(nombre)
	total = float(total)
	descripcion = str(descripcion)
	pid = str(pid)
	pcod = str(pcod)
	ptotal = str(ptotal)
	datames = str(datames)
	if pcod != 'Pagos' and pcod != 'Curso Dirigido':
		total = float(ptotal)
		descripcion = pcod
	if request.method == "POST":
		try:
			conexion = pymysql.connect(host='localhost', user='root', password='database', db='pagossis')
			try:
				with conexion.cursor() as cursor:
					if datames == '0':
						consulta = "INSERT INTO pagos(idcod,nombre,carnet,total,fecha,extra, recibo,user) VALUES (%s,%s,%s,%s,%s,%s,%s,%s);"
						cursor.execute(consulta, (pid, nombre, carnet, total, date.today(), descripcion, 0,session['idusercaja']))
					else:
						consulta = "INSERT INTO pagos(idcod,nombre,carnet,total,fecha,extra, recibo,user) VALUES (%s,%s,%s,%s,%s,%s,%s,%s);"
						cursor.execute(consulta, (pid, nombre, carnet, total, date.today(), descripcion + ' ' + datames, 0,session['idusercaja']))
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
		logeado = 0
	if logeado == 0:
		return redirect(url_for('login'))
	try:
		conexion = pymysql.connect(host='localhost', user='root', password='database', db='pagossis')
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
		logeado = 0
	if logeado == 0:
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
		logeado = 0
	if logeado == 0:
		return redirect(url_for('login'))
	tipo = int(tipo)
	carnet = str(carnet)
	nombre = str(nombre)
	if request.method == "POST":
		try:
			conexion = pymysql.connect(host='localhost', user='root', password='database', db='pagossis')
			try:
				with conexion.cursor() as cursor:
					if tipo == 1:
						consulta1 = 'SELECT idcodigos, precio FROM codigos WHERE cod = "GRADT"'
						cursor.execute(consulta1)
						precios1 = cursor.fetchall()
						print(precios1[0])
					elif tipo == 2:
						consulta1 = 'SELECT idcodigos, precio FROM codigos WHERE cod = "GRADL"'
						cursor.execute(consulta1)
						precios1 = cursor.fetchall()
						print(precios1[0])
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
		logeado = 0
	if logeado == 0:
		return redirect(url_for('login'))
	try:
		conexion = pymysql.connect(host='localhost', user='root', password='database', db='pagossis')
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
		logeado = 0
	if logeado == 0:
		return redirect(url_for('login'))
	try:
		conexion = pymysql.connect(host='localhost', user='root', password='database', db='pagossis')
		try:
			with conexion.cursor() as cursor:
				consulta = 'select billete1, billete5, billete10, billete20, billete50, billete100, billete200, facturas, vales, tarjeta, idefectivo from efectivo where fecha = CURDATE() and iduser = ' + str(session['idusercaja']) + ';'
				cursor.execute(consulta)
				efectivo = cursor.fetchall()
				if len(efectivo) > 0:
					efectivo = efectivo[0]
				else:
					consulta = 'INSERT INTO efectivo(billete1, billete5, billete10, billete20, billete50, billete100, billete200, facturas, vales, tarjeta, fecha, iduser) values (0,0,0,0,0,0,0,0,0,0,CURDATE(),%s);'
					cursor.execute(consulta, session['idusercaja'])
					conexion.commit()
					consulta = 'select billete1, billete5, billete10, billete20, billete50, billete100, billete200, facturas, vales, tarjeta, idefectivo from efectivo where fecha = CURDATE() and iduser = ' + str(session['idusercaja']) + ';'
					cursor.execute(consulta)
					efectivo = cursor.fetchone()
				consulta = 'SELECT c.cod, c.concepto, count(p.total), round(sum(p.total),2) FROM pagos p INNER JOIN codigos c ON p.idcod = c.idcodigos WHERE fecha = "'+str(date.today())+'" and p.recibo = 0 and p.user = ' + str(session['idusercaja']) + ' group by c.cod order by c.cod asc, p.nombre asc;'
				print(consulta)
				cursor.execute(consulta)
				sumas = cursor.fetchall()
				sumtotal = 0
				for i in sumas:
					sumtotal = sumtotal + float(i[3])
				consulta = 'SELECT p.fechadevuelto, c.cod, c.concepto, round(p.total,2) FROM pagos p INNER JOIN codigos c ON p.idcod = c.idcodigos WHERE fechadevuelto = "'+str(date.today())+'" order by c.cod asc, p.nombre asc;'
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
			conexion = pymysql.connect(host='localhost', user='root', password='database', db='pagossis')
			try:
				with conexion.cursor() as cursor:
					print(facturas)
					consulta = "UPDATE efectivo set billete1=%s, billete5=%s, billete10=%s, billete20=%s, billete50=%s, billete100=%s, billete200=%s, facturas=%s, vales=%s, tarjeta=%s where idefectivo = %s and iduser = %s;"
					cursor.execute(consulta, (q1, q5, q10, q20, q50, q100, q200, facturas, vales, tarjeta, efectivo[10], session['idusercaja']))
				conexion.commit()
			finally:
				conexion.close()
		except (pymysql.err.OperationalError, pymysql.err.InternalError) as e:
			print("Ocurrió un error al conectar: ", e)
		return redirect(url_for('reportes'))
	return render_template('reportes.html', title="Reportes", sumas = sumas, sumtotal=sumtotal, logeado=logeado, datadev=datadev, totaldev=totaldev, totaltotal=totaltotal, efectivo=efectivo)

@app.route('/repdiario', methods=['GET', 'POST'])
def repdiario():
	try:
		logeado = session['logeadocaja']
	except:
		logeado = 0
	if logeado == 0:
		return redirect(url_for('login'))
	try:
		conexion = pymysql.connect(host='localhost', user='root', password='database', db='pagossis')
		try:
			with conexion.cursor() as cursor:
				consulta = 'SELECT c.cod, c.concepto, count(p.total), round(sum(p.total),2), c.idcodigos FROM pagos p INNER JOIN codigos c ON p.idcod = c.idcodigos WHERE fecha = "'+str(date.today())+'" and p.recibo = 0 group by c.cod order by c.cod asc, p.nombre asc;'
				cursor.execute(consulta)
				resumen = cursor.fetchall()
				consulta = 'select recibo from pagos where (length(recibo) < 5 and fecha = date_sub(CURDATE(), interval 1 day)) or (fecha = CURDATE() and recibo <> 0 and length(recibo) < 5) or (length(recibo) < 5 and fecha = date_sub(CURDATE(), interval 2 day)) order by recibo desc;'
				cursor.execute(consulta)
				boletasig = cursor.fetchone()
				boletasig = boletasig[0]
				consulta = 'SELECT p.nombre, p.carnet, p.fecha, c.concepto, p.extra, round(p.total,2), p.idpagos, u.iniciales FROM pagos p INNER JOIN codigos c ON p.idcod = c.idcodigos inner join user u on u.iduser = p.user WHERE fecha = "'+str(date.today())+'" and p.recibo = 0 order by c.cod asc, p.nombre asc;'
				print(consulta)
				cursor.execute(consulta)
			# Con fetchall traemos todas las filas
				data = cursor.fetchall()
				suma = 0
				for i in data:
					suma = suma + i[5]
				consulta = 'SELECT p.fechadevuelto, c.cod, c.concepto, round(p.total,2) FROM pagos p INNER JOIN codigos c ON p.idcod = c.idcodigos WHERE fechadevuelto = "'+str(date.today())+'" order by c.cod asc, p.nombre asc;'
				cursor.execute(consulta)
				datadev = cursor.fetchall()
		finally:
			conexion.close()
	except (pymysql.err.OperationalError, pymysql.err.InternalError) as e:
		print("Ocurrió un error al conectar: ", e)
	if request.method == 'POST':
		try:
			conexion = pymysql.connect(host='localhost', user='root', password='database', db='pagossis')
			try:
				with conexion.cursor() as cursor:
					regen = request.form["regen"]
					if regen == '0' or len(regen) < 1:
						for i in resumen:
							aux = "resumen" + str(i[4])
							varaux = str(request.form[aux])
							if len(varaux) > 0:
								consulta = 'UPDATE pagos SET recibo = "'+str(varaux)+'" WHERE idcod = '+str(i[4])+' and fecha = CURDATE() and recibo = 0;'
								print(consulta)
								cursor.execute(consulta)
						for i in data:
							aux = "re"+str(i[6])
							varaux = str(request.form[aux])
							if len(varaux) > 0:
								consulta = 'UPDATE pagos SET recibo = "'+str(varaux)+'" WHERE idpagos = '+str(i[6])+';'
								print(consulta)
								cursor.execute(consulta)
					else:
						for i in data:
							consulta = 'UPDATE pagos SET recibo = "'+str(regen)+'" WHERE idpagos = '+str(i[6])+';'
							cursor.execute(consulta)
					consulta = "UPDATE efectivo set billete1=0, billete5=0, billete10=0, billete20=0, billete50=0, billete100=0, billete200=0, facturas=0, vales=0 where idefectivo = 1;"
					cursor.execute(consulta)
				conexion.commit()
			finally:
				conexion.close()
		except (pymysql.err.OperationalError, pymysql.err.InternalError) as e:
			print("Ocurrió un error al conectar: ", e)
		#webbrowser.open("http://galileoserver:5000/repdiariopdf")
		return redirect(url_for('repdiario'))
	return render_template('repdiario.html', title="Reporte diario", data = data, suma=suma, logeado=logeado, datadev=datadev, resumen=resumen, boletasig = boletasig)

@app.route('/repdiariopdf', methods=['GET', 'POST'])
def repdiariopdf():
	try:
		logeado = session['logeadocaja']
	except:
		logeado = 0
	if logeado == 0:
		return redirect(url_for('login'))
	today = date.today()
	d1 = today.strftime("%d/%m/%Y")
	try:
		conexion = pymysql.connect(host='localhost', user='root', password='database', db='pagossis')
		try:
			with conexion.cursor() as cursor:
				consulta = 'SELECT p.nombre, p.carnet, DATE_FORMAT(p.fecha,"%d/%m/%Y"), c.concepto, p.extra, round(p.total,2), p.idpagos, p.recibo, u.iniciales FROM pagos p INNER JOIN codigos c ON p.idcod = c.idcodigos inner join user u on u.iduser = p.user WHERE fecha = "'+str(date.today())+'" order by c.cod asc, p.nombre asc;'
				cursor.execute(consulta)
			# Con fetchall traemos todas las filas
				data = cursor.fetchall()
				suma = 0
				for i in data:
					suma = suma + float(i[5])
				consulta = 'SELECT p.nombre, p.carnet, DATE_FORMAT(p.fechadevuelto,"%d/%m/%Y"), c.concepto, p.extra, round(p.total), p.idpagos, p.recibo, u.iniciales FROM pagos p INNER JOIN codigos c ON p.idcod = c.idcodigos inner join user u on u.iduser = p.user WHERE fechadevuelto = "'+str(date.today())+'" order by c.cod asc, p.nombre asc;'
				cursor.execute(consulta)
				datadev = cursor.fetchall()
				contdev = len(datadev)
				sumadev = 0
				for i in datadev:
					sumadev = sumadev + float(i[5])
				consulta = 'SELECT c.cod, c.concepto, count(p.total), round(sum(p.total),2), p.recibo FROM pagos p INNER JOIN codigos c ON p.idcod = c.idcodigos WHERE fecha = "'+str(date.today())+'" group by recibo, cod order by p.recibo asc, c.cod asc, p.nombre asc;'
				cursor.execute(consulta)
				resumen = cursor.fetchall()
				cantidadresumen = len(resumen)
				consulta = "SELECT round(sum(total),2), recibo from pagos where fecha = '" + str(date.today()) + "' group by recibo order by recibo"
				cursor.execute(consulta)
				totalrecibo = cursor.fetchall()
				cantidadrecibo = len(totalrecibo)
				consulta = 'SELECT nombre, factura, recibo, total from transferencias where fecha = CURDATE() ORDER by nombre asc'
				cursor.execute(consulta)
				transferencias = cursor.fetchall()
				consulta = 'SELECT ROUND(SUM(total),2) from transferencias where fecha = CURDATE()'
				cursor.execute(consulta)
				totaltransferencias = cursor.fetchone()
				consulta = 'SELECT SUM(ROUND(billete1 + (billete5 * 5)  + (billete10 * 10) + (billete20 * 20) + (billete50 * 50) + (billete100 * 100) + (billete200 * 200), 2)), facturas, vales, tarjeta from efectivo where fecha = CURDATE()'
				cursor.execute(consulta)
				efectivo = cursor.fetchone()
				efectivo1 = []
				for i in efectivo:
					arreglo = str(i).split('+')
					total = 0
					for j in arreglo:
						total = total + float(j)
					efectivo1.append(total)
				efectivo = efectivo1
		finally:
			conexion.close()
	except (pymysql.err.OperationalError, pymysql.err.InternalError) as e:
		print("Ocurrió un error al conectar: ", e)
	
	rendered = render_template('repdiariopdf.html', title="Reporte diario", data = data, suma=suma, datadev=datadev, sumadev=sumadev, contdev=contdev, d1=d1, resumen = resumen, cantidadresumen = cantidadresumen, totalrecibo = totalrecibo, cantidadrecibo = cantidadrecibo, transferencias = transferencias, totaltransferencias=totaltransferencias, efectivo=efectivo)
	options = {'enable-local-file-access': None, 'page-size': 'Letter','margin-right': '10mm'}
	config = pdfkit.configuration(wkhtmltopdf="C:\\Program Files\\wkhtmltopdf\\bin\\wkhtmltopdf.exe")
	pdf = pdfkit.from_string(rendered, False, configuration=config, options=options)
	response = make_response(pdf)
	response.headers['Content-Type'] = 'application/pdf'
	response.headers['Content-Disposition'] = 'inline; filename=reportediario.pdf'
	print(response)
	return response

@app.route('/repdiariopdffecha/<dia>&<mes>&<anio>', methods=['GET', 'POST'])
def repdiariopdffecha(dia, mes, anio):
	try:
		logeado = session['logeadocaja']
	except:
		logeado = 0
	if logeado == 0:
		return redirect(url_for('login'))
	fechareq = str(anio) + '-' + str(mes) + '-' + str(dia)
	try:
		conexion = pymysql.connect(host='localhost', user='root', password='database', db='pagossis')
		try:
			with conexion.cursor() as cursor:
				consulta = 'SELECT p.nombre, p.carnet, DATE_FORMAT(p.fecha,"%d/%m/%Y"), c.concepto, p.extra, round(p.total,2), p.idpagos, p.recibo, u.iniciales FROM pagos p INNER JOIN codigos c ON p.idcod = c.idcodigos inner join user u on u.iduser = p.user WHERE fecha = "'+fechareq+'" order by c.cod asc, p.nombre asc;'
				cursor.execute(consulta)
			# Con fetchall traemos todas las filas
				data = cursor.fetchall()
				suma = 0
				for i in data:
					suma = suma + float(i[5])
				consulta = 'SELECT p.nombre, p.carnet, DATE_FORMAT(p.fechadevuelto,"%d/%m/%Y"), c.concepto, p.extra, round(p.total), p.idpagos, p.recibo, u.iniciales FROM pagos p INNER JOIN codigos c ON p.idcod = c.idcodigos inner join user u on u.iduser = p.user WHERE fechadevuelto = "'+fechareq+'" order by c.cod asc, p.nombre asc;'
				cursor.execute(consulta)
				datadev = cursor.fetchall()
				contdev = len(datadev)
				sumadev = 0
				for i in datadev:
					sumadev = sumadev + float(i[5])
				consulta = 'SELECT c.cod, c.concepto, count(p.total), round(sum(p.total),2), p.recibo FROM pagos p INNER JOIN codigos c ON p.idcod = c.idcodigos WHERE fecha = "'+fechareq+'" group by recibo, cod order by p.recibo asc, c.cod asc, p.nombre asc;'
				cursor.execute(consulta)
				resumen = cursor.fetchall()
				cantidadresumen = len(resumen)
				consulta = "SELECT round(sum(total),2), recibo from pagos where fecha = '" + fechareq + "' group by recibo order by recibo"
				cursor.execute(consulta)
				totalrecibo = cursor.fetchall()
				cantidadrecibo = len(totalrecibo)
				consulta = 'SELECT nombre, factura, recibo, total from transferencias where fecha = "' + fechareq + '" ORDER by nombre asc'
				cursor.execute(consulta)
				transferencias = cursor.fetchall()
				consulta = 'SELECT ROUND(SUM(total),2) from transferencias where fecha = "' + fechareq + '"'
				cursor.execute(consulta)
				totaltransferencias = cursor.fetchone()
				consulta = 'SELECT ROUND(billete1 + (billete5 * 5)  + (billete10 * 10) + (billete20 * 20) + (billete50 * 50) + (billete100 * 100) + (billete200 * 200), 2), facturas, vales, tarjeta from efectivo where fecha = "' + fechareq + '"'
				cursor.execute(consulta)
				efectivo = cursor.fetchone()
				print(consulta)
				efectivo1 = []
				for i in efectivo:
					arreglo = str(i).split('+')
					total = 0
					for j in arreglo:
						total = total + float(j)
					efectivo1.append(total)
				efectivo = efectivo1
		finally:
			conexion.close()
	except (pymysql.err.OperationalError, pymysql.err.InternalError) as e:
		print("Ocurrió un error al conectar: ", e)
	
	rendered = render_template('repdiariopdf.html', title="Reporte diario", data = data, suma=suma, datadev=datadev, sumadev=sumadev, contdev=contdev, d1=fechareq, resumen = resumen, cantidadresumen = cantidadresumen, totalrecibo = totalrecibo, cantidadrecibo = cantidadrecibo, transferencias = transferencias, totaltransferencias=totaltransferencias, efectivo=efectivo)
	options = {'enable-local-file-access': None}
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
		logeado = 0
	if logeado == 0:
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
		print(datafechapago)
		try:
			conexion = pymysql.connect(host='localhost', user='root', password='database', db='pagossis')
			try:
				with conexion.cursor() as cursor:
					consulta = 'SELECT nombre, carnet, fecha, practica, lugar, fechainicio, fechafin, idpracticalenq FROM practicalenq '
					consulta = consulta + 'where nombre like "%' + str(datanombre) + '%"'
					consulta = consulta + ' and carnet like "%' + str(datacarnet) + '%"'
					if len(datafechaini) != 0:
						consulta = consulta + ' and fechainicio = "' + str(datafechaini) + '"'
					if len(datafechafin) != 0:
						consulta = consulta + ' and fechafin = "' + str(datafechafin) + '"'
					if len(datafechapago) != 0:
						consulta = consulta + ' and fecha = "' + str(datafechapago) + '"'
					consulta = consulta + ' and lugar like "%' + str(datalugar) + '%"'
					consulta = consulta + ' and practica like "%' + str(datadescripcion) + '%"'
					consulta = consulta + ' order by fecha desc, practica asc, nombre asc;'
					print(consulta)
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
		logeado = 0
	if logeado == 0:
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
		print(datafechapago)
		try:
			conexion = pymysql.connect(host='localhost', user='root', password='database', db='pagossis')
			try:
				with conexion.cursor() as cursor:
					consulta = 'SELECT q.nombre, q.carnet, q.fecha, q.descripcion, q.idpracticalbcq, c.concepto FROM practicalbcq q '
					consulta = consulta + "inner join codigos c on q.idcodigo = c.idcodigos "
					consulta = consulta + 'where q.nombre like "%' + str(datanombre) + '%"'
					consulta = consulta + ' and q.carnet like "%' + str(datacarnet) + '%"'
					if len(datafechapago) != 0:
						consulta = consulta + ' and q.fecha = "' + str(datafechapago) + '"'
					consulta = consulta + ' and q.descripcion like "%' + str(datadescripcion) + '%"'
					consulta = consulta + ' and c.concepto like "%' + str(dataconcepto) + '%"'
					consulta = consulta + ' order by fecha desc, nombre asc;'
					print(consulta)
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
		logeado = 0
	if logeado == 0:
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
			conexion = pymysql.connect(host='localhost', user='root', password='database', db='pagossis')
			try:
				with conexion.cursor() as cursor:
					consulta = 'SELECT p.nombre, p.carnet, p.fecha, c.concepto, p.extra, p.recibo, p.total, p.idpagos, p.devuelto FROM pagos p INNER JOIN codigos c ON p.idcod = c.idcodigos '
					consulta = consulta + 'where p.nombre like "%' + str(datanombre) + '%"'
					consulta = consulta + ' and p.carnet like "%' + str(datacarnet) + '%"'
					if len(datafechaini) != 0:
						consulta = consulta + ' and p.fecha >= "' + str(datafechaini) + '"'
					if len(datafechafin) != 0:
						consulta = consulta + ' and p.fecha <= "' + str(datafechafin) + '"'
					consulta = consulta + ' and c.concepto like "%' + str(dataconcepto) + '%"'
					consulta = consulta + ' and p.extra like "%' + str(datadescripcion) + '%"'
					consulta = consulta + ' and p.recibo like "%' + str(datarecibo) + '%"'
					consulta = consulta + ' order by p.fecha desc, c.concepto asc, p.extra asc, p.nombre asc;'
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
		logeado = 0
	if logeado == 0:
		return redirect(url_for('login'))
	
	return render_template('pagos.html', title="Pagos", logeado=logeado)

@app.route('/transferencias', methods=['GET', 'POST'])
def transferencias():
	try:
		logeado = session['logeadocaja']
	except:
		logeado = 0
	if logeado == 0:
		return redirect(url_for('login'))
	if request.method == 'POST':
		recibo = request.form["recibo"]
		factura = request.form["factura"]
		nombre = request.form["nombre"]
		total = request.form["total"]
		try:
			conexion = pymysql.connect(host='localhost', user='root', password='database', db='pagossis')
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
		logeado = 0
	if logeado == 0:
		return redirect(url_for('login'))

	try:
		conexion = pymysql.connect(host='localhost', user='root', password='database', db='pagossis')
		try:
			with conexion.cursor() as cursor:
				consulta1 = 'SELECT nombre, fecha, factura, recibo, total from transferencias ORDER by fecha desc, nombre asc'
				cursor.execute(consulta1)
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
		logeado = 0
	if logeado == 0:
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
		conexion = pymysql.connect(host='localhost', user='root', password='database', db='pagossis')
		try:
			with conexion.cursor() as cursor:
				for i in range(numpagos):
					consulta = 'SELECT p.nombre, p.carnet, DATE_FORMAT(p.fecha,"%d/%m/%Y"), c.concepto, p.extra, p.total, u.iniciales FROM pagos p INNER JOIN codigos c ON p.idcod = c.idcodigos inner join user u on u.iduser = p.user WHERE p.idpagos = '+str(newarray[i])+';'
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

if __name__ == '__main__':
	app.run(host='0.0.0.0', port=5000, threaded=True, debug=True)