"""Agente responsable de implementar backend y frontend de forma integrada."""
from crewai import Agent, Task
from crew.llm_config import llm

KEY = 'ai-engineer'
LABEL = 'AI Engineer'
SPEC_FILE = 'ai_engineer_spec.md'
EXTRACT_CODE = True

INSTRUCTIONS = """Implementa conjuntamente backend Java 17+/Quarkus y frontend Angular,
de acuerdo con la feature, sus criterios de aceptación y los contratos aprobados.

Contratos y alcance:
- Identifica endpoints, métodos HTTP, DTOs, campos JSON y respuestas de Arquitectura;
  cuando exista, sigue el modelo, restricciones y migración aprobados por Datos.
- No cambies ni inventes contratos, tablas o columnas. Señala contradicciones,
  supuestos conservadores y decisiones pendientes. Sin Datos, cubre la persistencia necesaria.
- Implementa todos los criterios con cambios pequeños y verificables, sin placeholders.

Backend:
- Separa recursos HTTP, servicios y repositorios; valida entradas en DTOs y reglas de
  negocio en servicios. Usa inyección de dependencias y transacciones donde corresponda.
- Alinea entidades y consultas al modelo aprobado; parametriza SQL/JPQL y pagina listados.
  Separa entidades de DTOs y no expongas detalles internos o stack traces en errores.
- Usa jakarta.*, configuración externa para secretos y datos ficticios en pruebas.
  Cuando aplique, protege contraseñas con hash seguro, usa mensajes de autenticación
  genéricos, autorización basada en la identidad y tokens configurados con expiración.
  No registres credenciales, tokens ni datos sensibles.
- Si el contrato requiere llamadas externas, contempla tiempos de espera y resiliencia
  compatibles con la operación, sin reintentos inseguros ni errores ocultos.

Frontend:
- Implementa el consumo de API, las validaciones visibles y los estados de carga,
  vacío y error. El cliente no sustituye validación ni autorización del servidor.
- Usa HTML semántico, etiquetas, foco y navegación por teclado; presenta errores claros.

Entrega y verificación:
- Un bloque markdown por archivo, con nombre en la primera línea e imports completos.
  Para Java usa // Nombre.java y el package correspondiente a la ruta de extracción;
  para TypeScript // nombre.ts, HTML <!-- nombre.html --> y CSS /* nombre.css */.
- Incluye casos felices, inválidos y errores pertinentes, y comandos de verificación.
  Indica supuestos y pruebas pendientes; no inventes ejecuciones ni resultados."""
agent = Agent(role=LABEL,
              goal="Implementar backend y frontend integrados, seguros y verificables conforme a los contratos aprobados.",
              backstory="Eres el AI Engineer del equipo. Dominas Java, Quarkus y Angular; "
                        "trabajas con Arquitectura y Datos para implementar sus contratos, "
                        "cuidas la seguridad, la accesibilidad y la coherencia entre API e interfaz.",
              llm=llm,
              verbose=True, allow_delegation=False)


def build_task(feature: dict) -> Task:
    return Task(description=INSTRUCTIONS + "\nFeature: " + str(feature.get("title", ""))
                + "\n" + str(feature.get("description", ""))
                + "\n" + str(feature.get("acceptance_criteria", [])),
                expected_output='Implementación integrada y código en bloques markdown: Java con primera línea '
                '// Nombre.java y el package correspondiente; TypeScript con // nombre.ts; '
                'HTML con <!-- nombre.html --> y CSS con /* nombre.css */. '
                'Indica supuestos y pruebas propuestas sin inventar resultados.', agent=agent)
