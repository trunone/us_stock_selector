import json

with open("asset_analysis.ipynb", "r") as f:
    nb = json.load(f)

for cell in nb.get("cells", []):
    if cell["cell_type"] == "code":
        source = cell["source"]
        for i, line in enumerate(source):
            if "                 try:\n" == line:
                source[i] = "                try:\n"
            if "                     close = df['Close'][top_pick]\n" == line:
                source[i] = "                    close = df['Close'][top_pick]\n"
            if "                 except KeyError:\n" == line:
                source[i] = "                except KeyError:\n"
            if "                     close = df['Close']\n" == line:
                source[i] = "                    close = df['Close']\n"

with open("asset_analysis.ipynb", "w") as f:
    json.dump(nb, f, indent=1)

