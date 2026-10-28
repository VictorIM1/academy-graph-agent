from __future__ import annotations

import json
import math
import random
import struct
import wave
from datetime import datetime, timedelta
from pathlib import Path

from fpdf import FPDF
from fpdf.enums import XPos, YPos
from PIL import Image, ImageDraw

from src.memory.outcome_store import OutcomeStore

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
HERO_DIR = DATA_DIR / "hero_cases"


def _write_json(path: Path, payload: dict | list) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _create_pdf(path: Path, title: str, lines: list[str]) -> None:
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, title, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("Helvetica", size=12)
    for line in lines:
        pdf.multi_cell(180, 8, line, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.output(str(path))


def _create_audio_wav(path: Path, duration_seconds: int = 5, sample_rate: int = 16000) -> None:
    amplitude = 12000
    frequency = 220
    frame_count = duration_seconds * sample_rate

    with wave.open(str(path), "w") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)

        for i in range(frame_count):
            t = i / sample_rate
            envelope = min(1.0, i / (sample_rate * 0.3)) * min(1.0, (frame_count - i) / (sample_rate * 0.3))
            sample = int(amplitude * envelope * math.sin(2 * math.pi * frequency * t))
            wav_file.writeframes(struct.pack("<h", sample))


def _create_tactics_image(path: Path) -> None:
    img = Image.new("RGB", (1200, 700), color=(18, 90, 50))
    draw = ImageDraw.Draw(img)

    draw.rectangle((40, 40, 1160, 660), outline=(230, 230, 230), width=5)
    draw.line((600, 40, 600, 660), fill=(230, 230, 230), width=4)
    draw.ellipse((525, 285, 675, 435), outline=(230, 230, 230), width=4)

    for x in range(180, 1000, 160):
        draw.ellipse((x, 180, x + 20, 200), fill=(255, 255, 255))
        draw.line((x + 10, 200, x + 70, 260), fill=(255, 210, 0), width=5)

    draw.text((90, 70), "U17 Overlapping Wing High-Intensity Repeat Sprints (12x40m)", fill=(255, 240, 240))
    img.save(path)


def _create_match_report_image(path: Path) -> None:
    img = Image.new("RGB", (1100, 680), color=(245, 245, 245))
    draw = ImageDraw.Draw(img)

    draw.rectangle((60, 60, 1040, 620), outline=(0, 0, 0), width=4)
    draw.text((90, 100), "ACADEMY MATCH REPORT", fill=(0, 0, 0))
    draw.text((90, 180), "Player: Andrei P. | U14 Striker", fill=(0, 0, 0))
    draw.text((90, 250), "5 Goals, 2 Assists in Last 3 Matches - Top Rating 9.2", fill=(10, 70, 10))
    draw.text((90, 320), "Coach Notes: Excellent finishing and movement in half-spaces.", fill=(0, 0, 0))
    draw.text((90, 390), "Recommendation: Advanced development pathway", fill=(0, 0, 0))
    img.save(path)


def _build_roster() -> list[dict]:
    random.seed(42)
    first_names = [
        "Andrei", "Matei", "Luca", "Radu", "Darius", "Stefan", "Vlad", "Mihai", "Paul", "Ionut",
        "Cristian", "Alex", "Tudor", "Denis", "Bogdan", "Raul", "Robert", "David", "Sorin", "Petru",
    ]
    last_names = [
        "Popescu", "Ionescu", "Marin", "Dumitrescu", "Stan", "Gheorghe", "Nita", "Mocanu", "Ilie", "Petrescu",
        "Ciobanu", "Toma", "Dragomir", "Dobre", "Munteanu", "Pavel", "Balan", "Enache", "Nistor", "Filip",
    ]
    squads = [
        ("U14", "Coach Alin Georgescu"),
        ("U16", "Coach Andrei Popa"),
        ("U18", "Coach Mihnea Rusu"),
    ]

    roster: list[dict] = []
    idx = 1
    for squad, coach in squads:
        for _ in range(15):
            first = first_names[(idx * 3) % len(first_names)]
            last = last_names[(idx * 7) % len(last_names)]
            player_name = f"{first} {last}"
            attendance = random.randint(68, 99)
            status = "paid" if random.random() > 0.2 else "overdue"
            roster.append(
                {
                    "player_id": f"P{idx:03d}",
                    "player_name": player_name,
                    "squad": squad,
                    "attendance_pct": attendance,
                    "monthly_tuition_ron": 450,
                    "tuition_status": status,
                    "coach": coach,
                    "parent_name": f"{random.choice(['Elena', 'Cristi', 'Ioana', 'Marius', 'Ana', 'Violeta'])} {last}",
                }
            )
            idx += 1

    return roster


def _create_case_1(case_dir: Path) -> None:
    case_dir.mkdir(parents=True, exist_ok=True)

    _create_pdf(
        case_dir / "invoice_1042.pdf",
        "Academy Tuition Invoice #1042",
        [
            "Player: Luca M. (U15 Midfielder)",
            "Billed to: Elena M.",
            "Amount Due: 450 RON",
            "Status: 14 Days Overdue",
            f"Issued: {(datetime.now() - timedelta(days=14)).strftime('%Y-%m-%d')}",
        ],
    )

    _create_audio_wav(case_dir / "coach_voice_note.wav")

    _write_json(
        case_dir / "coach_voice_note_transcript.json",
        {
            "speaker": "Coach Andrei",
            "transcript": "Luca skipped Thursday's training again. On Tuesday his head was down the whole rondo, zero confidence since sitting on the bench Sunday.",
        },
    )

    _write_json(
        case_dir / "whatsapp_parent.json",
        {
            "from": "Elena M.",
            "message": "Bună ziua, nu știu dacă mai are rost să venim luna viitoare, Luca e tot mai demotivat după ce a stat pe bancă tot meciul de duminică.",
            "channel": "WhatsApp",
        },
    )

    _write_json(
        case_dir / "attendance_log.json",
        {
            "player": "Luca M.",
            "last_4_sessions": ["missed", "missed", "attended", "missed"],
            "summary": "Missed 3 of last 4 sessions",
        },
    )


def _create_case_2(case_dir: Path) -> None:
    case_dir.mkdir(parents=True, exist_ok=True)

    _create_pdf(
        case_dir / "medical_clearance.pdf",
        "Medical Clearance Report",
        [
            "Player: Matei D. (U17 Winger)",
            "Cleared 3 weeks ago from Grade 1 right hamstring strain.",
            "Caution advised on high-speed sprint volume.",
            "Progressive load monitoring mandatory.",
        ],
    )

    _create_tactics_image(case_dir / "whiteboard_tactics.png")

    _write_json(
        case_dir / "whatsapp_coach.json",
        {
            "from": "Coach Andrei Popa",
            "message": "Matei looked stiff in the final 15 minutes of Tuesday's drill.",
            "channel": "WhatsApp",
        },
    )


def _create_case_3(case_dir: Path) -> None:
    case_dir.mkdir(parents=True, exist_ok=True)
    _create_match_report_image(case_dir / "match_report.png")

    _write_json(
        case_dir / "whatsapp_parent.json",
        {
            "from": "Cristi P.",
            "message": "Salutare! Andrei vrea să lucreze suplimentar finalizarea cu piciorul stâng, aveți grupe de performanță sau antrenamente individuale?",
            "channel": "WhatsApp",
        },
    )


def _cached_extractions() -> dict:
    return {
        "case_1_luca": {
            "player_id": "case_1_luca",
            "player_name": "Luca M.",
            "squad": "U15",
            "signals": [
                {
                    "source_modality": "pdf",
                    "source_file": "invoice_1042.pdf",
                    "entity_type": "payment",
                    "summary": "Invoice #1042 for 450 RON is 14 days overdue.",
                    "severity_score": 0.78,
                    "target_node": "Invoice #1042",
                    "edge_label": "unpaid_invoice",
                },
                {
                    "source_modality": "audio",
                    "source_file": "coach_voice_note.wav",
                    "entity_type": "concern",
                    "summary": "Coach reports low confidence and bench-related morale drop.",
                    "severity_score": 0.84,
                    "target_node": "Low Morale",
                    "edge_label": "low_morale",
                },
                {
                    "source_modality": "text",
                    "source_file": "attendance_log.json",
                    "entity_type": "attendance",
                    "summary": "Missed 3 of last 4 sessions.",
                    "severity_score": 0.81,
                    "target_node": "Attendance Pattern",
                    "edge_label": "missed",
                },
                {
                    "source_modality": "text",
                    "source_file": "whatsapp_parent.json",
                    "entity_type": "concern",
                    "summary": "Parent expresses frustration and intent to stop attendance next month.",
                    "severity_score": 0.91,
                    "target_node": "Parent Frustration",
                    "edge_label": "expressed_frustration",
                },
            ],
            "risk_profile": {
                "dropout_risk": 89,
                "injury_load_risk": 28,
                "development_opportunity": 46,
                "parent_engagement_risk": 72,
                "collection_risk": 78,
            },
            "guardrail": {
                "triggered": True,
                "rule_name": "Anti-Stupid Billing Guardrail",
                "suppressed_action": "Suppress automated invoice chasing for 5 days",
                "reasoning_path": [
                    "[Audio: Low Confidence]",
                    "[Log: 3 Missed Sessions]",
                    "[WhatsApp: Parent Frustrated]",
                    "[Guardrail: Suppress Invoice Chaser]",
                ],
            },
            "interventions": [
                {
                    "channel": "Coach_Task",
                    "recipient": "Coach Andrei",
                    "subject_or_task": "1-on-1 confidence check-in before next training",
                    "draft_message": "Discută empatic cu Luca despre minutele de joc și setează un obiectiv pozitiv pentru sesiunea următoare.",
                    "priority": "CRITICAL",
                },
                {
                    "channel": "WhatsApp_Parent",
                    "recipient": "Elena M.",
                    "subject_or_task": "Parent reassurance and retention outreach",
                    "draft_message": "Bună ziua, Elena! Înțelegem perfect îngrijorarea. Coach Andrei va avea azi o discuție individuală cu Luca pentru a-l sprijini. Vă ținem la curent și vă mulțumim pentru încredere.",
                    "priority": "HIGH",
                },
                {
                    "channel": "Billing_Hold",
                    "recipient": "Finance Ops",
                    "subject_or_task": "Pause automated collection for 5 days",
                    "draft_message": "Aplicați hold de 5 zile la invoice #1042 până după contactul empatic al antrenorului.",
                    "priority": "HIGH",
                },
            ],
            "similar_past_case": {
                "episode_id": "EP-001",
                "pattern": "Coach check-in before billing reminder",
                "retention_rate": "92%",
            },
        },
        "case_2_matei": {
            "player_id": "case_2_matei",
            "player_name": "Matei D.",
            "squad": "U17",
            "signals": [
                {
                    "source_modality": "pdf",
                    "source_file": "medical_clearance.pdf",
                    "entity_type": "injury",
                    "summary": "Recently cleared from grade 1 right hamstring strain with caution on sprint volume.",
                    "severity_score": 0.87,
                    "target_node": "Recent Hamstring Injury",
                    "edge_label": "recent_hamstring_injury",
                },
                {
                    "source_modality": "image",
                    "source_file": "whiteboard_tactics.png",
                    "entity_type": "injury",
                    "summary": "Whiteboard plan includes high-intensity repeat sprints (12x40m).",
                    "severity_score": 0.83,
                    "target_node": "High Sprint Tactical Load",
                    "edge_label": "high_sprint_tactical_load",
                },
                {
                    "source_modality": "text",
                    "source_file": "whatsapp_coach.json",
                    "entity_type": "concern",
                    "summary": "Coach observed stiffness in final 15 minutes.",
                    "severity_score": 0.72,
                    "target_node": "Late Drill Stiffness",
                    "edge_label": "reported_concern",
                },
            ],
            "risk_profile": {
                "dropout_risk": 22,
                "injury_load_risk": 86,
                "development_opportunity": 58,
                "parent_engagement_risk": 30,
                "collection_risk": 12,
            },
            "guardrail": {
                "triggered": True,
                "rule_name": "Load Protection Guardrail",
                "suppressed_action": "Cap sprint load by 35% and alert parent proactively",
                "reasoning_path": [
                    "[Medical PDF: Recent Hamstring Injury]",
                    "[Whiteboard: Repeat Sprints 12x40m]",
                    "[Coach Note: Stiffness]",
                    "[Guardrail: Reduce Load 35%]",
                ],
            },
            "interventions": [
                {
                    "channel": "Training_Modification",
                    "recipient": "U17 Staff",
                    "subject_or_task": "Reduce high-speed sprint exposure by 35%",
                    "draft_message": "Ajustați microciclul pentru Matei: scădere volum sprinturi și monitorizare RPE post-sesiune.",
                    "priority": "CRITICAL",
                },
                {
                    "channel": "WhatsApp_Parent",
                    "recipient": "Parent Matei D.",
                    "subject_or_task": "Proactive injury-load update",
                    "draft_message": "Salut! Pentru siguranța lui Matei, ajustăm încărcarea de sprint în această săptămână și monitorizăm atent evoluția.",
                    "priority": "HIGH",
                },
            ],
            "similar_past_case": {
                "episode_id": "EP-003",
                "pattern": "Load cap and proactive parent messaging",
                "injury_reduction": "53%",
            },
        },
        "case_3_andrei": {
            "player_id": "case_3_andrei",
            "player_name": "Andrei P.",
            "squad": "U14",
            "signals": [
                {
                    "source_modality": "image",
                    "source_file": "match_report.png",
                    "entity_type": "opportunity",
                    "summary": "5 goals and 2 assists in last 3 matches with top rating 9.2.",
                    "severity_score": 0.88,
                    "target_node": "High Match Performance",
                    "edge_label": "high_match_performance",
                },
                {
                    "source_modality": "text",
                    "source_file": "whatsapp_parent.json",
                    "entity_type": "opportunity",
                    "summary": "Parent inquiry about advanced groups and 1-on-1 finishing sessions.",
                    "severity_score": 0.79,
                    "target_node": "Parent Inquiry",
                    "edge_label": "parent_inquiry",
                },
            ],
            "risk_profile": {
                "dropout_risk": 16,
                "injury_load_risk": 20,
                "development_opportunity": 80,
                "parent_engagement_risk": 24,
                "collection_risk": 8,
            },
            "guardrail": {
                "triggered": True,
                "rule_name": "Retention & Upsell Trigger",
                "suppressed_action": "Trigger U16 Shadow Invite + Paid 1-on-1 Striker Clinic Offer",
                "reasoning_path": [
                    "[Match Report: Elite Form]",
                    "[WhatsApp: Development Request]",
                    "[Guardrail: Offer Premium Pathway]",
                ],
            },
            "interventions": [
                {
                    "channel": "WhatsApp_Parent",
                    "recipient": "Cristi P.",
                    "subject_or_task": "Invite to advanced striker pathway",
                    "draft_message": "Salutare! Avem grupe de performanță și clinică individuală de finalizare. Îl invităm pe Andrei și la un shadow session cu U16.",
                    "priority": "HIGH",
                },
                {
                    "channel": "Coach_Task",
                    "recipient": "U14 Head Coach",
                    "subject_or_task": "Nominate for U16 shadow training",
                    "draft_message": "Programează pentru Andrei un shadow session U16 și plan de obiective tehnice pe piciorul stâng.",
                    "priority": "MEDIUM",
                },
            ],
            "similar_past_case": {
                "episode_id": "EP-004",
                "pattern": "Upsell pathway after parent inquiry",
                "conversion_rate": "88%",
            },
        },
    }


def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    HERO_DIR.mkdir(parents=True, exist_ok=True)

    roster = _build_roster()
    _write_json(DATA_DIR / "baseline_roster.json", roster)

    _create_case_1(HERO_DIR / "case_1_luca")
    _create_case_2(HERO_DIR / "case_2_matei")
    _create_case_3(HERO_DIR / "case_3_andrei")

    _write_json(DATA_DIR / "cached_extractions.json", _cached_extractions())

    store = OutcomeStore(DATA_DIR / "outcomes.db")
    store.seed_default_episodes()

    print("Synthetic data generated successfully in ./data")


if __name__ == "__main__":
    main()
