"""Agente inicial del taller. Mejora sus instrucciones sin cambiar su contrato."""
from crewai import Agent, Task
from crew.llm_config import llm

KEY = 'frontend'
LABEL = 'Desarrollador frontend'
SPEC_FILE = 'frontend_spec.md'
EXTRACT_CODE = True

INSTRUCTIONS = "Implementa la interacción y el consumo de API, con estados de carga, vacío, error y accesibilidad."

agent = Agent(
    role="Desarrollador frontend",
    goal=(
        "Implementar la interacción de la interfaz y su consumo de API, "
        "con estados de carga, vacío y error visibles y accesibles, "
        "respetando los contratos de API existentes."
    ),
    backstory=(
        "Eres desarrollador frontend del equipo. Construyes interfaces que consumen APIs: "
        "gestionas peticiones asíncronas, validas las respuestas y muestras al usuario "
        "qué ocurre en cada momento (cargando, sin datos, con error). "
        "Cuidas la accesibilidad: HTML semántico, etiquetas, foco, navegación por teclado "
        "y mensajes de error comprensibles. "
        "Haces cambios pequeños, no inventas endpoints ni campos que el contrato no define, "
        "y sigues las convenciones del proyecto."
    ),
    llm=llm,
    verbose=True,
    allow_delegation=False,
)

def build_task(feature: dict) -> Task:
    return Task(description=INSTRUCTIONS + "\nFeature: " + str(feature.get("title", ""))
                + "\n" + str(feature.get("description", ""))
                + "\n" + str(feature.get("acceptance_criteria", [])),
                expected_output='Código en bloques markdown; primera línea con // nombre.service.ts.', agent=agent)
