from flask import Flask, render_template, request, url_for, redirect, make_response
import pymysql
from datetime import date
import pdfkit as pdfkit

app = Flask(__name__)

@app.route('/')
@app.route('/home')
def home():
    return render_template('inicio.html', title="Inicio")

@app.route('/optica', methods=['GET', 'POST'])
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
		if len(aro) < 1:
			aro = 0
		if len(lente) < 1:
			lente = 0
		return redirect(url_for('confirmacionopt', carnet = carnet, nombre = nombre, aro=aro, lente=lente, exavis=exavis))
	return render_template('optica.html', title="Óptica")

@app.route('/confirmacionopt/<carnet>&<nombre>&<aro>&<lente>&<exavis>', methods=['GET', 'POST'])
def confirmacionopt(carnet, nombre, aro, lente, exavis):
	if request.method == "POST":
		try:
			conexion = pymysql.connect(host='localhost', user='root', password='database', db='pagossis')
			try:
				with conexion.cursor() as cursor:
					if exavis != 0:
						consulta = 'select idcodigos from codigos where cod = "EXAVIS"'
						cursor.execute(consulta)
						datos = cursor.fetchall()
						idexamen = datos[0][0]
						consulta = "INSERT INTO pagos(idcod,nombre,carnet,total,fecha,extra,recibo) VALUES (%s,%s,%s,%s,%s,%s,%s);"
						cursor.execute(consulta, (idexamen, nombre, carnet, 50, date.today(), "Examen de la Vista",0))
					if float(aro) > 0:
						consulta = 'select idcodigos from codigos where cod = "OPTARO"'
						cursor.execute(consulta)
						datos = cursor.fetchall()
						idaro = datos[0][0]
						consulta = "INSERT INTO pagos(idcod,nombre,carnet,total,fecha,extra,recibo) VALUES (%s,%s,%s,%s,%s,%s,%s);"
						cursor.execute(consulta, (idaro, nombre, carnet, aro, date.today(), "Aro - Optica",0))
					if float(lente) > 0:
						consulta = 'select idcodigos from codigos where cod = "OPTLEN"'
						cursor.execute(consulta)
						datos = cursor.fetchall()
						idlente = datos[0][0]
						consulta = "INSERT INTO pagos(idcod,nombre,carnet,total,fecha,extra,recibo) VALUES (%s,%s,%s,%s,%s,%s,%s);"
						cursor.execute(consulta, (idlente, nombre, carnet, lente, date.today(), "Lente - Optica",0))
				conexion.commit()
			finally:
				conexion.close()
		except (pymysql.err.OperationalError, pymysql.err.InternalError) as e:
			print("Ocurrió un error al conectar: ", e)
		return redirect(url_for('optica'))
	return render_template('confirmacionopt.html', title="Confirmación Óptica", carnet = carnet, nombre = nombre, aro=aro, lente=lente, exavis=exavis)

@app.route('/i', methods=['GET', 'POST'])
def i():
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
		return redirect(url_for('confirmacioni', carrera = datacarrera, carnet = datacarnet, nombre = datanombre, rinsc=rinsc, rint=rint, rrein=rrein, mesextra=mesextra, exavis=exavis))
	return render_template('inscripciones.html', title="Inscripciones", carreras=carreras)

@app.route('/confirmacioni/<carrera>&<carnet>&<nombre>&<rinsc>&<rint>&<rrein>&<mesextra>&<exavis>', methods=['GET', 'POST'])
def confirmacioni(carrera, carnet, nombre, rinsc, rint, rrein, mesextra, exavis):
	carrera = str(carrera)
	carnet = int(carnet)
	nombre = str(nombre)
	rinsc = int(rinsc)
	rint = int(rint)
	rrein = int(rrein)
	exavis = int(exavis)
	mesextra = int(mesextra)
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
						consulta = "INSERT INTO pagos(idcod,nombre,carnet,total,fecha,extra,recibo) VALUES (%s,%s,%s,%s,%s,%s,%s);"
						cursor.execute(consulta, (1, nombre, carnet, data[0][1], date.today(), data[0][0],0))
					if rint != 0:
						consulta = "INSERT INTO pagos(idcod,nombre,carnet,total,fecha,extra,recibo) VALUES (%s,%s,%s,%s,%s,%s,%s);"
						cursor.execute(consulta, (2, nombre, carnet, data[0][2], date.today(), "Internet " +str(data[0][3]), 0))
					if rrein != 0:
						consulta = "INSERT INTO pagos(idcod,nombre,carnet,total,fecha,extra,recibo) VALUES (%s,%s,%s,%s,%s,%s,%s);"
						cursor.execute(consulta, (3, nombre, carnet, 100, date.today(), "Internet Reinscripcion" +str(data[0][3]),0))
					if mesextra != 0:
						consulta = 'select idcodigos from codigos where cod = "MENE"'
						cursor.execute(consulta)
						datos = cursor.fetchall()
						idcodigo = datos[0][0]
						consulta = "INSERT INTO pagos(idcod,nombre,carnet,total,fecha,extra,recibo) VALUES (%s,%s,%s,%s,%s,%s,%s);"
						cursor.execute(consulta, (idcodigo, nombre, carnet, mesextra, date.today(), "Mensualidad Extra" +str(data[0][3]),0))
					if exavis != 0:
						consulta = 'select idcodigos from codigos where cod = "EXAVIS"'
						cursor.execute(consulta)
						datos = cursor.fetchall()
						idexamen = datos[0][0]
						consulta = "INSERT INTO pagos(idcod,nombre,carnet,total,fecha,extra,recibo) VALUES (%s,%s,%s,%s,%s,%s,%s);"
						cursor.execute(consulta, (idexamen, nombre, carnet, 50, date.today(), "Examen de la Vista",0))
				conexion.commit()
			finally:
				conexion.close()
		except (pymysql.err.OperationalError, pymysql.err.InternalError) as e:
			print("Ocurrió un error al conectar: ", e)
		return redirect(url_for('i'))
	return render_template('confirmacioni.html', title="Confirmación", carrera = carrera, carnet = carnet, nombre = nombre, data=data, rinsc=rinsc, rint=rint, rrein=rrein, mesextra=mesextra)

@app.route('/repi', methods=['GET', 'POST'])
def repi():
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
	return render_template('repi.html', title="Reporte inscripciones", data = data, suma=suma, carreras=carreras)

@app.route('/ini', methods=['GET', 'POST'])
def ini():
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
	return render_template('internetins.html', title="Internet Inscripciones",  carreras=carreras)

@app.route('/confirmacionini/<carrera>&<carnet>&<nombre>', methods=['GET', 'POST'])
def confirmacionini(carrera, carnet, nombre):
	carrera = str(carrera)
	carnet = int(carnet)
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
					consulta = "INSERT INTO pagos(idcod,nombre,carnet,total,fecha,extra,recibo) VALUES (%s,%s,%s,%s,%s,%s,%s);"
					cursor.execute(consulta, (precios1[0][0], nombre, carnet, precios1[0][1], date.today(), "",0))
				conexion.commit()
			finally:
				conexion.close()
		except (pymysql.err.OperationalError, pymysql.err.InternalError) as e:
			print("Ocurrió un error al conectar: ", e)
		return redirect(url_for('ini'))
	return render_template('confirmacionini.html', title="Confirmación", carrera = carrera, carnet = carnet, nombre = nombre)

@app.route('/repini', methods=['GET', 'POST'])
def repini():
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

	return render_template('repini.html', title="Reporte internet", data = data, suma=suma, carreras=carreras)

@app.route('/ir', methods=['GET', 'POST'])
def ir():
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
	return render_template('internetreins.html', title="Internet Reinscripciones",  carreras=carreras)

@app.route('/confirmacionir/<carrera>&<carnet>&<nombre>', methods=['GET', 'POST'])
def confirmacionir(carrera, carnet, nombre):
	carrera = str(carrera)
	carnet = int(carnet)
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
					consulta = "INSERT INTO pagos(idcod,nombre,carnet,total,fecha,extra, recibo) VALUES (%s,%s,%s,%s,%s,%s,%s);"
					cursor.execute(consulta, (precios1[0][0], nombre, carnet, precios1[0][1], date.today(), "",0))
				conexion.commit()
			finally:
				conexion.close()
		except (pymysql.err.OperationalError, pymysql.err.InternalError) as e:
			print("Ocurrió un error al conectar: ", e)
		return redirect(url_for('ir'))
	return render_template('confirmacionini.html', title="Confirmación", carrera = carrera, carnet = carnet, nombre = nombre)

@app.route('/repir', methods=['GET', 'POST'])
def repir():
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

	return render_template('repir.html', title="Reporte internet reingreso", data = data, suma=suma, carreras=carreras)

@app.route('/extra', methods=['GET', 'POST'])
def extra():
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
	return render_template('extra.html', title="Pagos extra", data = data)

@app.route('/confirmacionextra/<carnet>&<nombre>&<idp>&<cod>', methods=['GET', 'POST'])
def confirmacionextra(carnet, nombre, idp, cod):
	idp = int(idp)
	carnet = int(carnet)
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
					consulta = "INSERT INTO pagos(idcod,nombre,carnet,total,fecha,extra, recibo) VALUES (%s,%s,%s,%s,%s,%s,%s);"
					cursor.execute(consulta, (idp, nombre, carnet, precios1[0][0], date.today(), "",0))
				conexion.commit()
			finally:
				conexion.close()
		except (pymysql.err.OperationalError, pymysql.err.InternalError) as e:
			print("Ocurrió un error al conectar: ", e)
		return redirect(url_for('extra'))
	return render_template('confirmacionextra.html', title="Confirmación", carnet = carnet, nombre = nombre, idp = idp, cod = cod)

@app.route('/repextra', methods=['GET', 'POST'])
def repextra():
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

	return render_template('repextra.html', title="Reporte Pagos Extra", data = data, suma=suma)

@app.route('/u', methods=['GET', 'POST'])
def u():
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
	return render_template('uniformes.html', title="Uniformes",  carreras=carreras)

@app.route('/confirmacionu/<uid>&<carnet>&<nombre>&<total>&<talla>&<ucod>', methods=['GET', 'POST'])
def confirmacionu(uid, carnet, nombre, total, talla, ucod):
	uid = int(uid)
	carnet = int(carnet)
	nombre = str(nombre)
	total = float(total)
	talla = str(talla)
	ucod = str(ucod)
	if request.method == "POST":
		try:
			conexion = pymysql.connect(host='localhost', user='root', password='database', db='pagossis')
			try:
				with conexion.cursor() as cursor:
					consulta = "INSERT INTO pagos(idcod,nombre,carnet,total,fecha,extra,recibo) VALUES (%s,%s,%s,%s,%s,%s,%s);"
					cursor.execute(consulta, (uid, nombre, carnet, total, date.today(), "Talla: "+talla,0))
				conexion.commit()
			finally:
				conexion.close()
		except (pymysql.err.OperationalError, pymysql.err.InternalError) as e:
			print("Ocurrió un error al conectar: ", e)
		return redirect(url_for('u'))
	return render_template('confirmacionu.html', title="Confirmación", uid = uid, carnet = carnet, nombre = nombre, total = total, talla= talla, ucod = ucod)

@app.route('/repu', methods=['GET', 'POST'])
def repu():
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

	return render_template('repu.html', title="Reporte Uniformes", data = data, suma=suma, carreras=carreras)

@app.route('/p', methods=['GET', 'POST'])
def p():
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
	return render_template('practica.html', title="Practica",  carreras=carreras, numeros=numeros, meses=meses)

@app.route('/confirmacionp/<carnet>&<nombre>&<datames>&<pid>&<pcod>&<cantidad>', methods=['GET', 'POST'])
def confirmacionp(carnet, nombre, datames, pid, pcod,cantidad):
	carnet = int(carnet)
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
				meses[i] = 'Módulo ' + str(meses[i].split("'")[1])
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
					print(precios1[0])
					for i in range(cantidad):
						if 'TUEVQ' in pcod:
							consulta = "INSERT INTO pagos(idcod,nombre,carnet,total,fecha,extra,recibo) VALUES (%s,%s,%s,%s,%s,%s,%s);"
							cursor.execute(consulta, (precios1[0][0], nombre, carnet, meses[i], date.today(), 'Practica TUEVQ',0))
						else:
							consulta = "INSERT INTO pagos(idcod,nombre,carnet,total,fecha,extra,recibo) VALUES (%s,%s,%s,%s,%s,%s,%s);"
							cursor.execute(consulta, (precios1[0][0], nombre, carnet, precios1[0][1], date.today(), meses[i],0))
				conexion.commit()
			finally:
				conexion.close()
		except (pymysql.err.OperationalError, pymysql.err.InternalError) as e:
			print("Ocurrió un error al conectar: ", e)
		return redirect(url_for('p'))
	return render_template('confirmacionp.html', title="Confirmación", carnet = carnet, nombre = nombre, meses = meses, pid = pid, pcod = pcod, cantidad=cantidad)

@app.route('/repp', methods=['GET', 'POST'])
def repp():
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
	return render_template('repp.html', title="Reporte Prácticas", data = data, suma=suma, carreras=carreras)

@app.route('/mextra', methods=['GET', 'POST'])
def mextra():
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
	return render_template('mextra.html', title="Mes extra", carreras=carreras)

@app.route('/confirmacionme/<total>&<carnet>&<nombre>&<carrera>', methods=['GET', 'POST'])
def confirmacionme(total, carnet, nombre, carrera):
	total = float(total)
	carnet = int(carnet)
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
					consulta = "INSERT INTO pagos(idcod,nombre,carnet,total,fecha,extra, recibo) VALUES (%s,%s,%s,%s,%s,%s,%s);"
					cursor.execute(consulta, (precios1[0][0], nombre, carnet, total, date.today(), carrera, 0))
				conexion.commit()
			finally:
				conexion.close()
		except (pymysql.err.OperationalError, pymysql.err.InternalError) as e:
			print("Ocurrió un error al conectar: ", e)
		return redirect(url_for('mextra'))
	return render_template('confirmacionme.html', title="Confirmación", total = total, carnet = carnet, nombre = nombre, carrera = carrera)

@app.route('/repme', methods=['GET', 'POST'])
def repme():
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

	return render_template('repme.html', title="Reporte Meses Extra", data = data, suma=suma, carreras=carreras)

@app.route('/parqueo', methods=['GET', 'POST'])
def parqueo():
	if request.method == 'POST':
		datacantidad = request.form["cantidad"]
		return redirect(url_for('confirmacionparqueo', cantidad = datacantidad))
	return render_template('parqueo.html', title="Parqueo")

@app.route('/confirmacionparqueo/<cantidad>', methods=['GET', 'POST'])
def confirmacionparqueo(cantidad):
	cantidad = int(cantidad)
	total = cantidad * 10
	if request.method == "POST":
		try:
			conexion = pymysql.connect(host='localhost', user='root', password='database', db='pagossis')
			try:
				with conexion.cursor() as cursor:
					consulta = "INSERT INTO pagos(idcod,nombre,carnet,total,fecha,extra, recibo) VALUES (%s,%s,%s,%s,%s,%s,%s);"
					cursor.execute(consulta, (65, 'parqueo', 0, total, date.today(), "Cantidad parqueo: " +str(cantidad), 0))
				conexion.commit()
			finally:
				conexion.close()
		except (pymysql.err.OperationalError, pymysql.err.InternalError) as e:
			print("Ocurrió un error al conectar: ", e)
		return redirect(url_for('parqueo'))
	return render_template('confirmacionparqueo.html', title="Confirmación", cantidad = cantidad, total = total)

@app.route('/repparq', methods=['GET', 'POST'])
def repparq():
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

	return render_template('repparq.html', title="Reporte Parqueo", data = data, suma=suma)

@app.route('/m', methods=['GET', 'POST'])
def m():
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
	return render_template('manuales.html', title="Manuales",  carreras=carreras)

@app.route('/confirmacionm/<carnet>&<nombre>&<curso>&<mid>&<mcod>', methods=['GET', 'POST'])
def confirmacionm(carnet, nombre, curso, mid, mcod):
	carnet = int(carnet)
	nombre = str(nombre)
	mid = str(mid)
	mcod = str(mcod)
	curso = str(curso)
	cursos=curso.split(',')
	cantidad = len(cursos)
	for i in range(cantidad):
		cursos[i] = str(cursos[i].split("'")[1])
	if request.method == "POST":
		try:
			conexion = pymysql.connect(host='localhost', user='root', password='database', db='pagossis')
			try:
				with conexion.cursor() as cursor:
					consulta1 = 'SELECT idcodigos, precio FROM codigos WHERE idcodigos = "' + mid + '"'
					cursor.execute(consulta1)
					precios1 = cursor.fetchall()
					for i in range(cantidad):
						consulta = "INSERT INTO pagos(idcod,nombre,carnet,total,fecha,extra, recibo) VALUES (%s,%s,%s,%s,%s,%s,%s);"
						cursor.execute(consulta, (precios1[0][0], nombre, carnet, precios1[0][1], date.today(), "Curso: "+cursos[i], 0))
				conexion.commit()
			finally:
				conexion.close()
		except (pymysql.err.OperationalError, pymysql.err.InternalError) as e:
			print("Ocurrió un error al conectar: ", e)
		return redirect(url_for('m'))
	return render_template('confirmacionm.html', title="Confirmación", carnet = carnet, nombre = nombre, cursos = cursos, mid = mid, mcod = mcod, cantidad=cantidad)

@app.route('/repm', methods=['GET', 'POST'])
def repm():
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
	return render_template('repm.html', title="Reporte Manuales", data = data, suma=suma, carreras=carreras)

@app.route('/pag', methods=['GET', 'POST'])
def pag():
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
	if request.method == 'POST':
		datacarnet = request.form["carnet"]
		datanombre = request.form["nombre"]
		datatotal = request.form["total"]
		datadescripcion = request.form["descripcion"]
		datacarrera = request.form["carrera"]
		if len(datadescripcion) < 1:
			datadescripcion = 0
		if len(datatotal) < 1:
			datatotal = 0
		data = datacarrera.split(',')
		pid = data[0]
		pcod = data[1]
		ptotal = data[2]
		return redirect(url_for('confirmacionpag', carnet = datacarnet, nombre = datanombre, total = datatotal, descripcion= datadescripcion, pid = pid, pcod = pcod, ptotal = ptotal))
	return render_template('pag.html', title="Pagos", carreras = carreras)

@app.route('/confirmacionpag/<carnet>&<nombre>&<total>&<descripcion>&<pid>&<pcod>&<ptotal>', methods=['GET', 'POST'])
def confirmacionpag(carnet, nombre, total, descripcion, pid, pcod, ptotal):
	carnet = int(carnet)
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
			conexion = pymysql.connect(host='localhost', user='root', password='database', db='pagossis')
			try:
				with conexion.cursor() as cursor:
					consulta = "INSERT INTO pagos(idcod,nombre,carnet,total,fecha,extra, recibo) VALUES (%s,%s,%s,%s,%s,%s,%s);"
					cursor.execute(consulta, (pid, nombre, carnet, total, date.today(), descripcion, 0))
				conexion.commit()
			finally:
				conexion.close()
		except (pymysql.err.OperationalError, pymysql.err.InternalError) as e:
			print("Ocurrió un error al conectar: ", e)
		return redirect(url_for('pag'))
	return render_template('confirmacionpag.html', title="Confirmación", carnet = carnet, nombre = nombre, total=total, descripcion=descripcion, pid = pid, pcod = pcod,ptotal = ptotal)

@app.route('/reppag', methods=['GET', 'POST'])
def reppag():
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

	return render_template('reppag.html', title="Reporte Pagos", data = data, suma=suma)

@app.route('/grad', methods=['GET', 'POST'])
def grad():
	if request.method == 'POST':
		datacarnet = request.form["carnet"]
		datanombre = request.form["nombre"]
		datatipo = request.form["tipo"]
		return redirect(url_for('confirmaciongrad', tipo = datatipo, carnet = datacarnet, nombre = datanombre))
	return render_template('graduacion.html', title="Graduación")

@app.route('/confirmaciongrad/<tipo>&<carnet>&<nombre>', methods=['GET', 'POST'])
def confirmaciongrad(tipo, carnet, nombre):
	tipo = int(tipo)
	carnet = int(carnet)
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
					consulta = "INSERT INTO pagos(idcod,nombre,carnet,total,fecha,extra, recibo) VALUES (%s,%s,%s,%s,%s,%s,%s);"
					cursor.execute(consulta, (precios1[0][0], nombre, carnet, precios1[0][1], date.today(), "",0))
				conexion.commit()
			finally:
				conexion.close()
		except (pymysql.err.OperationalError, pymysql.err.InternalError) as e:
			print("Ocurrió un error al conectar: ", e)
		return redirect(url_for('grad'))
	return render_template('confirmaciongrad.html', title="Confirmación", nombre = nombre, carnet = carnet, tipo = tipo)

@app.route('/repgrad', methods=['GET', 'POST'])
def repgrad():
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

	return render_template('repgrad.html', title="Reporte Graduación", data = data, suma=suma)

@app.route('/reportes')
def reportes():
	try:
		conexion = pymysql.connect(host='localhost', user='root', password='database', db='pagossis')
		try:
			with conexion.cursor() as cursor:
				consulta = 'SELECT p.fecha, c.cod, c.concepto, p.total FROM pagos p INNER JOIN codigos c ON p.idcod = c.idcodigos WHERE fecha = "'+str(date.today())+'" and p.recibo = 0 order by c.cod asc, p.nombre asc;'
				cursor.execute(consulta)
			# Con fetchall traemos todas las filas
				data = cursor.fetchall()
				sumtotal = 0
				for i in data:
					sumtotal = sumtotal + i[3]
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

				
		finally:
			conexion.close()
	except (pymysql.err.OperationalError, pymysql.err.InternalError) as e:
		print("Ocurrió un error al conectar: ", e)
	return render_template('reportes.html', title="Reportes", sumas = sumas, sumtotal=sumtotal)

@app.route('/repdiario', methods=['GET', 'POST'])
def repdiario():
	try:
		conexion = pymysql.connect(host='localhost', user='root', password='database', db='pagossis')
		try:
			with conexion.cursor() as cursor:
				consulta = 'SELECT p.nombre, p.carnet, p.fecha, c.concepto, p.extra, p.total, p.idpagos FROM pagos p INNER JOIN codigos c ON p.idcod = c.idcodigos WHERE fecha = "'+str(date.today())+'" and p.recibo = 0 order by c.cod asc, p.nombre asc;'
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
		try:
			conexion = pymysql.connect(host='localhost', user='root', password='database', db='pagossis')
			try:
				with conexion.cursor() as cursor:
					regen = request.form["regen"]
					if regen == '0':
						for i in data:
							aux = "re"+str(i[6])
							varaux = request.form[aux]
							consulta = 'UPDATE pagos SET recibo = '+str(varaux)+' WHERE idpagos = '+str(i[6])+';'
							cursor.execute(consulta)
					else:
						for i in data:
							consulta = 'UPDATE pagos SET recibo = '+str(regen)+' WHERE idpagos = '+str(i[6])+';'
							cursor.execute(consulta)
				conexion.commit()
			finally:
				conexion.close()
		except (pymysql.err.OperationalError, pymysql.err.InternalError) as e:
			print("Ocurrió un error al conectar: ", e)
		return redirect(url_for('repdiario'))
	return render_template('repdiario.html', title="Reporte diario", data = data, suma=suma)

@app.route('/repdiariopdf', methods=['GET', 'POST'])
def repdiariopdf():
	try:
		conexion = pymysql.connect(host='localhost', user='root', password='database', db='pagossis')
		try:
			with conexion.cursor() as cursor:
				consulta = 'SELECT p.nombre, p.carnet, DATE_FORMAT(p.fecha,"%d/%m/%Y"), c.concepto, p.extra, p.total, p.idpagos, p.recibo FROM pagos p INNER JOIN codigos c ON p.idcod = c.idcodigos WHERE fecha = "'+str(date.today())+'" order by c.cod asc, p.nombre asc;'
				cursor.execute(consulta)
			# Con fetchall traemos todas las filas
				data = cursor.fetchall()
				suma = 0
				for i in data:
					suma = suma + float(i[5])
		finally:
			conexion.close()
	except (pymysql.err.OperationalError, pymysql.err.InternalError) as e:
		print("Ocurrió un error al conectar: ", e)
	
	rendered = render_template('repdiariopdf.html', title="Reporte diario", data = data, suma=suma)
	options = {'enable-local-file-access': None}
	config = pdfkit.configuration(wkhtmltopdf="C:\\Program Files\\wkhtmltopdf\\bin\\wkhtmltopdf.exe")
	pdf = pdfkit.from_string(rendered, False, configuration=config, options=options)
	response = make_response(pdf)
	response.headers['Content-Type'] = 'application/pdf'
	response.headers['Content-Disposition'] = 'inline; filename=reportediario.pdf'
	print(response)
	return response

@app.route('/repgen')
def repgen():
	try:
		conexion = pymysql.connect(host='localhost', user='root', password='database', db='pagossis')
		try:
			with conexion.cursor() as cursor:
				consulta = 'SELECT p.nombre, p.carnet, p.fecha, c.concepto, p.extra, p.recibo, p.total FROM pagos p INNER JOIN codigos c ON p.idcod = c.idcodigos order by p.fecha desc, c.concepto asc, p.extra asc, p.nombre asc;'
				cursor.execute(consulta)
			# Con fetchall traemos todas las filas
				data = cursor.fetchall()
		finally:
			conexion.close()
	except (pymysql.err.OperationalError, pymysql.err.InternalError) as e:
		print("Ocurrió un error al conectar: ", e)

	return render_template('repgen.html', title="Reporte general", data = data)

@app.route('/pagos')
def pagos():
    return render_template('pagos.html', title="Pagos")

if __name__ == '__main__':
	app.run(host='0.0.0.0', port=5000, threaded=True, debug=True)