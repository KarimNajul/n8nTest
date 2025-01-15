import os
import requests
import json
import shutil
from dotenv import load_dotenv

# Cargar las variables de entorno del archivo .env
load_dotenv()


class CreateWorkflow():

    host = os.environ.get("N8N_HOST")  # URL base de n8n
    token = os.environ.get("API_KEY")  # Token de autenticación
    pending_folder = "pending_workflows"
    created_folder = "created_workflows"

    def get_pending_workflows(self):
        """Leer los archivos JSON de la carpeta 'workflows_pendientes'"""
        workflows = []
        for filename in os.listdir(CreateWorkflow.pending_folder):
            if filename.endswith(".json"):
                file_path = os.path.join(CreateWorkflow.pending_folder, filename)
                with open(file_path, 'r') as f:
                    workflows.append((filename, json.load(f)))  # Guarda el nombre y los datos del flujo
        return workflows

    def move_to_created(self, filename):
        """Mover el archivo JSON a la carpeta 'workflows_creados'"""
        source = os.path.join(CreateWorkflow.pending_folder, filename)
        destination = os.path.join(CreateWorkflow.created_folder, filename)
        shutil.move(source, destination)
        print(f"Archivo movido a 'workflows_creados': {filename}")

    @classmethod
    def clean_workflow_data(cls, workflow_data):
        """
        Eliminar propiedades no permitidas en el JSON del workflow.
        """
        # Propiedades permitidas por la API (añadir 'settings' aunque sea vacío)
        valid_keys = {"name", "nodes", "connections", "settings"}
        cleaned_data = {key: workflow_data[key] for key in valid_keys if key in workflow_data}

        # Asegurarse de que 'settings' esté presente (vacío si no existe)
        if "settings" not in cleaned_data:
            cleaned_data["settings"] = {}

        # Limpiar nodos para eliminar propiedades no necesarias
        for node in cleaned_data.get("nodes", []):
            if "id" in node:
                del node["id"]  # Eliminar ID único del nodo si existe

        # Limpiar cualquier propiedad adicional en 'settings'
        cleaned_data["settings"] = {}

        return cleaned_data

    @classmethod
    def create_workflow(cls, workflow_data):
        workflow_data = cls.clean_workflow_data(workflow_data)
        url = f"{cls.host}/workflows"  # Endpoint para crear workflows
        headers = {
            "X-N8N-API-KEY": f"{cls.token}",
            "Content-Type": "application/json"
        }
        response = requests.post(url, headers=headers, json=workflow_data)
        if response.status_code == 200:
            print("Workflow creado con éxito!")
            return response.json()  # Retorna la respuesta JSON
        else:
            print(f"Error al crear el workflow: {response.status_code}")
            print(response.text)
            return False

    def process_workflows(self):
        """Procesar todos los flujos de trabajo pendientes"""
        workflows = self.get_pending_workflows()
        for filename, workflow_data in workflows:
            # Intentar crear el flujo de trabajo
            if self.create_workflow(workflow_data):
                # Si se crea exitosamente, mover el archivo
                self.move_to_created(filename)


# Crear el workflow
workflow_creator = CreateWorkflow()
workflow_creator.process_workflows()
