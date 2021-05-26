import smbus
import RPi.GPIO as IO
import time
import threading
import pandas as pd
import numpy as np
import paho.mqtt.client as paho
import os
import json
from datetime import datetime
import math
import connect2
import python_mysql_dbconfig as db

# Token del dispositivo y hostname usado para conexión con Thingsboard
ACCESS_TOKEN='dQ0s7zKo8KMn2Fi5Zpiy'
broker="demo.thingsboard.io"
port=1883

bus = smbus.SMBus(1) 	 
Device_Address1 = 0x68
Device_Address2 = 0x69


idsession=8

contador=0
now=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
# Registros de MPU6050 y las direcciones asociadas a cada uno.
powerManagementRegister = 0x6B
sampleRateDividerRegister = 0x19
configurationRegister = 0x1A
gyroscopeConfigutarionRegister = 0x1B
integerEnableRegister = 0x38
accelerometerXOutRegister = 0x3B
accelerometerYOutRegister = 0x3D
accelerometerZOutRegister = 0x3F
gyroscopeXOutRegister = 0x43
gyroscopeYOutRegister = 0x45
gyroscopeZOutRegister = 0x47

IO.setmode(IO.BOARD)
IO.setup(12, IO.IN)  # SENSOR INFRARROJO 1
IO.setup(16, IO.IN)  # SENSOR INFRARROJO 2
IO.setup(7, IO.OUT)  # LED VERDE
IO.setup(15, IO.OUT) # LED ROJA
IO.setup(18,IO.OUT)  # BUZZER

# Estructura de datos de soporte para guardado de datos, previo a envio a Excel.
gxValuesAcc1 = []
gyValuesAcc1 = []
gzValuesAcc1 = []
gxValuesAcc2 = []
gyValuesAcc2 = []
gzValuesAcc2 = []

axValuesAcc1 = []
ayValuesAcc1 = []
aZValuesAcc1 = []
aXValuesAcc2 = []
ayValuesAcc2 = []
azValuesAcc2 = []


# Funcion que establece la conexion con Thingsboard y crea un objeto cliente.
def on_publish(client,userdata,result):
    print("data published to thingsboard \n")
    pass
client1= paho.Client("control1")
client1.on_publish = on_publish
client1.username_pw_set(ACCESS_TOKEN)
client1.connect(broker,port,keepalive=60)


# Funcion que realiza la escritura en los registros de ambos acelerometros
def MPU_Init():
  bus.write_byte_data(Device_Address1, sampleRateDividerRegister, 7)
  bus.write_byte_data(Device_Address1, powerManagementRegister, 1)
  bus.write_byte_data(Device_Address1, configurationRegister, 0)
  bus.write_byte_data(Device_Address1, gyroscopeConfigutarionRegister, 24)
  bus.write_byte_data(Device_Address1, integerEnableRegister, 1)

  bus.write_byte_data(Device_Address2, sampleRateDividerRegister, 7)
  bus.write_byte_data(Device_Address2, powerManagementRegister, 1)
  bus.write_byte_data(Device_Address2, configurationRegister, 0)
  bus.write_byte_data(Device_Address2, gyroscopeConfigutarionRegister, 24)
  bus.write_byte_data(Device_Address2, integerEnableRegister, 1)

# Funcion que realiza la lectura de los datos en bruto de los acelerometros
def readRawData(fd1, addr):
    high = bus.read_byte_data(fd1, addr)
    low = bus.read_byte_data(fd1, addr+1)
    value = ((high << 8) | low)
    if(value > 32768):
        value = value - 65536
    return value

def readRawData2(fd2, addr):
    high = bus.read_byte_data(fd2, addr)
    low = bus.read_byte_data(fd2, addr+1) 
    value = ((high << 8) | low)
    if(value > 32768):
        value = value - 65536
    return value

# Funciones necesarios para calcular la inclinacion del eje x e y.
def dist(a,b):
    return math.sqrt((a*a)+(b*b))
 
def get_x_rotation(x,y,z):
    radians = math.atan(x / dist(y,z))
    return math.degrees(radians)
 
def get_y_rotation(x,y,z):
    radians = math.atan(y / dist(x,z))
    return math.degrees(radians)

# Funcion que establece un hilo concurrente con un contador de tiempo.
def threadDelayFunction():
    global isTimeLimit
    isTimeLimit = False
    time.sleep(20)
    isTimeLimit = True

# Funcion que inserta en la base de datos una nueva sesion de ejercicio
def insertExerciseSession(idExerciseSession,idUser,idSessionType,date):
    query = "INSERT INTO SesionEjercicio(idSesionEjercicio,idUsuario,idTipoSesion,fecha)" \
            "VALUES(%s,%s,%s,%s)"
    
    args = (idExerciseSession,idUser,idSessionType,date)

    try:
        db_config = db.read_db_config()
        conn = connect2.MySQLConnection(**db_config)
        cursor = conn.cursor()
        cursor.execute(query,args)
        conn.commit()
    
    except Error as error:
        print(error)

    finally:
        cursor.close()
        conn.close()

# Funcion que inserta en la base de datos una nueva ejercicio de muñeca     
def insertDataWrist(idExerciseSession,data1,data2):
    query = "INSERT INTO Muneca(idSesionEjercicio,giroscopio1Z,giroscopio2X)VALUES(%s,%s,%s)"
    
    args = (idExerciseSession,data1,data2)

    try:
        db_config = db.read_db_config()
        conn = connect2.MySQLConnection(**db_config)
        cursor = conn.cursor()
        cursor.execute(query, args)
        conn.commit()
    
    except Error as error:
        print(error)

    finally:
        cursor.close()
        conn.close()    
    
x = threading.Thread(target=threadDelayFunction) 
x.start()                
time.sleep(1)
print (" Empieza ejercicio")
MPU_Init()

connect2.connect()
insertExerciseSession(idsession,1,1,now)
print ("Leyendo datos de los sensores...")

while(isTimeLimit == False):       

    if(IO.input(12) == True and IO.input(16) == True):
       IO.output(7, False)
       IO.output(15, True)
       Infrarrojo=0
       
    if(IO.input(12) == False or IO.input(16) == False):
       IO.output(7, True)
       IO.output(15, False)
       Infrarrojo=1

    acc_x = readRawData(Device_Address1, accelerometerXOutRegister)
    acc_y = readRawData(Device_Address1, accelerometerYOutRegister)
    acc_z = readRawData(Device_Address1, accelerometerZOutRegister)
    
    gyro_x = readRawData(Device_Address1, gyroscopeXOutRegister)
    gyro_y = readRawData(Device_Address1, gyroscopeYOutRegister)
    gyro_z = readRawData(Device_Address1, gyroscopeZOutRegister)

    acc_x_2 = readRawData2(Device_Address2, accelerometerXOutRegister)
    acc_y_2 = readRawData2(Device_Address2, accelerometerYOutRegister)
    acc_z_2 = readRawData2(Device_Address2,accelerometerZOutRegister) 
    
    gyro_x_2 = readRawData2(Device_Address2, gyroscopeXOutRegister)
    gyro_y_2 = readRawData2(Device_Address2, gyroscopeYOutRegister)
    gyro_z_2 = readRawData2(Device_Address2, gyroscopeZOutRegister)
	
    Ax = acc_x/16384.0
    Ay = acc_y/16384.0
    Az = acc_z/16384.0
    Ax2 = acc_x_2/16384.0
    Ay2 = acc_y_2/16384.0
    Az2 = acc_z_2/16384.0
	
    Gx = gyro_x/131.0
    Gy = gyro_y/131.0
    Gz = gyro_z/131.0
    Gx2 = gyro_x_2/131.0
    Gy2 = gyro_y_2/131.0
    Gz2 = gyro_z_2/131.0
    
    gxValuesAcc1.append(Gx)
    gyValuesAcc1.append(Gy)
    gzValuesAcc1.append(Gz)
    gxValuesAcc2.append(Gx2)
    gyValuesAcc2.append(Gy2)
    gzValuesAcc2.append(Gy2)

    axValuesAcc1.append(Ax)
    ayValuesAcc1.append(Ay)
    aZValuesAcc1.append(Az)
    aXValuesAcc2.append(Ax2)
    ayValuesAcc2.append(Ay2)
    azValuesAcc2.append(Az2)
    
    insertDataWrist(idsession,Gz,Gx2)
   
    payload="{"
    payload+="\"X\": %s,"%Ax;
    payload+="\"Y\":%s,"%Ay;
    payload+="\"Z\":%s,"%Az;
    payload+="\"X2\":%s,"%Ax2;
    payload+="\"Y2\":%s,"%Ay2;
    payload+="\"Z2\":%s,"%Az2;
    payload+="\"Gx\":%s,"%Gx;
    payload+="\"Gy\":%s,"%Gy;
    payload+="\"Gz\":%s,"%Gz;
    payload+="\"Gx2\":%s,"%Gx2;
    payload+="\"Gy2\":%s,"%Gy2;
    payload+="\"Gz2\":%s,"%Gz2;
    payload+="\"AnguloX\": %s,"%get_x_rotation(acc_x,acc_y,acc_z);
    payload+="\"AnguloY\": %s,"%get_y_rotation(acc_x,acc_y,acc_z);
    payload+="\"Infrarrojo\": %s"%Infrarrojo;
    payload+="}"
    
    ret= client1.publish("v1/devices/me/telemetry",payload)
    print(payload)
    
    print ("Giro Acelerometro 1 X = %.2f" %Gx, u'\u00b0'+ "/s\n", 
           "Giro Acelerometro 1 Y = %.2f" %Gy, u'\u00b0'+ "/s\n", 
           "Giro Acelerometro 1 Z = %.2f" %Gz, u'\u00b0'+ "/s\n\n",
           "Giro Acelerometro 2 X = %.2f" %Gx2, u'\u00b0'+ "/s\n", 
           "Giro Acelerometro 2 Y = %.2f" %Gy2, u'\u00b0'+ "/s\n", 
           "Giro Acelerometro 2 Z = %.2f" %Gz2, u'\u00b0'+"/s\n\n",
           "Aceleracion Acelerometro 1 X = %.2f g\n" %Ax, 
           "Aceleracion Acelerometro 1 Y = %.2f g\n" %Ay, 
           "Aceleracion Acelerometro 1 Z = %.2f g\n\n" %Az,
           "Aceleracion Acelerometro 2 X = %.2f g\n" %Ax2, 
           "Aceleracion Acelerometro 2 Y = %.2f g\n" %Ay2, 
           "Aceleracion Acelerometro 2 Z = %.2f g\n\n" %Az2)
    time.sleep(0.05)


if (isTimeLimit == True): 
    IO.output(15, False)
    IO.output(7, False)
    print('El ejercicio ha finalizado')

     
data = {'Giro Acelerometro 1 X': gxValuesAcc1,
        'Giro Acelerometro 1 Y': gyValuesAcc1,
        'Giro Acelerometro 1 Z': gzValuesAcc1,
        'Giro Acelerometro 2 X': gxValuesAcc2,
        'Giro Acelerometro 2 Y': gyValuesAcc2,
        'Giro Acelerometro 2 Z': gzValuesAcc2,
        'Aceleracion Acelerometro 1 X': axValuesAcc1,
        'Aceleracion Acelerometro 1 Y': ayValuesAcc1,
        'Aceleracion Acelerometro 1 Z': aZValuesAcc1,
        'Aceleracion Acelerometro 2 X': aXValuesAcc2,
        'Aceleracion Acelerometro 2 Y': ayValuesAcc2,
        'Aceleracion Acelerometro 2 Z': azValuesAcc2}

df = pd.DataFrame(data, columns = ['Giro Acelerometro 1 X', 'Giro Acelerometro 1 Y', 'Giro Acelerometro 1 Z',
                                   'Giro Acelerometro 2 X', 'Giro Acelerometro 2 Y', 'Giro Acelerometro 2 Z',
                                   'Aceleracion Acelerometro 1 X', 'Aceleracion Acelerometro 1 Y', 'Aceleracion Acelerometro 1 Z',
                                   'Aceleracion Acelerometro 2 X', 'Aceleracion Acelerometro 2 Y', 'Aceleracion Acelerometro 2 Z'])
#df.to_excel('dataExercise.xlsx', sheet_name='example')

if (np.min(gzValuesAcc1) > -2.6 and np.max(gzValuesAcc1) < 3 and 
    np.min(gxValuesAcc2) > -4.75 and np.max(gxValuesAcc2) < 5.2): 
    print("El ejercicio se ha realizado correctamente")
else:
    print("El ejercicio no se ha realizado correctamente")
    IO.output(buzzer,IO.HIGH)
    time.sleep(5)
    IO.output(buzzer,IO.LOW)
