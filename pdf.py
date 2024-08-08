from pathlib import Path

import pymupdf


def parse_multiline_pdf_block(text: str) -> str:
    lines = text.split("  \n")
    return "\n".join([line.replace(" \n", " ") for line in lines])


def parse(text: str) -> dict:
    minor = {
        "code": text.split("\n")[0].strip(),
        "title": text.split("\n")[1].strip(),
        "cm_hours": int(text.split("CM \n")[1].split("h \n")[0] or 0),
        "td_hours": int(text.split("TD \n")[1].split("h \n")[0] or 0),
        "hne_hours": int(text.split("HNE \n")[1].split("h \n")[0] or 0),
        "availability": {},
        "in_charge": text.split("Responsable /  In charge of : ")[1].split(" (")[0].strip(),
        "email": text.split("Responsable /  In charge of : ")[1].split(" (")[1].split(")")[0].strip().lower(),
        "abstract": text.split("Résumé / Abstract :")[1].split("Prérequis / Prerequisite :")[0],
        "objective": text.split("Objectifs / Objectives :")[1].split("Contenu / Contents :")[0],
        "content": text.split("Contenu / Contents :")[1].split("Références / References : ")[0],
        "references": text.split("Références / References : ")[1].split("Acquis / Knowledge : ")[0],
        "knowledge": text.split("Acquis / Knowledge : ")[1].split("Evaluation / Assessment : ")[0],
        "assessment": text.split("Evaluation / Assessment : ")[1].split("Bibliographie / Bibliography : ")[0],
    }

    # split after "Cours proposé dans la mineure / Course offered in the minor :" and before "Responsable /  In charge of :"
    av = text.split("Cours proposé dans la mineure / Course offered in the minor : \n")[1].split(
        "Responsable /  In charge of :")[0].split(" \n")

    m_count = len([a for a in av if len(a) > 2])

    for i in range(0, m_count + 1):
        minor["availability"][av[i].strip()] = "X" in av[i + m_count + 1]

    return minor


def get_parsed_pdf() -> dict:
    minors = []

    pdf_document = pymupdf.open("syll.pdf")

    merged_page = ""

    for page_num in range(pdf_document.page_count):
        page = pdf_document.load_page(page_num)
        text = page.get_text("text")

        if "Cours proposé dans la mineure / Course offered in the minor :" in text:
            if merged_page:
                Path("output").mkdir(exist_ok=True)
                Path(f"output/{parse(merged_page)['title']}.txt").write_text(merged_page)
                minors.append(parse(merged_page))

            merged_page = text
        else:
            merged_page += text

    pdf_document.close()

    return minors


friends = {
    "Mélanie": "CyberSec",
    "Maxime": "CyberSec",
    "Karim": "IHM",
    "Damien": "IHM",
    "Nina": "IHM",
    "Michel": "IHM",
    "Yvann": "SSE",
    "Raphaël": "IF",
    "Apoorva": "SSE",
    "Tom": "CyberSec",
    "Marc Pinet": "IA-ID",
    "Simon": "CyberSec",
    "Tu": "IHM",
    "Cremy": "SSE",
    "Amir": "IHM",
    "Anas": "IHM",
    "Arnaud Dumanois": "CyberSec",
    "Arnaud Avocat Gros": "SSE",
    "Samuel": "SSE",
    "Alexis": "SSE",
    "Julien Didier": "SSE",
    "Benjamin": "SSE",
    "Axel": "SSE",
    "Carla": "SSE",
    "Manu": "SSE",
    "Lamya": "SSE",
    "Lucie": "IHM",
    "Saad": "IHM",
    "Clervie": "IHM",
    "Marcus": "IHM",
    "Wassim": "IHM",
    "Amandine": "CyberSec",
    "Arthur": "IA-ID",
    "Julien Soto": "IoT-CPS",
    "Nicolas": "IoT-CPS",
    "Nikan": "IF",
    "Timothé": "IA-ID",
}

if __name__ == "__main__":
    print(get_parsed_pdf())
