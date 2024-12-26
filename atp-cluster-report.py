import subprocess
import os
import datetime

# Función para ejecutar comandos en shell
def ejecutar_comando(comando):
    try:
        resultado = subprocess.run(comando, shell=True, check=True, text=True, capture_output=True)
        return resultado.stdout
    except subprocess.CalledProcessError as e:
        return f"Error ejecutando {comando}: {e.stderr.strip()}"
    
# Obtener el status de CEPH en el clúster
def verificar_ceph():
    namespace = "openshift-storage"
    # Obtener el nombre del pod de Rook Ceph Operator
    comando_rook_pod = f"oc -n {namespace} get pod -l app=rook-ceph-operator -o jsonpath='{{.items[0].metadata.name}}'"
    rook_pod = ejecutar_comando(comando_rook_pod).strip()
    
    if "Error" in rook_pod or not rook_pod:
        return f"Error obteniendo el pod de Rook Ceph Operator: {rook_pod}"
    
    # Ejecutar el comando de ceph -s en el pod de Rook
    comando_ceph_status = (
        f"oc exec -it {rook_pod} -n {namespace} -- "
        f"ceph -s --cluster={namespace} "
        f"--conf=/var/lib/rook/{namespace}/{namespace}.config "
        f"--keyring=/var/lib/rook/{namespace}/client.admin.keyring"
    )
    resultado_ceph = ejecutar_comando(comando_ceph_status)
    
    if "Error ejecutando" in resultado_ceph:
        return f"Error verificando el estado de CEPH: {resultado_ceph}"
    else:
        return resultado_ceph

# Obtener nombre del cluster
def obtener_nombre_cluster():
    comando = "oc get infrastructure cluster -o jsonpath='{.status.infrastructureName}'"
    nombre_cluster = ejecutar_comando(comando).strip().replace("'", "")
    return nombre_cluster

# Obtener la lista de nodos del clúster
def obtener_nodos():
    comando = "oc get nodes -o jsonpath='{.items[*].metadata.name}'"
    nodos = ejecutar_comando(comando).strip().split()
    return nodos

# Crear reporte
def generar_reporte(reporte, nombre_cluster):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    nombre_archivo = f"{nombre_cluster}_reporte_{timestamp}.txt"
    with open(nombre_archivo, 'w') as f:
        f.write(reporte)
    print(f"Reporte generado: {nombre_archivo}")

# Función para verificar el MTU en todos los nodos
def verificar_mtu():
    reporte_mtu = ""
    nodos = obtener_nodos()
    
    for nodo in nodos:
        reporte_mtu += f"MTU en nodo {nodo}:\n"
        comando_mtu = f"oc debug node/{nodo} -- chroot /host cat /sys/class/net/br-ex/mtu"
        resultado_mtu = ejecutar_comando(comando_mtu)
        
        if "Error ejecutando" in resultado_mtu or not resultado_mtu.strip():
            reporte_mtu += f"Error verificando el MTU en {nodo}. Detalles: {resultado_mtu}\n"
        else:
            reporte_mtu += f"{resultado_mtu.strip()}\n"
    
    return reporte_mtu

# Función para verificar el uso de recursos en cada nodo usando oc adm top
def verificar_recursos_nodos():
    reporte_recursos = ""
    nodos = obtener_nodos()
    
    for nodo in nodos:
        reporte_recursos += f"Uso de recursos en nodo {nodo}:\n"
        comando_recursos = f"oc adm top node {nodo}"
        resultado_recursos = ejecutar_comando(comando_recursos)
        
        if "Error ejecutando" in resultado_recursos or not resultado_recursos.strip():
            reporte_recursos += f"Error verificando los recursos en {nodo}. Detalles: {resultado_recursos}\n"
        else:
            reporte_recursos += f"{resultado_recursos.strip()}\n"
    
    return reporte_recursos

def verificar_ntp_nodos(nodos):
    """
    Función para verificar el estado de NTP en todos los nodos.
    Args:
        nodos (list): Lista de nombres de nodos.
    Returns:
        str: Resultado de la verificación de NTP en cada nodo.
    """
    reporte_ntp = "1. Verificación de NTP en todos los nodos:\n"

    for nodo in nodos:
        reporte_ntp += f"Verificando NTP en nodo {nodo}:\n"
        comando_ntp = f"oc debug node/{nodo} -- chroot /host timedatectl"

        try:
            # Ejecutar el comando para verificar NTP
            resultado_ntp = ejecutar_comando(comando_ntp)

            # Validar la salida para asegurarse de que es válida
            if resultado_ntp and "NTP" in resultado_ntp:
                reporte_ntp += f"Resultado NTP en {nodo}:\n{resultado_ntp}\n"
            else:
                # Si no hay información relevante o el comando no da resultados útiles
                reporte_ntp += f"Advertencia: No se pudo obtener información de NTP en {nodo}.\nDetalles: {resultado_ntp}\n"

        except Exception as e:
            # Manejar errores de ejecución de comando
            reporte_ntp += f"Error ejecutando NTP en {nodo}: {str(e)}\n"

    return reporte_ntp

def main():
    # Inicialización del reporte
    reporte = ""
    nombre_cluster = obtener_nombre_cluster()

    # Obtener la lista de nodos
    nodos = obtener_nodos()

    # 1. Check NTP en todos los nodos
    reporte = verificar_ntp_nodos(nodos)

     # 2. Verificación de CEPH
    reporte += "\n2. Verificación del estado de CEPH:\n"
    resultado_ceph = verificar_ceph()
    reporte += resultado_ceph + "\n"

    # 3. Verificación del MTU
    reporte += "\n3. Verificación del MTU en todos los nodos:\n"
    resultado_mtu = verificar_mtu()
    reporte += resultado_mtu + "\n"

    # 4. Verificación de uso de recursos en nodos
    reporte += "\n4. Verificación de uso de recursos en todos los nodos:\n"
    resultado_recursos = verificar_recursos_nodos()
    reporte += resultado_recursos + "\n"

    # 3. Crear Proyecto y Aplicación de Prueba
    reporte += "2. Crear Proyecto y Aplicación de Prueba:\n"
    reporte += ejecutar_comando("oc new-project test-oc") + "\n"
    reporte += ejecutar_comando("oc new-app rails-postgresql-example") + "\n"
    reporte += ejecutar_comando("oc logs -f buildconfig/rails-postgresql-example") + "\n"
    reporte += ejecutar_comando("oc get pods") + "\n"
    reporte += ejecutar_comando("oc status") + "\n"
    reporte += ejecutar_comando("oc delete project test-oc") + "\n"

    # 4. Verificación de Salud del Host, ETCD y Otros
    reporte += "3. Verificación de Salud del Host, ETCD y Otros:\n"
    reporte += ejecutar_comando("oc get nodes") + "\n"
    reporte += ejecutar_comando("oc get etcd -n openshift-etcd") + "\n"
    reporte += ejecutar_comando("oc get pods -n openshift-etcd") + "\n"
    reporte += ejecutar_comando("oc exec -it etcd-ocp4-master-cnt-01.ocpcnt.financiero.bco -n openshift-etcd -- /usr/bin/etcdctl endpoint health") + "\n"
    reporte += ejecutar_comando("oc exec -it etcd-ocp4-master-cnt-01.ocpcnt.financiero.bco -n openshift-etcd -- /usr/bin/etcdctl endpoint status") + "\n"
    reporte += ejecutar_comando("oc exec -it etcd-ocp4-master-cnt-01.ocpcnt.financiero.bco -n openshift-etcd -- /usr/bin/etcdctl member list") + "\n"

    # 5. Verificación del Router y Registro de Imágenes
    reporte += "4. Verificación del Router y Registro de Imágenes:\n"
    reporte += ejecutar_comando("oc get deployments/router-default -n openshift-ingress") + "\n"
    reporte += ejecutar_comando("oc get pods -n openshift-ingress") + "\n"
    reporte += ejecutar_comando("oc get deployments/image-registry -n openshift-image-registry") + "\n"
    reporte += ejecutar_comando("oc get pods -n openshift-image-registry | grep image-registry") + "\n"

    # 6. Verificación de Conectividad entre Nodos Master
    reporte += "5. Verificación de Conectividad entre Nodos Master:\n"
    reporte += ejecutar_comando("oc debug node/ocp4-master-cnt-01.ocpcnt.financiero.bco -- chroot /host ping ocp4-master-cnt-02.ocpcnt.financiero.bco") + "\n"
    reporte += ejecutar_comando("oc debug node/ocp4-master-cnt-01.ocpcnt.financiero.bco -- chroot /host ping ocp4-master-cnt-03.ocpcnt.financiero.bco") + "\n"
    reporte += ejecutar_comando("oc debug node/ocp4-master-cnt-02.ocpcnt.financiero.bco -- chroot /host ping ocp4-master-cnt-03.ocpcnt.financiero.bco") + "\n"

    # 7. Verificación de Servicios de Red
    reporte += "6. Verificación de Servicios de Red:\n"
    reporte += ejecutar_comando("oc get services --all-namespaces | grep -E 'kube-apiserver|etcd|controller-manager|scheduler|dns|router'") + "\n"
    reporte += ejecutar_comando("oc get pods -n openshift-etcd") + "\n"
    reporte += ejecutar_comando("oc get pods -n openshift-kube-apiserver") + "\n"
    reporte += ejecutar_comando("oc get pods -n openshift-kube-controller-manager") + "\n"
    reporte += ejecutar_comando("oc get pods -n openshift-kube-scheduler") + "\n"
    reporte += ejecutar_comando("oc get pods -n openshift-dns") + "\n"
    reporte += ejecutar_comando("oc get pods -n openshift-ingress") + "\n"

    # 8. Verificación del Consumo de Recursos
    reporte += "7. Verificación del Consumo de Recursos:\n"
    reporte += ejecutar_comando("oc adm top nodes") + "\n"

    # 9. Verificación del Almacenamiento
    reporte += "8. Verificación del Almacenamiento:\n"
    reporte += ejecutar_comando("df -hT") + "\n"

    # 10. Verificación del Servicio de API
    reporte += "9. Verificación del Servicio de API:\n"
    reporte += ejecutar_comando("oc get apiservices") + "\n"
    reporte += ejecutar_comando("oc get svc -n default kubernetes") + "\n"
    reporte += ejecutar_comando("oc get pods -n openshift-kube-apiserver") + "\n"

    # Generar reporte
    generar_reporte(reporte, nombre_cluster)

if __name__ == "__main__":
    main()
