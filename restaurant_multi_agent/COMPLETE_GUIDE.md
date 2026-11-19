# COMPLETE GUIDE - Restaurant multi-agent system (Groq) - macOS

## 0. Status in one minute
DONE and checked: 4 separate LLM agents (Manager, Order, Kitchen, Billing) with own prompts/tools/history,
LLM-decided routing, plan-act loops with step cap, shared memory + message log, trace, offline mock fallback,
Groq via the `openai` package (model openai/gpt-oss-120b), 28 offline tests, swimlane diagram (PNG+PDF),
explanation PDF with viva Q&A. On YOUR Mac the real Groq key and tool calling were confirmed, and real runs
routed correctly.
NOT yet confirmed on the live model: the latest fix (VERIFIED RECORD, which stops an agent from claiming it
added dishes it did not add) and the newest prompts. The Streamlit UI has never been run by the author on real
Streamlit: you must try it.
LEFT FOR YOU: install the latest zip -> run tests -> run the real demo -> try the UI -> check results (section 4).

You do NOT need GitHub. This project uses Groq only.

## 1. Get a Groq key (once)
1. https://console.groq.com -> sign up / log in.
2. https://console.groq.com/keys -> Create API Key. Copy it NOW (shown only once, starts with gsk_).

## 2. Fresh install of the LATEST zip (recommended - cleanest)
Download the zip from the chat first. Then open Terminal (Cmd+Space, type Terminal) and paste block A, then B.

### A. Unpack the newest good zip into ~/restaurant_final
```bash
python3 - <<'PYEOF'
import glob, os, shutil, sys, zipfile
zips = sorted(glob.glob(os.path.expanduser('~/Downloads/restaurant_multi_agent*.zip')), key=os.path.getmtime, reverse=True)
good = None
for z in zips:
    try:
        text = zipfile.ZipFile(z).read('restaurant_multi_agent/restaurant/prompts.py').decode()
    except Exception:
        text = ''
    ok = 'VERIFIED RECORD' in text
    print(('LATEST  ' if ok else 'old     ') + os.path.basename(z))
    if ok and good is None:
        good = z
if good is None:
    sys.exit('\nNo latest zip in ~/Downloads. Download the zip again from the chat, then rerun this block.')
tmp = '/tmp/rma_unpack'
shutil.rmtree(tmp, ignore_errors=True)
zipfile.ZipFile(good).extractall(tmp)
dest = os.path.expanduser('~/restaurant_final')
shutil.rmtree(dest, ignore_errors=True)
shutil.copytree(tmp + '/restaurant_multi_agent', dest)
print('\nInstalled', os.path.basename(good), '->', dest)
PYEOF
```

### B. Create the environment, install, add your key
```bash
cd ~/restaurant_final
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
cp .env.example .env
open -e .env
```
In the file that opens, change the line to `GROQ_API_KEY=gsk_yourrealkey` (no quotes, no spaces), save, close.
(If you already have a working .env, you can instead run: `cp ~/Downloads/restaurant_multi_agent/.env ~/restaurant_final/.env`)

## 3. Run everything (always: `cd ~/restaurant_final && source .venv/bin/activate` first)
```bash
python check_groq.py                       # want: Plain chat PASS, Tool calling PASS
python tests/test_offline.py | tail -1     # want: 28/28 passed
python scripts/real_demo.py 2>&1 | tee demo_output.txt     # real Groq, 7 messages, a few minutes
streamlit run app_streamlit.py             # UI at http://localhost:8501 (Ctrl+C to stop; press Enter if it asks for email)
jupyter notebook restaurant_demo.ipynb     # then Run > Run All Cells (Ctrl+C twice to stop the server)
python main.py                             # chat in the terminal (add --mock for offline)
```
Real outputs saved inside a notebook (no browser needed, takes several minutes, prints little):
```bash
jupyter nbconvert --to notebook --execute restaurant_demo.ipynb --output restaurant_demo_real.ipynb --ExecutePreprocessor.timeout=900
```

## 4. What a correct real run looks like (scripts/real_demo.py)
1. `BRAIN: Groq / openai/gpt-oss-120b` (no orange mock banner).
2. Msg 1: route manager->kitchen, manager->order, manager->kitchen; reply mentions "without onion" and ~17 minutes.
3. Msg 3 "Is the dal makhani available?": answered directly (out of stock, Dal Tadka suggested). No "which table?".
4. Msg 4 (table 2): butter naan added; dal makhani NOT added; Dal Tadka offered.
5. Msg 5 (table 5): all four dishes in FINAL MEMORY.
6. Bill table 4: Rs.577.50, no discount. Bill table 5: 10% discount, total Rs.1,115.10.
7. No "[ERROR]" / "[STEP CAP]". Replies have no ** asterisks.
If any item is wrong, that is a real finding: copy the output and ask for help (see section 7).

## 5. Using the UI
Green LIVE badge = real Groq. Orange OFFLINE MOCK = stand-in, not the real LLM.
Sidebar: paste key (optional), model, Test connection, Reset session. Click example messages in order.
Right side tabs: Manager / Order / Kitchen / Billing (each agent's actions), Restaurant board, Full trace.

## 6. Troubleshooting
| You see | Fix |
|---|---|
| `No GROQ_API_KEY found` | .env missing / placeholder still there / not in the project folder. Redo 2B. |
| 401 / 403 | Wrong or revoked key. Create a new one; paste without quotes or spaces. |
| 404 | Model not on your account: `GROQ_MODEL=openai/gpt-oss-120b` (or openai/gpt-oss-20b) in .env. NOT llama-3.3-70b-versatile (Enterprise-only). |
| 429 | Free-tier rate limit. Wait a minute; the code retries. |
| `No module named openai` | `source .venv/bin/activate` then `pip install -r requirements.txt`. |
| "No latest zip" in 2A | Download the zip again from the chat (file card), rerun 2A. |
| `head` prints a URL usage message | Your Mac's `head` is a different tool. Do not use `head`; use the Python blocks here. |
| Notebook "Kernel Connecting" forever | Close ALL localhost:8888 tabs, stop old Jupyter (Ctrl+C), restart it; or use the nbconvert command. |
| Notebook says "not trusted" | Harmless. Click Trust or just Run All. |
| Notebook/UI says MOCK BRAIN | Key not found: check .env in the project folder; start from the project folder. |
| Browser downloads "zip (1)", "(2)"... | Normal. 2A picks the newest one that really contains the latest code. |

## 7. If you are stuck (no helper available)
Keep these three outputs; they contain everything needed to diagnose:
`python check_groq.py` ; `python tests/test_offline.py | tail -15` ; `python scripts/real_demo.py 2>&1 | tee demo_output.txt`
The viva material is in docs/explanation.pdf. The diagram is docs/swimlane_data_flow.png/.pdf.

## 8. Before you submit
- Do NOT hand in `.env` (your key) or the `.venv` folder. Zip without them, from the folder above the project:
  `zip -r submission.zip restaurant_final -x "restaurant_final/.env" "restaurant_final/.venv/*" "*/__pycache__/*"`
- If your assignment names specific providers, tell your instructor you used Groq.

## 9. Honest limits
Memory is in RAM only (resets on restart). Agent histories grow each turn. Kitchen time is a simple formula.
If the table number is missing the manager may reuse the last table in the conversation. One customer at a time.
Live model behaviour can vary run to run. Real Streamlit and the latest fixes were not tested by the author on a live model.

## 10. Files
restaurant/ (config, menu, memory, trace, tools, prompts, llm, mock_brain, ui_helpers, system, agents/*),
main.py, app_streamlit.py, check_groq.py, restaurant_demo.ipynb, tests/test_offline.py,
scripts/ (real_demo, build_notebook, make_diagram, make_explanation_pdf), docs/ (diagram PNG+PDF, explanation PDF).
