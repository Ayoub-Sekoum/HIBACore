
import structlog

from app.engine.ai.circuit_breaker import ResilientLLMClient

logger = structlog.get_logger(__name__)

async def determine_writing_style(text: str, history: list[dict[str, str]] = []) -> str:
    """
    Analizza il contesto del messaggio e della storia per determinare lo stile di scrittura ottimale.
    In futuro integrerà Azure AI Text Analytics per analisi del sentiment e complessità.
    """

    # Esempio di logica "automatic" sotto la scocca:
    # Se il testo è corto -> Conciso
    # Se contiene termini tecnici ("codice", "python", "architettura") -> Accademico/Tecnico
    # Se è un saluto o colloquiale -> Creativo/Amichevole
    # Default -> Professionale

    prompt = f"""
    Analizza il seguente messaggio utente e determina lo stile di risposta migliore tra:
    - PROFESSIONAL: Formale e preciso.
    - CREATIVE: Coinvolgente ed espressivo.
    - CONCISE: Breve e diretto.
    - ACADEMIC: Analitico e strutturato.

    Messaggio: "{text}"
    
    Rispondi SOLO con la parola chiave dello stile (es. PROFESSIONAL).
    """

    try:
        llm_client = ResilientLLMClient()
        # Usiamo il modello mini per questa analisi veloce "sotto la scocca"
        response = await llm_client.complete(
            messages=[{"role": "system", "content": "Sei un analista linguistico esperto."}, {"role": "user", "content": prompt}],
            model="gpt-4o-mini"
        )

        style = response.choices[0].message.content.strip().upper() if response.choices else "PROFESSIONAL"

        if style not in ["PROFESSIONAL", "CREATIVE", "CONCISE", "ACADEMIC"]:
            style = "PROFESSIONAL"

        logger.info("automatic_style_determined", text=text[:50], style=style)
        return style

    except Exception as e:
        logger.warning("style_determination_failed_using_default", error=str(e))
        return "PROFESSIONAL"

def get_style_instructions(style: str) -> str:
    """Restituisce le istruzioni di sistema per lo stile selezionato."""
    instructions = {
        "PROFESSIONAL": "Usa un tono formale, professionale e ben strutturato. Evita slang.",
        "CREATIVE": "Sii creativo, usa un linguaggio vivace e coinvolgente. Se opportuno, usa metafore.",
        "CONCISE": "Rispondi in modo estremamente sintetico e diretto. Vai subito al punto senza preamboli.",
        "ACADEMIC": "Usa un tono analitico, tecnico e rigoroso. Struttura la risposta in punti logici se necessario."
    }
    return instructions.get(style, instructions["PROFESSIONAL"])

