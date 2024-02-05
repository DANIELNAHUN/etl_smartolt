from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.options import Options
from webdriver_manager.microsoft import EdgeChromiumDriverManager
from dotenv import load_dotenv
from pathlib import Path
import os
import time
import shutil
import pandas as pd
import numpy as np
import pymysql

load_dotenv()


def inicio_sesion():
    edgeOptions = Options()
    edgeOptions.add_experimental_option("prefs",{
        "download.default_directory":"C:\Descargas_ETL",
    })

    driver  = webdriver.Edge(EdgeChromiumDriverManager().install(),options = edgeOptions)
    driver.get(os.getenv('URL_SMART'))
    driver.find_element(By.XPATH, '//*[@id="identity"]').send_keys(os.getenv('USER_SMART'))
    driver.find_element(By.XPATH, '//*[@id="password"]').send_keys(os.getenv('PASSWORD_SMART'))
    driver.find_element(By.XPATH, '/html/body/div/div/div/div/div[2]/form/fieldset/input').click()
    return driver

def eval_directory(path,name_dir):
    try:
        p=os.path.join(path,name_dir)
        if not os.path.exists(p):
            os.mkdir(p)
            print("Directory " , p ,  " Created ")
        return p
    except FileExistsError:
        print("Directory " , p ,  " already exists")

def get_path_file_recient(path):
    files=os.listdir(path)
    paths = [os.path.join(path, basename) for basename in files]
    epath=[]
    for file in paths:
        if(file.endswith(".csv")):
            epath.append(file)
    if len(epath)>0:
            return max(epath, key=os.path.getmtime)
    else:
        return None

def move_file(path_from,path_to,name_file):
    to=os.path.join(path_to,name_file)
    print(to)
    shutil.move(path_from,to)
    return to

def connection_db_local():
    conn = pymysql.connect(host=os.getenv("IP_SERVER_DATABASE"), database=os.getenv(
        'BD_SERVER'), user=os.getenv('USER_SERVER'), passwd=os.getenv('PASSWORD_SERVER'))
    return conn

def save_database(file):
    df = pd.read_csv(file, header=0)
    query_insert = "INSERT INTO onus(id_onus, onu_external_id, pon_type, sn, onu_type, name, olt, board, port, allocated_onu, zone, address, latitude, longitude, "\
        "odb_splitter, mode, wan_mode, ip_address, subnet_mask, default_gateway, dns1, dns2, username, password, catv, administrative_status, auth_date, status, "\
        "signal_onu, signal_1310, service_port, service_port_vlan, service_port_cvlan, service_port_svlan, service_port_tag_transform_mode, service_port_upload_speed, "\
        "service_port_download_speed, fecha_insert, fecha_update) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"
    query_truncate = "TRUNCATE onus"
    query_reset_id = "ALTER TABLE onus AUTO_INCREMENT = 1"
    params = df.to_numpy().tolist()
    params = [tuple(subparams) for subparams in params]

    params = [tuple(None if isinstance(x, float) and np.isnan(x) else x for x in tupla) for tupla in params]
    #Subir Datos a la DB Local
    try:
        conn = connection_db_local()
        try:
            with conn.cursor() as cur:
                cur.execute(query_truncate)
                cur.execute(query_reset_id)
                cur.executemany(query_insert, params)
                conn.commit()
            print("Success save in mysql")
        finally:
            conn.close()
    except (pymysql.err.OperationalError, pymysql.err.InternalError) as e:
        print(f"Error not save in mysql {e} ")

def get_csv():
    driver = inicio_sesion()
    driver.get("https://comunicacionescabapice.smartolt.com/onu/configured")
    time.sleep(5)
    driver.find_element(By.XPATH, '//*[@id="export-selection"]').click()
    time.sleep(20)
    #Manejo de archivo move a un directorio específico y le cambia de nombre
    p=eval_directory(str(Path.home() / "C:\Descargas_ETL"),os.getenv('DIR_ONUS'))
    file=get_path_file_recient(Path.home() / "C:\Descargas_ETL")

    file_onus = ""

    if file != None:
        file_onus = move_file(file,p,"Onus List.csv")
    driver.quit()
    time.sleep(5)
    save_database(file_onus)

get_csv()
