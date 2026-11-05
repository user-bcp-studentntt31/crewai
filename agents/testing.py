"""Agente inicial del taller. Mejora sus instrucciones sin cambiar su contrato."""
from crewai import Agent, Task
from crew.llm_config import llm

KEY = 'testing'
LABEL = 'Ingeniero de pruebas'
SPEC_FILE = 'testing_report.md'
EXTRACT_CODE = True

INSTRUCTIONS = ("Como Ingeniero de pruebas, ejecuta y verifica cada tarea asignada. "
                "Para cada una: define los casos de prueba (camino feliz, bordes y errores), "
                "ejecútalos, registra el comando y su resultado real, y reporta cualquier fallo con su causa. "
                "No marques una tarea como probada sin evidencia verificable.")
agent = Agent(role='Ingeniero de pruebas', goal="Probar todas las tareas del equipo y generar evidencias tangibles y reproducibles "
        "(comandos ejecutados, resultados, cobertura y fallos detectados), "
        "sin dar por válido ningún resultado que no haya sido ejecutado.",
              backstory="Eres un ingeniero de calidad con amplia experiencia en pruebas automatizadas y de regresión. "
        "Has trabajado en equipos donde un cambio sin evidencia no se acepta, por lo que desconfías "
        "de las afirmaciones sin pruebas y documentas cada verificación. Priorizas proteger el "
        "comportamiento existente con pruebas de caracterización antes de aprobar cambios, "
        "y reportas con claridad qué pasó, qué falló y qué falta por verificar.", llm=llm,
              verbose=True, allow_delegation=False)


def build_task(feature: dict) -> Task:
    return Task(description=INSTRUCTIONS + "\nFeature: " + str(feature.get("title", ""))
                + "\n" + str(feature.get("description", ""))
                + "\n" + str(feature.get("acceptance_criteria", [])),
                expected_output='Un informe de pruebas.', agent=agent)
