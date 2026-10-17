from flask import Flask, request, jsonify, render_template_string
import requests
import re
from bs4 import BeautifulSoup
from collections import OrderedDict

app = Flask(__name__)
# Configure JSON encoding to properly display emojis
app.config['JSON_AS_ASCII'] = False

# Define the copyright string without the Unicode escape sequence
COPYRIGHT_STRING = "@never_delete this source maker"

# Define the desired order of keys in the output
DESIRED_ORDER = [
    "Owner Name", "Father's Name", "Owner Serial No", "Model Name", "Maker Model",
    "Vehicle Class", "Fuel Type", "Fuel Norms", "Registration Date", "Insurance Company",
    "Insurance No", "Insurance Expiry", "Insurance Upto", "Fitness Upto", "Tax Upto",
    "PUC No", "PUC Upto", "Financier Name", "Registered RTO", "Address", "City Name", "Phone"
]

# ------------------- #
# VEHICLE INFO FETCHER#
# ------------------- #
def get_vehicle_details(rc_number: str) -> dict:
    rc = rc_number.strip().upper()

    headers = {
        "Host": "vahanx.in",
        "Connection": "keep-alive",
        "sec-ch-ua": "\"Chromium\";v=\"130\", \"Google Chrome\";v=\"130\", \"Not?A_Brand\";v=\"99\"",
        "sec-ch-ua-mobile": "?1",
        "sec-ch-ua-platform": "\"Android\"",
        "Upgrade-Insecure-Requests": "1",
        "User-Agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Mobile Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Referer": "https://vahanx.in/rc-search",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Accept-Language": "en-US,en;q=0.9"
    }

    try:
        session = requests.Session()
        search_page = session.get("https://vahanx.in/rc-search", headers=headers, timeout=10)
        search_page.raise_for_status()

        token_match = re.search(r'rc:\s*"([^"]+)"', search_page.text)
        if not token_match:
            return {"error": "Vehicle search service token was not found"}

        url = f"https://vahanx.in/rc-search/{rc}?t={token_match.group(1)}"
        response = session.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
    except requests.exceptions.RequestException as e:
        return {"error": f"Network error: {e}"}
    except Exception as e:
        return {"error": str(e)}

    def get_value(label):
        try:
            div = soup.find("span", string=label).find_parent("div")
            return div.find("p").get_text(strip=True)
        except AttributeError:
            return None

    data = {
        "Owner Name": get_value("Owner Name"),
        "Father's Name": get_value("Father's Name"),
        "Owner Serial No": get_value("Owner Serial No"),
        "Model Name": get_value("Model Name"),
        "Maker Model": get_value("Maker Model"),
        "Vehicle Class": get_value("Vehicle Class"),
        "Fuel Type": get_value("Fuel Type"),
        "Fuel Norms": get_value("Fuel Norms"),
        "Registration Date": get_value("Registration Date"),
        "Insurance Company": get_value("Insurance Company"),
        "Insurance No": get_value("Insurance No"),
        "Insurance Expiry": get_value("Insurance Expiry"),
        "Insurance Upto": get_value("Insurance Upto"),
        "Fitness Upto": get_value("Fitness Upto"),
        "Tax Upto": get_value("Tax Upto"),
        "PUC No": get_value("PUC No"),
        "PUC Upto": get_value("PUC Upto"),
        "Financier Name": get_value("Financier Name"),
        "Registered RTO": get_value("Registered RTO"),
        "Address": get_value("Address"),
        "City Name": get_value("City Name"),
        "Phone": get_value("Phone")
    }

    detail_keys = (
        "Owner Name",
        "Model Name",
        "Registration Date",
        "Vehicle Class",
        "Fuel Type",
    )
    if not any(data[key] is not None for key in detail_keys):
        return {"error": "Vehicle details were not found for this registration number"}

    return data


# ------------------- #
# API ROUTES          #
# ------------------- #

@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "message": "🚗 Vehicle Info API by Mohd Kaif is running!",
        "developer": COPYRIGHT_STRING
    })


@app.route("/ui", methods=["GET"])
def vehicle_ui():
    return render_template_string("""
<!doctype html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Vehicle Info Lookup</title>
    <style>
        :root { color-scheme: light; font-family: Arial, sans-serif; }
        body { margin: 0; background: #f3f4f6; color: #1f2937; }
        main { max-width: 760px; margin: 48px auto; padding: 0 16px; }
        .card { background: white; border-radius: 12px; padding: 24px;
                box-shadow: 0 4px 18px rgb(0 0 0 / 10%); }
        h1 { margin-top: 0; font-size: 1.6rem; }
        form { display: flex; gap: 10px; }
        input, button { border: 1px solid #d1d5db; border-radius: 7px;
                        font-size: 1rem; padding: 11px 12px; }
        input { flex: 1; text-transform: uppercase; }
        button { border-color: #2563eb; background: #2563eb; color: white;
                 cursor: pointer; }
        button:disabled { cursor: wait; opacity: .7; }
        #status { min-height: 24px; margin: 18px 0 8px; }
        .error { color: #b91c1c; }
        .result { overflow-x: auto; }
        table { width: 100%; border-collapse: collapse; }
        td { border-bottom: 1px solid #e5e7eb; padding: 10px 6px;
             text-align: left; vertical-align: top; }
        td:first-child { color: #4b5563; font-weight: 600; width: 38%; }
        @media (max-width: 520px) {
            form { flex-direction: column; }
            button { width: 100%; }
        }
    </style>
</head>
<body>
<main>
    <section class="card">
        <h1>Vehicle Info Lookup</h1>
        <form id="lookup-form">
            <input id="rc" name="rc" placeholder="e.g. DL01AB1234"
                   autocomplete="off" required>
            <button id="submit" type="submit">Search</button>
        </form>
        <div id="status" role="status" aria-live="polite"></div>
        <div id="result" class="result"></div>
    </section>
</main>
<script>
const form = document.getElementById("lookup-form");
const input = document.getElementById("rc");
const button = document.getElementById("submit");
const status = document.getElementById("status");
const result = document.getElementById("result");

form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const rc = input.value.trim();
    if (!rc) return;

    button.disabled = true;
    status.className = "";
    status.textContent = "Searching...";
    result.replaceChildren();

    try {
        const response = await fetch(`/lookup?rc=${encodeURIComponent(rc)}`);
        const data = await response.json();
        if (!response.ok || data.error) {
            throw new Error(data.error || "Lookup failed");
        }

        const table = document.createElement("table");
        for (const [label, value] of Object.entries(data)) {
            if (label === "copyright" || value === null || value === "") continue;
            const row = table.insertRow();
            const keyCell = row.insertCell();
            const valueCell = row.insertCell();
            keyCell.textContent = label;
            valueCell.textContent = value;
        }
        result.appendChild(table);
        status.textContent = "Vehicle details found.";
    } catch (error) {
        status.className = "error";
        status.textContent = error.message;
    } finally {
        button.disabled = false;
    }
});
</script>
</body>
</html>
    """)


@app.route("/lookup", methods=["GET"])
def lookup_vehicle():
    rc_number = request.args.get("rc")
    if not rc_number:
        return jsonify({
            "error": "Please provide ?rc= parameter",
            "copyright": COPYRIGHT_STRING
        }), 400

    details = get_vehicle_details(rc_number)
    if "error" in details:
        return jsonify(details), 502
    
    # Create an ordered dictionary with the desired sequence
    ordered_details = OrderedDict()
    
    # Add keys in the desired order
    for key in DESIRED_ORDER:
        if key in details:
            ordered_details[key] = details[key]
    
    # Add copyright at the end
    ordered_details["copyright"] = COPYRIGHT_STRING
    
    return jsonify(ordered_details)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)