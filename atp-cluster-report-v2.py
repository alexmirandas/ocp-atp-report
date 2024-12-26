import subprocess
import os
import datetime
from tabulate import tabulate

# Función para ejecutar comandos en shell
def ejecutar_comando(comando):
    try:
        resultado = subprocess.run(comando, shell=True, check=True, text=True, capture_output=True)
        return resultado.stdout.strip()
    except subprocess.CalledProcessError as e:
        return f"Error ejecutando {comando}: {e.stderr.strip()}"

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

# Verificar el estado de OpenShift Data Foundation (ODF)
def verificar_odf():
    namespace = "openshift-storage"
    comando_pods_odf = f"oc get pods -n {namespace} -o wide"
    resultado_pods_odf = ejecutar_comando(comando_pods_odf)
    
    return [("ODF Pods", resultado_pods_odf)]

# Verificar el estado de SSO
def verificar_sso():
    namespace = "openshift-sso"
    comando_pods_sso = f"oc get pods -n {namespace} -o wide"
    resultado_pods_sso = ejecutar_comando(comando_pods_sso)
    
    return [("SSO Pods", resultado_pods_sso)]

# Verificar el estado de 3scale API Management
def verificar_3scale():
    namespace = "3scale"
    comando_pods_3scale = f"oc get pods -n {namespace} -o wide"
    resultado_pods_3scale = ejecutar_comando(comando_pods_3scale)
    
    return [("3scale Pods", resultado_pods_3scale)]

# Obtener el nombre del clúster
def obtener_nombre_cluster():
    comando = "oc get infrastructure cluster -o jsonpath='{.status.infrastructureName}'"
    return ejecutar_comando(comando).replace("'", "")

# Obtener la lista de nodos del clúster
def obtener_nodos():
    comando = "oc get nodes -o jsonpath='{.items[*].metadata.name}'"
    return ejecutar_comando(comando).split()

# Crear reporte en archivo
def generar_reporte(reporte, nombre_cluster):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    nombre_archivo = f"{nombre_cluster}_reporte_{timestamp}.txt"
    with open(nombre_archivo, 'w') as f:
        f.write(reporte)
    print(f"Reporte generado: {nombre_archivo}")

# Verificar el MTU en todos los nodos
def verificar_mtu(nodos):
    resultados = []
    for nodo in nodos:
        comando_mtu = f"oc debug node/{nodo} -- chroot /host cat /sys/class/net/br-ex/mtu"
        resultado_mtu = ejecutar_comando(comando_mtu)

        if "Error" in resultado_mtu or not resultado_mtu:
            resultados.append((nodo, f"Error verificando MTU: {resultado_mtu}"))
        else:
            resultados.append((nodo, f"MTU: {resultado_mtu}"))

    return resultados

# Verificar recursos usando 'oc adm top'
def verificar_recursos_nodos(nodos):
    resultados = []
    for nodo in nodos:
        comando_recursos = f"oc adm top node {nodo}"
        resultado_recursos = ejecutar_comando(comando_recursos)

        if "Error" in resultado_recursos or not resultado_recursos:
            resultados.append((nodo, f"Error verificando recursos: {resultado_recursos}"))
        else:
            resultados.append((nodo, resultado_recursos))
    
    return resultados

# Verificar NTP en los nodos
def verificar_ntp_nodos(nodos):
    resultados = []
    for nodo in nodos:
        comando_ntp = f"oc debug node/{nodo} -- chroot /host timedatectl"
        resultado_ntp = ejecutar_comando(comando_ntp)

        if "Error" in resultado_ntp or not resultado_ntp:
            resultados.append((nodo, f"Error verificando NTP: {resultado_ntp}"))
        else:
            resultados.append((nodo, resultado_ntp))

    return resultados

def verificar_conectividad_nodos(nodos):
    """Verifica la conectividad entre los nodos del clúster."""
    resultados = []
    for nodo in nodos:
        for otro_nodo in nodos:
            if nodo != otro_nodo:
                comando = f"oc debug node/{nodo} -- chroot /host ping {otro_nodo}"
                resultado = ejecutar_comando(comando)
                resultados.append((f"{nodo} -> {otro_nodo}", resultado))
    return resultados

def verificar_almacenamiento():
    """Verifica el estado del almacenamiento."""
    comando = "df -hT"
    return [("Uso de disco", ejecutar_comando(comando))]

def generar_reporte(reporte, nombre_cluster):
    """Genera un reporte en formato de tabla."""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    nombre_archivo = f"{nombre_cluster}_reporte_{timestamp}.txt"
    with open(nombre_archivo, 'w') as f:
        for titulo, contenido in reporte:
            f.write(f"{titulo}:\n{contenido}\n")
    print(f"Reporte generado: {nombre_archivo}")

# Ejecución principal
def main():
    reporte = []
    nombre_cluster = obtener_nombre_cluster()
    nodos = obtener_nodos()

    reporte.append(("NTP", tabulate(verificar_ntp_nodos(nodos), headers=["Nodo", "Resultado"], tablefmt="pretty")))
    reporte.append(("Estado de CEPH", tabulate(verificar_ceph(), headers=["Componente", "Estado"], tablefmt="pretty")))
    reporte.append(("MTU", tabulate(verificar_mtu(nodos), headers=["Nodo", "Resultado"], tablefmt="pretty")))
    reporte.append(("Recursos de Nodos", tabulate(verificar_recursos_nodos(nodos), headers=["Nodo", "Recursos"], tablefmt="pretty")))
    reporte.append(("Estado de ODF", tabulate(verificar_odf(), headers=["Componente", "Estado"], tablefmt="pretty")))
    reporte.append(("Estado de SSO", tabulate(verificar_sso(), headers=["Componente", "Estado"], tablefmt="pretty")))
    reporte.append(("Estado de 3scale", tabulate(verificar_3scale(), headers=["Componente", "Estado"], tablefmt="pretty")))
    reporte.append(("Conectividad entre nodos", tabulate(verificar_conectividad_nodos(nodos), headers=["Nodos", "Resultado"], tablefmt="pretty")))
    reporte.append(("Almacenamiento", tabulate(verificar_almacenamiento(), headers=["Componente", "Estado"], tablefmt="pretty")))
    reporte_final = "\n".join([f"{titulo}:\n{contenido}" for titulo, contenido in reporte])
    
    generar_reporte(reporte_final, nombre_cluster)

if __name__ == "__main__":
    main()
