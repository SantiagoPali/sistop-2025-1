import struct

# Paso 1: Crear el archivo FiUnamFS.img de 1440 KB y llenar con ceros
with open("FiUnamFS.img", "wb") as file:
    file.write(b'\x00' * (1440 * 1024))  # 1440 KB llenos de ceros

# Paso 2: Configuración del superbloque en FiUnamFS.img
with open("FiUnamFS.img", "r+b") as file:
    # Nombre del sistema (bytes 0-8)
    file.seek(0)
    file.write(b'FiUnamFS')

    # Versión del sistema (bytes 10-14)
    file.seek(10)
    file.write(b'25-1')

    # Tamaño de cluster (bytes 40-44) - 1024 bytes en formato little endian
    file.seek(40)
    file.write(struct.pack('<I', 1024))

    # Clusters para el directorio (suponemos 4 clusters en esta implementación)
    file.seek(45)
    file.write(struct.pack('<I', 4))

    # Número total de clusters (calculado en base al tamaño total de 1440 KB)
    total_clusters = (1440 * 1024) // 1024  # Tamaño total / tamaño del cluster
    file.seek(50)
    file.write(struct.pack('<I', total_clusters))

# Leer y verificar los primeros datos en FiUnamFS.img
with open("FiUnamFS.img", "rb") as file:
    # Leer el nombre del sistema
    file.seek(0)
    name = file.read(8)
    print("Nombre del sistema:", name.decode())

    # Leer la versión
    file.seek(10)
    version = file.read(4)
    print("Versión del sistema:", version.decode())

    # Leer tamaño del cluster
    file.seek(40)
    cluster_size = struct.unpack('<I', file.read(4))[0]
    print("Tamaño del cluster:", cluster_size)

    # Leer total de clusters
    file.seek(50)
    total_clusters = struct.unpack('<I', file.read(4))[0]
    print("Total de clusters:", total_clusters)

import struct

# Tamaño de una entrada del directorio en bytes
DIR_ENTRY_SIZE = 64
DIRECTORY_START_CLUSTER = 1
DIRECTORY_END_CLUSTER = 4
CLUSTER_SIZE = 1024  # tamaño de cluster en bytes

# Función para leer y listar las entradas del directorio
def listar_contenido_directorio():
    with open("FiUnamFS.img", "rb") as file:
        # Leer cada entrada en los clusters de directorio
        file.seek(DIRECTORY_START_CLUSTER * CLUSTER_SIZE)
        
        print("Contenido del Directorio:")
        for i in range((DIRECTORY_END_CLUSTER - DIRECTORY_START_CLUSTER + 1) * (CLUSTER_SIZE // DIR_ENTRY_SIZE)):
            entry = file.read(DIR_ENTRY_SIZE)
            
            # Extraer y decodificar datos de la entrada
            tipo_archivo = entry[0:1].decode()
            nombre = entry[1:16].decode().strip("-")  # nombre es de 15 bytes
            tamaño = struct.unpack('<I', entry[16:20])[0]
            cluster_inicial = struct.unpack('<I', entry[20:24])[0]
            fecha_creacion = entry[24:38].decode()
            fecha_modificacion = entry[38:52].decode()

            # Verificar si la entrada está vacía (sin archivo)
            if nombre == "":
                continue  # saltamos las entradas vacías

            # Imprimir detalles de la entrada
            print(f"Tipo: {tipo_archivo}, Nombre: {nombre}, Tamaño: {tamaño} bytes, " +
                  f"Cluster inicial: {cluster_inicial}, Creación: {fecha_creacion}, Modificación: {fecha_modificacion}")

import time

# Función para agregar un archivo desde tu equipo hacia FiUnamFS
def agregar_archivo_a_fiunamfs(ruta_archivo_local):
    # Leer el archivo local
    try:
        with open(ruta_archivo_local, "rb") as archivo:
            contenido_archivo = archivo.read()
            tamaño_archivo = len(contenido_archivo)
    except FileNotFoundError:
        print("El archivo no se encontró en tu equipo.")
        return

    nombre_archivo = ruta_archivo_local.split('/')[-1]  # Extraer solo el nombre
    if len(nombre_archivo) > 15:
        print("El nombre del archivo es demasiado largo (máximo 15 caracteres).")
        return

    # Buscar una entrada vacía en el directorio
    with open("FiUnamFS.img", "r+b") as fiunamfs:
        fiunamfs.seek(DIRECTORY_START_CLUSTER * CLUSTER_SIZE)
        entrada_libre = None

        # Recorrer todas las entradas del directorio
        for i in range((DIRECTORY_END_CLUSTER - DIRECTORY_START_CLUSTER + 1) * (CLUSTER_SIZE // DIR_ENTRY_SIZE)):
            posicion = fiunamfs.tell()
            entry = fiunamfs.read(DIR_ENTRY_SIZE)
            tipo_archivo = entry[0:1].decode()

            # Identificar entrada vacía
            if tipo_archivo == '#':
                entrada_libre = posicion
                break

        if entrada_libre is None:
            print("No hay espacio en el directorio para agregar otro archivo.")
            return

        # Encontrar el próximo cluster libre para almacenar el archivo
        cluster_inicial = 5  # asumimos que el espacio de datos empieza en el cluster 5
        fiunamfs.seek(cluster_inicial * CLUSTER_SIZE)

        # Guardar el contenido del archivo en el área de datos
        fiunamfs.write(contenido_archivo)

        # Escribir la entrada en el directorio
        fiunamfs.seek(entrada_libre)
        fecha_actual = time.strftime("%Y%m%d%H%M%S")  # formato AAAAMMDDHHMMSS
        entrada = (
            b"." +  # Tipo de archivo
            nombre_archivo.ljust(15, "-").encode() +  # Nombre del archivo
            struct.pack("<I", tamaño_archivo) +  # Tamaño del archivo en bytes
            struct.pack("<I", cluster_inicial) +  # Cluster inicial
            fecha_actual.encode() +  # Fecha de creación
            fecha_actual.encode() +  # Fecha de última modificación
            b"\x00" * 12  # Espacio reservado
        )
        fiunamfs.write(entrada)

    print(f"Archivo '{nombre_archivo}' agregado correctamente a FiUnamFS.")

# Ejemplo de uso:
agregar_archivo_a_fiunamfs("prueba.txt")
listar_contenido_directorio()
