from flask import Flask, render_template, request, url_for, redirect, make_response, session
import pymysql
from datetime import date, datetime
import os
import webbrowser
import pdfkit as pdfkit


app = Flask(__name__)
app.secret_key = 'd589d3d0d15d764ed0a98ff5a37af547'

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
		filename = 'dev' + str(idpago) + '.'
		if '.png' in file.filename:
			filename = filename + 'png'
		elif '.pdf' in file.filename:
			filename = filename + 'pdf'
		elif '.jpg' in file.filename:
			filename = filename + 'jpg'
		elif '.jpeg' in file.filename:
			filename = filename + 'jpeg'
		file.save(os.path.join("flaskapp\\static\\uploads", filename))
		try:
			conexion = pymysql.connect(host='localhost', user='root', password='database', db='pagossis')
			try:
				with conexion.cursor() as cursor:
					consulta = 'UPDATE pagos set devuelto = 1, urldevuelto = %s, fechadevuelto=%s, user=%s where idpagos = %s;'
					cursor.execute(consulta, (filename, date.today(), session['idusercaja'], idpago))
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
				consulta = 'SELECT idcodigos, precio from codigos where cod like "INGLES%" order by cod asc'
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
	return render_template('ingles.html', title='Academia', logeado=logeado, meses=meses, cuotas=cuotas)

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
					consulta = 'SELECT idcodigos, precio from codigos where cod = "INGLEST"'
					cursor.execute(consulta)
					datainsc = cursor.fetchone()
					consulta = 'SELECT idcodigos, precio from codigos where cod = "MEINGLEST"'
					cursor.execute(consulta)
					datamen = cursor.fetchone()
				else:
					consulta = 'SELECT idcodigos, precio from codigos where cod = "INGLESS"'
					cursor.execute(consulta)
					datainsc = cursor.fetchone()
					consulta = 'SELECT idcodigos, precio from codigos where cod = "MEINGLESS"'
					cursor.execute(consulta)
					datamen = cursor.fetchone()
		finally:
			conexion.close()
	except (pymysql.err.OperationalError, pymysql.err.InternalError) as e:
		print("Ocurrió un error al conectar: ", e)
	total = 0
	if insc == 1:
		total = total + float(datainsc[1])
	total = total + (cantidad * float(datamen[1]))
	if request.method == 'POST':
		try:
			conexion = pymysql.connect(host='localhost', user='root', password='database', db='pagossis')
			try:
				with conexion.cursor() as cursor:
					idpagos = []
					if insc == 1:
						consulta = "INSERT INTO pagos(idcod,nombre,carnet,total,fecha,extra,recibo, user) VALUES (%s,%s,%s,%s,%s,%s,%s, %s);"
						cursor.execute(consulta, (datainsc[0], nombre, carnet,datainsc[1], date.today(), 'Ciclo: ' + str(ciclo) ,0, session['idusercaja']))
						conexion.commit()
						consulta = "Select MAX(idpagos) from pagos;"
						cursor.execute(consulta)
						idpago = cursor.fetchone()
						idpago = idpago[0]
						idpagos.append(idpago)
					for i in range(cantidad):
						consulta = "INSERT INTO pagos(idcod,nombre,carnet,total,fecha,extra,recibo, user) VALUES (%s,%s,%s,%s,%s,%s,%s, %s);"
						cursor.execute(consulta, (datamen[0], nombre, carnet, datamen[1], date.today(), 'Mes: ' + meses[i] ,0, session['idusercaja']))
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
		if len(aro) < 1:
			aro = 0
		if len(lente) < 1:
			lente = 0
		return redirect(url_for('confirmacionopt', carnet = carnet, nombre = nombre, aro=aro, lente=lente, exavis=exavis))
	return render_template('optica.html', title="Óptica", logeado=logeado)

@app.route('/confirmacionopt/<carnet>&<nombre>&<aro>&<lente>&<exavis>', methods=['GET', 'POST'])
def confirmacionopt(carnet, nombre, aro, lente, exavis):
	try:
		logeado = session['logeadocaja']
	except:
		logeado = 0
	if logeado == 0:
		return redirect(url_for('login'))
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
					if float(aro) > 0:
						consulta = 'select idcodigos from codigos where cod = "OPTARO"'
						cursor.execute(consulta)
						datos = cursor.fetchall()
						idaro = datos[0][0]
						consulta = "INSERT INTO pagos(idcod,nombre,carnet,total,fecha,extra,recibo, user) VALUES (%s,%s,%s,%s,%s,%s,%s,%s);"
						cursor.execute(consulta, (idaro, nombre, carnet, aro, date.today(), "Aro - Optica",0, session['idusercaja']))
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
		return redirect(url_for('optica'))
	return render_template('confirmacionopt.html', title="Confirmación Óptica", carnet = carnet, nombre = nombre, aro=aro, lente=lente, exavis=exavis, logeado=logeado)

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
	if request.method == "POST":
		try:
			conexion = pymysql.connect(host='localhost', user='root', password='database', db='pagossis')
			try:
				with conexion.cursor() as cursor:
					if rinsc != 0:
						consulta = "INSERT INTO pagos(idcod,nombre,carnet,total,fecha,extra,recibo, user) VALUES (%s,%s,%s,%s,%s,%s,%s,%s);"
						cursor.execute(consulta, (1, nombre, carnet, data[0][1], date.today(), data[0][0],0, session['idusercaja']))
					if rint != 0:
						consulta = "INSERT INTO pagos(idcod,nombre,carnet,total,fecha,extra,recibo, user) VALUES (%s,%s,%s,%s,%s,%s,%s, %s);"
						cursor.execute(consulta, (2, nombre, carnet, data[0][2], date.today(), "Internet " +str(data[0][3]), 0, session['idusercaja']))
					if rrein != 0:
						consulta = "INSERT INTO pagos(idcod,nombre,carnet,total,fecha,extra,recibo, user) VALUES (%s,%s,%s,%s,%s,%s,%s,%s);"
						cursor.execute(consulta, (3, nombre, carnet, 100, date.today(), "Internet Reinscripcion" +str(data[0][3]),0, session['idusercaja']))
					if mesextra != 0:
						consulta = 'select idcodigos from codigos where cod = "MENE"'
						cursor.execute(consulta)
						datos = cursor.fetchall()
						idcodigo = datos[0][0]
						consulta = "INSERT INTO pagos(idcod,nombre,carnet,total,fecha,extra,recibo,user) VALUES (%s,%s,%s,%s,%s,%s,%s, %s);"
						cursor.execute(consulta, (idcodigo, nombre, carnet, mesextra, date.today(), "Mensualidad Extra" +str(data[0][3]),0, session['idusercaja']))
					if exavis != 0:
						consulta = 'select idcodigos from codigos where cod = "EXAVIS"'
						cursor.execute(consulta)
						datos = cursor.fetchall()
						idexamen = datos[0][0]
						consulta = "INSERT INTO pagos(idcod,nombre,carnet,total,fecha,extra,recibo, user) VALUES (%s,%s,%s,%s,%s,%s,%s,%s);"
						cursor.execute(consulta, (idexamen, nombre, carnet, 50, date.today(), "Examen de la Vista",0, session['idusercaja']))
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
		return redirect(url_for('i'))
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
		dataextra = request.form["extra"]
		data = dataextra.split(',')
		extraid = data[0]
		extracod = data[1]
		return redirect(url_for('confirmacionextra', carnet = datacarnet, nombre = datanombre, idp = extraid, cod = extracod))
	return render_template('extra.html', title="Pagos extra", data = data, logeado=logeado)

@app.route('/confirmacionextra/<carnet>&<nombre>&<idp>&<cod>', methods=['GET', 'POST'])
def confirmacionextra(carnet, nombre, idp, cod):
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
	if request.method == "POST":
		try:
			conexion = pymysql.connect(host='localhost', user='root', password='database', db='pagossis')
			try:
				with conexion.cursor() as cursor:
					consulta1 = 'SELECT precio FROM codigos WHERE idcodigos = "' + str(idp) + '"'
					cursor.execute(consulta1)
					precios1 = cursor.fetchall()
					consulta = "INSERT INTO pagos(idcod,nombre,carnet,total,fecha,extra, recibo,user) VALUES (%s,%s,%s,%s,%s,%s,%s,%s);"
					cursor.execute(consulta, (idp, nombre, carnet, precios1[0][0], date.today(), "",0,session['idusercaja']))
				conexion.commit()
			finally:
				conexion.close()
		except (pymysql.err.OperationalError, pymysql.err.InternalError) as e:
			print("Ocurrió un error al conectar: ", e)
		return redirect(url_for('extra'))
	return render_template('confirmacionextra.html', title="Confirmación", carnet = carnet, nombre = nombre, idp = idp, cod = cod, logeado=logeado)

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
	for i in range(25):
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
		return redirect(url_for('confirmacionp', carnet = datacarnet, nombre = datanombre, datames= datames, pid = pid, pcod = pcod, cantidad=cantidad))
	return render_template('practica.html', title="Practica",  carreras=carreras, numeros=numeros, meses=meses, logeado=logeado)

@app.route('/confirmacionp/<carnet>&<nombre>&<datames>&<pid>&<pcod>&<cantidad>', methods=['GET', 'POST'])
def confirmacionp(carnet, nombre, datames, pid, pcod,cantidad):
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
					consulta1 = 'SELECT idcodigos, precio FROM codigos WHERE idcodigos = "' + str(pid) + '"'
					cursor.execute(consulta1)
					precios1 = cursor.fetchall()
					for i in range(cantidad):
						if 'TUEVQ' in pcod:
							consulta = "INSERT INTO pagos(idcod,nombre,carnet,total,fecha,extra,recibo,user) VALUES (%s,%s,%s,%s,%s,%s,%s,%s);"
							cursor.execute(consulta, (precios1[0][0], nombre, carnet, meses[i], date.today(), 'Practica TUEVQ',0,session['idusercaja']))
						else:
							consulta = "INSERT INTO pagos(idcod,nombre,carnet,total,fecha,extra,recibo,user) VALUES (%s,%s,%s,%s,%s,%s,%s,%s);"
							cursor.execute(consulta, (precios1[0][0], nombre, carnet, precios1[0][1], date.today(), meses[i],0,session['idusercaja']))
						conexion.commit()
			finally:
				conexion.close()
		except (pymysql.err.OperationalError, pymysql.err.InternalError) as e:
			print("Ocurrió un error al conectar: ", e)
		return redirect(url_for('p'))
	return render_template('confirmacionp.html', title="Confirmación", carnet = carnet, nombre = nombre, meses = meses, pid = pid, pcod = pcod, cantidad=cantidad, logeado=logeado)

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
				consulta = '''select p.nombre, p.carnet, p.fecha, d.cod, p.extra, p.total from pagos p 
				inner join codigos d on p.idcod = d.idcodigos
				inner join carreras c on d.idcarrera = c.idcarreras
				where d.practica = 1
				order by p.fecha asc, c.codigo desc, p.nombre asc, p.extra asc'''
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
				consulta = '''select p.nombre, p.carnet, p.fecha, c.codigo, p.extra, p.total from pagos p 
				inner join codigos d on p.idcod = d.idcodigos
				inner join carreras c on d.idcarrera = c.idcarreras
				where d.cod LIKE 'M%' and d.cod != 'MENE'
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
					where d.cod LIKE 'M%' and d.cod != 'MENE' and p.fecha >= "'''
					consulta = consulta + str(defecha) + '" and p.fecha <= "' + str(afecha)
					consulta = consulta + '" order by p.fecha asc, c.codigo desc'
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
				consulta = 'select billete1, billete5, billete10, billete20, billete50, billete100, billete200, facturas, vales from efectivo where idefectivo = 1;'
				cursor.execute(consulta)
				efectivo = cursor.fetchone()
				consulta = 'SELECT p.fecha, c.cod, c.concepto, p.total FROM pagos p INNER JOIN codigos c ON p.idcod = c.idcodigos WHERE fecha = "'+str(date.today())+'" and p.recibo = 0 order by c.cod asc, p.nombre asc;'
				cursor.execute(consulta)
			# Con fetchall traemos todas las filas
				data = cursor.fetchall()
				sumtotal = 0
				for i in data:
					sumtotal = sumtotal + i[3]
				sumtotal = round(sumtotal, 2)
				sumas = []
				suma = 0
				cod = ""
				concep = ""
				cont = 1
				for i in data:
					temp = i[1]
					if temp != cod:
						if cod == "":
							suma = i[3]
							cod = i[1]
							concep = i[2]
							cont = 1
						else:
							aux = [cod, concep, suma, cont]
							sumas.append(aux)
							suma = i[3]
							cod = temp
							concep = i[2]
							cont = 1
					else:
						suma = suma + i[3]
						cont = cont + 1
				aux = [cod, concep, suma, cont]
				sumas.append(aux)
				consulta = 'SELECT p.fechadevuelto, c.cod, c.concepto, p.total FROM pagos p INNER JOIN codigos c ON p.idcod = c.idcodigos WHERE fechadevuelto = "'+str(date.today())+'" order by c.cod asc, p.nombre asc;'
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
		try:
			conexion = pymysql.connect(host='localhost', user='root', password='database', db='pagossis')
			try:
				with conexion.cursor() as cursor:
					consulta = "UPDATE efectivo set billete1=%s, billete5=%s, billete10=%s, billete20=%s, billete50=%s, billete100=%s, billete200=%s, facturas=%s, vales=%s where idefectivo = 1;"
					cursor.execute(consulta, (q1, q5, q10, q20, q50, q100, q200, facturas, vales))
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
				consulta = 'SELECT p.nombre, p.carnet, p.fecha, c.concepto, p.extra, p.total, p.idpagos, u.iniciales FROM pagos p INNER JOIN codigos c ON p.idcod = c.idcodigos inner join user u on u.iduser = p.user WHERE fecha = "'+str(date.today())+'" and p.recibo = 0 order by c.cod asc, p.nombre asc;'
				cursor.execute(consulta)
			# Con fetchall traemos todas las filas
				data = cursor.fetchall()
				suma = 0
				for i in data:
					suma = suma + i[5]
				consulta = 'SELECT p.fechadevuelto, c.cod, c.concepto, p.total FROM pagos p INNER JOIN codigos c ON p.idcod = c.idcodigos WHERE fechadevuelto = "'+str(date.today())+'" order by c.cod asc, p.nombre asc;'
				cursor.execute(consulta)
				datadev = cursor.fetchall()
		finally:
			conexion.close()
	except (pymysql.err.OperationalError, pymysql.err.InternalError) as e:
		print("Ocurrió un error al conectar: ", e)
	if data == 1 or data == '1':
		mensaje = "No se pudo eliminar el elemento seleccionado"
	else:
		mensaje = ""
	if request.method == 'POST':
		try:
			conexion = pymysql.connect(host='localhost', user='root', password='database', db='pagossis')
			try:
				with conexion.cursor() as cursor:
					regen = request.form["regen"]
					if regen == '0' or len(regen) < 1:
						for i in data:
							aux = "re"+str(i[6])
							varaux = request.form[aux]
							if len(varaux) > 0:
								consulta = 'UPDATE pagos SET recibo = '+str(varaux)+' WHERE idpagos = '+str(i[6])+';'
								print(consulta)
								cursor.execute(consulta)
					else:
						for i in data:
							consulta = 'UPDATE pagos SET recibo = '+str(regen)+' WHERE idpagos = '+str(i[6])+';'
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
	return render_template('repdiario.html', title="Reporte diario", data = data, suma=suma, logeado=logeado, datadev=datadev, mensaje=mensaje)

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
				consulta = 'SELECT p.nombre, p.carnet, DATE_FORMAT(p.fecha,"%d/%m/%Y"), c.concepto, p.extra, p.total, p.idpagos, p.recibo, u.iniciales FROM pagos p INNER JOIN codigos c ON p.idcod = c.idcodigos inner join user u on u.iduser = p.user WHERE fecha = "'+str(date.today())+'" order by c.cod asc, p.nombre asc;'
				cursor.execute(consulta)
			# Con fetchall traemos todas las filas
				data = cursor.fetchall()
				suma = 0
				for i in data:
					suma = suma + float(i[5])
				consulta = 'SELECT p.nombre, p.carnet, DATE_FORMAT(p.fechadevuelto,"%d/%m/%Y"), c.concepto, p.extra, p.total, p.idpagos, p.recibo, u.iniciales FROM pagos p INNER JOIN codigos c ON p.idcod = c.idcodigos inner join user u on u.iduser = p.user WHERE fechadevuelto = "'+str(date.today())+'" order by c.cod asc, p.nombre asc;'
				cursor.execute(consulta)
				datadev = cursor.fetchall()
				contdev = len(datadev)
				sumadev = 0
				for i in datadev:
					sumadev = sumadev + float(i[5])

		finally:
			conexion.close()
	except (pymysql.err.OperationalError, pymysql.err.InternalError) as e:
		print("Ocurrió un error al conectar: ", e)
	
	rendered = render_template('repdiariopdf.html', title="Reporte diario", data = data, suma=suma, datadev=datadev, sumadev=sumadev, contdev=contdev, d1=d1)
	options = {'enable-local-file-access': None}
	config = pdfkit.configuration(wkhtmltopdf="C:\\Program Files\\wkhtmltopdf\\bin\\wkhtmltopdf.exe")
	pdf = pdfkit.from_string(rendered, False, configuration=config, options=options)
	response = make_response(pdf)
	response.headers['Content-Type'] = 'application/pdf'
	response.headers['Content-Disposition'] = 'inline; filename=reportediario.pdf'
	print(response)
	return response

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
	if request.method == "POST":
		datacarnet = request.form["carnet"]
		datanombre = request.form["nombre"]
		datafechaini = request.form["fechaini"]
		datafechafin = request.form["fechafin"]
		dataconcepto = request.form["concepto"]
		datadescripcion = request.form["descripcion"]
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
					consulta = consulta + ' order by p.fecha desc, c.concepto asc, p.extra asc, p.nombre asc;'
					print(consulta)
					cursor.execute(consulta)
				# Con fetchall traemos todas las filas
					data = cursor.fetchall()
					conteo = len(data)
			finally:
				conexion.close()
		except (pymysql.err.OperationalError, pymysql.err.InternalError) as e:
			print("Ocurrió un error al conectar: ", e)
		return render_template('repgen.html', title="Reporte general", data = data, logeado=logeado, conteo=conteo, datacarnet = datacarnet, datanombre = datanombre, datafechaini = datafechaini, datafechafin = datafechafin, dataconcepto = dataconcepto, datadescripcion = datadescripcion)
	return render_template('repgen.html', title="Reporte general", data = data, logeado=logeado, conteo=conteo, datacarnet = datacarnet, datanombre = datanombre, datafechaini = datafechaini, datafechafin = datafechafin, dataconcepto = dataconcepto, datadescripcion = datadescripcion)

@app.route('/pagos')
def pagos():
	try:
		logeado = session['logeadocaja']
	except:
		logeado = 0
	if logeado == 0:
		return redirect(url_for('login'))
	
	return render_template('pagos.html', title="Pagos", logeado=logeado)

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
	
	rendered = render_template('imprimir.html', title="Reporte diario", datagen = datagen, suma=suma)
	options = {'enable-local-file-access': None, 'page-size': 'A8', 'orientation': 'Portrait', 'margin-left': '0', 'margin-right': '0', 'margin-top': '0', 'margin-bottom': '5', 'encoding': 'utf-8', 'zoom': '0.8'}
	config = pdfkit.configuration(wkhtmltopdf="C:\\Program Files\\wkhtmltopdf\\bin\\wkhtmltopdf.exe")
	pdf = pdfkit.from_string(rendered, False, configuration=config, options=options)
	response = make_response(pdf)
	response.headers['Content-Type'] = 'application/pdf'
	response.headers['Content-Disposition'] = 'inline; filename=reportediario.pdf'
	print(response)
	#webbrowser.open("http://galileoserver:5000/pagos")
	return response

if __name__ == '__main__':
	app.run(host='0.0.0.0', port=5000, threaded=True, debug=True)