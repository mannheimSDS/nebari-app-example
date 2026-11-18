# Nebari app example

A small web app to deploy on a Nebari cluster. It uses [FastHTML](https://fastht.ml/), keeps its data in SQLite, and runs with [uv](https://docs.astral.sh/uv/). It shows a table of quotes that you can sort, shuffle and filter. The web page only reads the database; nobody on the internet can write to it.

For a React front end, see [nebari-react-app-example](https://github.com/mannheimSDS/nebari-react-app-example).

Use it as a template. Copy it, check that it deploys, then change `main.py` into your own app.

## Deploy it

You need an account on the cluster. Every step runs in your browser.

1. Log in and start a JupyterLab server. The smallest instance is enough.
2. In JupyterLab, open File → New → Terminal and run:

   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh   # installs uv into ~/.local/bin, once
   cd ~
   git clone https://github.com/mannheimSDS/nebari-app-example.git
   cd nebari-app-example
   ~/.local/bin/uv sync                               # creates .venv with the packages
   ```

3. Optional: test the app in the terminal with `~/.local/bin/uv run main.py`. Stop it with Ctrl-C.
4. Go back to the hub home page and click "Deploy App". Fill in:
   - Name: anything, e.g. `My App`
   - Framework: `Custom Command`
   - Custom command, with your username in both places:

     ```
     /home/YOURUSER/.local/bin/uv run --directory /home/YOURUSER/nebari-app-example main.py {port}
     ```

   - Software Environment: leave empty, because uv brings the packages.
   - Sharing: choose public access only if people without an account must see the app.
5. Click Next, choose the smallest Server Type, and deploy. After about 30 seconds the app is live. You can stop, start, edit and delete it from the hub home page.

To ship a change, edit the files in `~/nebari-app-example` (or `git pull`), run `uv sync` if you changed dependencies, then stop and start the app from the hub home page.

## Run it on your own computer

```bash
uv run main.py        # http://localhost:8000
```

## How it works

1. `main.py` is the whole app. On startup it creates the SQLite file `data.db` next to itself and fills it with ten quotes if the table is empty. The file stays there between restarts. It is not committed to git.
2. After startup the app opens the database read-only (`mode=ro`) and has no route that writes. To add or change rows, use a JupyterLab terminal:

   ```bash
   cd ~/nebari-app-example
   python -c "import sqlite3; c = sqlite3.connect('data.db'); c.execute('insert into quotes (text, author, topic) values (?, ?, ?)', ('Hello', 'Me', 'demo')); c.commit()"
   ```

   Reload the page to see the row.
3. The buttons and column headers use HTMX, which comes with FastHTML. Each click fetches a new table from the server and swaps it into the page, so all sorting and shuffling happens in Python and SQL.

## Rules your app must follow

Give this section to your coding agent.

1. Read the port from the first command-line argument and listen on `0.0.0.0`. Never hard-code a port.
2. Use relative URLs in links, forms and HTMX attributes: `hx_get="table"`, never `hx_get="/table"`. The app is served under a path prefix, so a leading slash points outside it.
3. Manage packages with uv only: `uv add PACKAGE`, then `uv sync`. Do not use `pip install` or conda. Run `uv sync` in JupyterLab before starting the app.
4. Keep everything the app needs in its own folder: code, `.venv` and data such as SQLite. Write full paths in the command, and do not use `cd ~` or paths relative to your home. The app sees only the folders its command names, and anything it writes elsewhere is lost when it stops.
5. Do not open the same SQLite file for writing from many processes at once.
6. Stopping JupyterLab does not stop the app.
7. A public app is open to the whole internet. Do not add forms or routes that write to your database or files unless the app checks who is logged in. Load and edit data from JupyterLab instead. Never run a debug server.
8. Never put secrets in the repository. Pass API keys as environment variables in the "Deploy App" form.
9. Logs: if the app does not start, open it from the hub home page; the start-up log shows the Python error. The most common causes are a wrong path in the command, a file outside the app folder, a missing `uv sync`, or a hard-coded port.
