"""Panneaux terminal en lecture seule ; aucune dépendance hors bibliothèque standard."""

import json
import os
import sys
import threading
import time
import unicodedata


def snapshot(output, mode):
    """Projette les preuves disponibles sans compter deux fois une réponse modèle."""

    # seules les lignes complètes entrent dans les compteurs
    try:
        raw = (output / "events.jsonl").read_bytes()
    except FileNotFoundError:
        raw = b""
    lines = raw.split(b"\n")
    events = [json.loads(line) for line in lines[:-1]]
    notice = "fragment JSONL en attente" if lines[-1] else ""
    try:
        report = json.loads((output / "result.json").read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        report = {}

    # bridge porte l'usage ; engine répète le candidat, sans nouvel appel
    payloads = [event["payload"] for event in events]
    calls = [payload for payload in payloads if "endpoint" in payload]
    engine = [payload for payload in payloads if payload.get("scope") == "engine"]
    started = [payload for payload in engine if payload.get("operation") == "running"]
    done = [payload for payload in engine if payload.get("operation") == "candidate_response"]
    tools = [event for event in events if event["type"] == "tool_activity"]
    receipts = [event for event in events if event["type"] == "validation"]
    tokens = {}
    for key in ("prompt_tokens", "completion_tokens", "total_tokens"):
        measured = [call.get("usage", {}).get(key) for call in calls]
        known = [value for value in measured if isinstance(value, int)]
        tokens[key] = sum(known) if known else None
        if known and len(known) != len(calls):
            notice = "usage partiel : certains appels sans mesure"

    # progression et activités proviennent des événements, jamais d'une minuterie
    step = "Préparation du scénario" if mode == "selftest" else "Sonde de capacité Ollama"
    node = "—"
    detail = ""
    for payload in engine:
        node = payload.get("node_id", node)
        operation = payload.get("operation")
        step = {
            "running": "Génération du candidat en cours",
            "candidate_response": "Vérification du candidat",
            "passed": "Validation attestée par reçu",
            "blocked": "Tentative bloquée",
            "budget_limited": "Budget de tentative épuisé",
        }.get(operation, operation or step)
        detail = payload.get("detail", "")
    if report:
        step = report.get("status") or report.get("error") or "Sonde terminée"
        detail = report.get("detail") or report.get("cause") or detail
    recent = []
    for event in events[-8:]:
        payload = event["payload"]
        label = payload.get("operation") or payload.get("outcome") or event["type"]
        subject = payload.get("function_name") or payload.get("node_id") or ""
        recent.append(f"#{event.get('event_id', '?')}  {label}  {subject}")
    gates = list(output.glob("invariant-*/result.json"))

    return {
        "step": step,
        "node": node,
        "detail": detail,
        "calls": len(calls),
        "model": calls[-1].get("model", "—") if calls else "en attente de trace",
        "tokens": tokens,
        "turns_started": len(started),
        "turns_done": len(done),
        "tools": len(tools),
        "receipts": len(receipts),
        "gates": len(gates),
        "recent": recent,
        "notice": notice,
        "report": report,
    }


def _fit(value, width):
    """Borne en colonnes terminal et neutralise les contrôles issus des traces."""

    result = []
    used = 0
    for character in str(value):
        if not character.isprintable():
            character = " "
        size = 0 if unicodedata.combining(character) else 1
        if unicodedata.east_asian_width(character) in ("W", "F"):
            size = 2
        if used + size > width:
            break
        result.append(character)
        used += size

    return "".join(result) + " " * (width - used)


def _panel(title, content, width, height):
    label = f" {title} "
    top = "┌" + label + "─" * (width - len(label) - 2) + "┐"
    lines = [top]
    for index in range(height - 2):
        value = content[index] if index < len(content) else ""
        lines.append("│ " + _fit(value, width - 4) + " │")
    lines.append("└" + "─" * (width - 2) + "┘")

    return lines


def frame(args, output, state, elapsed, width, height):
    """Construit quatre blocs fixes, ou un suivi compact pour un petit terminal."""

    # identité et mesures absentes explicitement distinguées de zéro
    scenario = getattr(args, "case", "")
    repo = getattr(args, "repo", output / "workspace")
    budget = "Sonde : limite propre de 60 s"
    if args.mode == "trial":
        budget = f"Budget tentative : {args.seconds:g} s"
    elif args.mode == "selftest":
        budget = "Bridge/Git simulés"
    project = [
        f"Banc audio · {args.mode} {scenario}",
        f"Dépôt : {repo}" if args.mode != "probe" else "Admission du modèle local",
        "Cible : clamp_level · projection [0, 1]" if args.mode != "probe" else "Critère structuré · JSON strict",
        f"Run : {output.name}",
        f"Preuves : {output}",
        budget,
    ]
    tokens = {}
    for key, value in state["tokens"].items():
        tokens[key] = "n/d" if value is None else f"{value:,}"
    inference = [
        "Modèle scénarisé" if args.mode == "selftest" else state["model"],
        f"Appels modèle journalisés : {state['calls']}",
        f"Tokens in/out : {tokens['prompt_tokens']} / {tokens['completion_tokens']}",
        f"Tokens total : {tokens['total_tokens']}",
        f"Tours : {state['turns_done']} reçus / {state['turns_started']} lancés",
        "Usage à réception · pas de streaming",
    ]
    report = state["report"]
    evidence = f"Outils : {state['tools']} · invariants exécutés : {state['gates']} · reçus : {state['receipts']}"
    effect = state["notice"]
    if "restored" in report:
        effect = "Octets initiaux retrouvés" if report["restored"] else "Fichier modifié · voir result.json"
    current = [
        state["step"],
        f"Nœud : {state['node']} · {state['detail']}",
        "Tool calls modèle : non utilisés (réponse JSON stricte)",
        evidence,
        effect,
        "Selftest conforme au scénario" if report.get("checks_passed") else "",
    ]
    pulse = "|/-\\"[int(elapsed * 4) % 4]
    header = f" PITHOS / RELOADED  {pulse}  {elapsed:7.1f} s"
    footer = " Ctrl+C : interrompre · preuves conservées · JSON final à la sortie"
    if width < 60 or height < 22:
        compact = [header, state["step"], inference[4], evidence, "Agrandir à 60 × 22 pour les panneaux", footer]
        lines = (compact + [""] * height)[:height]

        return [_fit(line, width) for line in lines]

    # panneaux fixes ; seul leur contenu évolue, leur largeur suit le terminal
    left_width = width // 2
    left = _panel("Projet", project, left_width, 8)
    right = _panel("Inférence", inference, width - left_width, 8)
    lines = [_fit(header, width)]
    lines.extend(first + second for first, second in zip(left, right))
    lines.extend(_panel("Travail actuel", current, width, 8))
    recent_height = height - 18
    recent = state["recent"][-(recent_height - 2):] or ["En attente d'événements durables…"]
    lines.extend(_panel("Activité récente", recent, width, recent_height))
    lines.append(_fit(footer, width))

    return lines


class Dashboard:
    """Rafraîchit l'écran en arrière-plan ; le run garde son thread et ses transactions."""

    def __init__(self, args, output, *, stream=None):
        self.args = args
        self.output = output
        self.stream = sys.stdout if stream is None else stream
        self.enabled = self.stream.isatty() and os.environ.get("TERM", "dumb") != "dumb"
        self.stop = threading.Event()
        self.thread = None
        self.started = time.monotonic()
        self.error = ""

    def draw(self):
        # la taille du terminal est relue à chaque frame, y compris après resize
        try:
            size = os.get_terminal_size(self.stream.fileno())
        except (OSError, ValueError):
            size = os.terminal_size((80, 24))
        state = snapshot(self.output, self.args.mode)
        elapsed = time.monotonic() - self.started
        lines = frame(self.args, self.output, state, elapsed, max(1, size.columns - 1), max(1, size.lines))
        content = "\x1b[H" + "\r\n".join(lines)
        self.stream.write(content)
        self.stream.flush()

        return state

    def refresh(self):
        while not self.stop.wait(0.2):
            try:
                self.draw()
            except (OSError, ValueError, KeyError, TypeError) as error:
                self.error = f"TUI : {type(error).__name__}: {error}"
                break

    def __enter__(self):
        if not self.enabled:
            return self
        try:
            self.stream.write("\x1b[?1049h\x1b[?25l\x1b[2J")
            self.draw()
            self.thread = threading.Thread(target=self.refresh, name="pithos-tui", daemon=True)
            self.thread.start()
        except BaseException:
            self.stream.write("\x1b[?25h\x1b[?1049l")
            self.stream.flush()
            raise

        return self

    def __exit__(self, exc_type, exc, traceback):
        if self.enabled:
            self.stop.set()
            final_state = None
            try:
                self.thread.join()
                if exc_type is None and not self.error:
                    final_state = self.draw()
            except (OSError, ValueError, KeyError, TypeError) as error:
                self.error = f"TUI : {type(error).__name__}: {error}"
            finally:
                self.stream.write("\x1b[?25h\x1b[?1049l")
                self.stream.flush()

            # le dernier usage reste visible même après un run inférieur à une frame
            if self.error:
                print(self.error, file=sys.stderr)
            elif final_state:
                total = final_state["tokens"]["total_tokens"]
                tokens = "n/d" if total is None else str(total)
                summary = (
                    f"Pithos · {final_state['step']} · appels : {final_state['calls']} · "
                    f"tokens : {tokens} · tours reçus : {final_state['turns_done']}"
                )
                print(_fit(summary, len(summary)).rstrip(), file=sys.stderr)

        return False
