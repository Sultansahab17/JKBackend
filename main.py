
from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import time

app = Flask(__name__)
CORS(app)

FREEPIK_API_KEY = "FPSX581c2cafb70ede3a4e04ab8e5b39772c"  # Replace with your real key
MYSTIC_URL = "https://api.freepik.com/v1/ai/mystic"
MYSTIC_RESULT_URL = "https://api.freepik.com/v1/ai/mystic/{}"

@app.route('/generate-image', methods=['POST'])
def generate_image():
    data = request.get_json()
    prompt = data.get("prompt")
    if not prompt:
        return jsonify({"error": "Missing prompt"}), 400

    headers = {
        "x-freepik-api-key": FREEPIK_API_KEY,
        "Content-Type": "application/json"
    }

    # Minimal payload for now (you can expand it later)
    payload = {
        "prompt": prompt,
        "structure_strength": 50,
        "adherence": 50,
        "hdr": 50,
        "resolution": "2k",
        "aspect_ratio": "square_1_1",
        "model": "realism",
        "creative_detailing": 33,
        "engine": "automatic",
        "fixed_generation": False,
        "filter_nsfw": True
    }

    try:
        # Step 1: Create task
        res = requests.post(MYSTIC_URL, headers=headers, json=payload)
        print("Create response:", res.status_code, res.text)
        res.raise_for_status()
        data = res.json()
        task_id = data.get("data", {}).get("task_id")

        if not task_id:
            return jsonify({"error": "No task_id received"}), 500

        # Step 2: Poll result
        for _ in range(90):  # Wait up to 90 seconds
            time.sleep(1)
            poll_url = MYSTIC_RESULT_URL.format(task_id)
            poll_res = requests.get(poll_url, headers=headers)
            print("Poll:", poll_res.status_code, poll_res.text)

            if poll_res.status_code == 404:
                continue

            poll_res.raise_for_status()
            result = poll_res.json()

            data_block = result.get("data", {})
            if data_block.get("status") == "COMPLETED":
                images = data_block.get("generated", [])
                if images:
                    print("✅ Image ready:", images[0])
                    return jsonify({"image_url": images[0]})
                else:
                    return jsonify({"error": "No image found in response"}), 500

        return jsonify({"error": "Image generation timed out"}), 504

    except Exception as e:
        print("Server Exception:", repr(e))
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5500)
