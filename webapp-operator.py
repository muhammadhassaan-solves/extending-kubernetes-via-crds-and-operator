from kubernetes import client, config, watch
import yaml
import time

GROUP = "example.com"
VERSION = "v1"
PLURAL = "webapps"
NAMESPACE = "default"

def main():
    # Load kubeconfig (Minikube/dev mode)
    config.load_kube_config()
    
    api = client.CustomObjectsApi()
    apps_v1 = client.AppsV1Api()

    w = watch.Watch()

    print("Watching for WebApp changes...")
    for event in w.stream(api.list_namespaced_custom_object,
                          group=GROUP,
                          version=VERSION,
                          namespace=NAMESPACE,
                          plural=PLURAL,
                          timeout_seconds=0):
        obj = event["object"]
        event_type = event["type"]
        name = obj["metadata"]["name"]
        spec = obj.get("spec", {})
        image = spec.get("image")
        replicas = spec.get("replicas", 1)

        print(f"Event: {event_type} - WebApp: {name}")

        if event_type in ["ADDED", "MODIFIED"]:
            # Define deployment spec
            deployment = client.V1Deployment(
                metadata=client.V1ObjectMeta(name=name),
                spec=client.V1DeploymentSpec(
                    replicas=replicas,
                    selector=client.V1LabelSelector(
                        match_labels={"app": name}
                    ),
                    template=client.V1PodTemplateSpec(
                        metadata=client.V1ObjectMeta(labels={"app": name}),
                        spec=client.V1PodSpec(
                            containers=[
                                client.V1Container(
                                    name=name,
                                    image=image,
                                    ports=[client.V1ContainerPort(container_port=80)]
                                )
                            ]
                        )
                    )
                )
            )

            try:
                # Check if deployment exists
                apps_v1.read_namespaced_deployment(name=name, namespace=NAMESPACE)
                # If it exists, update it
                apps_v1.replace_namespaced_deployment(
                    name=name,
                    namespace=NAMESPACE,
                    body=deployment
                )
                print(f"Updated Deployment: {name}")
            except client.exceptions.ApiException as e:
                if e.status == 404:
                    # Doesn't exist, create it
                    apps_v1.create_namespaced_deployment(
                        namespace=NAMESPACE,
                        body=deployment
                    )
                    print(f"Created Deployment: {name}")
                else:
                    print(f"Error handling deployment: {e}")
        elif event_type == "DELETED":
            try:
                apps_v1.delete_namespaced_deployment(
                    name=name,
                    namespace=NAMESPACE
                )
                print(f"Deleted Deployment: {name}")
            except client.exceptions.ApiException as e:
                print(f"Failed to delete Deployment: {name} - {e}")

if __name__ == "__main__":
    while True:
        try:
            main()
        except Exception as e:
            print(f"Operator crashed: {e}")
            time.sleep(2)
