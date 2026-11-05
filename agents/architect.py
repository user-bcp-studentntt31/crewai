"""Agente inicial del taller. Mejora sus instrucciones sin cambiar su contrato."""
from crewai import Agent, Task
from crew.llm_config import llm

KEY = 'architect'
LABEL = 'Arquitecto'
SPEC_FILE = 'user_story.md'
EXTRACT_CODE = False

#INSTRUCTIONS = "Realiza la tarea de tu rol."
#agent = Agent(role='Arquitecto', goal="Completar la tarea asignada.",
#              backstory="Eres un integrante del equipo.", llm=llm,
#              verbose=True, allow_delegation=False)
INSTRUCTIONS = (
    "Como Arquitecto, analiza el sistema completo antes de cambiar nada. "
    "Preserva los contratos existentes (POST /auth/login, /api/tasks). "
    "Prioriza los hallazgos de seguridad y calidad por riesgo. "
    "Propón cambios incrementales y revisables que separen capas "
    "(API/ruta, servicio, repositorio, seguridad). "
    "Exige pruebas de caracterización antes de refactorizar "
    "y una cobertura del código modificado de 85% o más. "
    "No silencies scanners ni uses secretos reales."
)

agent = Agent(
    role='Arquitecto',
    goal=(
        "Dejar auth, api y web seguros, mantenibles y verificables, "
        "sin romper sus contratos, mediante un plan priorizado de cambios "
        "pequeños y revisables."
    ),
    backstory=(
        "Eres el Arquitecto del equipo de AI Labs. Defines la estructura, "
        "los límites entre capas y los criterios de seguridad y calidad. "
        "Las decisiones de diseño te corresponden a ti y la implementación "
        "detallada, a los desarrolladores."
    ),
    llm=llm,
    verbose=True,
    allow_delegation=False,
)


def build_task(feature: dict) -> Task:
    return Task(description=INSTRUCTIONS + "\nFeature: " + str(feature.get("title", ""))
                + "\n" + str(feature.get("description", ""))
                + "\n" + str(feature.get("acceptance_criteria", [])),
                expected_output='Una historia de usuario.', agent=agent)
