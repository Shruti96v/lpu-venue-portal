"""
Draws docs/swimlane_data_flow.png and .pdf  (one lane per agent + a shared-memory lane).
Needs matplotlib:   pip install -r requirements-docs.txt
Run from the project folder:   python scripts/make_diagram.py
"""
import textwrap
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

OUT = Path(__file__).resolve().parent.parent / "docs"
LANES = ["Customer", "Manager agent", "Order agent", "Kitchen agent", "Billing agent", "Shared memory"]
COLORS = ["#e5e7eb", "#bfdbfe", "#bbf7d0", "#fed7aa", "#ddd6fe", "#fef08a"]
EDGE = ["#6b7280", "#2563eb", "#16a34a", "#ea580c", "#7c3aed", "#ca8a04"]
W, LANE_W, X0 = 17.0, 2.75, 0.25
CX = [X0 + LANE_W * (i + 0.5) for i in range(len(LANES))]
BOX_W = 2.45
WRAP = 27
MEM = 5

# Each step: (lane index, text, [memory note, mode], label on the arrow that comes INTO this box, failure?)
# A "band" is a phase title across the whole diagram.
STEPS = [
 ("band", "PHASE 1 - Customer places an order:  \"Table 4 wants 2 paneer tikka and 1 butter naan, one without onion\""),
 (0, "Types a natural-language message", None, None, False),
 (1, "Writes the message to the message log.\nLLM call #1 (manager prompt, tool: hand_off) DECIDES the route.\nIt chooses: ask the kitchen first.", ["WRITE message_log", "w"], "customer message", False),
 (3, "Receives the request as a message.\nOwn LLM loop (kitchen prompt):\nstep 1: check_stock('Paneer Tikka'), check_stock('Butter Naan')\nstep 2: no more tools -> writes answer", ["READ stock", "r"], "HANDOFF manager -> kitchen\n(message in the log)", False),
 (1, "LLM call #2 reads the kitchen's answer: both dishes available.\nDecides: now ask the order agent.", ["WRITE message_log (answer)", "w"], "HANDOFF BACK kitchen -> manager", False),
 (2, "Receives self-contained request.\nOwn LLM loop (order prompt):\nstep 1: add_item x2  (note = 'without onion')\nstep 2: get_order(4) to confirm\nstep 3: writes answer", ["WRITE orders[4]\nWRITE stock (minus qty)", "w"], "HANDOFF manager -> order", False),
 (1, "LLM call #3 reads the order agent's answer.\nDecides: ask kitchen for the waiting time.", ["WRITE message_log (answer)", "w"], "HANDOFF BACK order -> manager", False),
 (3, "Own LLM loop:\nstep 1: estimate_time(4)\nstep 2: writes answer ('about 17 minutes')", ["READ orders[4]", "r"], "HANDOFF manager -> kitchen", False),
 (1, "Final LLM call combines the three answers into ONE friendly reply, with no mention of agents or tools.", ["WRITE message_log (reply)", "w"], "HANDOFF BACK kitchen -> manager", False),
 (0, "Reads one reply from 'a single staff member'", None, "REPLY manager -> customer", False),

 ("band", "PHASE 2 - Customer asks for the bill:  \"Give me the bill for table 4\""),
 (0, "Types a message that names the table", None, None, False),
 (1, "LLM call #1 DECIDES: this is a billing job.\nSends a self-contained request.", ["WRITE message_log", "w"], "customer message", False),
 (4, "Own LLM loop (billing prompt):\nstep 1: apply_discount(4)\n   -> the TOOL checks subtotal >= Rs.1000 (here 550, so NOT applied)\nstep 2: compute_bill(4, tax 5%)\nstep 3: writes answer with the numbers", ["READ orders[4]\nWRITE bills[4] = prepared", "rw"], "HANDOFF manager -> billing", False),
 (1, "Final LLM call turns the billing answer into a polite reply and quotes the numbers exactly.", ["WRITE message_log (reply)", "w"], "HANDOFF BACK billing -> manager", False),
 (0, "Receives the bill: total Rs.577.50", None, "REPLY manager -> customer", False),

 ("band", "WHEN SOMETHING GOES WRONG - each failure stays inside one lane (dashed red boxes)"),
 (3, "Kitchen's LLM call fails (network, rate limit).\nGroqLLM retries 3 times, then raises.\nreceive() catches it and answers:\n'[kitchen agent is unavailable]'", None, None, True),
 (1, "Manager reads that message like any other answer and tells the customer honestly.\nThe system keeps running; other agents are unaffected.", ["trace: ERROR event\nmessage_log keeps the failure", "w"], "failure answer returns as a normal message", True),
 (2, "Tool refuses a bad request, e.g. add_item for an out-of-stock dish or unknown dish name.\nIt returns {ok: false, error, suggestions} and the LLM reads it and adapts.", ["stock never goes negative", "r"], None, True),
 (4, "Agent keeps calling tools forever? The loop stops at the STEP CAP (6 for specialists, 8 for manager) and returns partial results.", ["trace: STEP CAP event", "w"], None, True),
]
LEGEND = [("solid", "#1f2937", "Hand-off message between agents (also written to the message log)"),
          ("dashed", "#92400e", "Read / write of the shared memory by a tool"),
          ("dashed", "#dc2626", "Failure path (stays inside one agent)")]


def box_height(text):
    lines = sum(len(textwrap.wrap(p, WRAP)) or 1 for p in text.split("\n"))
    return 0.27 * lines + 0.36


def layout():
    """first pass: y measured downward from the top; returns items with positions and total height."""
    y, placed = 2.2, []                                   # space for the title + lane headers
    for step in STEPS:
        if step[0] == "band":
            y += 0.25
            placed.append(("band", step[1], y + 0.28)); y += 0.85
            continue
        lane, text, mem, label, fail = step
        h = box_height(text)
        if mem:
            h = max(h, 0.27 * (mem[0].count("\n") + 1) + 0.36)
        gap = 0.2 + (0.5 if label else 0)
        y += gap
        placed.append(("box", step, y + h / 2, h)); y += h
    return placed, y + 2.4                                # room for the legend


def draw():
    placed, total = layout()
    fig, ax = plt.subplots(figsize=(W, total))
    ax.set_xlim(0, W); ax.set_ylim(0, total); ax.axis("off")
    Y = lambda yy: total - yy                              # flip so 0 is the top

    ax.text(W / 2, Y(0.5), "Restaurant multi-agent system - swimlane data flow", ha="center", fontsize=20, weight="bold")
    ax.text(W / 2, Y(1.0), "One lane per agent. Time flows downward. Every arrow between lanes is a message; every dashed line is a tool touching shared memory.",
            ha="center", fontsize=10, color="#374151")
    # lane backgrounds and headers
    for i, name in enumerate(LANES):
        x = X0 + LANE_W * i
        ax.add_patch(plt.Rectangle((x + 0.04, Y(total - 0.2 + 0) ), LANE_W - 0.08, total - 0.2 - 1.3 + 0.0,
                                   facecolor=COLORS[i], alpha=0.18, edgecolor="none", zorder=0))
        ax.add_patch(FancyBboxPatch((x + 0.12, Y(1.95)), LANE_W - 0.24, 0.6, boxstyle="round,pad=0.02,rounding_size=0.1",
                                    facecolor=COLORS[i], edgecolor=EDGE[i], linewidth=2, zorder=3))
        ax.text(CX[i], Y(1.65), name, ha="center", va="center", fontsize=12, weight="bold", zorder=4)
        ax.plot([CX[i], CX[i]], [Y(2.0), Y(total - 1.9)], color=EDGE[i], linestyle=(0, (4, 4)), linewidth=1, alpha=0.5, zorder=1)

    prev = None                                            # previous box (lane, ycenter, height)
    for item in placed:
        if item[0] == "band":
            _, text, yc = item
            ax.add_patch(FancyBboxPatch((0.3, Y(yc) - 0.28), W - 0.6, 0.56, boxstyle="round,pad=0.02,rounding_size=0.08",
                                        facecolor="#1f2937", edgecolor="none", zorder=5))
            ax.text(W / 2, Y(yc), text, ha="center", va="center", color="white", fontsize=11.5, weight="bold", zorder=6)
            prev = None
            continue
        _, (lane, text, mem, label, fail), yc, h = item
        x = CX[lane]
        ax.add_patch(FancyBboxPatch((x - BOX_W / 2, Y(yc) - h / 2), BOX_W, h, boxstyle="round,pad=0.02,rounding_size=0.1",
                                    facecolor="white", edgecolor="#dc2626" if fail else EDGE[lane],
                                    linewidth=2, linestyle="--" if fail else "-", zorder=4))
        wrapped = "\n".join("\n".join(textwrap.wrap(p, WRAP)) for p in text.split("\n"))
        ax.text(x, Y(yc), wrapped, ha="center", va="center", fontsize=8.6, linespacing=1.3, zorder=5)
        # arrow from the previous box into this one (a hand-off or reply)
        if prev and label:
            pl, pyc, ph = prev
            ax.annotate("", xy=(x, Y(yc) + h / 2), xytext=(CX[pl], Y(pyc) - ph / 2),
                        arrowprops=dict(arrowstyle="-|>", color="#dc2626" if fail else "#1f2937", lw=2,
                                        linestyle="--" if fail else "-", shrinkA=0, shrinkB=0), zorder=3)
            mx, my = (x + CX[pl]) / 2, (Y(yc) + h / 2 + Y(pyc) - ph / 2) / 2
            ax.text(mx, my, label, ha="center", va="center", fontsize=7.8, style="italic", zorder=7,
                    bbox=dict(boxstyle="round,pad=0.2", facecolor="white", edgecolor="#9ca3af", linewidth=0.6))
        # memory note + dashed arrow(s)
        if mem:
            note, mode = mem
            mh = 0.27 * (note.count("\n") + 1) + 0.36
            ax.add_patch(FancyBboxPatch((CX[MEM] - BOX_W / 2, Y(yc) - mh / 2), BOX_W, mh, boxstyle="round,pad=0.02,rounding_size=0.1",
                                        facecolor="#fefce8", edgecolor=EDGE[MEM], linewidth=1.6, zorder=4))
            ax.text(CX[MEM], Y(yc), note, ha="center", va="center", fontsize=8.4, zorder=5)
            style = {"r": "<|-", "w": "-|>", "rw": "<|-|>"}[mode]
            ax.annotate("", xy=(CX[MEM] - BOX_W / 2, Y(yc)), xytext=(x + BOX_W / 2, Y(yc)),
                        arrowprops=dict(arrowstyle=style, color="#92400e", lw=1.6, linestyle=(0, (4, 3)), shrinkA=0, shrinkB=0), zorder=3)
        prev = (lane, yc, h)

    # legend
    ly = 0.9
    for i, (ls, col, txt) in enumerate(LEGEND):
        yy = ly + 0.45 * (len(LEGEND) - 1 - i)
        ax.plot([0.6, 1.5], [yy, yy], color=col, lw=2.2, linestyle="-" if ls == "solid" else (0, (4, 3)))
        ax.text(1.7, yy, txt, va="center", fontsize=9.5)
    return fig


if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    fig = draw()
    fig.savefig(OUT / "swimlane_data_flow.png", dpi=110, bbox_inches="tight", facecolor="white")
    fig.savefig(OUT / "swimlane_data_flow.pdf", bbox_inches="tight", facecolor="white")
    print("Wrote", OUT / "swimlane_data_flow.png", "and .pdf")
