import json

with open("asset_analysis.ipynb", "r") as f:
    nb = json.load(f)

for cell in nb.get("cells", []):
    if cell["cell_type"] == "code":
        source = cell["source"]
        
        # Imports
        for i, line in enumerate(source):
            if "import io\n" in line or "import time\n" in line:
                source[i] = ""
        
        # Read CSV footer
        for i, line in enumerate(source):
            if "pd.read_csv(" in line and "nasdaqtraded.txt" in source[i-2]:
                source[i] = source[i].replace("pd.read_csv(url, sep='|')", "pd.read_csv(url, sep='|', skipfooter=1, engine='python')")
                
        # Batch size
        for i, line in enumerate(source):
            if "BATCH_SIZE = 100\n" in line:
                source[i] = "batch_size = 100\n"
            if "BATCH_SIZE" in line:
                source[i] = source[i].replace("BATCH_SIZE", "batch_size")

        # Strip empty lines from removed imports
        cell["source"] = [s for s in source if s != ""]

with open("asset_analysis.ipynb", "w") as f:
    json.dump(nb, f, indent=1)

