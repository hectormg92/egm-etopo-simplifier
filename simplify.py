#############################
###Importación de módulos####
#############################

from math import sin, cos, pi

#Módulo de python con herramientas de iteraciones
import itertools

#Módulo de python de tiempo. Para calcular el tiempo del proceso
import time

#Tiempo de inicio desde dónde cuenta la duración del proceso
start = time.time()

#############################
###Parámetros modificables###
#############################

#Ficheros de entrada
#Fichero EGM2008
egm = open('EGM2008_2_5min_N.dat')
#Fichero ETOPO2
etopo = open('ETOPO2_10min_km.txt')

#Paso de malla de salida (en minutos)
paso_malla_salida = 30

#Factor de exageración de h
f_exa = 100

#Subida del nivel del mar
nivel_mar = 6

#Nombre fichero de salida sup. topográfica
nom_st = 'sup_top_30min_f1_mar6.obj'
#Nombre fichero de salida geoide
nom_ge = 'geoide_30min_f1_mar6.obj'

print 'Proceso iniciado con:'
print '  -Paso de malla de salida: ' + str(paso_malla_salida) + "'"
print '  -Factor de exageración: ' + str(f_exa)
print '  -Subida del nivel del mar: ' + str(nivel_mar) + 'm'

#############################
#########Funciones###########
#############################

#Función para simplificar egm08
def simplify_egm(fitx, paso_salida):

    #Paso de malla del fichero de entrada
    paso_entrada = 2.5

    #Variable que almacena el número de bloques
    itbloq = 360 * 60 / paso_salida

    #Número de lineas que se ha de saltar en longitud para obtener el paso de malla de salida deseado
    step = paso_salida / paso_entrada

    #Número de lineas de cada bloque
    bloq = step**2 * itbloq
    
    #Lista vacia
    egm = []
    #Bucle que dónde se itera según el número de bloques
    for i in range(0,itbloq):

        #Iterador que coge el bloque entero y salta según step
        it = itertools.islice(fitx, 0, bloq, step)

        cont = 0
        #Recorremos el iterador
        for j in it:
            #y comprobamos que el nº de lineas que cogemos es menor a itbloq
            if cont < itbloq:
                #Añadimos a la lista la linea
                egm.append(j)

            #Vamos sumando al contador
            cont += 1
            
    #Devuelve una lista con lat, lon y ondulación dentro de cada elemento de la lista
    return egm

#Función para simplificar etopo2
def simplify_etopo(fitx, paso_salida):
    
    #Paso de malla del fichero de entrada
    paso_entrada = 10
    
    #Variable que almacena el número de bloques
    it_lon = 360 * 60 / paso_salida

    #Paso
    step = paso_salida / paso_entrada

    #Lista vacia
    etop = []
    #Bucle que recorre el fichero de entrada
    for idx,value in enumerate(fitx):
        #Si el número de linea es múltiple del paso...
        if idx%step==0:
            #Contador para cuantos valores de cada linea se cogen
            cont = 0
            #Creamos dos lineas vacias para darle la vuelta (de 0º a 360º de long)
            sal1 = []
            sal2 = []
            #Bucle para recorrer los valores de cada linea
            for idx2, value2 in enumerate(value.split()):
                #Si el valor es múltiple del paso...
                if idx2%step==0:
                    #Si el contador llega al tope se termina este bucle
                    if cont==it_lon: break
                    #Si el contador es menor a la mitad se añada a una lista
                    if cont<it_lon/2:
                        sal2.append(value2)
                    #Si es mayor se añade a la otra
                    elif cont>=it_lon/2:
                        sal1.append(value2)

                    #Se incrementa el contador
                    cont +=1

            #Se añade ya organizado como se ha comentado antes
            etop.append(sal1+sal2)
    #Devuelve una lista con cada elemento siendo otra lista con los valores de H ortométrica de cada latitud
    return etop

#Función de transformación de coordenadas con factor de exageración
#De geodésicas a cartesianas geocéntricas
#Parámetros del GRS80
def geo2car(lat_sex, lon_sex, h_elip, f_exag=1):

    #Transformamos lat y lon de sexagesimal a radianes
    lat = lat_sex * pi / 180
    lon = lon_sex * pi / 180

    #Aplicamos el factor de exageración a la h elipsoidal
    h = h_elip * f_exag

    #Parámetros del elipsoide GRS1980
    a = 6378137.0
    f = 1/298.257223563
    b = a - (a * f)
    e = (a**2-b**2)/(a**2)

    #Radio del primer vertical
    v = a / ((1-e*(sin(lat))**2)**(1/2))

    #Cálculo de coordenadas cartesianas geocéntricas
    X = (v + h) * cos(lat) * cos(lon)
    Y = (v + h) * cos(lat) * sin(lon)
    Z = (((b**2/a**2) * v) + h) * sin(lat)

    #Devuelve una tupla con las coordenadas
    return X,Y,Z


#############################
#####PROGRAMA PRINCIPAL######
#############################

#Realizamos las operaciones de simplificación y las guardamos
egm_simp = simplify_egm(egm,paso_malla_salida)
top_simp = simplify_etopo(etopo,paso_malla_salida)

#Lista vacía para almacenar la H ortométrica
Hort = []
#Recorremos las lineas de top_simp
for lat in top_simp:
    #Para cada linea recorremos los elementos
    for i in lat:
        #Pasamos la altura ortométrica a metros
        H = float(i)*1000

        #La añadimos a la lista vacía
        Hort.append(H)

#Creamos dos listas vacias para la superficie topográfica y para el geoide
coord_st = []
coord_ge = []
#Recorremos el fichero egm_simp
for idx, lin in enumerate(egm_simp):
    #Extraemos la ondulación
    N_ond  = float(lin.split()[2])
    #Calculamos la h elipsoidal
    h_elip = N_ond + Hort[idx]

    #Extraemos la latitud y longitud
    lat = float(lin.split()[0])
    lon = float(lin.split()[1])

    #Realizamos la transformación de coordenadas con h_elip y N_ond para obtener las diferentes superficies
    #Añadimos a la lista correspondiente
    coord_st.append(geo2car(lat,lon,h_elip,f_exa))
    coord_ge.append(geo2car(lat,lon,N_ond + nivel_mar,f_exa))

    
#Abrimos el fichero de salida en modo de escritura de la superficie topográfica
with open(nom_st,'wt') as fitx:
    #Recorremos la lista
    for i in coord_st:
        #Escribimos en el fichero con formato de 6 decimales y dividido entre 1 millón (según unidades utilizadas en Blender)
        fitx.write('v ' + str("{0:.6f}".format(i[0]/1000000)) + ' ' +  str("{0:.6f}".format(i[1]/1000000)) + ' ' + str("{0:.6f}".format(i[2]/1000000)) + '\n')

#Abrimos el fichero de salida en modo de escritura de la superficie del geoide
with open(nom_ge,'wt') as fitx:
    #Recorremos la lista
    for i in coord_ge:
        #Escribimos en el fichero con formato de 6 decimales y dividido entre 1 millón (según unidades utilizadas en Blender)
        fitx.write('v ' + str("{0:.6f}".format(i[0]/1000000)) + ' ' +  str("{0:.6f}".format(i[1]/1000000)) + ' ' + str("{0:.6f}".format(i[2]/1000000)) + '\n')


#Tiempo de fin del proceso
stop = time.time()

print 'El proceso ha concluido satisfactoriamente en: ' + str(stop - start) + 's'

