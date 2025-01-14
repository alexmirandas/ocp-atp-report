import subprocess
import datetime
from tabulate import tabulate

# Función para ejecutar comandos en shell
def ejecutar_comando(comando):
    try:
        resultado = subprocess.run(comando, shell=True, check=True, text=True, capture_output=True)
        return resultado.stdout.strip()
    except subprocess.CalledProcessError as e:
        return f"Error ejecutando {comando}: {e.stderr.strip()}"

# Obtener información general del clúster
def obtener_info_cluster():
    datos = []
    nombre_cluster = ejecutar_comando("oc get infrastructure cluster -o jsonpath='{.status.infrastructureName}'")
    version_cluster = ejecutar_comando("oc version | grep 'Server Version' | awk '{print $3}'")
    proveedor_infra = ejecutar_comando("oc get infrastructure cluster -o jsonpath='{.status.platformStatus.type}'")

    datos.append(("Nombre del Clúster", nombre_cluster))
    datos.append(("Versión del Clúster", version_cluster))
    datos.append(("Proveedor de Infraestructura", proveedor_infra))

    return datos

# Verificar el estado de CEPH
def verificar_ceph():
    namespace = "openshift-storage"
    comando_rook_pod = f"oc -n {namespace} get pod -l app=rook-ceph-operator -o jsonpath='{{.items[0].metadata.name}}'"
    rook_pod = ejecutar_comando(comando_rook_pod)

    if "Error" in rook_pod or not rook_pod:
        return [("Error", f"Error obteniendo el pod de Rook Ceph Operator: {rook_pod}")]

    comando_ceph_status = (
        f"oc exec -it {rook_pod} -n {namespace} -- "
        f"ceph -s --cluster={namespace} "
        f"--conf=/var/lib/rook/{namespace}/{namespace}.config "
        f"--keyring=/var/lib/rook/{namespace}/client.admin.keyring"
    )
    return [("Ceph Status", ejecutar_comando(comando_ceph_status))]

# Verificar nodos
def obtener_nodos():
    comando = "oc get nodes -o jsonpath='{.items[*].metadata.name}'"
    return ejecutar_comando(comando).split()

# Verificar el MTU en todos los nodos
def verificar_mtu(nodos):
    resultados = []
    for nodo in nodos:
        comando_mtu = f"oc debug node/{nodo} -- chroot /host cat /sys/class/net/ens192/mtu"
        resultado_mtu = ejecutar_comando(comando_mtu)
        resultados.append((nodo, f"MTU: {resultado_mtu}" if "Error" not in resultado_mtu else f"Error verificando MTU: {resultado_mtu}"))
    return resultados

# Verificar recursos usando 'oc adm top'
def verificar_recursos_nodos(nodos):
    resultados = []
    for nodo in nodos:
        comando_recursos = f"oc adm top node {nodo}"
        resultado_recursos = ejecutar_comando(comando_recursos)
        resultados.append((nodo, resultado_recursos if "Error" not in resultado_recursos else f"Error verificando recursos: {resultado_recursos}"))
    return resultados

# Verificar conectividad entre nodos
def verificar_conectividad_nodos(nodos):
    resultados = []
    for nodo in nodos:
        for otro_nodo in nodos:
            if nodo != otro_nodo:
                comando = f"oc debug node/{nodo} -- chroot /host ping -c 1 {otro_nodo}"
                resultado = ejecutar_comando(comando)
                resultados.append((f"{nodo} -> {otro_nodo}", resultado))
    return resultados

# Verificar almacenamiento
def verificar_almacenamiento():
    comando = "df -hT"
    return [("Uso de disco", ejecutar_comando(comando))]

# Generar reporte en archivo
def generar_reporte(reporte, nombre_cluster):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    nombre_archivo = f"{nombre_cluster}_reporte_{timestamp}.txt"
    with open(nombre_archivo, 'w') as f:
        for titulo, contenido in reporte:
            f.write(f"{titulo}:
{contenido}\n\n")
    print(f"Reporte generado: {nombre_archivo}")

# Ejecución principal
def main():
    reporte = []
    nodos = obtener_nodos()

    # Información general del clúster
    reporte.extend(obtener_info_cluster())

    # Estado del clúster
    reporte.append(("Estado de CEPH", tabulate(verificar_ceph(), headers=["Componente", "Estado"], tablefmt="pretty")))
    reporte.append(("MTU", tabulate(verificar_mtu(nodos), headers=["Nodo", "Resultado"], tablefmt="pretty")))
    reporte.append(("Recursos de Nodos", tabulate(verificar_recursos_nodos(nodos), headers=["Nodo", "Recursos"], tablefmt="pretty")))
    reporte.append(("Conectividad entre nodos", tabulate(verificar_conectividad_nodos(nodos), headers=["Nodos", "Resultado"], tablefmt="pretty")))
    reporte.append(("Almacenamiento", tabulate(verificar_almacenamiento(), headers=["Componente", "Estado"], tablefmt="pretty")))

    # Generar reporte
    nombre_cluster = ejecutar_comando("oc get infrastructure cluster -o jsonpath='{.status.infrastructureName}'")
    generar_reporte(reporte, nombre_cluster)

if __name__ == "__main__":
    main()
